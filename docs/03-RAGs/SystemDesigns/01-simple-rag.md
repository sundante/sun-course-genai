# System Design: Simple RAG Pipeline

> **Domain:** Enterprise Knowledge Base · **Pattern:** Naive → Production-Grade RAG
>
> ← [Back to RAG Concepts](../Notes/01-RAG-Fundamentals.md) | [RAG Types & Advanced Patterns →](../Notes/05-RAG-Types-and-Advanced-Patterns.md)

---

## Interview Problem Statement

> **"Design a production-grade RAG system that enables employees to query a company's internal knowledge base of 5 million documents (PDFs, Word, HTML) and receive accurate, cited answers in under 3 seconds at 1,000 concurrent users."**

---

## Clarifying Questions

| Question | Why It Matters |
|---|---|
| What document types? (PDF, Word, HTML, scanned images?) | Determines parsers needed — scanned PDFs require OCR (Document AI) |
| Expected query types? (factual lookup, comparison, summarization?) | Factual → top-3 chunks sufficient; summarization → may need 20+ chunks |
| What is the acceptable hallucination rate? (0%? <5%?) | Drives need for guardrails, grounding checks, citation enforcement |
| Does freshness matter? (new docs within minutes, hours, or daily batch?) | Real-time → streaming ingestion; batch is fine → scheduled pipelines |
| Is PII present in documents? | Drives redaction pipeline before chunking and logging controls |
| Multi-language support needed? | Affects embedding model choice (multilingual models vs. per-language indexes) |
| Is the query population internal employees or external users? | Security perimeter, auth model, and rate limiting design |

---

## System Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           INGESTION PIPELINE                                 │
│                                                                              │
│  Cloud Storage (raw docs)                                                    │
│       │                                                                      │
│       ▼                                                                      │
│  Cloud Run: Document Parser                                                  │
│  ┌─────────────────────────────────────────────────────────┐                │
│  │  PDF → Document AI (OCR + layout)                       │                │
│  │  Word/HTML → python-docx / BeautifulSoup                │                │
│  │  Output: cleaned text + metadata JSON                   │                │
│  └─────────────────────────────────────────────────────────┘                │
│       │                                                                      │
│       ▼                                                                      │
│  Cloud Tasks Queue (back-pressure management)                                │
│       │                                                                      │
│       ▼                                                                      │
│  Cloud Run: Chunker + Embedder                                               │
│  ┌─────────────────────────────────────────────────────────┐                │
│  │  Semantic chunking (512 tokens, 10% overlap)            │                │
│  │  Vertex AI text-embedding-005 → 768-dim vectors         │                │
│  │  Metadata: doc_id, chunk_id, source_url, date, section  │                │
│  └─────────────────────────────────────────────────────────┘                │
│       │                                                                      │
│       ├─────────────────────┬──────────────────────────────┤                │
│       ▼                     ▼                              ▼                │
│  Vertex AI Vector      AlloyDB (BM25         BigQuery (metadata            │
│  Search (ANN)          sparse index)         + eval logging)               │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                            QUERY PIPELINE                                    │
│                                                                              │
│  User Query                                                                  │
│       │                                                                      │
│       ▼                                                                      │
│  API Gateway → Cloud Run: Query Service                                      │
│  ┌─────────────────────────────────────────────────────────┐                │
│  │  1. Auth check (IAP or OAuth2)                          │                │
│  │  2. Query embedding (text-embedding-005)                │                │
│  │  3. Check Memorystore (Redis) semantic cache            │                │
│  └─────────────────────────────────────────────────────────┘                │
│                   │  (cache miss)                                            │
│                   ▼                                                          │
│  ┌─────────────────────────────────────────────────────────┐                │
│  │  HYBRID RETRIEVAL                                        │                │
│  │                                                          │                │
│  │  Dense:  Vertex AI Vector Search → top-20 chunks        │                │
│  │  Sparse: AlloyDB full-text (BM25) → top-20 chunks       │                │
│  │  Fusion: Reciprocal Rank Fusion → top-5                 │                │
│  │  Rerank: Vertex AI Reranker (cross-encoder) → top-3     │                │
│  └─────────────────────────────────────────────────────────┘                │
│                   │                                                          │
│                   ▼                                                          │
│  ┌─────────────────────────────────────────────────────────┐                │
│  │  GENERATION                                              │                │
│  │                                                          │                │
│  │  Prompt assembly: system + context + query              │                │
│  │  Vertex AI Gemini 1.5 Pro → answer + citations          │                │
│  │  Grounding check: Vertex AI Grounding API               │                │
│  │  Citation extraction: source_url per claim              │                │
│  └─────────────────────────────────────────────────────────┘                │
│                   │                                                          │
│                   ▼                                                          │
│  Response → User + log to BigQuery (for eval/feedback)                      │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Design

### 1. Document Ingestion

**Trigger:** New file lands in Cloud Storage bucket → Eventarc → Cloud Run parser job.

**Parser decisions:**
- Native PDF (text layer present) → `pdfplumber` / `pypdf` — fast, no API cost
- Scanned PDF / image PDFs → Document AI (Form Parser or Document OCR) — preserves layout, tables
- Word/PPTX → `python-docx`, `python-pptx` — extract paragraphs + headings
- HTML → `BeautifulSoup` with `boilerpy3` to strip navigation/ads

**Metadata enriched at parse time:**
```json
{
  "doc_id": "uuid",
  "source_path": "gs://bucket/hr/policies/pto-policy-v3.pdf",
  "title": "PTO Policy v3",
  "section": "Human Resources",
  "author": "HR Team",
  "created_date": "2024-01-15",
  "last_modified": "2024-11-01",
  "language": "en",
  "page_count": 12
}
```

---

### 2. Chunking Strategy

**Why this matters:** Chunk size is the single biggest quality lever in RAG.

| Strategy | Chunk Size | Use Case |
|---|---|---|
| Fixed-token | 256–512 tokens | Simple factual docs, uniform structure |
| Semantic (sentence-boundary) | Variable 200–600 tokens | Prose documents, policies, articles |
| Parent-child hierarchical | Parent: 1024 / Child: 256 | When you need summary retrieval + precise citation |
| Document-level | Full doc | Short docs (<2k tokens), global summarization |

**Recommended for this system:** Semantic chunking (512 token target, 50-token overlap) using `sentence-transformers` sentence boundary detection. Store both the child chunk (for retrieval) and a parent context window (±1 paragraph, for generation).

---

### 3. Embedding + Vector Index

**Embedding model:** `text-embedding-005` (Vertex AI)
- 768 dimensions
- Optimized for retrieval tasks
- Batched at 250 docs/batch via Cloud Tasks

**Index:** Vertex AI Vector Search
- Algorithm: ScaNN (Scalable Nearest Neighbor) — tree-AH hybrid
- Recall target: 98% at top-10
- Shards: 5 (5M docs ÷ 1M per shard)
- Online updates enabled for near-real-time ingestion

**Fallback sparse index:** AlloyDB `tsvector` column + GIN index for BM25 keyword search. Critical for queries with rare proper nouns, product codes, and acronyms that embedding models underrepresent.

---

### 4. Hybrid Retrieval + Reranking

```
Dense:  score_dense  = cosine_similarity(q_emb, chunk_emb)
Sparse: score_sparse = BM25(q_tokens, chunk_tokens)

RRF fusion:
  rrf_score(d) = Σ 1 / (k + rank_i(d))   where k=60
  
  Final ranking: top-5 by rrf_score

Reranker:
  Cross-encoder: Vertex AI Reranker API
  Input: (query, chunk_text) → relevance score 0–1
  Keep: top-3 chunks above threshold 0.4
```

**Why rerank after RRF?** RRF is an unsupervised fusion — it can elevate lexically-matching but semantically-shallow chunks. A cross-encoder cross-attends between query and full chunk text and produces calibrated relevance scores.

---

### 5. Generation

**Prompt template:**
```
You are a knowledgeable assistant for [Company] employees.
Answer the question below using ONLY the provided context.
If the answer is not in the context, say "I don't have that information."
Cite each claim with [Source N] notation.

Context:
[1] {chunk_1_text} (Source: {source_url_1})
[2] {chunk_2_text} (Source: {source_url_2})
[3] {chunk_3_text} (Source: {source_url_3})

Question: {user_query}

Answer:
```

**Model:** Gemini 1.5 Pro (128k context window — fits 3-10 chunks comfortably, no lost-in-middle risk at this scale)

**Grounding check:** Vertex AI Grounding API validates that each sentence in the answer is attributable to the provided context. Claims without grounding are flagged.

---

## GCP Services Map

| Component | GCP Service | Why |
|---|---|---|
| Raw document storage | Cloud Storage | Durable, cheap, Eventarc integration |
| Document parsing (scanned) | Document AI (OCR / Form Parser) | Layout-aware OCR, table extraction |
| Parse/chunk/embed jobs | Cloud Run (CPU jobs) | Serverless, scales to 0, 1000 concurrent |
| Job queue / back-pressure | Cloud Tasks | Rate limits API calls, retries failures |
| Embedding model | Vertex AI text-embedding-005 | Low-latency, 768-dim, GCP-native |
| Vector index | Vertex AI Vector Search | Managed ANN, online updates, SLA |
| Keyword index | AlloyDB for PostgreSQL (pgvector + tsvector) | Hybrid: vector + BM25 in one store |
| Reranker | Vertex AI Reranker API | Cross-encoder, no self-hosting overhead |
| LLM generation | Vertex AI Gemini 1.5 Pro | 128k context, grounding support |
| Grounding validation | Vertex AI Grounding API | Attribution and hallucination guard |
| Semantic cache | Memorystore for Redis (7.x) | Vector similarity cache on query embedding |
| Auth | Identity-Aware Proxy (IAP) | Internal employee auth, no code changes |
| API frontend | API Gateway + Cloud Run | Rate limiting, auth, versioning |
| Logging | Cloud Logging + BigQuery | Structured logs, RAGAS eval dataset |
| Monitoring | Cloud Monitoring + Trace | Latency percentiles, error rates |
| CI/CD | Cloud Build + Artifact Registry | Automated embed pipeline deployments |

---

## Scalability Considerations

### Throughput: 1,000 Concurrent Users

**Bottleneck analysis:**

| Stage | Latency (P99) | Parallelizable? | Mitigation |
|---|---|---|---|
| Query embedding | 20ms | Yes (stateless) | Cloud Run autoscale |
| Cache lookup | 5ms | Yes | Redis cluster mode |
| Vector search | 80ms | Yes | Vector Search handles concurrency |
| Sparse search | 30ms | Yes | AlloyDB read replicas |
| Reranking | 50ms | Yes (batched) | Reranker API auto-scales |
| Generation (Gemini) | 800–1500ms | Yes | Vertex AI handles quota per project |
| **Total P99** | **~2.5s** | — | Within 3s SLA |

**Scaling levers:**
- Cloud Run: `--min-instances=10` to prevent cold starts under load
- Memorystore: 10–20% of queries hit cache after 24h warm-up (semantic cache)
- Vector Search: add shards as corpus grows beyond 5M docs
- Gemini quota: request higher TPM limits via GCP support for production

### Corpus Scale: Beyond 5M Documents

| Corpus Size | Vector Search Config | Embedding Cost | Strategy |
|---|---|---|---|
| <1M | Single shard, DiskANN | Low | Simple |
| 1M–10M | 5–10 shards, ScaNN | Moderate | Shard by department/domain |
| 10M–100M | 50+ shards + index versioning | High | Domain-specific sub-indexes + routing |
| 100M+ | Multi-index with pre-filter | Very High | Metadata filtering before ANN search |

**Domain partitioning:** Split indexes by department (HR, Legal, Engineering). Query router classifies department from query → hits targeted sub-index. Reduces search space 10x, improves recall.

### Freshness: Near-Real-Time Updates

Vertex AI Vector Search supports online index updates (upsert/delete) without reindexing. For batch ingestion of 100k docs/day:
- Cloud Tasks queue with 50 concurrent workers
- Each worker: parse → chunk → embed (batched 250/call) → upsert to Vector Search
- Throughput: ~20k chunks/minute, 100k docs ingested within 2–3 hours

### Cost Optimization

| Lever | Saving |
|---|---|
| Semantic cache (Redis) | 15–20% LLM cost reduction |
| Batch embedding during off-hours | 50% cheaper with committed use discounts |
| Gemini Flash for simple factual queries | 5× cheaper than Pro, detect via query classifier |
| Index compression (PQ in Vector Search) | 4× storage reduction, ~3% recall tradeoff |

---

## Failure Modes and Mitigations

| Failure | Symptom | Mitigation |
|---|---|---|
| Hallucination | Answer not grounded in context | Grounding API check + fallback "I don't know" |
| Retrieval miss | Right doc exists but not returned | Hybrid retrieval (sparse catches what dense misses) |
| Chunk boundary splits key fact | Incomplete context | 50-token overlap + parent-child retrieval |
| Stale index | New doc not yet indexed | Show doc freshness timestamp; warn if >24h old |
| LLM context overflow | Long docs exceed context window | Chunk top-3 only; limit to 6k tokens context |
| Toxic/injection query | Prompt injection in user query | Input sanitization + Vertex AI safety filters |

---

## Q&A Review Bank

**Q1: A user complains that a critical answer "isn't in the system" even though you can manually find it in a document. What are the top 3 causes and how do you diagnose each?** `[Hard]`

A: (1) **Embedding model mismatch** — the document uses domain-specific terminology (e.g., "SOX compliance audit cycle") that the embedding model encodes differently than the user's query ("financial audit timeline"). Diagnose by running the query against BM25 alone — if BM25 finds it but vector search doesn't, it's a semantic gap. Fix: domain-adapted embedding or expand query with HyDE. (2) **Chunking boundary problem** — the key fact spans two chunks and neither chunk alone contains enough context for a high similarity score. Diagnose by inspecting which chunk contains the sentence. Fix: increase overlap, or use parent-child retrieval where the parent chunk contains the full context. (3) **Metadata filtering too aggressive** — a pre-filter by department/date excluded the relevant document. Diagnose by running without filters. Fix: broaden filter logic or remove it for fallback queries.

---

**Q2: Why is hybrid retrieval (dense + sparse) better than dense-only retrieval, and when does sparse search have a structural advantage?** `[Medium]`

A: Dense (embedding) search excels at semantic similarity — it finds chunks that mean the same thing even with different words. Sparse (BM25) search excels at exact-match retrieval — it finds documents containing the exact query tokens, which is critical for product codes, acronyms, proper nouns, and rare technical terms that embedding models compress into similar vectors as related-but-wrong concepts. Example: query "CVE-2024-1234 vulnerability" — a dense model may retrieve general "vulnerability management" content; BM25 will pinpoint the exact CVE document because it exact-matches the token. Hybrid search with RRF combines both signals without requiring a learned fusion model, making it robust to distributional shifts in the query population.

---

**Q3: How does the semantic cache work and what are the failure modes introduced by caching RAG responses?** `[Hard]`

A: The semantic cache stores `(query_embedding → cached_response)` pairs in Redis. On each new query, its embedding is computed and a nearest-neighbor lookup in the cache checks whether a "similar enough" prior query has been answered (typically cosine similarity > 0.95). If yes, the cached response is returned without hitting Vector Search or the LLM. Failure modes: (1) **Stale cache** — if the underlying document is updated after the cache entry was created, the cached answer is outdated. Fix: short TTL (1–4 hours) or invalidate on document update. (2) **Similarity threshold too low** — different questions get the same answer (e.g., "Who is the CEO?" vs "Who is the CFO?" may have embeddings close enough to hit the same cache entry). Fix: tighten threshold to 0.98+. (3) **Cache pollution** — rare or malicious queries poison cache slots. Fix: only cache queries above a minimum frequency threshold.

---

**Q4: Design the latency budget for a 3-second P99 SLA. Which stage is the most dangerous and why?** `[Hard]`

A: Budget breakdown: auth (20ms) → query embedding (20ms) → cache lookup (5ms) → vector search (80ms) → sparse search (30ms) → RRF fusion (5ms) → reranking (50ms) → prompt assembly (5ms) → Gemini generation (800–1500ms P99) → response serialization (10ms) = ~1.5–2.2s under normal load. The **generation stage is most dangerous** because it's the only stage that doesn't scale horizontally in a way you control — it depends on Gemini API P99 latency which can spike under shared infrastructure load. Mitigations: (1) semantic cache to skip generation for repeated queries; (2) Gemini Flash for short factual queries (3× faster); (3) streaming responses so users perceive faster response even if total latency is 3s; (4) timeout budget of 2s for generation with fallback to "Please try again."

---

**Q5: A regulatory audit requires you to prove that every answer the system gave was grounded in a specific document version. How do you design for this?** `[Hard]`

A: Three layers of auditability needed: (1) **Document versioning** — every document in Cloud Storage is versioned (Object Versioning enabled). Each chunk stores `doc_id + version_hash` as metadata. When a document is updated, old chunks are soft-deleted (marked `archived: true`) rather than deleted, so historical retrievals can be reconstructed. (2) **Query logging** — every query logs to BigQuery: `query_id, user_id, timestamp, query_text, retrieved_chunk_ids (with version_hash), prompt_sent_to_llm, llm_response, grounding_score`. This creates a complete audit trail. (3) **Grounding verification** — the Vertex AI Grounding API response includes which sentences are attributed to which source segments. This response is logged alongside the answer. An auditor can replay the query, retrieve the same versioned chunks, and verify the answer was derivable from those specific document versions.

---

**Q6: Compare Vertex AI Vector Search vs. AlloyDB pgvector for this use case. When would you choose each?** `[Medium]`

A: Vertex AI Vector Search is a dedicated ANN service — it handles billion-scale corpora, online index updates, and ~80ms P99 at scale with no operational overhead. It's the right choice when vector search is your primary query pattern and you need managed scaling. AlloyDB pgvector runs vector search as a PostgreSQL extension — you get SQL joins between vector results and structured metadata in the same query (e.g., `WHERE department = 'HR' AND cosine_similarity > 0.8`). It's the right choice when your retrieval requires complex metadata joins, when corpus size is <10M docs, or when you want hybrid BM25 + vector in one query. For this system: use both in tandem — Vector Search for high-throughput dense retrieval; AlloyDB for sparse BM25 and metadata-filtered lookups. The hybrid retrieval layer fuses results from both.

---

**Q7: What is "lost-in-the-middle" and how do you mitigate it in this system?** `[Medium]`

A: Lost-in-the-middle is the empirically-observed degradation in LLM attention on context chunks placed in the middle of a long context window — information in positions 2 through N-1 is less well-utilized than the first and last chunks. For a 3-chunk RAG context, this is minimal, but for 10+ chunks it significantly degrades answer quality. Mitigations: (1) **Limit to 3–5 chunks** — enforce a hard cap on context size, relying on the reranker to surface only the most relevant. (2) **Positional priority** — place the highest-relevance chunk first and second, not in the middle. (3) **Summary-then-detail** — prepend a 2-sentence summary of each chunk before the full text, giving the model anchor points. (4) **Gemini 1.5 Pro's 128k window** — while the problem exists, it's less severe in Gemini 1.5 than earlier models, which exhibited sharper degradation at the 4–8k mark.
