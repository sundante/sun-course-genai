# RAG System Design

This is the highest-leverage section for Google/Amazon interviews. Every system design question about RAG follows the same structure — learn to decompose it into components, draw the two pipelines, and then drill into trade-offs.

---

## Interview Framework: How to Approach Any RAG System Design

When an interviewer asks "Design a RAG system for X," structure your answer in 5 minutes:

```
1. Clarify requirements  (2 min)
   - Scale: How many documents? How many QPS?
   - Latency SLA: p95 under how many seconds?
   - Freshness: How often does content change?
   - Quality: Precision vs recall vs cost trade-off?
   - Multi-tenancy: One corpus or per-tenant isolation?

2. Draw two pipelines  (3 min)
   - Ingest (offline): how documents get into the system
   - Query (online): how user questions get answered

3. Drill into each component  (5 min)
   - Chunking strategy
   - Embedding model choice
   - Vector DB choice + configuration
   - Retrieval strategy (dense / hybrid / rerank)
   - Prompt design

4. Discuss trade-offs  (3 min)
   - Latency vs quality
   - Cost vs accuracy
   - Freshness vs stability

5. Production concerns  (2 min)
   - Monitoring: what metrics do you watch?
   - Failure modes: what breaks first at scale?
```

---

## Full Production Architecture

```
INGEST PIPELINE (offline / async)
─────────────────────────────────────────────────────────────────────
Data Sources                Document Processor         Vector Store
(S3, GCS, SharePoint,  →  [Loader → Extract →  →  [Upsert vectors
 Confluence, database)      Clean → Chunk →             + metadata]
                            Embed]
                               ↕
                         Queue (Pub/Sub, SQS)
                         for async processing

QUERY PIPELINE (online / synchronous, user-facing)
─────────────────────────────────────────────────────────────────────
User query
    ↓
[Query Preprocessing]         ← query rewrite / expand / classify
    ↓
[Cache Layer]                 ← semantic cache (Redis + vector search)
    ↓ (cache miss)
[Retriever]                   ← hybrid (dense + BM25) → top-20 candidates
    ↓
[Reranker]                    ← cross-encoder → top-4 chunks
    ↓
[Context Assembly]            ← format chunks + metadata citations
    ↓
[LLM Generation]              ← Gemini / GPT-4 with grounding prompt
    ↓
[Post-processing]             ← citation formatting, PII scrubbing
    ↓
Answer + Source Citations

FEEDBACK LOOP (async)
─────────────────────────────────────────────────────────────────────
[User Feedback] → [Eval Store] → [Quality Metrics] → [Trigger Re-index / Rerank Tuning]
```

---

## Ingest Pipeline Design

### Concept

The ingest pipeline runs offline or on a schedule. It's the foundation — errors here propagate silently to all future queries.

**Stages:**

**1. Document Loading**
Different document types require different loaders:
- PDFs: `PyPDFLoader`, `pymupdf` (better for complex layouts), or cloud services (Google Document AI, AWS Textract) for scanned PDFs
- HTML: `BeautifulSoupTransformer`, `Trafilatura` (extracts clean content, ignores nav/footer)
- DOCX/PPTX: `Docx2txtLoader`, `python-pptx`
- Databases: custom SQL queries → structured rows → templated text

**2. Document Cleaning**
Remove: HTML tags, page numbers, headers/footers, boilerplate legal text, repeated disclaimers. Extract: meaningful metadata (title, author, date, section, URL) for later filtering.

**3. Chunking**
(see file 03 for full details). Default: `RecursiveCharacterTextSplitter`, 500 chars, 50 overlap. For domain-specific: semantic chunking.

**4. Embedding**
Batch embed chunks. CRITICAL: batch size matters — most embedding APIs accept 100-2048 texts per call. Batching 1 text at a time is 100x slower and 100x more expensive.

**5. Upsert**
Write (vector, metadata, document_id) to vector DB. Handle:
- **De-duplication**: hash chunk content, skip if hash exists
- **Updates**: when a document changes, delete old vectors by document_id, re-embed, re-upsert

### Code

```python
import hashlib
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader

def ingest_document(file_path: str, source_id: str, vectorstore: Chroma):
    # Load
    loader = PyPDFLoader(file_path)
    docs = loader.load()
    
    # Clean and add metadata
    for doc in docs:
        doc.metadata["source_id"] = source_id
        doc.metadata["ingested_at"] = datetime.utcnow().isoformat()
    
    # Chunk
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)
    
    # De-duplicate: skip chunks already in index
    new_chunks = []
    for chunk in chunks:
        content_hash = hashlib.md5(chunk.page_content.encode()).hexdigest()
        if not chunk_exists(vectorstore, content_hash):
            chunk.metadata["content_hash"] = content_hash
            new_chunks.append(chunk)
    
    # Batch embed + upsert (batches of 100)
    for i in range(0, len(new_chunks), 100):
        batch = new_chunks[i:i+100]
        vectorstore.add_documents(batch)
    
    print(f"Ingested {len(new_chunks)} new chunks from {source_id}")

def update_document(source_id: str, vectorstore: Chroma):
    # Delete all vectors for this source, then re-ingest
    vectorstore.delete(where={"source_id": source_id})
    ingest_document(new_file_path, source_id, vectorstore)
```

---

## Query Pipeline: Latency Budget

### Concept

For a p95 latency SLA of 2 seconds, you need to budget time across each stage:

| Stage | Typical Latency | Notes |
|---|---|---|
| Query preprocessing (rewrite) | 200-400ms | Optional — skip if query is clear |
| Cache lookup | 5-20ms | Redis or in-memory |
| Query embedding | 10-30ms | Cached if same query |
| ANN search (dense) | 5-20ms | HNSW at k=20 |
| BM25 search | 2-10ms | In-memory |
| RRF merge | <1ms | Trivial computation |
| Cross-encoder rerank | 80-200ms | 20 pairs × ~8ms each |
| LLM generation | 800-1500ms | First token; streaming hides this |
| **Total (optimistic)** | **~900ms** | With caching + fast LLM |
| **Total (pessimistic)** | **~2200ms** | Without caching, with rewrite |

**Optimization hierarchy (biggest wins first):**
1. **Semantic caching** — deduplicate near-identical queries (30-60% hit rate for customer support)
2. **Skip reranking for high-confidence retrievals** — if top BM25 and top dense agree, skip cross-encoder
3. **Smaller reranker model** — `MiniLM-L-6-v2` (6-layer) is 3x faster than `L-12-v2` at ~80% quality
4. **Streaming LLM output** — stream tokens immediately; users perceive faster responses
5. **Pre-computed query embeddings cache** — hash query string, cache embedding for 24h

### Code

```python
import hashlib, json
import redis

cache = redis.Redis(host="localhost", port=6379)
CACHE_TTL = 3600  # 1 hour

def semantic_cache_lookup(query: str, threshold: float = 0.95) -> str | None:
    """Check if a semantically similar query was answered recently."""
    query_vec = embeddings.embed_query(query)
    
    # Check vector similarity against cached query embeddings
    cached_queries = cache.keys("rag_cache:*")
    for key in cached_queries[:100]:  # limit lookup to 100 recent queries
        cached = json.loads(cache.get(key))
        sim = cosine_similarity(query_vec, cached["query_vec"])
        if sim >= threshold:
            return cached["answer"]
    return None

def cache_answer(query: str, query_vec: list[float], answer: str):
    key = f"rag_cache:{hashlib.md5(query.encode()).hexdigest()}"
    cache.setex(key, CACHE_TTL, json.dumps({
        "query": query,
        "query_vec": query_vec,
        "answer": answer
    }))
```

---

## Scalability: Designing for 100M+ Documents

### Concept

At 100M documents, several assumptions of standard RAG break. Here's how to handle each:

**1. Index size**
100M documents × 500 chars avg × 1.2 chunks/doc = 120M chunks
120M chunks × 768 floats × 4 bytes = ~369 GB — won't fit in memory on a single machine.

Solution: **IVF (Inverted File Index)** + optionally PQ compression, OR distributed vector DB (Vertex AI Vector Search, Pinecone, Qdrant distributed mode).

**2. Query throughput (QPS)**
A single vector DB node handles ~500-2000 QPS. At 10K QPS, you need horizontal scaling.

Solution: **Read replicas** — the vector index is read-heavy; create multiple read replicas. Queries are load-balanced across replicas.

**3. Write throughput (ingestion rate)**
Re-indexing 100M documents is not feasible in real-time. 

Solution: **Write-ahead log** — new documents go to a write log; a background job merges them into the main index on a schedule. Queries search both the main index and the recent write log (union of results).

**4. Sharding**
Two strategies:
- **Document-based sharding**: shard by document source, category, or date range. Queries route to the relevant shard(s). Requires a routing layer.
- **Hash-based sharding**: distribute vectors uniformly by ID hash. All queries fan out to all shards. Simpler but all shards participate in every query.

**5. Multi-region**
For global products, replicate the index to multiple regions. Use eventual consistency for index updates — slight staleness (seconds to minutes) is acceptable for most RAG use cases.

```
Architecture for 100M documents:
┌─────────────────────────────────────────────────────────────┐
│  Ingest Service (Cloud Run)                                 │
│  ├─ Doc processor × 10 workers (async, Pub/Sub queue)       │
│  └─ Batch embedding (text-embedding-004, batch=512)         │
│                      ↓                                      │
│  Vertex AI Vector Search (managed HNSW, auto-scaled)        │
│  ├─ Index: 120M vectors, 768-dim, cosine                    │
│  ├─ Read replicas: 3 (auto-scaled based on QPS)             │
│  └─ Deployed endpoint: http call → top-k                    │
│                      ↓                                      │
│  Query Service (Cloud Run, min-instances=3)                 │
│  ├─ Semantic cache (Cloud Memorystore Redis)                 │
│  ├─ Hybrid search (Vector Search + BM25 on Elasticsearch)   │
│  ├─ Reranker (MiniLM deployed on Cloud Run GPU)             │
│  └─ Gemini API for generation                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Caching Strategies

### Concept

Three caching layers, each with different hit rates and complexity:

**1. Query embedding cache**
- Cache: query_text → embedding_vector
- TTL: 24 hours
- Hit rate: ~40-70% (many users ask the same question)
- Cost savings: eliminates repeated embedding API calls

**2. Semantic result cache**
- Cache: (query_embedding, filters) → (retrieved_chunks, answer)
- Uses vector similarity to find "close enough" cached queries (threshold ~0.95)
- TTL: 30-60 minutes (balance freshness vs hit rate)
- Hit rate: ~30-60% for customer support, ~10-20% for open-domain
- Implementation: GPTCache, Redis + FAISS, or Qdrant as cache store

**3. LLM response cache**
- Cache: exact prompt hash → LLM response
- TTL: 5-30 minutes
- Only useful for deterministic prompts (temperature=0)
- Hit rate: very low for open-ended queries; high for templated reports

---

## Index Freshness

### Concept

How quickly do changes in source documents appear in the RAG system?

**Batch re-indexing** (simplest):
- Schedule: nightly or weekly
- Freshness: up to 24h stale
- Use when: content changes slowly (annual reports, product documentation)

**Event-driven incremental updates** (real-time):
- Trigger: document change event (Pub/Sub, Webhooks)
- Freshness: seconds to minutes
- Process: extract changed doc → re-chunk → re-embed → update vector DB (delete old, insert new)
- Complexity: need to handle document versioning and ID-based deletion

**Hybrid (write-ahead log)**:
- New/changed documents go to a "hot" index (small, always fresh)
- Large corpus stays in "cold" index (stale by hours)
- Query searches both indices, merges results
- Best balance of cost and freshness

### Code

```python
# Event-driven update using Pub/Sub
from google.cloud import pubsub_v1
import json

subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(project_id, "doc-updates-sub")

def process_update_message(message):
    event = json.loads(message.data.decode())
    doc_id = event["document_id"]
    action = event["action"]  # "created", "updated", "deleted"
    
    if action == "deleted":
        vectorstore.delete(where={"doc_id": doc_id})
    elif action in ("created", "updated"):
        if action == "updated":
            vectorstore.delete(where={"doc_id": doc_id})
        new_doc = fetch_document(doc_id)
        ingest_document(new_doc, doc_id, vectorstore)
    
    message.ack()

streaming_pull_future = subscriber.subscribe(subscription_path, callback=process_update_message)
```

---

## Failure Handling and Graceful Degradation

### Concept

Production RAG systems must handle partial failures gracefully. The user should always get an answer, even if degraded.

**Failure hierarchy:**
```
Vector DB unavailable
    → Fallback to BM25-only (Elasticsearch / in-memory index)
    → If BM25 also unavailable → fallback to LLM with no context + uncertainty disclaimer

Embedding model API unavailable
    → If query embedding fails → serve stale cache if available
    → If no cache → fallback to BM25

LLM API rate limited / unavailable
    → Queue request, return "processing" response
    → For synchronous requirement → switch to smaller/faster fallback model

Reranker unavailable
    → Skip reranking, use first-stage retrieval order
    → Monitor precision drop in downstream metrics
```

**Circuit breaker pattern:**
Wrap each external dependency (embedding API, vector DB, LLM) in a circuit breaker. If error rate exceeds threshold (e.g., 5% in 60 seconds), open the circuit and immediately serve fallback responses. Reset after a probe interval.

```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60, expected_exception=Exception)
def embed_with_circuit_breaker(query: str) -> list[float]:
    return embeddings.embed_query(query)

@circuit(failure_threshold=10, recovery_timeout=30, expected_exception=Exception)
def vector_search_with_circuit_breaker(query_vec: list[float], k: int) -> list:
    return vectorstore.similarity_search_by_vector(query_vec, k=k)
```

---

## System Design Walkthrough: Enterprise Knowledge Base

**Question:** "Design a RAG system for a 10M-document enterprise knowledge base with 5,000 employees querying it. SLA: p95 < 2.5s. Documents update daily. Multi-tenant: HR, Legal, Engineering departments have separate access."

**Sample answer structure:**

**Requirements:**
- Scale: 10M docs → ~12M chunks after chunking
- QPS: 5,000 users × estimated 20 queries/day / 28,800 working seconds = ~3.5 QPS average, ~20 QPS peak
- Freshness: daily batch re-indexing acceptable
- Multi-tenancy: namespace isolation by department + RBAC

**Architecture:**

```
Ingest (daily batch, 9 PM):
  SharePoint / Confluence → Doc processor (Cloud Run) → 
  Text clean + chunk (500 chars) → Batch embed (text-embedding-004) →
  Vertex AI Vector Search (upsert, namespace=department)

Query (real-time):
  Employee query
    → Auth check (IAM → map user to department)
    → Semantic cache (Redis) — 30-60% hit rate expected
    → Cache miss: hybrid retrieval (Vector Search + Elasticsearch BM25)
                  filter={"department": user_dept}  ← tenant isolation
    → Cohere Rerank API (top-20 → top-5)
    → Gemini Pro (generation, streaming)
    → Answer + citations (doc title, department, URL)
```

**Latency budget:**
- Cache hit: ~20ms total
- Cache miss: embed (20ms) + Vector Search (15ms) + BM25 (5ms) + Rerank (150ms) + Gemini (800ms) = ~990ms → within SLA

**Failure handling:**
- Vector Search unavailable → fallback to Elasticsearch full-text search
- Reranker unavailable → skip, use RRF-merged first-stage results
- Gemini rate limited → queue + async delivery, or switch to Gemini Flash

**Monitoring:**
- Retrieval latency p50/p95 per department
- Answer quality score (RAGAS faithfulness, sampled 1%)
- Cache hit rate (alert if drops below 20%)
- Daily: run eval set of 100 golden Q&A pairs, alert if Recall@5 drops below baseline

---

## Interview Q&A

**Q: A product manager asks you to design a RAG system for a company with 10M internal documents. Walk me through your approach.** `[Hard]`
A: I'd start with 5 clarifying questions: QPS, latency SLA, update frequency, access control requirements, and whether answers need citations. Then I'd draw the two pipelines — ingest (offline: load → chunk → embed → upsert) and query (online: cache check → hybrid retrieval → rerank → generate). For 10M docs at ~5 QPS, I'd use Vertex AI Vector Search for managed scale, Elasticsearch for BM25, Cohere Rerank, and Gemini Pro. Daily batch re-indexing at low-traffic hours. Namespace-based tenant isolation if multiple departments. p95 target: under 2s (cache hit: 20ms, cache miss: ~1s).

**Q: How do you handle index freshness in a RAG system where documents update every hour?** `[Medium]`
A: Use event-driven incremental updates. Subscribe to document change events (Pub/Sub or Webhooks). On each event: (1) delete existing vectors with that document_id from the vector DB, (2) re-chunk and re-embed the new version, (3) upsert new vectors. For high-throughput update scenarios, buffer changes in a "hot" write-ahead index that is searched alongside the main "cold" index. This avoids re-indexing the entire corpus for each update.

**Q: What is a semantic cache and how does it differ from a standard key-value cache?** `[Medium]`
A: A standard key-value cache returns a hit only on exact string matches. A semantic cache stores query embeddings alongside answers and returns a cache hit when a new query's embedding is within a cosine similarity threshold (e.g., 0.95) of a cached query. This handles paraphrases: "What is your refund policy?" and "How do I get a refund?" both hit the same cache entry. Tools: GPTCache (open source), Redis + FAISS, or Qdrant as a vector-based cache store.

**Q: How would you design a multi-tenant RAG system where tenants must not see each other's data?** `[Hard]`
A: Two isolation strategies: (1) **Namespace isolation** — store all tenants in one vector DB but with a tenant_id namespace/collection. At query time, apply a mandatory metadata filter: `filter={"tenant_id": current_user.tenant_id}`. This is simple but relies on correct filter application at every query — a missed filter leaks data. (2) **Index isolation** — separate vector DB indices per tenant. Stronger isolation, but higher operational overhead (N indices to manage). For high-security requirements (HIPAA, SOC2), index isolation is preferred. For standard enterprise, namespace isolation with application-layer enforcement + audit logging is sufficient.

**Q: How do you detect and handle retrieval quality degradation in production?** `[Hard]`
A: Set up three signals: (1) **Offline eval**: a fixed set of 100-500 golden (question, expected_answer) pairs; run weekly, alert if Recall@5 or faithfulness score drops >5% from baseline. (2) **Online signals**: thumbs down / feedback buttons; low user rating rate is a leading indicator of quality degradation. (3) **Embedding distribution drift**: periodically compute the centroid of recent query embeddings; if it drifts significantly from the training distribution of your embedding model, re-evaluate whether to switch models. Common causes of degradation: corpus changes (new document types or vocabulary), index staleness, or changes in user query patterns.

**Q: What are the trade-offs between batch and streaming ingestion for a RAG system?** `[Medium]`
A: Batch ingestion (nightly runs) is simple, cost-efficient (bulk embedding API rates), and idempotent — easy to retry and monitor. Freshness SLA: hours to a day. Streaming ingestion (event-driven) achieves minute-level freshness but adds operational complexity: you need idempotent updates (delete old vectors → insert new ones), handling of race conditions (same document updated twice in quick succession), and dead-letter queues for failed ingestion events. Choose based on freshness requirement: most enterprise knowledge bases are fine with daily batch; customer support (where KB articles change hourly) needs streaming.

**Q: How do you prevent the RAG system from returning confidential documents to unauthorized users?** `[Hard]`
A: Defense in depth: (1) **Metadata tagging at ingest** — tag every document with its access control level (public, internal, confidential, top-secret) and owner group during ingestion. (2) **Mandatory metadata filtering at query time** — the retrieval function always includes a filter based on the authenticated user's permissions. This filter must be applied at the vector DB layer, not in application code after retrieval. (3) **Audit logging** — log every (user, query, retrieved_doc_ids) tuple for forensic capability. (4) **Index-level isolation** for highly sensitive data (never co-locate top-secret documents with general documents in the same index, regardless of filters).
