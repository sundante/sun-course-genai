# Retrieval Strategies

## Dense Retrieval (Embedding-Based)

### Concept

Dense retrieval uses bi-encoder models to embed both queries and documents into the same vector space, then retrieves by approximate nearest neighbor (ANN) search. It is the backbone of modern RAG — semantically equivalent text has similar vectors regardless of exact word choice.

**How it works:**
1. Offline: embed every document chunk → store in vector index
2. Online: embed query → ANN search → top-k document vectors → return chunks

**Strengths:**
- Handles paraphrase and synonym: "show me pricing" retrieves chunks about "cost" and "rate plans"
- Language-independent (multilingual models)
- No index to maintain when query vocabulary changes

**Weaknesses (important for interviews):**
- **Lexical gap for rare terms**: Product codes, proper nouns, abbreviations ("CVE-2024-1234", "SOC2 Type II") — embedding models trained on general text may not represent these precisely
- **Recall ceiling**: Even the best bi-encoder misses ~10-15% of relevant documents that BM25 finds, especially for exact-match queries
- **Out-of-distribution queries**: Queries far from the training distribution of the embedding model retrieve poorly

**Key insight:** Dense retrieval is a **recall** mechanism at first-stage retrieval. You retrieve k=20-50 candidates to ensure relevant documents are in the candidate set, then use a cross-encoder reranker to re-score and return the top 4-6.

### Code

```python
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma

embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
vectorstore = Chroma(persist_directory="./db", embedding_function=embeddings)

# Dense retriever with score threshold
dense_retriever = vectorstore.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={
        "k": 20,          # retrieve many for reranking
        "score_threshold": 0.6  # filter very low similarity results
    }
)
```

---

## Sparse Retrieval (BM25)

### Concept

Sparse retrieval is keyword-based. Documents and queries are represented as sparse vectors in term space (one dimension per vocabulary term, most values zero). BM25 is the gold standard sparse retrieval algorithm.

**BM25 Formula:**
```
BM25(q, d) = Σᵢ IDF(qᵢ) × [f(qᵢ, d) × (k₁ + 1)] / [f(qᵢ, d) + k₁ × (1 - b + b × |d|/avgdl)]

Where:
  f(qᵢ, d) = term frequency of query term i in document d
  |d|       = document length (in terms)
  avgdl     = average document length in the corpus
  k₁        = term frequency saturation parameter (typically 1.2–2.0)
  b         = length normalization parameter (typically 0.75)
  IDF(qᵢ)   = log((N - n(qᵢ) + 0.5) / (n(qᵢ) + 0.5) + 1)
               N = total documents, n(qᵢ) = documents containing term i
```

**Why BM25 outperforms raw TF-IDF:**
1. **Saturation**: TF-IDF gives unbounded reward for high-frequency terms. BM25's `k₁` parameter saturates the term frequency reward — a term appearing 100 times is not 100x more relevant than appearing once. The formula asymptotes to `(k₁+1) × IDF` as frequency → ∞.
2. **Length normalization**: BM25 normalizes by document length via the `b` parameter, preventing long documents from always winning. TF-IDF has no length normalization.

**Worked example:**
- Query: "refund policy"
- Doc A (50 words): "refund" appears 3 times, "policy" appears 2 times
- Doc B (500 words): "refund" appears 10 times, "policy" appears 8 times
- TF-IDF would rank Doc B higher (more occurrences). BM25 with b=0.75 normalizes Doc B's length, likely ranking Doc A higher because it's more focused on the query terms.

**When sparse beats dense:**
- Exact technical terms: model numbers, CVE IDs, product SKUs, legal citations
- Rare named entities: specific company names, person names not in training data
- Short queries where context is insufficient for semantic matching
- Numeric matching: "version 3.4.2", "RFC 7231"

### Code

```python
from langchain_community.retrievers import BM25Retriever
from langchain.schema import Document
import math

# BM25 retriever (uses rank_bm25 under the hood)
bm25_retriever = BM25Retriever.from_documents(chunks, k=10)

# Custom BM25 from scratch (for interviews — shows you understand the algorithm)
class SimpleBM25:
    def __init__(self, corpus: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.corpus = corpus
        self.N = len(corpus)
        self.avgdl = sum(len(d) for d in corpus) / self.N
        self.df = {}  # document frequency per term
        self.idf = {}
        for doc in corpus:
            for term in set(doc):
                self.df[term] = self.df.get(term, 0) + 1
        for term, df in self.df.items():
            self.idf[term] = math.log((self.N - df + 0.5) / (df + 0.5) + 1)

    def score(self, query: list[str], doc: list[str]) -> float:
        score = 0.0
        dl = len(doc)
        tf_map = {}
        for term in doc:
            tf_map[term] = tf_map.get(term, 0) + 1
        for term in query:
            if term not in self.idf:
                continue
            tf = tf_map.get(term, 0)
            idf = self.idf[term]
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * dl / self.avgdl)
            score += idf * numerator / denominator
        return score

    def retrieve(self, query: list[str], k: int = 5) -> list[int]:
        scores = [(i, self.score(query, doc)) for i, doc in enumerate(self.corpus)]
        return [i for i, _ in sorted(scores, key=lambda x: -x[1])[:k]]
```

---

## Hybrid Search (Dense + Sparse)

### Concept

Hybrid search combines dense retrieval (semantic) and sparse retrieval (keyword) to get the best of both. Dense retrieval handles semantic matching; sparse retrieval handles exact keyword matching. Together, they achieve higher recall than either alone — empirically 5-15% Recall@10 improvement.

**Reciprocal Rank Fusion (RRF)**

RRF is the standard algorithm for merging ranked lists from multiple retrievers without requiring score normalization:

```
RRF(d) = Σᵣ 1 / (k + rank(d, r))

Where:
  r     = each retrieval system (dense, sparse, etc.)
  rank  = rank of document d in system r (1-indexed)
  k     = constant to prevent high-ranking documents from dominating (typically 60)
```

**Why RRF over score combination:**
- Dense and sparse scores are on completely different scales (cosine similarity vs BM25 score) — you cannot add them directly without normalization
- RRF only uses rank positions, not scores — robust to scale differences
- The `k=60` constant means rank 1 gets score 1/61 ≈ 0.016, rank 10 gets 1/70 ≈ 0.014 — top results from both systems are always promoted
- Documents appearing at the top of BOTH lists get a strong boost (sum of two high RRF scores)

**Alpha weighting (alternative to RRF):**
Some systems use normalized score interpolation:
```
final_score(d) = α × dense_score(d) + (1-α) × bm25_score(d)
```
This requires normalizing both score distributions to [0,1]. α is tuned on a validation set — typically 0.5-0.7 for general domains, lower for jargon-heavy domains.

### Code

```python
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever

# BM25 retriever
bm25 = BM25Retriever.from_documents(chunks)
bm25.k = 10

# Dense retriever  
dense = vectorstore.as_retriever(search_kwargs={"k": 10})

# Hybrid with RRF (EnsembleRetriever uses RRF internally)
hybrid = EnsembleRetriever(
    retrievers=[bm25, dense],
    weights=[0.4, 0.6]  # weights tune the RRF contribution, not direct score mixing
)

results = hybrid.invoke("CVE-2024-1234 authentication bypass")
# BM25 will surface exact CVE ID matches; dense will surface semantically related security docs


# Manual RRF implementation (for interviews)
def reciprocal_rank_fusion(results_lists: list[list], k: int = 60) -> list:
    scores = {}
    for results in results_lists:
        for rank, doc in enumerate(results, start=1):
            doc_id = doc.page_content  # use content as ID
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank)
    return sorted(scores.keys(), key=lambda d: -scores[d])
```

---

## Re-ranking

### Concept

Re-ranking is a post-retrieval step that re-scores the top-k candidates from the first-stage retriever using a more expensive but more precise model. The two-stage approach (bi-encoder retrieval → cross-encoder reranking) is the standard production pattern.

**Why re-rank?**
First-stage retrieval (ANN search) optimizes for speed using bi-encoders that process query and document independently. Cross-encoders see the (query, document) pair jointly, capturing fine-grained interaction signals like query term proximity, negations, and conditional relevance. This typically improves Precision@3 by 15-30%.

**Re-ranking latency math:**
- Dense retrieval: embed query (~10ms) + ANN search (~5ms) = ~15ms
- Re-ranking top-20: cross-encoder inference on 20 (query, doc) pairs = 80-200ms
- Total: ~100-220ms — acceptable for most RAG systems

**Bi-Encoder vs Cross-Encoder — deep dive:**

| Dimension | Bi-Encoder (Dual Encoder) | Cross-Encoder |
|---|---|---|
| **Input encoding** | Query and document encoded independently into separate vectors | Query and document concatenated as one input: `[CLS] query [SEP] document [SEP]` |
| **Precomputation** | Document embeddings computed offline and cached | Cannot precompute — requires the query at inference time |
| **Speed** | Fast: ANN search on precomputed vectors (~5–15ms) | Slow: full model forward pass per (query, doc) pair (~5–10ms per pair; 100–200ms for 20 pairs) |
| **Accuracy** | Good for broad recall; misses subtle contextual cues (negations, conditionals) | High precision; full token-level attention between query and document captures nuanced relevance |
| **Scalability** | Scales to billions of documents (ANN index) | Not scalable to first-stage retrieval; limited to re-scoring ~20–50 candidates |
| **Use case** | First-stage retrieval: cast a wide net efficiently | Second-stage reranking: precision filter over candidate set |
| **Example models** | `text-embedding-004`, `BAAI/bge-m3`, `E5-mistral-7b` | `cross-encoder/ms-marco-MiniLM-L-6-v2`, `Cohere Rerank`, Vertex AI ReRanker |

**Interview tip:** "Bi-encoders are efficient for broad retrieval but miss subtle contextual cues — a query like 'what causes X NOT to work' can retrieve documents about 'X works well' because the negation is lost in the aggregate embedding. Cross-encoders attend to every token in both query and document jointly, so they correctly score the negative. The two-stage pattern uses bi-encoders to recall 20 candidates cheaply, then cross-encoders to re-score those 20 with full attention — you get recall efficiency plus precision quality."

**Cross-encoder models:**

| Model | Notes |
|---|---|
| `cross-encoder/ms-marco-MiniLM-L-6-v2` | Fast (6-layer), English, good quality |
| `cross-encoder/ms-marco-MiniLM-L-12-v2` | Slower, higher quality |
| `BAAI/bge-reranker-large` | Strong on Chinese + English |
| `Cohere Rerank API` | Managed, multilingual, state-of-the-art |
| `mixedbread-ai/mxbai-rerank-large-v1` | Strong on MTEB reranking benchmark |
| `Vertex AI ReRanker API` | GCP-native, integrates with Matching Engine, `semantic-ranker-512@latest` |

**Cohere Rerank** is the standard managed option for non-GCP stacks. **Vertex AI ReRanker** is the GCP-native choice, covered in depth in [09-Vertex-AI-RAG.md](09-Vertex-AI-RAG.md).

### Code

```python
# Open-source cross-encoder reranker
from sentence_transformers import CrossEncoder

reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

def rerank(query: str, candidates: list[str], top_k: int = 4) -> list[str]:
    pairs = [(query, doc) for doc in candidates]
    scores = reranker.predict(pairs)  # returns list of relevance scores
    ranked = sorted(zip(candidates, scores), key=lambda x: -x[1])
    return [doc for doc, _ in ranked[:top_k]]

# Cohere managed reranker
import cohere

co = cohere.Client(os.getenv("COHERE_API_KEY"))

def cohere_rerank(query: str, candidates: list[str], top_k: int = 4) -> list[str]:
    response = co.rerank(
        model="rerank-english-v3.0",
        query=query,
        documents=candidates,
        top_n=top_k
    )
    return [candidates[r.index] for r in response.results]

# LangChain integration
from langchain.retrievers.document_compressors import CohereRerank
from langchain.retrievers import ContextualCompressionRetriever

compressor = CohereRerank(top_n=4)
reranking_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=dense_retriever  # first-stage: retrieve 20, rerank to 4
)
```

---

## Query Transformation

### Concept

Query transformation modifies the user's query before retrieval to improve recall. This is the "pre-retrieval" stage of Advanced RAG.

**HyDE (Hypothetical Document Embeddings)**
Instead of embedding the raw query, ask the LLM to write a hypothetical document that would answer the query, then embed THAT document. The hypothesis is closer to the document distribution in embedding space than the short query.

```
Query: "What causes transformer attention to fail on long sequences?"
       ↓ LLM generates hypothesis
Hypothesis: "Transformer attention fails on long sequences due to the quadratic
             complexity O(n²) of the self-attention mechanism. As sequence length
             grows, memory and compute requirements grow quadratically..."
       ↓ Embed hypothesis (not query)
       ↓ ANN search using hypothesis vector
Better recall on technical documents.
```

**When HyDE helps:** Technical/domain-specific queries where the user's phrasing is brief but the relevant documents use detailed terminology. **When HyDE hurts:** If the hypothesis contains plausible-sounding but incorrect information, it retrieves documents about that incorrect hypothesis.

**Multi-Query Expansion**
Generate N variants of the query (different phrasings, perspectives), retrieve for each, then deduplicate and merge results.
```
Original: "authentication performance"
Variant 1: "login speed and latency"
Variant 2: "identity verification throughput"
Variant 3: "OAuth token validation benchmarks"
→ Retrieve for all 4, deduplicate, rerank merged set
```

**Step-Back Prompting**
Generalize the specific query to a broader question first, retrieve for the broader question, then use that broader context to answer the specific question.
```
Specific: "What is the melting point of sodium chloride?"
Step-back: "What are the physical properties of ionic compounds?"
→ Retrieve broader context first, then narrow answer
```

**MMR (Maximal Marginal Relevance)**
Returns diverse results by penalizing redundant chunks. For each subsequent chunk after the first, select the chunk that maximizes: `λ × similarity(query, chunk) - (1-λ) × max_similarity(chunk, already_selected)`. The λ parameter trades off relevance vs diversity (typically 0.5-0.7).

### Code

```python
# HyDE
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

hyde_prompt = ChatPromptTemplate.from_template(
    "Write a short technical paragraph that would answer this question. "
    "Be specific and use domain terminology.\n\nQuestion: {question}\n\nAnswer paragraph:"
)

def hyde_retrieve(query: str, k: int = 4) -> list:
    hypothesis = (hyde_prompt | llm | StrOutputParser()).invoke({"question": query})
    hypothesis_vec = embeddings.embed_query(hypothesis)
    return vectorstore.similarity_search_by_vector(hypothesis_vec, k=k)

# Multi-query retriever
from langchain.retrievers.multi_query import MultiQueryRetriever

multi_query = MultiQueryRetriever.from_llm(
    retriever=dense_retriever,
    llm=llm
)
# Internally generates 3-5 query variants and deduplicates results

# MMR retrieval (diversity-aware)
mmr_retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 4, "fetch_k": 20, "lambda_mult": 0.7}
    # fetch_k=20: retrieve 20 candidates, apply MMR, return top 4
    # lambda_mult=0.7: 70% relevance, 30% diversity
)
```

---

## Interview Q&A

**Q: Explain the BM25 formula and why it outperforms TF-IDF.** `[Hard]`
A: BM25 = Σ IDF(term) × saturation(TF) × length_normalization. The two key improvements over TF-IDF: (1) **Saturation**: BM25 uses a saturation function so term frequency contributes logarithmically rather than linearly — doubling occurrences doesn't double the score. This prevents very repetitive documents from dominating. (2) **Length normalization**: the `b` parameter (typically 0.75) normalizes scores by document length relative to corpus average. Short focused documents aren't penalized vs long comprehensive ones. TF-IDF has neither, so it rewards raw term frequency and long documents systematically.

**Q: When does sparse retrieval beat dense retrieval?** `[Medium]`
A: Three scenarios: (1) Rare exact-match terms — product codes, CVE IDs, model numbers, regulatory citations that appear infrequently in the embedding model's training data; the model can't represent them precisely. (2) Short queries with no context for semantic matching — a one-word query "churn" could mean many things; BM25 returns documents containing the exact word. (3) Highly technical jargon in specialized domains where the embedding model was trained on general-purpose text.

**Q: What is Reciprocal Rank Fusion and why is it preferred over score interpolation for hybrid search?** `[Hard]`
A: RRF(d) = Σ 1/(k + rank(d, r)) summed over each retriever r. It's preferred because dense and sparse retrieval scores are on incomparable scales — BM25 scores might range 0-20, cosine similarity 0-1. Normalizing these distributions to combine them requires assumptions about their shape (min-max, z-score, sigmoid). RRF sidesteps normalization by only using rank positions. It's also theoretically grounded: documents appearing at the top of multiple independent ranked lists are likely more relevant than those appearing in only one. The k=60 constant prevents rank 1 from getting a score 60x higher than rank 60, maintaining robustness.

**Q: Your RAG system is giving good results for most queries but failing on queries containing product version numbers (e.g., "bug in v3.4.2"). What's wrong and how do you fix it?** `[Medium]`
A: This is a lexical gap issue — version numbers are rare tokens not well-represented in the embedding model's training data. Dense retrieval will fail for exact version matches. Fix: add BM25 to the retrieval pipeline (hybrid search). Specifically, add the version string "v3.4.2" as a metadata filter OR ensure BM25 can exact-match on the tokenized version string. Also consider adding version numbers as metadata fields during indexing and using metadata pre-filtering before ANN search.

**Q: A user says "the system retrieves the same document 3 times in different chunks." How do you fix this without degrading relevance?** `[Medium]`
A: Use MMR (Maximal Marginal Relevance) retrieval — it penalizes chunks that are similar to already-selected chunks, promoting diversity. Set λ=0.7 to retain 70% relevance weighting and 30% diversity. Alternatively, apply a post-retrieval deduplication step: cluster retrieved chunks by source document and keep only the highest-scoring chunk per source. If parent-child chunking is set up, this is solved architecturally — small chunks retrieve, parent chunks return.

**Q: How would you tune the alpha weight in hybrid search (dense + sparse)?** `[Medium]`
A: Hold out 100-500 query-answer pairs from production traffic as a validation set. For each alpha value (e.g., 0.3, 0.5, 0.7), compute Recall@5 on the validation set. The optimal alpha typically varies by domain: lexically rich domains (legal, technical documentation) often benefit from higher sparse weight (alpha=0.4-0.5), while conversational/general domains benefit from higher dense weight (alpha=0.6-0.7). Re-run this periodically as your corpus and query distribution evolves.

**Q: Explain the two-stage retrieval architecture. Why not just use a cross-encoder for all retrieval?** `[Easy]`
A: A cross-encoder must process each (query, document) pair jointly — for a 1M-document corpus, that's 1M model inference calls per query, taking minutes. The two-stage approach: first-stage bi-encoder ANN search (milliseconds) narrows down to top-20-100 candidates, then a cross-encoder re-scores only those 20-100 pairs (100-200ms). You get 99%+ of cross-encoder quality at bi-encoder speed, because the cross-encoder only needs to distinguish among the already-good first-stage candidates.

**Q: What is HyDE and when should you use caution with it?** `[Hard]`
A: HyDE embeds a hypothetical document generated by the LLM instead of the raw query, bringing the query representation closer to the document distribution. Use with caution when: (1) the LLM's generated hypothesis might be confidently wrong — this contaminates the embedding with incorrect information and retrieves documents about the wrong topic. (2) The domain requires precise terminology — a wrong hypothesis in medical/legal domains could retrieve dangerously misleading documents. Monitor HyDE vs direct-query recall on a test set; HyDE rarely helps when queries are already well-phrased.

**Q: How do you handle multi-hop questions in standard (non-agentic) RAG?** `[Hard]`
A: Multi-query expansion is the simplest approach: decompose the question into 2-3 sub-questions, retrieve for each, merge and deduplicate the results, then provide all chunks as context. For example, "What was the revenue of Company A's UK division in the year their CTO resigned?" decomposes into (1) "Company A UK division revenue by year", (2) "Company A CTO resignation date." The caveat is that context window stuffing can occur if sub-questions retrieve many chunks. A better solution for complex multi-hop is Agentic RAG, where an agent iteratively retrieves and synthesizes.

**Q: What is MMR and how does it differ from standard top-k retrieval?** `[Medium]`
A: MMR (Maximal Marginal Relevance) selects documents greedily: the first document is the most relevant; each subsequent document is selected to maximize a trade-off between relevance to the query AND dissimilarity from already-selected documents. Formula: argmax_d [λ·sim(query, d) - (1-λ)·max_d'∈S sim(d, d')]. Standard top-k just returns the k most similar documents, which often returns 4 nearly-identical paragraphs from the same document. MMR promotes diversity, surfacing different aspects of the query topic across the k returned chunks.
