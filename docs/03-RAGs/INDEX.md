# 03 — RAG (Retrieval-Augmented Generation)

**Level:** General to Advanced  
**Format:** Prose + code + Q&A pairs tagged `[Easy]` `[Medium]` `[Hard]`

---

## What You Will Learn

- Why LLMs hallucinate and how RAG addresses it (and its limits)
- How embeddings and vector databases enable semantic search — the math and the algorithms
- Chunking and indexing strategies that determine retrieval quality
- Dense, sparse, hybrid retrieval — BM25 formula, RRF, reranking mechanics
- Advanced patterns: Self-RAG, GraphRAG, FLARE, CRAG, Agentic RAG
- How to evaluate RAG systems with RAGAS and how to debug failures
- The complete taxonomy of RAG types from Naive → GraphRAG
- Production system design for 10M-100M document corpora
- Vertex AI Search, RAG Engine, Grounding API — when to use which
- Deploying, monitoring, and scaling RAG in production on GCP
- LLM-specific failure modes: hallucination, lost-in-the-middle, prompt injection
- 80+ curated Q&A pairs covering all weak spots

---

## Chapter Map

| # | File | Topic | Difficulty |
|---|------|-------|-----------|
| 1 | [RAG Fundamentals](Notes/01-RAG-Fundamentals.md) | What RAG is, pipeline, RAG vs fine-tuning, naive RAG limitations | ★★☆ |
| 2 | [Embeddings and Vector Stores](Notes/02-Embeddings-and-Vector-Stores.md) | Embedding math, cosine vs dot vs euclidean, HNSW/IVF/PQ, vector DB comparison | ★★★ |
| 3 | [Chunking and Indexing](Notes/03-Chunking-and-Indexing.md) | Fixed/semantic/hierarchical chunking, parent-child, metadata filtering | ★★☆ |
| 4 | [Retrieval Strategies](Notes/04-Retrieval-Strategies.md) | BM25 math, hybrid search, RRF formula, reranking, HyDE, MMR | ★★★ |
| 5 | [RAG Types & Advanced Patterns](Notes/05-RAG-Types-and-Advanced-Patterns.md) | Naive→Modular→Agentic evolution; Self-RAG, FLARE, GraphRAG, CRAG, Multimodal | ★★★ |
| 6 | [Evaluation and Failure Modes](Notes/06-RAG-Evaluation-and-Failure-Modes.md) | RAGAS metrics/formulas, LLM-as-Judge, tracing, A/B testing | ★★★ |
| 7 | [RAG System Design](Notes/08-RAG-System-Design.md) | Production architecture, latency budgets, caching, scaling 100M docs | ★★★ |
| 8 | [Vertex AI RAG](Notes/09-Vertex-AI-RAG.md) | Vertex AI Search, RAG Engine, Grounding API, Vector Search, AlloyDB | ★★★ |
| 9 | [Production Deployment](Notes/10-Production-Deployment.md) | Cloud Run vs GKE, monitoring, CI/CD eval gates, security, PII | ★★★ |
| 10 | [Scaling and LLM Issues](Notes/11-Scaling-and-LLM-Issues.md) | Hallucination types, lost-in-the-middle, context management, prompt injection | ★★★ |
| 11 | [Q&A Review Bank](Notes/12-Interview-QA-Bank.md) | 80+ Q&A pairs: fundamentals → system design → GCP → production debugging | ★★★ |

---

## System Designs

End-to-end production system designs with GCP service mapping, scalability analysis, and interview-style Q&A.

| # | Design | Pattern | Difficulty |
|---|--------|---------|-----------|
| SD-1 | [Simple RAG Pipeline](SystemDesigns/01-simple-rag.md) | Vector + BM25 hybrid, reranking, semantic cache | ★★★ |
| SD-2 | [Agentic RAG — Hybrid Vector + Graph](SystemDesigns/02-agentic-rag-hybrid.md) | ReAct agent, Spanner Graph, multi-hop reasoning | ★★★★ |

---

## Recommended Learning Paths

### Path A: First time through (full learning)
1. [RAG Types & Advanced Patterns](Notes/05-RAG-Types-and-Advanced-Patterns.md) — mental map first (taxonomy section)
2. [RAG Fundamentals](Notes/01-RAG-Fundamentals.md) — why RAG exists
3. [Embeddings and Vector Stores](Notes/02-Embeddings-and-Vector-Stores.md) — the retrieval engine
4. [Chunking and Indexing](Notes/03-Chunking-and-Indexing.md) — the quality bottleneck
5. [Retrieval Strategies](Notes/04-Retrieval-Strategies.md) — improve recall and precision
6. [RAG Types & Advanced Patterns](Notes/05-RAG-Types-and-Advanced-Patterns.md) — production-grade patterns (full read)
7. [Evaluation and Failure Modes](Notes/06-RAG-Evaluation-and-Failure-Modes.md) — measure and debug
8. [RAG System Design](Notes/08-RAG-System-Design.md) — interview system design depth
9. [Vertex AI RAG](Notes/09-Vertex-AI-RAG.md) — GCP-specific knowledge
10. [Scaling and LLM Issues](Notes/11-Scaling-and-LLM-Issues.md) — tricky edge cases
11. [Production Deployment](Notes/10-Production-Deployment.md) — real-world ops
12. [Q&A Review Bank](Notes/12-Interview-QA-Bank.md) — final consolidation

### Path B: Accelerated Deep Dive (4–5 hours)
1. [RAG Types & Advanced Patterns](Notes/05-RAG-Types-and-Advanced-Patterns.md) — taxonomy + GraphRAG, Self-RAG (60 min)
2. [Retrieval Strategies](Notes/04-Retrieval-Strategies.md) — BM25 + hybrid math (45 min)
3. [RAG System Design](Notes/08-RAG-System-Design.md) — system design depth (60 min)
4. [Vertex AI RAG](Notes/09-Vertex-AI-RAG.md) — GCP specifics (30 min)
5. [Q&A Review Bank](Notes/12-Interview-QA-Bank.md) — all 80 Q&A pairs (90 min)

### Path C: Weak spots only
- System design → [08-RAG-System-Design.md](Notes/08-RAG-System-Design.md)
- Retrieval math → [04-Retrieval-Strategies.md](Notes/04-Retrieval-Strategies.md)
- Advanced patterns + taxonomy → [05-RAG-Types-and-Advanced-Patterns.md](Notes/05-RAG-Types-and-Advanced-Patterns.md)
- Vertex AI / GCP → [09-Vertex-AI-RAG.md](Notes/09-Vertex-AI-RAG.md)

---

## Why RAG Comes After Prompts

RAG is fundamentally a prompt construction strategy — you retrieve context and inject it into a prompt. You need solid prompting foundations (Topic 02) before tackling RAG. You also need to understand embeddings, which require understanding how LLMs represent text (Topic 01).

## Why RAG Comes Before MCP and Agents

RAG solves the knowledge problem for a single-turn pipeline. MCP generalizes this into a protocol. Agents generalize it further into autonomous retrieval decisions. RAG is the stepping stone.

---

## Navigation

[Previous: 02 — Prompt Engineering](../02-Prompts/INDEX.md) | [Next: 04 — MCP](../04-MCP/INDEX.md)
