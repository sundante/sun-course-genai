# Embeddings and Vector Stores

## What Are Embeddings

### Concept

An embedding is a dense, fixed-length numerical vector that represents the semantic meaning of text (or any other modality). The key property: **semantically similar inputs map to nearby points in the embedding space**, so similarity in vector space approximates similarity in meaning.

**How embeddings are created:**
A neural network (the embedding model) is trained on a large corpus with an objective that forces semantically related text to produce similar output vectors. For sentence transformers, the training objective is typically contrastive learning: similar sentences have high cosine similarity, dissimilar sentences have low cosine similarity.

**Dimensionality:**
- `text-embedding-004` (Google): 768 dimensions
- `text-embedding-3-large` (OpenAI): 3072 dimensions (also supports Matryoshka compression)
- `bge-large-en-v1.5` (open source): 1024 dimensions
- Larger dimensions ≠ always better. Matryoshka Representation Learning (MRL) allows truncating to lower dimensions with minimal quality loss.

**Bi-encoder vs Cross-encoder:**

| | Bi-encoder | Cross-encoder |
|---|---|---|
| **How** | Query and document embedded independently | Query+document concatenated, scored together |
| **Speed** | Fast — embed query once, search all docs | Slow — must run model on each (query, doc) pair |
| **Quality** | Good | Excellent |
| **Use in RAG** | First-stage retrieval | Re-ranking top-k results |
| **Example** | `text-embedding-004` | `cross-encoder/ms-marco-MiniLM-L-6-v2` |

**Why this architecture matters:** You can't afford to run a cross-encoder at query time against 10M documents. Bi-encoder is fast enough for ANN search; cross-encoder is fast enough to re-score only the top-100 retrieved candidates.

### Code

```python
from google.cloud import aiplatform
from vertexai.language_models import TextEmbeddingModel
import numpy as np

# Google's text-embedding-004 via Vertex AI
model = TextEmbeddingModel.from_pretrained("text-embedding-004")

def embed_text(texts: list[str]) -> list[list[float]]:
    embeddings = model.get_embeddings(texts)
    return [e.values for e in embeddings]

# Embed query and document
query_vec = embed_text(["What is the refund policy?"])[0]
doc_vec = embed_text(["Customers may request a full refund within 30 days."])[0]

# Cosine similarity
def cosine_sim(a, b):
    a, b = np.array(a), np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

print(f"Similarity: {cosine_sim(query_vec, doc_vec):.4f}")
```

---

## How Semantic Search Works

### Concept

Semantic search is approximate nearest neighbor (ANN) search in embedding space. The full pipeline:

```
Query text → embedding model → query vector (768-dim)
                                        ↓
                           ANN index (HNSW / IVF)
                                        ↓
               top-k most similar vectors → retrieve document chunks
```

**Why ANN and not exact nearest neighbor?**
Exact k-NN requires computing the distance from the query to every vector in the index — O(n × d) where n is corpus size and d is dimensions. At 10M documents with 768 dimensions, that's 7.68 billion multiplications per query. ANN algorithms trade a small recall loss (typically 1-5%) for 10-1000x speedup.

**The Recall@k metric:** For a given query, Recall@k = (number of relevant docs in top-k) / (total relevant docs). At Recall@10 = 0.85, 15% of relevant documents are missed by the first-stage ANN retrieval.

**Indexing trade-off (build time vs query time vs recall):**
- More connections in HNSW (higher M parameter) → better recall, slower build
- More IVF clusters → better recall at scale, slower build  
- Adding PQ compression → smaller memory footprint, slightly lower recall

### Code

```python
import faiss
import numpy as np

# Build an HNSW index (good default for most production use cases)
d = 768  # embedding dimensions
M = 32   # number of connections per node (higher = better recall, more memory)

index = faiss.IndexHNSWFlat(d, M)
index.hnsw.efConstruction = 200  # search depth during construction (higher = better recall)

# Add document vectors
doc_vectors = np.array(embed_text(documents)).astype('float32')
index.add(doc_vectors)

# Search at query time
index.hnsw.efSearch = 64  # search depth at query time (can be tuned after build)
query_vector = np.array(embed_text(["refund policy"])[0]).astype('float32').reshape(1, -1)

distances, indices = index.search(query_vector, k=4)  # returns top 4 nearest neighbors
retrieved_docs = [documents[i] for i in indices[0]]
```

---

## Similarity Metrics

### Concept

Three similarity/distance metrics are commonly used. Knowing which to use when is a genuine interview question.

**Cosine Similarity**
```
cos(q, d) = (q · d) / (||q|| × ||d||)     range: [-1, 1]
```
Measures the angle between vectors, ignoring magnitude. Two vectors pointing in the same direction have cosine similarity = 1, regardless of their length. **Best for: text embeddings**, because the magnitude of an embedding often reflects the "strength" of features, not relevance.

**Dot Product (Inner Product)**
```
q · d = Σ(qᵢ × dᵢ)     range: (-∞, +∞)
```
Measures both angle AND magnitude. If vectors are L2-normalized (unit vectors), dot product equals cosine similarity. **Best for: embeddings that have been explicitly trained with dot product** (e.g., some bi-encoder training regimes optimize dot product directly).

**Euclidean Distance (L2)**
```
||q - d||₂ = √(Σ(qᵢ - dᵢ)²)     range: [0, ∞)
```
Measures straight-line distance in the vector space. For embeddings with unit norm, L2 distance and cosine similarity are equivalent (monotonically related). **Best for: low-dimensional embeddings**, or when magnitude differences are meaningful (e.g., image embeddings).

**When cosine similarity outperforms dot product for text:**
Text embedding models like `text-embedding-004` output vectors with varying L2 norms. The norm often correlates with confidence or lexical density, not semantic relevance. Normalizing to unit vectors (which cosine similarity does implicitly) removes this bias. Using raw dot product would unfairly rank verbose, information-dense documents higher regardless of topical relevance.

**Practical note:** Most vector databases use cosine similarity as default for text. Always check what metric your embedding model was trained with — using a different metric degrades recall.

### Code

```python
import numpy as np

def cosine_similarity(a: list[float], b: list[float]) -> float:
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def dot_product(a: list[float], b: list[float]) -> float:
    return float(np.dot(np.array(a), np.array(b)))

def euclidean_distance(a: list[float], b: list[float]) -> float:
    return float(np.linalg.norm(np.array(a) - np.array(b)))

# When vectors are L2-normalized: cosine ≈ dot product
a_norm = a / np.linalg.norm(a)
b_norm = b / np.linalg.norm(b)
assert abs(cosine_similarity(a_norm, b_norm) - dot_product(a_norm, b_norm)) < 1e-6
```

---

## ANN Algorithms: HNSW, IVF, and PQ

### Concept

**HNSW (Hierarchical Navigable Small World)**
A graph-based ANN algorithm. Builds a multilayer graph where nodes are vectors and edges connect neighbors. Search navigates this graph greedily, starting from an entry point at the top layer and descending to find nearest neighbors.

- **Pros:** Very high recall at low k, fast query time, works well in-memory
- **Cons:** Build is slower for large corpora; memory-heavy (each vector has M outgoing edges stored)
- **When to use:** Default choice for most RAG systems up to ~10M vectors

**IVF (Inverted File Index)**
Clusters vectors into `nlist` Voronoi cells (typically using k-means). At query time, searches only `nprobe` of the closest clusters rather than all clusters.

- **Pros:** More memory-efficient than HNSW, scales to hundreds of millions of vectors
- **Cons:** Lower recall unless `nprobe` is set high; recall degrades for out-of-distribution queries
- **When to use:** Very large corpora (>10M vectors) where HNSW's memory footprint is prohibitive

**PQ (Product Quantization)**
Compresses each vector by dividing it into M sub-vectors and quantizing each sub-vector to a codebook entry. Reduces memory 4-16x at the cost of 5-10% recall drop.

- **Typically combined with IVF:** `IndexIVFPQ` in FAISS = clustering + compression
- **When to use:** When memory is the primary constraint and 5-10% recall loss is acceptable

**Vertex AI Vector Search** uses HNSW internally and handles replication, scaling, and updates for you.

### Code

```python
import faiss

d = 768  # embedding dimension
n_vecs = 1_000_000  # 1M documents

# HNSW — best recall for moderate scale
hnsw_index = faiss.IndexHNSWFlat(d, 32)  # M=32

# IVF — for large scale
nlist = 4096  # number of clusters (rule of thumb: sqrt(n_vecs) to 4*sqrt(n_vecs))
quantizer = faiss.IndexFlatL2(d)
ivf_index = faiss.IndexIVFFlat(quantizer, d, nlist)
ivf_index.train(doc_vectors)  # must train on a representative sample
ivf_index.nprobe = 64  # search 64 of 4096 clusters (tune for recall vs speed)

# IVF + PQ — maximum compression
M_pq = 8   # number of sub-vectors
nbits = 8  # bits per sub-vector (256 centroids)
ivfpq_index = faiss.IndexIVFPQ(quantizer, d, nlist, M_pq, nbits)
ivfpq_index.train(doc_vectors)
# Memory: d*4 bytes/vector (flat) → M_pq bytes/vector (PQ) → 96x compression for d=768, M_pq=8
```

---

## Vector Databases

### Concept

A vector database stores embedding vectors alongside metadata and provides ANN search, filtering, and CRUD operations at scale. Choosing the right one is a legitimate system design decision.

| Database | Type | Scale | Filter support | Managed | When to use |
|---|---|---|---|---|---|
| **Chroma** | In-process / local | Small (<1M) | Basic | No | Local dev, prototypes |
| **Weaviate** | Self-hosted / cloud | Medium-Large | Rich (GraphQL) | Yes (cloud) | Multi-tenancy, complex filters |
| **Pinecone** | Fully managed | Very large | Metadata filters | Yes | Teams wanting no infra |
| **Qdrant** | Self-hosted / cloud | Large | Rich (JSON payload) | Yes (cloud) | Full control + payload filtering |
| **pgvector** | PostgreSQL extension | Medium | Full SQL | No (self-host) | Existing Postgres infra |
| **Vertex AI Vector Search** | GCP managed | Very large (1B+) | Numeric/string | Yes | GCP-native, Gemini integration |
| **AlloyDB (pgvector)** | GCP managed Postgres | Medium-Large | Full SQL | Yes | SQL + vector, GCP |

**Key capabilities to evaluate:**
- **Metadata pre-filtering** — filter by document source, date, category BEFORE ANN search (significant performance win)
- **Multi-tenancy** — namespace/tenant isolation so one tenant's data isn't retrievable by another
- **Hybrid search** — built-in BM25 + vector search (Weaviate, Qdrant)
- **Streaming updates** — can you upsert vectors in real-time or only in batch?

### Code (Chroma local + Pinecone production pattern)

```python
# Local development with Chroma
from langchain_community.vectorstores import Chroma

local_vs = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    collection_metadata={"hnsw:space": "cosine"}  # explicit metric
)

# Production with Pinecone
from langchain_pinecone import PineconeVectorStore
import pinecone

pc = pinecone.Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("knowledge-base")

prod_vs = PineconeVectorStore(
    index=index,
    embedding=embeddings,
    namespace="enterprise-docs"  # tenant isolation
)

# Metadata pre-filtering
results = prod_vs.similarity_search(
    query="refund policy",
    k=4,
    filter={"department": "legal", "year": {"$gte": 2023}}  # pre-filter before ANN
)
```

---

## Embedding Model Selection

### Concept

Picking the wrong embedding model is one of the most common production RAG mistakes. The model determines the ceiling of retrieval quality — no amount of downstream reranking recovers from poor embeddings.

**MTEB (Massive Text Embedding Benchmark)** is the authoritative benchmark for evaluating embedding models. Key tasks: retrieval, reranking, classification, clustering. Always check MTEB leaderboard scores in your domain.

**Selection framework:**

| Criterion | Questions to Ask |
|---|---|
| **Quality** | What's the MTEB Retrieval score? Does it have a domain-specific eval? |
| **Dimension** | 768 is practical; 1536+ improves quality but increases storage/compute cost |
| **Latency** | Can you embed queries within your SLA? (typical: <50ms for bi-encoder) |
| **Language** | Multilingual required? → `multilingual-e5-large` or `text-multilingual-embedding-002` |
| **Cost** | API calls per query → cached? Off-the-shelf? Self-hosted? |
| **Domain** | Medical, legal, code — domain-specific models often outperform general-purpose by 5-15% |

**Key models (2024-2025):**

| Model | Dims | MTEB Avg | Notes |
|---|---|---|---|
| `text-embedding-004` (Google) | 768 | 66.3 | Solid all-around, GCP native |
| `text-embedding-3-large` (OpenAI) | 3072 | 64.6 | MRL: can truncate to 256 |
| `bge-large-en-v1.5` (BAAI) | 1024 | 64.2 | Best open-source for English |
| `e5-mistral-7b-instruct` | 4096 | 66.6 | Instruction-tuned, best quality |
| `multilingual-e5-large` | 1024 | 62.2 | Best open multilingual |
| `text-multilingual-embedding-002` (Google) | 768 | ~62 | GCP multilingual |

**Matryoshka Representation Learning (MRL):** Models trained with MRL (like OpenAI's text-embedding-3 series) encode information hierarchically — truncating the vector to fewer dimensions preserves most quality. This lets you store compressed vectors at low cost and expand to full dimensions for quality-critical reranking.

### Code

```python
# Comparing embedding models for domain-specific retrieval
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from sentence_transformers import SentenceTransformer
import numpy as np

# Google text-embedding-004
google_model = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

# BGE-large (open source, self-hosted)
bge_model = SentenceTransformer("BAAI/bge-large-en-v1.5")

def evaluate_retrieval(model, query: str, docs: list[str], relevant_idx: int) -> float:
    """Returns rank of the relevant document (lower = better)."""
    if hasattr(model, 'embed_query'):
        q_vec = model.embed_query(query)
        d_vecs = model.embed_documents(docs)
    else:
        q_vec = model.encode([query])[0]
        d_vecs = model.encode(docs)
    
    scores = [np.dot(q_vec, d) / (np.linalg.norm(q_vec) * np.linalg.norm(d)) for d in d_vecs]
    rank = sorted(range(len(scores)), key=lambda i: -scores[i]).index(relevant_idx) + 1
    return rank

# Run on your domain-specific test set before committing to a model
```

---

## Interview Q&A

**Q: Why must you use the same embedding model for indexing and querying?** `[Easy]`
A: Each embedding model defines its own vector space — a specific mapping from text to points in n-dimensional space. The similarity scores (cosine, dot product) are only meaningful within the same coordinate system. If you index with model A and query with model B, the query vector lives in a completely different space, making similarity scores meaningless. The result: the system silently returns random-looking results with no error or warning.

**Q: When does cosine similarity outperform dot product for text retrieval?** `[Medium]`
A: When embedding vectors have non-unit norms that don't correlate with relevance. Text embedding models often produce vectors with varying magnitudes — verbose, information-dense chunks get higher magnitude vectors. Dot product unfairly boosts these high-magnitude vectors even when they're less topically relevant. Cosine similarity normalizes away magnitude, so only the angular direction (semantic direction) matters. Exception: if your model was explicitly trained with dot product as the objective (some DPR variants), use dot product.

**Q: How does HNSW achieve fast approximate nearest neighbor search?** `[Hard]`
A: HNSW builds a multilayer graph where each node represents a vector. The top layers are sparse (long-range connections for fast navigation), and lower layers are dense (local connections for precision). At query time, search starts at the top layer and greedily navigates toward the query vector, then descends to lower layers for refinement. The key insight is that greedy graph navigation in high-dimensional space finds approximate nearest neighbors much faster than exhaustive search. The `efSearch` parameter controls how many candidate neighbors to explore at each layer — higher values give better recall at the cost of query latency.

**Q: Your RAG system needs to serve 10 tenants with 5M documents each (50M total) with strict data isolation. What vector database architecture would you use?** `[Hard]`
A: Namespace/tenant-isolated indices. Most vector databases (Pinecone, Qdrant, Weaviate) support namespace or collection-level isolation where data and access controls are separated per tenant. Architecture: one namespace per tenant, metadata filtering enforces tenant boundaries at the application layer. Alternative: separate indices per tenant — stronger isolation, but higher operational overhead. For 50M vectors, Pinecone or Vertex AI Vector Search are good managed options; Weaviate or Qdrant if you want self-hosted control. Always benchmark: at this scale, namespace isolation in a single index is often better than 10 separate indices due to index build costs.

**Q: What is Matryoshka Representation Learning and why is it useful for production RAG?** `[Hard]`
A: MRL trains embedding models to encode information in a nested way: the first N dimensions of the vector capture the most important semantic information, and adding more dimensions adds progressively finer detail. This means you can truncate an MRL-trained vector (like OpenAI's text-embedding-3 series) to 256 or 512 dimensions with minimal quality loss instead of storing the full 3072 dimensions. In production, this enables a two-stage retrieval: first-stage retrieval with compressed 256-dim vectors (fast, cheap), followed by re-scoring with the full 3072-dim vectors for the top-k candidates (precision). This cuts storage and query costs significantly.

**Q: What is the difference between a bi-encoder and a cross-encoder, and when would you use each?** `[Medium]`
A: A bi-encoder embeds the query and document independently, producing two separate vectors that are compared by cosine similarity. This is fast because documents can be pre-embedded offline — at query time, you only embed the query. A cross-encoder takes a (query, document) pair as a single input and produces a scalar relevance score; it sees the interaction between query and document terms, giving much higher precision. Cross-encoders are 10-100x slower because they must process each (query, document) pair at query time. The standard pattern: bi-encoder for first-stage ANN retrieval (fast, moderate precision), cross-encoder for reranking top-k candidates (slow, high precision).

**Q: How would you reduce embedding costs in a RAG system with 10 million documents and 100K daily queries?** `[Medium]`
A: Three levers: (1) **Batch indexing** — embed documents in batches of 100-2048 (most API providers give bulk discounts and lower per-call overhead), not one by one. (2) **Query embedding cache** — hash the query string and cache the embedding; many users ask near-identical questions. A TTL of 24 hours with an LRU cache can hit 30-60% cache rates for customer support use cases. (3) **Smaller embedding model** — if quality is acceptable, a 256-dim MRL-truncated model costs 6x less to store and compute than the full 1536-dim model. (4) **Embedding model self-hosting** — open-source models (BGE, E5) hosted on Cloud Run or GKE eliminate per-token API costs at the cost of infrastructure management.
