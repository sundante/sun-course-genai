# Vertex AI RAG

GCP offers three distinct managed services for RAG. Choosing the wrong one is a common interview mistake — each occupies a different point on the control vs. convenience spectrum.

---

## GCP Recommended Stack for Hybrid RAG

When building production-grade RAG on Google Cloud, each pipeline stage has a recommended GCP-native or GCP-compatible service. This table is a starting point for interviews and architecture reviews.

| Pipeline Stage | GCP-Recommended Option | Alternatives on GCP | Notes |
|---|---|---|---|
| **Embeddings** | Vertex AI Embeddings API (`text-embedding-004`, 768-dim) | BAAI `bge-m3` on Vertex AI Model Garden; `gemini-embedding-001` (3072-dim) | `text-embedding-004` is the production default; `bge-m3` is stronger for multilingual/domain-specific corpora |
| **Vector Store** | Vertex AI Vector Search (Matching Engine, ANN-based) | Pinecone, Weaviate, Qdrant via Cloud Run | Managed, scales to 1B+ vectors; use when staying fully GCP-native |
| **Graph Store** | Neo4j AuraDS (managed graph DB) | Spanner Graph (preview), AlloyDB + age extension | Required for GraphRAG or entity-relationship queries; Neo4j AuraDS is the easiest managed option |
| **Sparse / Keyword** | Elasticsearch on GKE | OpenSearch on GKE, BigQuery full-text search | Vertex AI Vector Search has no built-in BM25; must pair with Elasticsearch for hybrid search |
| **Re-ranker** | Vertex AI ReRanker API (`text-reranker@001`) | Cohere Rerank API; `BAAI/bge-reranker-v2-m3` on Vertex AI Model Garden | Vertex AI ReRanker is fully integrated with Matching Engine; Cohere is stronger multilingual |
| **LLM Generator** | Gemini 1.5 Flash (latency-sensitive) / Gemini 1.5 Pro (quality-sensitive) | Gemini 2.0 Flash, Claude on Vertex AI (via Model Garden) | Gemini has native tool integration with RAG Engine corpus |
| **Orchestration** | LangGraph (stateful agent graphs) + Vertex AI Pipelines (batch/scheduled) | LangChain + Cloud Run, CrewAI on GKE | LangGraph for real-time agents; Vertex AI Pipelines for batch ingestion jobs |
| **Observability** | Cloud Trace + Langfuse (self-hosted on Cloud Run) | Arize Phoenix on GKE, LangSmith | Cloud Trace for infrastructure; Langfuse for LLM-specific span tracing and RAGAS integration |

**Typical Hybrid RAG architecture on GCP:**
```
User query
    ↓
Cloud Run (query service)
    ├─ text-embedding-004 → Vertex AI Vector Search (dense k=20)
    ├─ Elasticsearch on GKE (BM25 k=20)
    └─ RRF fusion → 20 candidates
         ↓
    Vertex AI ReRanker API → top 5 chunks
         ↓
    Gemini 1.5 Pro (generator)
         ↓
    Response + citations
```

---

## The Vertex AI RAG Landscape

```
                   ← more managed / less control        more control / less managed →
   
┌────────────────────┐   ┌──────────────────────────┐   ┌────────────────────────────────┐
│  Vertex AI Search  │   │  Vertex AI RAG Engine     │   │  Custom RAG on GCP             │
│                    │   │  (Vertex AI RAG API)       │   │                                │
│ - Managed search   │   │ - Managed retrieval corpus │   │ - AlloyDB/pgvector + Cloud Run │
│   over your data   │   │ - Gemini integration       │   │ - Vertex AI Vector Search +    │
│ - Structured +     │   │ - No infra to manage       │   │   your own embedding + LLM     │
│   unstructured     │   │ - Only works with Gemini   │   │ - Full control of all stages   │
│ - Not directly     │   │ - Supports file-based      │   │ - Bring any embedding model    │
│   tied to LLM      │   │   retrieval corpus         │   │ - Most flexible                │
└────────────────────┘   └──────────────────────────┘   └────────────────────────────────┘
     "I need search"       "I need RAG with Gemini"        "I need full control"
```

**Quick decision matrix:**

| If you need... | Use |
|---|---|
| Search UI + API over enterprise docs | Vertex AI Search |
| Fast RAG with Gemini, no infra management | Vertex AI RAG Engine |
| Multi-tenant with custom embedding model | Custom (Vector Search + Cloud Run) |
| RAG + real-time Grounding with Google Search | Grounding API |
| SQL over structured data + RAG over unstructured | AlloyDB + pgvector (custom) |

---

## Vertex AI Search

### Concept

Vertex AI Search (formerly Enterprise Search / Generative AI App Builder) is a fully managed search and answer service over your enterprise data. You don't write retrieval code — you configure data stores and search apps via the console or API.

**Key components:**
- **Data stores**: containers for your documents. Types: Unstructured (PDFs, HTML, DOCX), Structured (BigQuery tables, JSON), Website (crawled URLs), Healthcare FHIR
- **Search apps**: a search endpoint tied to one or more data stores
- **Grounding**: when linked to Gemini, provides grounded answers with citations

**What it handles for you:**
- Chunking and indexing
- Embedding (Google's internal models)
- ANN search infrastructure
- Re-ranking (built-in)
- Extractive Q&A (extracts relevant passages from matched documents)

**What you give up:**
- Control over chunking strategy
- Choice of embedding model
- Custom reranking logic

### Code

```python
from google.cloud import discoveryengine_v1 as discoveryengine

def search_vertex_ai(
    project_id: str,
    location: str,
    search_engine_id: str,
    query: str,
    page_size: int = 5
) -> list[dict]:
    client = discoveryengine.SearchServiceClient()
    serving_config = (
        f"projects/{project_id}/locations/{location}"
        f"/collections/default_collection/engines/{search_engine_id}"
        f"/servingConfigs/default_config"
    )
    
    request = discoveryengine.SearchRequest(
        serving_config=serving_config,
        query=query,
        page_size=page_size,
        content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
            # Extractive Q&A: returns relevant passages
            extractive_content_spec=discoveryengine.SearchRequest.ContentSearchSpec.ExtractiveContentSpec(
                max_extractive_answer_count=3,
                max_extractive_segment_count=3
            ),
            # Snippet: returns key snippet from each document
            snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
                return_snippet=True
            )
        )
    )
    
    response = client.search(request)
    results = []
    for result in response.results:
        doc = result.document
        extractive_answers = []
        if doc.derived_struct_data:
            for ea in doc.derived_struct_data.get("extractive_answers", []):
                extractive_answers.append(ea.get("content", ""))
        results.append({
            "id": doc.id,
            "title": doc.derived_struct_data.get("title", ""),
            "snippets": extractive_answers,
            "link": doc.derived_struct_data.get("link", "")
        })
    return results

# Use results in a RAG prompt
results = search_vertex_ai(project_id, "global", engine_id, "What is the refund policy?")
context = "\n\n".join([f"Source: {r['title']}\n{chr(10).join(r['snippets'])}" for r in results])
answer = llm.invoke(f"Context:\n{context}\n\nQuestion: What is the refund policy?\nAnswer:")
```

---

## Vertex AI RAG Engine (RAG API)

### Concept

Vertex AI RAG Engine is the closest to a "managed RAG backend" on GCP. It provides:
- **RagCorpus**: a named collection of documents (equivalent to a vector store)
- **RagFile**: individual documents uploaded to a corpus
- **RetrieveContexts**: the retrieval API — returns relevant chunks for a query
- **Gemini native integration**: directly wire a corpus to a Gemini model via `tool_config`

**Key differentiator from Vertex AI Search:**
RAG Engine is purpose-built for retrieval to feed into Gemini. It exposes a retrieval API you call directly in your application code, whereas Vertex AI Search is a search service with its own query interface.

**Supported sources for import:**
- Google Drive
- Google Cloud Storage (PDFs, text files)
- Inline text
- Slack, Jira (via connectors — in preview)

### Code

```python
import vertexai
from vertexai.preview import rag
from vertexai.generative_models import GenerativeModel, Tool

vertexai.init(project=PROJECT_ID, location="us-central1")

# 1. Create a corpus (one-time setup)
corpus = rag.create_corpus(display_name="enterprise-knowledge-base")
corpus_name = corpus.name  # e.g., "projects/.../ragCorpora/..."
print(f"Created corpus: {corpus_name}")

# 2. Upload documents to the corpus
rag_file = rag.upload_file(
    corpus_name=corpus_name,
    path="gs://my-bucket/policy-documents/refund-policy.pdf",
    display_name="Refund Policy",
    description="Customer refund policy document"
)

# Or import from GCS bucket (bulk)
rag.import_files(
    corpus_name=corpus_name,
    paths=["gs://my-bucket/docs/"],  # all files in bucket
    chunk_size=512,        # characters
    chunk_overlap=50
)

# 3. Retrieve contexts (direct retrieval API)
response = rag.retrieval_query(
    rag_resources=[rag.RagResource(rag_corpus=corpus_name)],
    text="What is the Enterprise plan refund policy?",
    similarity_top_k=5,
    vector_distance_threshold=0.5  # filter below this similarity
)

for context in response.contexts.contexts:
    print(f"Score: {context.score:.3f}")
    print(f"Source: {context.source_uri}")
    print(f"Text: {context.text[:200]}\n")

# 4. Native Gemini integration (corpus as grounding tool)
rag_retrieval_tool = Tool.from_retrieval(
    retrieval=rag.Retrieval(
        source=rag.VertexRagStore(
            rag_resources=[rag.RagResource(rag_corpus=corpus_name)],
            similarity_top_k=5,
        )
    )
)

gemini = GenerativeModel("gemini-2.0-flash-001", tools=[rag_retrieval_tool])
response = gemini.generate_content("What is the Enterprise plan refund policy?")
print(response.text)
```

---

## Grounding with Google Search

### Concept

Grounding is a distinct capability: rather than retrieving from your own corpus, you ground Gemini's responses in live Google Search results. This is Gemini's way of accessing up-to-date public information without you maintaining a search index.

**Two grounding modes:**
1. **Google Search grounding** — Gemini automatically searches Google when the query warrants it. Returns grounded answers with web citations.
2. **Custom corpus grounding** — Ground in your own Vertex AI Search data store or RAG Engine corpus (overlaps with Vertex AI Search integration above).

**Dynamic retrieval threshold:**
You control how often grounding activates via a `dynamic_retrieval_config`. Setting `dynamic_threshold=0.3` means "ground if model confidence in its parametric answer is below 0.3." Higher threshold = more grounding (more accurate, slightly slower). Lower = less grounding (faster, but higher hallucination risk for recent events).

**When to use Google Search grounding vs RAG Engine:**
- **Google Search grounding**: for queries about public, recent information (news, prices, public company data)
- **RAG Engine**: for queries about your private internal documents
- **Both together**: combine a RAG corpus tool and Google Search retrieval tool — Gemini decides which to call

### Code

```python
from vertexai.generative_models import (
    GenerativeModel, Tool, GoogleSearchRetrieval, 
    DynamicRetrievalConfig
)

# Option 1: Always-on Google Search grounding
google_search_tool = Tool(
    google_search_retrieval=GoogleSearchRetrieval()
)

model = GenerativeModel("gemini-2.0-flash-001", tools=[google_search_tool])
response = model.generate_content("What is the current price of NVIDIA stock?")
print(response.text)

# Option 2: Dynamic retrieval (grounding activates only when model is uncertain)
dynamic_retrieval_tool = Tool(
    google_search_retrieval=GoogleSearchRetrieval(
        dynamic_retrieval_config=DynamicRetrievalConfig(
            mode=DynamicRetrievalConfig.Mode.MODE_DYNAMIC,
            dynamic_threshold=0.7  # 0.0-1.0; higher = more grounding
        )
    )
)

model_dynamic = GenerativeModel("gemini-2.0-flash-001", tools=[dynamic_retrieval_tool])

# Option 3: Combine RAG corpus + Google Search
combined_model = GenerativeModel(
    "gemini-2.0-flash-001",
    tools=[rag_retrieval_tool, google_search_tool]  # agent decides which to call
)

# Check grounding metadata in response
response = model.generate_content("What is today's news about AI safety regulations?")
if response.candidates[0].grounding_metadata:
    for chunk in response.candidates[0].grounding_metadata.grounding_chunks:
        if chunk.web:
            print(f"Source: {chunk.web.uri}")
            print(f"Title: {chunk.web.title}")
```

---

## Custom RAG on GCP

### Concept

When you need full control — custom embedding model, custom chunking, hybrid search, your own reranker — you build RAG yourself on GCP components.

**Stack options:**

**Option A: Vertex AI Vector Search + Cloud Run**
```
GCS bucket (raw docs)
    ↓ Cloud Run ingest service
text-embedding-004 (Vertex AI API) → Vertex AI Vector Search index
                                         ↓ Cloud Run query service
                               Hybrid: Vector Search + Elasticsearch on GKE
                                         ↓ Cohere Rerank API
                                         ↓ Gemini API
```

**Option B: AlloyDB pgvector + Cloud Run** (when you want SQL + vector in one place)
```
AlloyDB (PostgreSQL + pgvector extension)
    ├─ store documents + metadata (SQL tables)
    ├─ store vectors (pgvector column)
    └─ hybrid queries: SQL WHERE + <=> (cosine distance operator)
```

**Option B is great when:**
- You need to filter by structured attributes (user_id, date, category) AND do semantic search
- Your team is comfortable with SQL
- You want ACID transactions on document updates (vector + metadata updated atomically)

### Code

```python
# Vertex AI Vector Search — building and querying an index
from google.cloud import aiplatform

aiplatform.init(project=PROJECT_ID, location="us-central1")

# Create index
my_index = aiplatform.MatchingEngineIndex.create_tree_ah_index(
    display_name="enterprise-knowledge-index",
    contents_delta_uri="gs://my-bucket/embeddings/",  # pre-computed embeddings in JSONL
    dimensions=768,
    approximate_neighbors_count=20,
    distance_measure_type="COSINE_DISTANCE"
)

# Deploy index to an endpoint
my_endpoint = aiplatform.MatchingEngineIndexEndpoint.create(
    display_name="enterprise-knowledge-endpoint",
    public_endpoint_enabled=True
)
my_endpoint.deploy_index(index=my_index, deployed_index_id="knowledge_v1")

# Query at runtime
def vector_search_vertex(query: str, k: int = 10) -> list[dict]:
    query_vec = embed_text([query])[0]
    response = my_endpoint.find_neighbors(
        deployed_index_id="knowledge_v1",
        queries=[query_vec],
        num_neighbors=k
    )
    return [{"id": n.id, "distance": n.distance} for n in response[0]]

# AlloyDB pgvector example
import psycopg2
import json

conn = psycopg2.connect(dsn="postgresql://user:pass@alloydb-ip/mydb")

# Create table with vector column
with conn.cursor() as cur:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            content TEXT,
            embedding vector(768),
            department TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    cur.execute("CREATE INDEX ON documents USING hnsw (embedding vector_cosine_ops)")
    conn.commit()

# Hybrid query: SQL filter + vector similarity
def hybrid_alloydb_search(query: str, department: str, k: int = 5) -> list:
    query_vec = embed_text([query])[0]
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, content, 1 - (embedding <=> %s::vector) AS similarity
            FROM documents
            WHERE department = %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """, (json.dumps(query_vec), department, json.dumps(query_vec), k))
        return cur.fetchall()
```

---

## Vertex AI Vector Search Deep Dive

### Concept

Vertex AI Vector Search (formerly Matching Engine) is Google's managed ANN service, built on ScaNN (Scalable Approximate Nearest Neighbors) — Google's own ANN algorithm used in production at Google Search and YouTube recommendations scale.

**Index types:**
- **Tree-AH (Recommended)**: Combines tree-based space partitioning with asymmetric hashing. Best recall at most scales.
- **Brute Force**: Exact k-NN (expensive, for small corpora or ground truth evaluation only)

**Key configuration parameters:**
- `dimensions`: must match your embedding model (768 for text-embedding-004)
- `approximate_neighbors_count`: affects recall — 10-20 is typical
- `leaf_node_embedding_count` + `leaf_nodes_to_search_percent`: trade-off between recall and speed
- `distance_measure_type`: COSINE_DISTANCE, DOT_PRODUCT_DISTANCE, SQUARED_L2_DISTANCE

**Streaming vs batch updates:**
- **Batch update**: re-index from GCS JSONL files. Cheaper, higher recall, for large infrequent updates
- **Streaming update**: real-time upsert via API. Slightly lower recall during the streaming window, for real-time corpora

### Code

```python
# Streaming upsert to deployed index
from google.cloud.aiplatform_v1 import MatchServiceClient
from google.cloud.aiplatform_v1.types import UpsertDatapointsRequest, IndexDatapoint

match_client = MatchServiceClient(
    client_options={"api_endpoint": f"{REGION}-aiplatform.googleapis.com"}
)

# Upsert a batch of vectors
datapoints = [
    IndexDatapoint(
        datapoint_id=f"doc_{i}",
        feature_vector=embedding_vectors[i],
        restricts=[
            IndexDatapoint.Restriction(
                namespace="department",
                allow_list=["engineering"]  # metadata for pre-filtering
            )
        ]
    )
    for i in range(len(embedding_vectors))
]

request = UpsertDatapointsRequest(
    index=f"projects/{PROJECT_ID}/locations/{REGION}/indexes/{INDEX_ID}",
    datapoints=datapoints
)
match_client.upsert_datapoints(request=request)
```

---

## Vertex AI ReRanker API

### Concept

Vertex AI provides a managed cross-encoder reranker (`text-reranker@001`) that integrates with both the RAG Engine corpus and custom Vertex AI Vector Search indices. It accepts (query, document) pairs and returns a relevance score in [0, 1].

**Impact of adding the reranker to a typical RAG pipeline:**

| Metric | Before ReRanker (k=20, dense only) | After ReRanker (k=20 → top 5) |
|---|---|---|
| Recall@5 | 0.70 | 0.75 |
| Precision@5 | 0.68 | 0.84 |
| Faithfulness (downstream RAGAS) | 0.72 | 0.86 |
| Latency added | — | ~80–150ms |

Precision improvement is larger than recall improvement — the reranker primarily reduces noise rather than recovering missed documents.

**Best practices:**
- Over-retrieve at stage 1: set k=15–25 before reranking; narrowing from k=5 gives no room for the reranker to improve
- Score threshold: filter documents with reranker score < 0.4 before passing to the LLM to avoid low-signal context
- Combine with Matching Engine `restricts` (metadata filtering) before reranking to reduce latency

### Code

```python
from vertexai.language_models import TextEmbeddingModel
from google.cloud.aiplatform_v1 import RerankServiceClient

# Vertex AI ReRanker via the Ranking API (us-central1)
from google.cloud import discoveryengine_v1alpha as discoveryengine

def vertex_rerank(
    query: str,
    candidates: list[str],
    project_id: str,
    location: str = "global",
    top_n: int = 5
) -> list[tuple[str, float]]:
    """Rerank candidate documents using Vertex AI ReRanker API."""
    client = discoveryengine.RankServiceClient()
    
    ranking_config = client.ranking_config_path(
        project=project_id,
        location=location,
        ranking_config="default_ranking_config"
    )
    
    records = [
        discoveryengine.RankingRecord(id=str(i), content=doc)
        for i, doc in enumerate(candidates)
    ]
    
    request = discoveryengine.RankRequest(
        ranking_config=ranking_config,
        model="semantic-ranker-512@latest",
        top_n=top_n,
        query=query,
        records=records,
    )
    
    response = client.rank(request=request)
    return [(candidates[int(r.id)], r.score) for r in response.records]


# Full pipeline: Vector Search → ReRanker → Gemini
def rag_with_reranker(
    query: str,
    project_id: str,
    vector_endpoint,
    top_k_retrieve: int = 20,
    top_k_rerank: int = 5
) -> str:
    # Stage 1: dense retrieval
    query_vec = embed_text([query])[0]
    raw_results = vector_endpoint.find_neighbors(
        deployed_index_id="knowledge_v1",
        queries=[query_vec],
        num_neighbors=top_k_retrieve
    )
    candidate_texts = [fetch_document_text(n.id) for n in raw_results[0]]
    
    # Stage 2: rerank
    reranked = vertex_rerank(query, candidate_texts, project_id, top_n=top_k_rerank)
    
    # Filter low-confidence results
    filtered = [(doc, score) for doc, score in reranked if score > 0.4]
    context = "\n\n".join([doc for doc, _ in filtered])
    
    # Stage 3: generate
    from vertexai.generative_models import GenerativeModel
    model = GenerativeModel("gemini-1.5-flash-001")
    return model.generate_content(
        f"Context:\n{context}\n\nQuestion: {query}\nAnswer:"
    ).text
```

---

## Interview Q&A

**Q: What are the three main Vertex AI RAG services and when would you choose each?** `[Medium]`
A: Vertex AI Search for managed enterprise search where you want a search UI + API with no retrieval code to write; it handles chunking, embedding, and ranking automatically. Vertex AI RAG Engine for managed retrieval directly integrated with Gemini — you get a RagCorpus, file import, and retrieval API, but you're tied to Gemini as the generator. Custom RAG (Vertex AI Vector Search + Cloud Run + your own LLM) when you need control over chunking strategy, embedding model choice, hybrid search, or multi-tenancy at scale. The custom path is most work but most flexible.

**Q: How does Vertex AI RAG Engine integrate with Gemini natively?** `[Medium]`
A: You create a `Tool.from_retrieval()` wrapping a `VertexRagStore` with your corpus name, then pass it to `GenerativeModel`. When Gemini generates a response, it automatically queries the RAG corpus as a tool call, retrieves relevant chunks, and grounds its answer. You don't write the retrieval-augment-generate loop explicitly — Gemini decides when to call the retrieval tool. This is the simplest path to production RAG on GCP if you're already using Gemini.

**Q: When would you use Google Search grounding vs your own RAG corpus?** `[Easy]`
A: Google Search grounding for public, recent information (current events, public company financials, latest product specs) where maintaining your own index would be stale or impractical. Your own RAG corpus for private internal documents (policy manuals, internal wikis, proprietary research, customer data) that are not public and cannot be retrieved via web search. Many production systems use both: RAG corpus for internal knowledge + Google Search grounding for current public context.

**Q: What is the dynamic retrieval threshold in Grounding and how do you tune it?** `[Hard]`
A: The dynamic_threshold (0.0-1.0) controls when grounding activates. Below the threshold, the model uses parametric knowledge without retrieval. Above it, the model grounds in Google Search. A higher threshold means more queries trigger grounding. Tuning: start with 0.5, evaluate on a test set of queries where you know whether grounding is needed. For time-sensitive domains (news, prices), use 0.3-0.5 to trigger grounding more often. For general knowledge Q&A, use 0.7-0.8 to avoid unnecessary retrieval overhead. Monitor the `grounding_metadata` in responses to see how often grounding fires.

**Q: How does Vertex AI Vector Search differ from FAISS in production?** `[Medium]`
A: FAISS is a library — you manage the index in memory, handle persistence, and scale it yourself. Vertex AI Vector Search is a managed service: it handles horizontal scaling, replication, index serving infrastructure, health checks, and auto-scaling based on QPS. You pay per query and per GB stored. FAISS is appropriate for development, small corpora (<1M vectors), or when you need full control over the ANN algorithm. Vertex AI Vector Search is appropriate for production at any scale where you want a managed endpoint with SLAs, especially when already on GCP.

**Q: How would you design a multi-tenant RAG system on Vertex AI where each customer's data must be completely isolated?** `[Hard]`
A: Two approaches: (1) **Separate RAG Engine corpora per tenant** — create one RagCorpus per customer, store the corpus name per customer in your database, query only the customer's corpus per request. Strong isolation, simple access control, but N corpora to manage. (2) **Vertex AI Vector Search with namespace-based filtering** — one index with `restricts` (metadata filters) scoped to tenant_id; every query includes a mandatory `numeric_restricts` or `restricts` filter. The second approach is more operationally efficient at scale (one index endpoint vs hundreds of corpora), but requires strict enforcement of the tenant filter at the application layer — a missed filter leaks data. For enterprise SLA and compliance, approach 1 (corpus-per-tenant) is safer.

**Q: What are the limitations of Vertex AI RAG Engine compared to building custom RAG?** `[Medium]`
A: Key limitations: (1) **Gemini-only** — the native tool integration only works with Gemini models; you can use `RetrieveContexts` API with any generator, but lose the native tool flow. (2) **Limited chunking control** — you specify chunk_size and chunk_overlap, but can't use semantic chunking or custom chunking logic. (3) **No hybrid search** — pure dense retrieval; no BM25 or hybrid fusion. (4) **No custom embedding model** — uses Google's internal embeddings, which may not be optimal for specialized domains (legal, medical, code). (5) **No reranker integration** — no cross-encoder reranking step. For production quality on specialized domains, custom RAG on Vertex AI Vector Search + your own embedding + Cohere Rerank often achieves 15-25% better Recall@5.
