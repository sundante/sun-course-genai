# System Design: Agentic RAG with Hybrid Data (Vector + Graph)

> **Domain:** Life Sciences / Enterprise Knowledge Graph · **Pattern:** Agentic RAG + Graph Traversal + Multi-hop Reasoning
>
> ← [Back to RAG Concepts](../Notes/05-RAG-Types-and-Advanced-Patterns.md) | [Simple RAG Design ←](01-simple-rag.md)

---

## Interview Problem Statement

> **"Design an AI system for a pharmaceutical company that enables researchers to answer complex multi-hop questions like: 'Which of our drug candidates interact with proteins implicated in both Alzheimer's and Type 2 Diabetes, and what clinical trials have investigated those targets?' The knowledge base includes 2M research papers, internal trial documents, and a curated molecular interaction database."**

---

## Why Simple RAG Fails Here

| Limitation | Why It Breaks This Use Case |
|---|---|
| Single-hop retrieval | Question requires: Drug → Protein → Disease (×2) → Trial — 4 hops across entity types |
| No entity relationships | Vector search returns similar text, not connected facts |
| No structured reasoning | "Both Alzheimer's AND Type 2 Diabetes" requires set intersection, not similarity |
| Context window bottleneck | 2M papers → top-5 chunks rarely co-contain all hops |
| No iterative refinement | Answer to hop 1 should inform retrieval for hop 2 |

**The solution:** Hybrid Data — pair a Vector Index (semantic document retrieval) with a Knowledge Graph (structured entity relationships). An agent orchestrates multi-hop traversal across both stores.

---

## Clarifying Questions

| Question | Why It Matters |
|---|---|
| What entity types exist in the domain? (drugs, proteins, genes, diseases, trials?) | Defines graph schema — nodes and edge types |
| Is the molecular database structured (SQL/graph) or unstructured (papers only)? | Structured → import directly to graph; unstructured → NER extraction pipeline |
| How often is data updated? (daily trial updates? weekly paper ingestion?) | Incremental graph update strategy vs. full rebuild |
| What is the maximum acceptable latency? (research tool: 10s OK; clinical decision: 3s max) | Determines whether multi-hop can be synchronous or needs streaming |
| Does the agent need to take actions (flag a trial, create a report) or only answer? | Read-only vs. read-write agent design |
| Are there compliance requirements? (FDA, HIPAA — PII in trial documents?) | Drives data masking and audit logging depth |

---

## System Architecture Overview

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         INGESTION PIPELINE                                  │
│                                                                              │
│  Sources:                                                                    │
│  ├── Cloud Storage: research papers (PDF), internal trial docs (PDF/Word)   │
│  └── Cloud SQL: molecular interaction DB (structured rows)                  │
│                                                                              │
│                    ┌──────────────────────────────────────┐                 │
│  PDF/Word ─────►  │  Cloud Run: Document Parser           │                 │
│                    │  ├── Document AI (OCR, layout)        │                 │
│                    │  └── Named Entity Recognizer          │                 │
│                    │      (Vertex AI NLP API + custom NER) │                 │
│                    │  Output: text chunks + entities JSON  │                 │
│                    └──────────────┬───────────────────────┘                 │
│                                   │                                          │
│                    ┌──────────────▼────────────────────────┐                │
│  Structured DB ──► │  Cloud Run: Graph Builder             │                │
│                    │  ├── Entity deduplication (fuzzy match)│                │
│                    │  ├── Relation extraction (LLM-assisted)│                │
│                    │  └── Upsert to Spanner Graph           │                │
│                    └──────────────┬────────────────────────┘                │
│                                   │                                          │
│             ┌─────────────────────▼───────────────────────┐                 │
│             │  Spanner Graph (knowledge graph)              │                │
│             │  Nodes: Drug, Protein, Gene, Disease, Trial   │                │
│             │  Edges: TARGETS, ASSOCIATED_WITH, TESTED_IN   │                │
│             └───────────────────────────────────────────────┘                │
│                                                                              │
│             ┌───────────────────────────────────────────────┐                │
│             │  Cloud Run: Chunker + Embedder                 │                │
│             │  → Vertex AI Vector Search (dense index)       │                │
│             └───────────────────────────────────────────────┘                │
└────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────────┐
│                         AGENTIC QUERY PIPELINE                              │
│                                                                              │
│  Researcher Query                                                            │
│       │                                                                      │
│       ▼                                                                      │
│  ┌───────────────────────────────────────────────────┐                      │
│  │  Cloud Run: Orchestrator Agent (ADK / LangGraph)  │                      │
│  │                                                    │                      │
│  │  Step 1: Query Decomposition                       │                      │
│  │  "Which drug candidates interact with proteins     │                      │
│  │   implicated in both AD and T2D with trials?"      │                      │
│  │   → Sub-queries:                                   │                      │
│  │     a) proteins linked to Alzheimer's              │                      │
│  │     b) proteins linked to Type 2 Diabetes          │                      │
│  │     c) intersection of (a) ∩ (b)                   │                      │
│  │     d) drug candidates targeting those proteins    │                      │
│  │     e) clinical trials for those drugs             │                      │
│  └───────────────────┬───────────────────────────────┘                      │
│                       │  calls tools                                         │
│         ┌─────────────┼─────────────────────┐                               │
│         ▼             ▼                     ▼                               │
│  ┌─────────────┐ ┌──────────────┐ ┌─────────────────┐                      │
│  │ graph_query │ │ vector_search│ │ synthesis_tool  │                      │
│  │             │ │              │ │                 │                      │
│  │ Spanner     │ │ Vertex AI    │ │ Gemini 1.5 Pro  │                      │
│  │ Graph GQL   │ │ Vector Search│ │ (answer builder)│                      │
│  │ traversal   │ │ + AlloyDB    │ │                 │                      │
│  └─────────────┘ └──────────────┘ └─────────────────┘                      │
│         │                │                 │                                │
│         └────────────────┴─────────────────┘                               │
│                          │                                                   │
│                          ▼                                                   │
│  ┌───────────────────────────────────────────────────┐                      │
│  │  ReAct Loop (Reasoning + Acting)                  │                      │
│  │  Thought → Action → Observation → Thought → ...  │                      │
│  │  Max 8 iterations, timeout 15s                    │                      │
│  └───────────────────────────────────────────────────┘                      │
│                          │                                                   │
│                          ▼                                                   │
│  Final Answer: entities + citations + graph path + source papers             │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Knowledge Graph Schema

### Node Types

| Node Label | Key Properties | Example |
|---|---|---|
| `Drug` | name, candidate_id, mechanism, phase | Lecanemab, Phase 3 |
| `Protein` | name, uniprot_id, function, subcellular_location | APOE, tau, amyloid-beta |
| `Gene` | symbol, entrez_id, chromosome | APOE, TREM2, IDE |
| `Disease` | name, icd10, mesh_id, category | Alzheimer's (G30), T2D (E11) |
| `ClinicalTrial` | nct_id, phase, status, sponsor, start_date | NCT02714153 |
| `Paper` | doi, title, authors, year, journal | Nature 2024 APOE study |

### Edge Types

| Edge | From → To | Properties |
|---|---|---|
| `TARGETS` | Drug → Protein | mechanism, affinity_nM, confidence |
| `ENCODES` | Gene → Protein | — |
| `ASSOCIATED_WITH` | Protein → Disease | evidence_type, score, pmid |
| `IMPLICATED_IN` | Gene → Disease | gwas_p_value, effect_size |
| `TESTED_IN` | Drug → ClinicalTrial | primary_endpoint, result |
| `MENTIONS` | Paper → Drug/Protein/Disease | context, section |
| `INTERACTS_WITH` | Protein → Protein | interaction_type, experimental_evidence |

### Example Multi-hop Query in Graph Query Language

```sql
-- Proteins implicated in BOTH Alzheimer's AND Type 2 Diabetes
SELECT p.name, p.uniprot_id,
       ad_edge.score AS ad_score,
       t2d_edge.score AS t2d_score
FROM Protein p
JOIN ProteinDiseaseAssociation ad_edge ON p.id = ad_edge.protein_id
JOIN Disease ad ON ad_edge.disease_id = ad.id AND ad.mesh_id = 'D000544'   -- Alzheimer's
JOIN ProteinDiseaseAssociation t2d_edge ON p.id = t2d_edge.protein_id
JOIN Disease t2d ON t2d_edge.disease_id = t2d.id AND t2d.icd10 = 'E11'    -- T2D
WHERE ad_edge.score > 0.7 AND t2d_edge.score > 0.7;

-- Then: Drug candidates targeting those proteins
SELECT d.name, d.phase, t.mechanism
FROM Drug d
JOIN DrugProteinTarget t ON d.id = t.drug_id
WHERE t.protein_id IN (/* above result */);
```

---

## Agent Tool Definitions

### Tool 1: `graph_query`

```python
@agent.tool
async def graph_query(
    query_type: str,       # "entity_lookup" | "traversal" | "intersection"
    entity_name: str,      # starting entity
    entity_type: str,      # "Drug" | "Protein" | "Disease" | "Trial"
    hops: int = 2,         # max traversal depth
    filters: dict = None   # {edge_type: "TARGETS", min_confidence: 0.7}
) -> list[dict]:
    """
    Traverses the Spanner Graph knowledge graph.
    Returns a list of connected entities with relationship metadata.
    """
```

**Why bounded hops?** Unbounded graph traversal can return millions of nodes. Cap at 2–3 hops for response time; if more depth is needed, decompose into sub-queries.

### Tool 2: `vector_search`

```python
@agent.tool
async def vector_search(
    query: str,
    top_k: int = 5,
    filters: dict = None,    # {year: {gte: 2020}, source: "internal_trials"}
    include_snippets: bool = True
) -> list[dict]:
    """
    Semantic search over research papers and trial documents.
    Returns top_k chunks with source metadata and relevance scores.
    """
```

### Tool 3: `entity_intersection`

```python
@agent.tool
async def entity_intersection(
    entity_lists: list[list[str]],   # list of entity ID lists to intersect
    entity_type: str
) -> list[str]:
    """
    Computes set intersection of entity IDs returned by prior graph queries.
    Used for "implicated in BOTH disease A AND disease B" queries.
    """
```

### Tool 4: `synthesis`

```python
@agent.tool
async def synthesis(
    question: str,
    graph_facts: list[dict],
    document_chunks: list[dict]
) -> str:
    """
    Calls Gemini 1.5 Pro to synthesize a grounded answer
    from structured graph facts and unstructured document evidence.
    """
```

---

## ReAct Loop Trace (Example)

**Query:** "Which drug candidates target proteins implicated in both Alzheimer's and Type 2 Diabetes?"

```
Thought 1: I need to find proteins linked to Alzheimer's Disease.
Action 1: graph_query(entity_name="Alzheimer's Disease", entity_type="Disease", query_type="traversal", hops=1, filters={edge_type: "ASSOCIATED_WITH", min_score: 0.7})
Observation 1: [APOE, tau, amyloid-beta, TREM2, CLU] with association scores

Thought 2: Now I need proteins linked to Type 2 Diabetes with same criteria.
Action 2: graph_query(entity_name="Type 2 Diabetes", entity_type="Disease", query_type="traversal", hops=1, filters={edge_type: "ASSOCIATED_WITH", min_score: 0.7})
Observation 2: [IDE, APOE, INSR, GLP1R, IRS1] with association scores

Thought 3: Compute the intersection — proteins in both lists.
Action 3: entity_intersection([[APOE, tau, TREM2, CLU], [IDE, APOE, INSR, IRS1]], entity_type="Protein")
Observation 3: [APOE]

Thought 4: Find drug candidates targeting APOE.
Action 4: graph_query(entity_name="APOE", entity_type="Protein", query_type="traversal", hops=1, filters={edge_type: "TARGETS", phase: {gte: 2}})
Observation 4: [Lecanemab (Phase 3), ABBV-916 (Phase 2), PTC-027 (Phase 2)]

Thought 5: Find clinical trials for these drug candidates.
Action 5: graph_query(entity_name="Lecanemab", entity_type="Drug", query_type="traversal", hops=1, filters={edge_type: "TESTED_IN"})
Observation 5: [NCT03887455 (Phase 3, completed), NCT04468659 (Phase 3, active)]

Thought 6: Get supporting evidence from research papers.
Action 6: vector_search(query="APOE Alzheimer's Type 2 Diabetes drug target clinical evidence", top_k=3, filters={year: {gte: 2020}})
Observation 6: [Paper 1: "APOE4 metabolic dysfunction links AD and T2D...", Paper 2: "...]

Thought 7: I have enough to synthesize a grounded answer.
Action 7: synthesis(question=..., graph_facts=[...], document_chunks=[...])
Observation 7: Final answer with citations
```

---

## GCP Services Map

| Component | GCP Service | Why |
|---|---|---|
| Raw document storage | Cloud Storage | Source of truth; Eventarc triggers ingestion |
| Structured DB import | Cloud SQL → Dataflow | Bulk import molecular DB into graph format |
| Document parsing | Document AI (Form Parser + OCR) | Layout-aware parsing of research PDFs |
| Named Entity Recognition | Vertex AI Natural Language API + custom AutoML NER | Extract Drug/Protein/Disease entities |
| Relation extraction | Vertex AI Gemini 1.5 Flash (batch) | "Paper says Drug X targets Protein Y" → edge |
| Knowledge graph store | Spanner Graph | Managed, ACID, GQL support, multi-region |
| Entity deduplication | Dataflow + Fuzzy matching (jaro-winkler) | "Aβ" and "amyloid-beta" are the same node |
| Graph update queue | Pub/Sub + Dataflow | Streaming graph updates from new papers |
| Vector index | Vertex AI Vector Search | ANN over 2M paper embeddings |
| Sparse index | AlloyDB pgvector + tsvector | BM25 for exact term matching |
| Embedding model | Vertex AI text-embedding-005 | Unified embedding space for papers |
| Agent orchestration | Vertex AI Agent Engine (ADK) | Managed agent runtime, session state |
| LLM (synthesis) | Vertex AI Gemini 1.5 Pro | 128k context, tool use, grounding |
| LLM (relation extraction) | Vertex AI Gemini 1.5 Flash (batch) | Cost-efficient batch NER/relation jobs |
| Semantic cache | Memorystore for Redis | Cache frequent research queries |
| Session state | Firestore | Per-researcher agent session context |
| Auth | Identity-Aware Proxy + VPC Service Controls | Internal research tool, strict perimeter |
| Audit logging | Cloud Logging + BigQuery | Compliance audit trail per query |
| Monitoring | Cloud Monitoring + Cloud Trace | Latency per agent step, error rates |
| Offline eval | Vertex AI Experiments + BigQuery | RAGAS scores, graph recall metrics |
| CI/CD | Cloud Build + Artifact Registry | Graph pipeline + agent deployment |

---

## Scalability Considerations

### Graph Scalability

| Scale | Spanner Config | Query Latency | Strategy |
|---|---|---|---|
| <10M nodes | Single region, 3 nodes | <100ms | Default config |
| 10M–100M nodes | Multi-region, 10 nodes | 100–500ms | Partition by entity type |
| 100M+ nodes | Multi-region, 30+ nodes | 500ms–2s | Sub-graph caching + materialized views |

**Key insight:** Graph traversal latency grows with degree (number of edges per node), not graph size. High-degree nodes (e.g., APOE protein connected to thousands of papers) need degree-bounded queries and result truncation. Always specify `LIMIT` in graph queries.

### Agent Scalability

**Problem:** ReAct loops are inherently sequential — each action depends on the prior observation.

**Mitigations:**
1. **Parallel tool calls within a step** — when sub-queries are independent (e.g., "proteins in AD" and "proteins in T2D"), execute both graph queries concurrently. ADK supports parallel tool dispatch.
2. **Materialized sub-graph caching** — pre-compute and cache common sub-graphs (e.g., "all proteins implicated in Alzheimer's") in Redis. Graph traversal for common starting nodes takes 1ms (cache hit) vs. 300ms (live query).
3. **Iteration cap** — hard limit of 8 ReAct iterations with timeout of 15s. If exceeded, return partial answer with "further research needed" flag.
4. **Query complexity classifier** — simple single-hop queries (entity lookup) bypass the agent loop entirely and go directly to vector search + graph_query.

### Ingestion Scalability: 2M Papers

| Stage | Throughput | GCP Config |
|---|---|---|
| PDF parsing | 500 docs/min | Cloud Run 50 instances × 10 RPS |
| Entity extraction (NLP API) | 300 docs/min | Vertex AI NLP: 300 RPS quota |
| Relation extraction (Gemini Flash batch) | 1000 docs/min | Batch Prediction API, async |
| Graph upsert (Spanner) | 10k mutations/sec | Spanner 10-node cluster |
| Vector embed + index | 20k chunks/min | Cloud Tasks + Vector Search online updates |

Full initial load of 2M papers: ~3–4 days. Incremental updates (100 papers/day): <30 minutes.

### Cost Optimization at Scale

| Lever | Saving |
|---|---|
| Gemini Flash for NER/relation extraction (batch) | 5–10× cheaper than Pro |
| Materialized sub-graph cache for top-100 disease entities | 60% reduction in Spanner queries |
| Semantic cache for agent responses | 20–30% LLM cost reduction |
| Committed use discounts on Spanner + Cloud Run | 25–57% savings |
| Offline batch embedding vs. real-time | 40% cheaper with batch API |

---

## Failure Modes and Mitigations

| Failure | Symptom | Mitigation |
|---|---|---|
| Graph entity not found | Agent gets empty traversal result | Fall back to vector search; flag "not in graph yet" |
| Entity disambiguation failure | "insulin" maps to wrong protein | Canonical entity disambiguation using UniProt/MeSH IDs |
| Agent infinite loop | ReAct exceeds iteration cap | Hard 8-iteration + 15s timeout; return partial answer |
| Stale graph data | Drug candidate phase changed | Graph edges have `last_updated` timestamp; warn if >30 days |
| High-degree node explosion | Query returns 50k edges | Degree-bounded traversal (LIMIT 100 per hop) |
| Hallucinated graph paths | Agent invents relationships | Synthesis tool only uses `graph_facts` actually returned — no interpolation |
| NER extraction errors | Wrong entity extracted | Human-in-the-loop review queue for low-confidence extractions; threshold 0.85 |

---

## Simple RAG vs. Agentic RAG Hybrid — Decision Matrix

| Criterion | Simple RAG | Agentic RAG Hybrid |
|---|---|---|
| Query type | Single-hop factual | Multi-hop relational |
| Data structure | Unstructured text only | Text + structured relationships |
| Latency requirement | <3s | 5–15s acceptable |
| Entity relationships critical? | No | Yes |
| Set operations needed? | No | Yes (intersection, union) |
| Agent complexity | Low | High (ReAct loop) |
| Operational cost | Low | High (graph infra + agent) |
| Use Simple RAG when... | Q&A, summarization, policy lookup | — |
| Use Hybrid when... | — | Drug discovery, compliance tracing, financial fraud chains |

---

## Q&A Review Bank

**Q1: Why can't a standard RAG pipeline answer multi-hop questions like "proteins implicated in both Disease A and Disease B"? What specifically breaks?** `[Medium]`

A: Three structural failures: (1) **No set operations** — vector similarity returns the most similar chunks, not the intersection of entity sets. A query for "both Alzheimer's AND T2D" may retrieve chunks about each disease separately but has no mechanism to compute the protein overlap. (2) **No entity relationship traversal** — the relationship `Drug TARGETS Protein` is implicit in text but not navigable. A chunk that says "Lecanemab binds APOE" and a chunk that says "APOE is associated with T2D" exist in different embedding neighborhoods — the system has no way to connect them without explicitly traversing an edge. (3) **Context window bottleneck** — even if you retrieved all relevant chunks (hundreds), the LLM would struggle to compute a precise intersection from unstructured prose across a 100k-token context window. Knowledge graphs make these relationships explicit and queryable.

---

**Q2: What is the risk of an unbounded graph traversal in the agent's `graph_query` tool, and how do you design against it?** `[Hard]`

A: Unbounded traversal from a high-degree node (e.g., "APOE", which may connect to 50,000 papers and 10,000 proteins in a large biomedical graph) can return millions of nodes, consuming all available memory and timing out the agent within seconds. Three defenses: (1) **Hard `LIMIT` per hop** — cap results at 100–500 edges per traversal level; the agent sees the most relevant (by confidence score) rather than all. (2) **Hop depth limit** — cap at 2–3 hops; queries requiring 4+ hops should be decomposed by the agent into chained 2-hop queries. (3) **Degree pruning** — edges are sorted by `confidence` or `evidence_count` before applying the limit, ensuring high-quality edges are retained. The agent must be designed to recognize "too many results" as a signal to add more filters, not to use all results.

---

**Q3: Describe the role of Spanner Graph specifically — why not use Neo4j, or just use AlloyDB with a graph extension?** `[Hard]`

A: Spanner Graph is the right choice for this use case for three reasons: (1) **ACID + global scale** — Spanner provides externally consistent transactions across regions. For a pharmaceutical knowledge graph where an incorrect drug-protein edge could affect drug safety decisions, transactional consistency matters — you cannot have partial edge inserts. Neo4j Community provides ACID locally but not across multi-region deployments without enterprise licensing. (2) **GQL (Graph Query Language) ISO standard** — Spanner Graph supports the ISO/IEC GQL standard, making queries portable and the team's skills transferable. (3) **GCP-native integration** — Spanner integrates natively with Dataflow (ingestion), IAM (access control), VPC Service Controls (compliance perimeter), and Cloud Monitoring — all required for enterprise pharma. AlloyDB with Apache AGE provides graph extensions but is better suited for small graphs (<10M nodes) where SQL-first modeling is more natural; at 100M+ node scale, native graph storage with graph-optimized query execution (like Spanner Graph) significantly outperforms.

---

**Q4: The agent is hallucinating graph paths — claiming Drug X targets Protein Y when that edge doesn't exist. How do you prevent this?** `[Hard]`

A: This happens when the synthesis step extrapolates from implicit context rather than explicit graph facts. Three-layer fix: (1) **Structural grounding constraint** — the synthesis tool prompt explicitly prohibits generating relationship claims not present in the `graph_facts` parameter: "Only state relationships that appear verbatim in the provided graph facts. Do not infer or extrapolate." (2) **Citation enforcement** — every relationship claim in the answer must be tagged with its source: either a graph edge ID (e.g., `[Graph: Drug-Protein edge #4521, confidence=0.92]`) or a document citation. Any uncited relational claim is flagged as unverified. (3) **Post-generation fact check** — after generation, extract all relational claims from the answer and verify each against the knowledge graph with a `graph_query(query_type="entity_lookup")`. Any claim not found in the graph is either removed or flagged with "not confirmed in knowledge base." This adds ~200ms but eliminates hallucinated relationships.

---

**Q5: How do you handle the cold-start problem when the knowledge graph is first populated from 2M unstructured research papers?** `[Hard]`

A: Cold-start is a 3–4 day batch pipeline, not an online process. (1) **Entity extraction at scale** — use Vertex AI Gemini Flash batch prediction to run NER across all 2M papers in parallel. Each paper produces a JSON of extracted entities: `{drugs: [], proteins: [], diseases: [], relations: []}`. At Flash pricing, 2M papers cost ~$200–400. (2) **Deduplication** — entities must be canonicalized before graph insertion. "amyloid-beta", "Aβ", "A-beta" must map to the same protein node (UniProt Q9Y287). Use fuzzy string matching (Jaro-Winkler > 0.92) + lookup against MeSH, UniProt, and ChEMBL canonical name dictionaries. Run in Dataflow. (3) **Confidence scoring** — each extracted edge gets a confidence score based on: extraction model confidence + number of papers supporting the claim + whether the paper is a review article (higher weight) vs. a single study. Only edges with confidence > 0.7 are inserted at cold-start; lower-confidence edges are stored in a review queue. (4) **Incremental updates** — after cold-start, new papers trigger streaming Pub/Sub messages → Dataflow → NER → graph upsert, keeping the graph current within hours of new publications.

---

**Q6: A researcher reports that the agent gives inconsistent answers to the same question on different days. What are the likely causes and how do you build reproducibility?** `[Hard]`

A: Three sources of non-determinism: (1) **Graph data changes** — new papers added edges between old cold-start queries. The answer was correct both times given the graph state at that moment. Fix: log the graph state snapshot (edge version IDs) used for each query in BigQuery. Reproducibility means replaying a query against the same graph version. (2) **LLM temperature > 0** — synthesis step uses sampling, producing different phrasings or emphasis on different runs. Fix: set temperature=0 for synthesis in research/compliance contexts; accept that some variation is normal in phrasing but ensure core entity claims are deterministic from graph facts. (3) **Semantic cache invalidation race** — cached response from Day 1 returned on Day 2, but graph was updated in between; then cache expired and live query returned different (more current) answer. Fix: cache keys include `graph_version_hash` so cache entries are invalidated when the underlying graph changes. Include the query timestamp and graph version in the response so researchers know which data generation answered their question.

---

**Q7: Design the observability stack for this system. What metrics do you track at each layer?** `[Medium]`

A: Four layers: (1) **Infrastructure** (Cloud Monitoring): Cloud Run CPU/memory per service, Spanner read/write latency P50/P99, Vector Search query latency, Redis cache hit rate. Alert on: Spanner P99 > 500ms, cache hit rate < 10%, Cloud Run error rate > 1%. (2) **Agent** (Cloud Trace + custom spans): total ReAct loop duration, iterations per query, tool call latency per tool type (graph_query vs. vector_search), timeout rate. Track `mean_iterations_per_query` — if it rises, queries are getting more complex or the agent is getting confused. (3) **Retrieval quality** (BigQuery + offline eval): graph traversal recall (did the graph path exist?), vector search MRR@5, entity extraction precision/recall on a labeled test set. Run RAGAS weekly on a sample of queries. (4) **Answer quality** (human feedback + LLM-as-judge): thumbs up/down from researchers, LLM-as-judge faithfulness score (are answer claims grounded in graph facts?), hallucination rate on labeled golden set. Dashboard in Looker Studio.
