# RAG Types Taxonomy

A mental map before diving into mechanics. Every RAG system falls into one of five generations — understanding where a system sits on this spectrum is the first question you should answer in any interview.

```
Naive RAG
    ↓ add pre/post-retrieval steps
Advanced RAG
    ↓ decompose into swappable modules
Modular RAG
    ↓ add autonomous retrieval decisions
Agentic RAG
    ↓ replace vector index with knowledge graph
GraphRAG
```

---

## Naive RAG

### Concept

Naive RAG is the original formulation: index documents once, embed a query at runtime, retrieve top-k chunks, stuff them into a prompt, generate an answer. No preprocessing of the query, no post-processing of results.

**Pipeline:**
```
Documents → chunk → embed → store in vector DB
Query → embed → similarity search → top-k chunks → prompt → LLM → answer
```

**What works:** Simple, fast, cheap to build. Handles factual recall well when the corpus is clean and the query is specific.

**What breaks:**
- Poorly phrased queries retrieve irrelevant chunks (garbage in, garbage out)
- Chunks may contain the right information but wrong context (mid-sentence splits)
- No handling of complex multi-hop questions
- No feedback loop — errors are silent
- Context window stuffing: top-k chunks may still exceed the LLM's effective attention window

**When to use Naive RAG:** Prototypes, internal tools with small clean corpora (<10K docs), or when latency budget is very tight and precision requirements are moderate.

### Code

```python
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# Index
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
vectorstore = Chroma.from_texts(texts=documents, embedding=embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

# Query pipeline
prompt = ChatPromptTemplate.from_template(
    "Context:\n{context}\n\nQuestion: {question}\nAnswer:"
)
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

naive_rag = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt | llm | StrOutputParser()
)

answer = naive_rag.invoke("What is the refund policy?")
```

---

## Advanced RAG

### Concept

Advanced RAG adds intelligence at three stages: **pre-retrieval**, **retrieval**, and **post-retrieval**. It fixes Naive RAG's core weaknesses while keeping a single retrieval step.

**Pre-retrieval improvements:**
- **Query rewriting** — rephrase the query to be more retrieval-friendly
- **HyDE** — generate a hypothetical answer, embed that instead of the raw query
- **Step-back prompting** — generalize a specific question to retrieve broader context first
- **Multi-query** — generate 3-5 query variants, retrieve for each, deduplicate

**Retrieval improvements:**
- **Hybrid search** — combine dense (semantic) + sparse (BM25) retrieval
- **Metadata filtering** — pre-filter by date, source, category before ANN search
- **MMR** — penalize redundant chunks, increase diversity

**Post-retrieval improvements:**
- **Re-ranking** — cross-encoder model scores (query, chunk) pairs, promotes best chunks
- **Contextual compression** — extract only the relevant sentences from each retrieved chunk
- **Chunk stitching** — restore surrounding sentences for mid-sentence chunks

**When to use:** Production systems with real users. The combination of query rewriting + hybrid search + reranking often improves answer quality 20-40% over Naive RAG with modest added latency.

### Code

```python
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor

# Hybrid retriever
bm25 = BM25Retriever.from_texts(documents)
dense = vectorstore.as_retriever(search_kwargs={"k": 6})
hybrid = EnsembleRetriever(
    retrievers=[bm25, dense], weights=[0.4, 0.6]
)

# Post-retrieval compression
compressor = LLMChainExtractor.from_llm(llm)
advanced_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=hybrid
)

# Query expansion (pre-retrieval)
from langchain.retrievers.multi_query import MultiQueryRetriever
multi_query_retriever = MultiQueryRetriever.from_llm(
    retriever=advanced_retriever, llm=llm
)
```

---

## Modular RAG

### Concept

Modular RAG (proposed by Gao et al., 2023) treats each RAG component as a swappable module. Instead of a fixed pipeline, you compose modules depending on the task:

| Module Type | Options |
|---|---|
| **Search** | Vector DB, BM25, Google Search, SQL, Knowledge Graph |
| **Memory** | Short-term (conversation), Long-term (episodic store) |
| **Fusion** | RRF, linear interpolation, learned weights |
| **Routing** | Classifier, LLM-based, rule-based |
| **Predict** | Standard generation, chain-of-thought, self-consistency |
| **Task Adaption** | Domain fine-tuned retriever, task-specific prompt |

**Key insight:** Different queries need different retrieval modules. A question about recent news needs web search. A question about internal policy needs a vector DB. A question about product relationships needs a knowledge graph. Modular RAG routes dynamically.

**Routing example:** An LLM-based router classifies the query and dispatches to the right sub-pipeline. This is the architectural parent of Agentic RAG.

```
Query
  ↓
Router (classify intent)
  ├─ "factual/internal" → Vector DB retriever → context → LLM
  ├─ "recent events"    → Web search → snippet → LLM
  ├─ "structured data"  → SQL agent → table → LLM
  └─ "relationship"     → Graph traversal → paths → LLM
```

### Code

```python
from langchain_core.runnables import RunnableBranch, RunnableLambda

def route_query(query: str) -> str:
    routing_prompt = f"""Classify this query into one of: internal, web_search, sql, graph.
Query: {query}
Classification:"""
    return llm.invoke(routing_prompt).content.strip().lower()

pipeline = RunnableBranch(
    (lambda x: route_query(x["query"]) == "internal",   internal_rag_chain),
    (lambda x: route_query(x["query"]) == "web_search", web_search_chain),
    (lambda x: route_query(x["query"]) == "sql",        sql_agent_chain),
    fallback_chain,
)
```

---

## Agentic RAG

### Concept

Agentic RAG gives an LLM-based agent the autonomy to decide **when** to retrieve, **what** to retrieve, and **whether to retrieve again** after seeing an initial result. This is a fundamental shift from pipeline RAG (fixed sequence) to agent RAG (dynamic control flow).

**Differences from pipeline RAG:**

| Dimension | Pipeline RAG | Agentic RAG |
|---|---|---|
| Retrieval timing | Always, at start | Agent decides |
| Number of retrievals | One | One to many |
| Fallback behavior | None | Agent retries with different query |
| Multi-hop | Not native | Natural via tool calls |
| Latency | Predictable | Variable |
| Complexity | Low | High |

**Patterns within Agentic RAG:**
- **ReAct** — interleave reasoning and retrieval actions
- **Plan-and-solve** — decompose into sub-questions, retrieve for each
- **Self-RAG** — retrieval triggered by reflection tokens (see file 05)
- **CRAG** — evaluate retrieval quality, fall back to web search if poor

**When to use:** Multi-hop questions, tasks requiring synthesis across multiple documents, when the retrieval plan cannot be determined statically.

### Code

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional

class AgentState(TypedDict):
    query: str
    retrieved_docs: list[str]
    answer: Optional[str]
    needs_more_retrieval: bool

def retrieve_node(state: AgentState) -> AgentState:
    docs = retriever.invoke(state["query"])
    return {"retrieved_docs": [d.page_content for d in docs]}

def reason_node(state: AgentState) -> AgentState:
    context = "\n".join(state["retrieved_docs"])
    response = llm.invoke(
        f"Context: {context}\nQuery: {state['query']}\n"
        f"If you can answer confidently, start with ANSWER:. "
        f"If you need more info, start with RETRIEVE_MORE: and give a follow-up query."
    ).content
    if response.startswith("ANSWER:"):
        return {"answer": response[7:].strip(), "needs_more_retrieval": False}
    else:
        new_query = response.replace("RETRIEVE_MORE:", "").strip()
        return {"query": new_query, "needs_more_retrieval": True}

builder = StateGraph(AgentState)
builder.add_node("retrieve", retrieve_node)
builder.add_node("reason", reason_node)
builder.add_edge("retrieve", "reason")
builder.add_conditional_edges("reason",
    lambda s: "retrieve" if s["needs_more_retrieval"] else END,
    {"retrieve": "retrieve", END: END}
)
builder.set_entry_point("retrieve")
graph = builder.compile()
```

---

## GraphRAG

### Concept

GraphRAG (Microsoft, 2024) replaces or supplements the flat vector index with a knowledge graph. The key insight: for questions that span many documents or require reasoning about relationships between entities, a graph index captures structure that a vector index cannot.

**Two retrieval modes:**
- **Local search** — relevant entities, relationships, and community summaries for a specific query (most questions)
- **Global search** — community-level summaries to answer broad thematic questions ("What are the main topics in this corpus?")

**Build pipeline:**
1. Extract entities and relationships from each document chunk (LLM-based)
2. Build a graph: nodes = entities, edges = relationships
3. Run community detection (Leiden algorithm) to group related entities
4. Generate community summaries at multiple levels (hierarchical)
5. At query time: identify relevant communities → retrieve their summaries + specific node context

**When GraphRAG beats dense retrieval:**
- Questions requiring multi-hop reasoning: "Which executives at Company A also worked at Company B before 2020?"
- Cross-document synthesis: "What is the overall sentiment toward X across 10,000 news articles?"
- Relationship queries: "What caused Event Y?" (requires causal edge traversal)

**GraphRAG limitations:**
- 2-5x more expensive to build (LLM calls per chunk for entity extraction)
- 3-10x more expensive per query (community summaries use many tokens)
- Overkill for simple factual retrieval

### Code (using the `graphrag` library)

```python
# Install: pip install graphrag
# Build: python -m graphrag.index --root ./my_corpus --method local
# Query:
import asyncio
from graphrag.query.cli import run_local_search, run_global_search

# Local search (specific entity questions)
result = asyncio.run(run_local_search(
    config_dir="./my_corpus",
    query="What are the main products of Acme Corp?"
))

# Global search (broad thematic questions)
result = asyncio.run(run_global_search(
    config_dir="./my_corpus",
    query="What are the recurring themes in this document collection?"
))
```

---

## Multimodal RAG

### Concept

Multimodal RAG retrieves across image, text, table, and audio modalities. The key challenges are:
1. **Embedding heterogeneous content** — images and text need to share the same embedding space
2. **Cross-modal queries** — a text query should retrieve relevant images and vice versa

**Approaches:**

| Approach | How It Works | When to Use |
|---|---|---|
| **Caption-based** | Extract text captions from images, embed captions | Fast, low cost; loses visual detail |
| **CLIP embeddings** | Shared image+text embedding space | Good for photo/diagram retrieval |
| **ColPali** | Late interaction: each image patch gets a vector | Best precision for document images |
| **GPT-4V summaries** | LLM describes image content, embed description | High quality, high cost |

**ColPali** (2024) is state-of-the-art for document image retrieval — it embeds entire page images as a bag of patch vectors and uses MaxSim (late interaction) to score (query, page) pairs without OCR.

### Code (Caption-based, pragmatic approach)

```python
from PIL import Image
import base64, io

def image_to_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def extract_image_caption(image_path: str) -> str:
    b64 = image_to_base64(image_path)
    response = llm.invoke([{
        "type": "image_url",
        "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
    }, {"type": "text", "text": "Describe this image for retrieval. Include key entities, numbers, and concepts."}])
    return response.content

# Build multimodal index
captions = {path: extract_image_caption(path) for path in image_paths}
vectorstore = Chroma.from_texts(
    texts=list(captions.values()),
    metadatas=[{"source": k, "type": "image"} for k in captions],
    embedding=embeddings
)
```

---

## Comparison Table

| Type | Retrieval Complexity | Build Cost | Query Cost | Latency | Best For |
|---|---|---|---|---|---|
| **Naive RAG** | Single ANN search | Low | Very Low | ~100ms | Prototypes, simple Q&A |
| **Advanced RAG** | Hybrid + rerank | Low | Low-Medium | ~300-600ms | Production Q&A systems |
| **Modular RAG** | Multiple retrievers | Medium | Medium | ~400-800ms | Diverse query types |
| **Agentic RAG** | Dynamic multi-step | Low | High | ~1-5s | Multi-hop, complex reasoning |
| **GraphRAG** | Graph traversal | Very High | Very High | ~2-10s | Relationship queries, synthesis |
| **Multimodal RAG** | Cross-modal ANN | High | Medium | ~500ms-2s | Image+text corpora |

---

## Interview Q&A

**Q: What's the difference between Advanced RAG and Modular RAG?** `[Medium]`
A: Advanced RAG improves a fixed pipeline at pre/retrieval/post stages but keeps the same structure. Modular RAG deconstructs the pipeline entirely into swappable components and adds a routing layer that selects different retrieval modules (web, SQL, graph, vector DB) based on query classification. Modular RAG is the generalization that subsumes Advanced RAG.

**Q: When would you recommend GraphRAG over dense vector retrieval?** `[Hard]`
A: GraphRAG wins for three scenarios: (1) multi-hop questions requiring entity traversal (who collaborated with whom, causal chains), (2) broad thematic synthesis across a large corpus where community summaries help, (3) relationship-heavy domains like legal or scientific literature where named entity relationships are the primary retrieval signal. For straightforward factual Q&A, GraphRAG's 2-5x cost premium rarely justifies the improvement.

**Q: What is the core architectural difference between pipeline RAG and Agentic RAG?** `[Medium]`
A: Pipeline RAG has a fixed control flow — retrieve once, generate once. Agentic RAG gives an LLM agent the ability to dynamically decide when to retrieve, what query to use, and whether to retrieve again based on intermediate results. Pipeline RAG has predictable latency; Agentic RAG has variable latency but handles multi-hop and ambiguous queries naturally.

**Q: How does ColPali differ from CLIP for image retrieval?** `[Hard]`
A: CLIP produces one embedding per image (a global vector), so it loses spatial/layout information. ColPali uses a Vision Language Model to produce per-patch embeddings (typically 1024 patches per page image), then scores (query, image) pairs using MaxSim — the max similarity over all patch-query pairs. This preserves layout information critical for document page retrieval (charts, tables, diagrams) and achieves significantly higher precision on document QA benchmarks.

**Q: A user asks a Naive RAG system "What was the revenue growth in Q3 vs Q4 2023 and what caused the difference?" — what will fail and why?** `[Medium]`
A: This is a multi-hop question requiring: (1) retrieve Q3 revenue, (2) retrieve Q4 revenue, (3) retrieve the cause of the difference. Naive RAG retrieves once with a single embedding. The query embedding will be a blend of all three information needs, likely missing at least one. The right approach is either Agentic RAG (retrieve once per sub-question) or GraphRAG (traverse causal relationships in a financial knowledge graph).

**Q: What is Modular RAG's routing mechanism and how is it implemented?** `[Medium]`
A: Routing can be rule-based (keyword triggers), classifier-based (a small fine-tuned model), or LLM-based (a prompt asking the model to classify query type). LLM-based routing is most flexible but adds ~100-200ms latency. In practice, a hybrid approach works best: fast rule-based routing for common patterns, LLM fallback for ambiguous cases.

**Q: How does Multimodal RAG handle cross-modal relevance scoring?** `[Hard]`
A: There are two approaches. CLIP-based: images and text are projected into a shared embedding space, so cosine similarity works directly across modalities. Caption-based: images are described in text by an LLM, and similarity is computed text-to-text — simpler but loses visual detail. For production document retrieval, ColPali's late interaction (MaxSim over patch embeddings) currently achieves the best recall@k on document image benchmarks without requiring OCR.

**Q: What would make you choose Naive RAG over Advanced RAG for a production system?** `[Easy]`
A: Latency constraints (Naive RAG is 3-5x faster than Advanced RAG with reranking), cost constraints (no reranking API calls), or when the corpus is small, clean, and queries are simple factual lookups where the extra precision of reranking provides negligible benefit. Naive RAG is also easier to debug and monitor.
