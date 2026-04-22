# RAG Types, Taxonomy & Advanced Patterns

← **Back to Overview:** [RAG](../INDEX.md)

A complete reference: the RAG evolution ladder from Naive to GraphRAG, deep-dive implementations of each pattern, the extended variant taxonomy, and the comparison matrix.

---

## RAG Evolution Overview

Every RAG system sits on this spectrum. Understanding where a system sits is the first question in any architecture discussion.

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
    ↓ retrieve across image, text, audio
Multimodal RAG
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
- Poorly phrased queries retrieve irrelevant chunks
- Chunks may contain the right information but wrong context (mid-sentence splits)
- No handling of complex multi-hop questions
- No feedback loop — errors are silent
- Context window stuffing: top-k chunks may exceed the LLM's effective attention window

**When to use:** Prototypes, internal tools with small clean corpora (<10K docs), or when latency budget is very tight and precision requirements are moderate.

### Code

```python
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
vectorstore = Chroma.from_texts(texts=documents, embedding=embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

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
- **Multi-query** — generate 3–5 query variants, retrieve for each, deduplicate

**Retrieval improvements:**
- **Hybrid search** — combine dense (semantic) + sparse (BM25) retrieval
- **Metadata filtering** — pre-filter by date, source, category before ANN search
- **MMR** — penalize redundant chunks, increase diversity

**Post-retrieval improvements:**
- **Re-ranking** — cross-encoder model scores (query, chunk) pairs, promotes best chunks
- **Contextual compression** — extract only the relevant sentences from each retrieved chunk
- **Chunk stitching** — restore surrounding sentences for mid-sentence chunks

**When to use:** Production systems with real users. The combination of query rewriting + hybrid search + reranking often improves answer quality 20–40% over Naive RAG with modest added latency.

### Code

```python
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain.retrievers.multi_query import MultiQueryRetriever

# Hybrid retriever (dense + sparse)
bm25 = BM25Retriever.from_texts(documents)
dense = vectorstore.as_retriever(search_kwargs={"k": 6})
hybrid = EnsembleRetriever(retrievers=[bm25, dense], weights=[0.4, 0.6])

# Post-retrieval compression
compressor = LLMChainExtractor.from_llm(llm)
advanced_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=hybrid
)

# Pre-retrieval: query expansion
multi_query_retriever = MultiQueryRetriever.from_llm(
    retriever=advanced_retriever, llm=llm
)
```

---

## Modular RAG

### Concept

Modular RAG (Gao et al., 2023) treats each RAG component as a swappable module. Instead of a fixed pipeline, you compose modules depending on the task:

| Module Type | Options |
|---|---|
| **Search** | Vector DB, BM25, Google Search, SQL, Knowledge Graph |
| **Memory** | Short-term (conversation), Long-term (episodic store) |
| **Fusion** | RRF, linear interpolation, learned weights |
| **Routing** | Classifier, LLM-based, rule-based |
| **Predict** | Standard generation, chain-of-thought, self-consistency |
| **Task Adaption** | Domain fine-tuned retriever, task-specific prompt |

**Key insight:** Different queries need different retrieval modules. A question about recent news needs web search. A question about internal policy needs a vector DB. A question about product relationships needs a knowledge graph. Modular RAG routes dynamically. This is the architectural parent of Agentic RAG.

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
from langchain_core.runnables import RunnableBranch

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

## Multi-Query RAG

### Concept

Multi-Query RAG addresses a fundamental limitation of single-query retrieval: a single embedding of the user's question represents one point in vector space, and relevant documents spread across multiple semantic dimensions may not be captured by that single point.

The pattern: use an LLM to generate 3–5 paraphrased or decomposed variants of the original query, retrieve separately for each variant, then deduplicate and merge the results.

**When it helps:**
- Ambiguous queries with multiple valid interpretations
- Complex questions that decompose into sub-questions
- Queries using informal language when documents use formal terminology

**When it doesn't help:**
- Precise technical queries (e.g., "error code E4013") — variants can't improve on the exact term
- Adds latency: N queries × embedding time + N × ANN searches + deduplication

**Deduplication strategy:** De-duplicate by content hash before reranking. If two variants retrieve the same chunk, keep it once but boost its effective score — found by multiple independent queries signals higher relevance.

### Code

```python
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import BaseOutputParser

class LineListParser(BaseOutputParser):
    def parse(self, text: str) -> list[str]:
        return [line.strip() for line in text.strip().split("\n") if line.strip()]

query_gen_prompt = ChatPromptTemplate.from_template(
    """Generate {n} different versions of this question to improve document retrieval.
Each version should approach the question from a different angle.
Original question: {question}
Output one question per line, no numbering."""
)

def multi_query_retrieve(query: str, n: int = 3) -> list:
    variants = (query_gen_prompt | llm | LineListParser()).invoke(
        {"question": query, "n": n}
    )
    all_docs = {}
    for variant in [query] + variants:
        docs = vectorstore.similarity_search(variant, k=6)
        for doc in docs:
            doc_id = hash(doc.page_content)
            if doc_id not in all_docs:
                all_docs[doc_id] = (doc, 1)
            else:
                all_docs[doc_id] = (doc, all_docs[doc_id][1] + 1)
    # Docs found by multiple queries rank higher
    return [doc for doc, _ in sorted(all_docs.values(), key=lambda x: -x[1])]
```

---

## Contextual Compression

### Concept

Standard retrieval returns full document chunks regardless of whether every sentence is relevant to the query. Contextual compression post-processes each retrieved chunk to extract only the sentences relevant to the query.

**The problem it solves:**
A 500-character chunk about "refund policy" might contain 4 sentences: one about refunds, one about exchanges, one about store credit, one about contact info. A query about refunds only needs the first sentence. Returning all 4 wastes context window space and can confuse the LLM.

**Two types of compressors:**

| Compressor | How | Cost | Quality |
|---|---|---|---|
| `LLMChainExtractor` | LLM extracts relevant sentences | High (LLM call per chunk) | Excellent |
| `LLMChainFilter` | LLM decides keep/discard per chunk | Medium | Good |
| `EmbeddingsFilter` | Embedding similarity between chunk and query | Very Low | Moderate |

**Practical choice:** `EmbeddingsFilter` with threshold=0.7 is fast and free; `LLMChainExtractor` is more precise but costs an extra LLM call per retrieved chunk.

### Code

```python
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import (
    LLMChainExtractor, EmbeddingsFilter, DocumentCompressorPipeline
)

# Option 1: LLM extraction (best quality)
extractor = LLMChainExtractor.from_llm(llm)
compression_retriever = ContextualCompressionRetriever(
    base_compressor=extractor,
    base_retriever=vectorstore.as_retriever(search_kwargs={"k": 8})
)

# Option 2: Embedding filter (fast, free)
embeddings_filter = EmbeddingsFilter(
    embeddings=embeddings,
    similarity_threshold=0.70
)
fast_retriever = ContextualCompressionRetriever(
    base_compressor=embeddings_filter,
    base_retriever=vectorstore.as_retriever(search_kwargs={"k": 8})
)

# Option 3: Pipeline — filter first (cheap), then extract from remaining
pipeline_compressor = DocumentCompressorPipeline(
    transformers=[embeddings_filter, extractor]
)
pipeline_retriever = ContextualCompressionRetriever(
    base_compressor=pipeline_compressor,
    base_retriever=vectorstore.as_retriever(search_kwargs={"k": 10})
)
```

---

## Self-RAG

### Concept

Self-RAG (Asai et al., 2023) teaches an LLM to adaptively retrieve and critique by generating special **reflection tokens** alongside regular text. These tokens control the retrieval process.

**Reflection tokens:**
| Token | Meaning |
|---|---|
| `[Retrieve]` | Should I retrieve documents for this query? |
| `[IsRel]` / `[IsIRel]` | Is the retrieved document relevant? |
| `[IsSup]` / `[IsNotSup]` | Does the document support the generated statement? |
| `[IsUse]` / `[IsNotUse]` | Is the response useful to the user? |

**How it works (inference):**
1. LLM generates text until it produces `[Retrieve]` token
2. If `[Retrieve]` → fetch documents from retriever
3. LLM produces `[IsRel]` to evaluate each retrieved doc
4. LLM generates answer segments, producing `[IsSup]` to verify each claim
5. If `[IsNotSup]` → retrieve again with a refined query

**Key insight:** Unlike standard RAG (always retrieves once), Self-RAG retrieves only when needed and performs in-generation verification — reducing unnecessary retrievals for questions the model can answer from parametric knowledge.

### Code

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

def self_rag(query: str) -> dict:
    # Step 1: Assess if retrieval is needed
    retrieval_decision_prompt = ChatPromptTemplate.from_template(
        """Should I retrieve documents to answer this question?
        If the answer requires specific facts, recent information, or private knowledge → RETRIEVE
        If it's general knowledge or reasoning → NO_RETRIEVE
        
        Question: {query}
        Decision (RETRIEVE or NO_RETRIEVE):"""
    )
    decision = (retrieval_decision_prompt | llm | StrOutputParser()).invoke({"query": query}).strip()

    if "NO_RETRIEVE" in decision:
        return {"answer": llm.invoke(query).content, "retrieved": False}

    docs = retriever.invoke(query)
    context = "\n\n".join(doc.page_content for doc in docs)

    # Step 2: Assess document relevance
    relevance_prompt = ChatPromptTemplate.from_template(
        """Is this context relevant to answering the question?
        Question: {query}
        Context: {context}
        Answer (RELEVANT or IRRELEVANT):"""
    )
    relevance = (relevance_prompt | llm | StrOutputParser()).invoke(
        {"query": query, "context": context[:500]}
    ).strip()

    if "IRRELEVANT" in relevance:
        docs = retriever.invoke(f"detailed information about {query}")
        context = "\n\n".join(doc.page_content for doc in docs)

    # Step 3: Generate with grounding assessment
    grounded_gen_prompt = ChatPromptTemplate.from_template(
        """Answer using only the context. After the answer, rate:
        FULLY_SUPPORTED, PARTIALLY_SUPPORTED, or NOT_SUPPORTED
        
        Context: {context}
        Question: {query}
        
        Answer:
        Support level:"""
    )
    response = (grounded_gen_prompt | llm | StrOutputParser()).invoke(
        {"context": context, "query": query}
    )
    parts = response.split("Support level:")
    return {
        "answer": parts[0].replace("Answer:", "").strip(),
        "support_level": parts[1].strip() if len(parts) > 1 else "unknown",
        "retrieved": True,
    }
```

---

## FLARE (Forward-Looking Active REtrieval)

### Concept

FLARE (Jiang et al., 2023) addresses a different problem from Self-RAG: during long-form generation, the model may need to retrieve additional information **mid-generation** to continue accurately.

**How it works:**
1. Model starts generating a response
2. At each generation step, it produces a "tentative" next sentence with token probabilities
3. If any word has probability < threshold (e.g., 0.2), the model is uncertain
4. Trigger retrieval on the uncertain span
5. Continue generation with the newly retrieved context

**When FLARE excels:**
- Long-form generation (essays, reports) where the model needs fresh context mid-generation
- Multi-part questions where each sub-part needs different retrieval

**Key distinction from Self-RAG:** Self-RAG retrieves at designated decision points; FLARE retrieves on-demand whenever generation uncertainty rises.

### Code

```python
def flare_generate(query: str, max_iterations: int = 5) -> str:
    generated_text = ""
    retrieval_contexts = []

    for iteration in range(max_iterations):
        prompt = f"""Context: {chr(10).join(retrieval_contexts)}

Previous text: {generated_text}

Continue the response for: {query}
If you're uncertain about any fact, prefix that sentence with [UNCERTAIN]:"""

        next_segment = llm.invoke(prompt).content

        if "[UNCERTAIN]" in next_segment:
            uncertain_part = next_segment.split("[UNCERTAIN]")[1].split(".")[0]
            new_docs = retriever.invoke(uncertain_part)
            retrieval_contexts.extend([doc.page_content for doc in new_docs[:2]])
            continue

        generated_text += " " + next_segment

        if next_segment.strip().endswith((".", "!", "?")):
            break

    return generated_text.strip()
```

---

## Agentic RAG

### Concept

Agentic RAG gives an LLM-based agent autonomy to decide **when** to retrieve, **what** to retrieve, and **whether to retrieve again** after seeing an initial result. This is a fundamental shift from pipeline RAG (fixed sequence) to agent RAG (dynamic control flow).

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
- **Self-RAG** — retrieval triggered by reflection tokens (see above)
- **CRAG** — evaluate retrieval quality, fall back to web search if poor (see below)

**ReAct trace:**
```
Thought: I need to find Q3 revenue
Action: retrieve("Q3 2024 revenue")
Observation: [retrieved chunks — Q3 = $4.2B]
Thought: I found Q3, now I need Q4 and the reason for the change
Action: retrieve("Q4 2024 revenue cause of change")
Observation: [retrieved chunks]
Thought: I now have enough information
Action: generate_final_answer
```

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

# With LangChain tools API
from langchain.tools.retriever import create_retriever_tool
from langchain.agents import AgentExecutor, create_react_agent

retriever_tool = create_retriever_tool(
    retriever=hybrid_retriever,
    name="knowledge_search",
    description="Search the knowledge base for relevant documents."
)
agent = create_react_agent(llm=llm, tools=[retriever_tool], prompt=react_prompt)
agent_executor = AgentExecutor(agent=agent, tools=[retriever_tool], max_iterations=5)
```

---

## GraphRAG

### Concept

GraphRAG (Microsoft Research, 2024) replaces or supplements the flat vector index with a knowledge graph. For questions that span many documents or require reasoning about relationships between entities, a graph index captures structure that a vector index cannot.

**Build pipeline:**
```
Document corpus
    ↓ LLM extracts entities and relationships from each chunk
Entity-Relationship triples: (Entity_A, relation, Entity_B)
    ↓ Build knowledge graph (nodes=entities, edges=relations)
    ↓ Run community detection (Leiden algorithm)
Communities (groups of related entities)
    ↓ LLM generates summary for each community at multiple levels
Hierarchical community summaries (C0 = coarse, C4 = fine-grained)
```

**Two retrieval modes:**
- **Local search** — relevant entities, relationships, and community summaries for a specific query
- **Global search** — broad community-level summaries to answer thematic questions

**Why GraphRAG beats dense for relationship queries:**

Example: "Which employees worked at both Google and Apple?"
- Dense RAG: retrieves chunks mentioning Google or Apple — can't traverse the "employee of" relationship across documents
- GraphRAG: entity "Alice Chen" is a node; edges "worked_at" connect to both "Google" and "Apple"; a graph traversal directly answers this

**Cost reality:** Indexing costs ~$1–5 per 1M tokens (LLM calls for entity extraction). Justified only when relationship traversal or global synthesis is a core query pattern.

### Code

```python
# Using the official Microsoft graphrag library
# pip install graphrag
import asyncio
from graphrag.query.cli import run_local_search, run_global_search

# Local search (specific entity questions)
result = asyncio.run(run_local_search(
    config_dir="./my_corpus",
    query="What products did Tesla announce in Q3 2024?"
))

# Global search (broad thematic questions)
result = asyncio.run(run_global_search(
    config_dir="./my_corpus",
    query="What are the recurring safety concerns mentioned across all reports?"
))

# DIY with NetworkX (smaller corpora)
import networkx as nx

def build_knowledge_graph(chunks: list[str], llm) -> nx.DiGraph:
    G = nx.DiGraph()
    for chunk in chunks:
        triples_text = llm.invoke(
            f"Extract entity-relationship triples. Format: entity1 | relation | entity2 (one per line)\nText: {chunk}"
        ).content
        for line in triples_text.strip().split("\n"):
            parts = [p.strip() for p in line.split("|")]
            if len(parts) == 3:
                G.add_edge(parts[0], parts[2], relation=parts[1])
    return G

def graph_retrieve(G: nx.DiGraph, query: str, k_hops: int = 2) -> list[str]:
    entities = llm.invoke(f"List named entities in: '{query}'. One per line.").content.split("\n")
    relevant_nodes = set()
    for entity in entities:
        if entity.strip() in G:
            neighborhood = nx.ego_graph(G, entity.strip(), radius=k_hops)
            relevant_nodes.update(neighborhood.nodes())
    return [
        f"{u} {data['relation']} {v}"
        for u, v, data in G.edges(data=True)
        if u in relevant_nodes or v in relevant_nodes
    ]
```

---

## Corrective RAG (CRAG)

### Concept

CRAG (Yan et al., 2024) adds a quality gate after retrieval: evaluate whether the retrieved documents are actually relevant to the query. If not, fall back to web search instead of forcing the generator to work with irrelevant context.

**The problem it solves:** Standard RAG always uses retrieved documents, even if they're irrelevant. The LLM then hallucinates or says "I don't know" — wasting the query. CRAG detects retrieval failure and has a recovery strategy.

**CRAG states:**
- `CORRECT` — retrieved docs are highly relevant → use directly
- `INCORRECT` — retrieved docs are irrelevant → fall back to web search
- `AMBIGUOUS` — partial relevance → use retrieved docs + web search, merge

### Code

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional

class CRAGState(TypedDict):
    query: str
    retrieved_docs: list[str]
    retrieval_grade: str
    web_results: list[str]
    final_context: list[str]
    answer: Optional[str]

def grade_retrieval(state: CRAGState) -> CRAGState:
    grade = llm.invoke(
        f"""Are these documents relevant to the query?
        Query: {state['query']}
        Documents: {state['retrieved_docs'][:2]}
        Answer: CORRECT, INCORRECT, or AMBIGUOUS"""
    ).content.strip()
    return {"retrieval_grade": grade}

def web_search_node(state: CRAGState) -> CRAGState:
    from langchain_community.tools import TavilySearchResults
    results = TavilySearchResults(k=3).invoke(state["query"])
    return {"web_results": [r["content"] for r in results]}

def assemble_context(state: CRAGState) -> CRAGState:
    if state["retrieval_grade"] == "CORRECT":
        return {"final_context": state["retrieved_docs"]}
    elif state["retrieval_grade"] == "INCORRECT":
        return {"final_context": state["web_results"]}
    return {"final_context": state["retrieved_docs"] + state["web_results"]}

builder = StateGraph(CRAGState)
builder.add_node("retrieve", lambda s: {"retrieved_docs": [d.page_content for d in retriever.invoke(s["query"])]})
builder.add_node("grade_docs", grade_retrieval)
builder.add_node("web_search", web_search_node)
builder.add_node("assemble", assemble_context)
builder.add_node("generate", lambda s: {"answer": llm.invoke(
    f"Context: {s['final_context']}\nQuestion: {s['query']}"
).content})

builder.set_entry_point("retrieve")
builder.add_edge("retrieve", "grade_docs")
builder.add_conditional_edges("grade_docs",
    lambda s: "web_search" if s["retrieval_grade"] in ("INCORRECT", "AMBIGUOUS") else "assemble",
    {"web_search": "web_search", "assemble": "assemble"}
)
builder.add_edge("web_search", "assemble")
builder.add_edge("assemble", "generate")
builder.add_edge("generate", END)
crag = builder.compile()
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
| **GPT-4V / Gemini summaries** | LLM describes image content, embed description | High quality, higher cost |

**ColPali** (2024) is state-of-the-art for document image retrieval — it embeds entire page images as a bag of patch vectors and uses MaxSim (late interaction) to score (query, page) pairs without OCR.

### Code (Caption-based)

```python
import base64

def image_to_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def extract_image_caption(image_path: str) -> str:
    b64 = image_to_base64(image_path)
    return llm.invoke([
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
        {"type": "text", "text": "Describe this image for retrieval. Include key entities, numbers, and concepts."}
    ]).content

# Build multimodal index
captions = {path: extract_image_caption(path) for path in image_paths}
vectorstore = Chroma.from_texts(
    texts=list(captions.values()),
    metadatas=[{"source": k, "type": "image"} for k in captions],
    embedding=embeddings
)
```

---

## Comparison Matrix

| Type | Retrieval Complexity | Build Cost | Query Cost | Latency | Best For |
|---|---|---|---|---|---|
| **Naive RAG** | Single ANN search | Low | Very Low | ~100ms | Prototypes, simple Q&A |
| **Advanced RAG** | Hybrid + rerank | Low | Low–Medium | ~300–600ms | Production Q&A systems |
| **Modular RAG** | Multiple retrievers | Medium | Medium | ~400–800ms | Diverse query types |
| **Agentic RAG** | Dynamic multi-step | Low | High | ~1–5s | Multi-hop, complex reasoning |
| **GraphRAG** | Graph traversal | Very High | Very High | ~2–10s | Relationship queries, synthesis |
| **Multimodal RAG** | Cross-modal ANN | High | Medium | ~500ms–2s | Image+text corpora |

---

## Extended Variant Taxonomy

Beyond the six types above, production systems exhibit specialized patterns. These are named variants — most are specializations of Agentic or Advanced RAG.

| Variant | What It Does | Distinguishing Feature | Best For |
|---|---|---|---|
| **Corrective RAG (CRAG)** | Meta-evaluates retrieved chunks; falls back to web search if below threshold | Self-correcting retrieval loop | High-stakes domains where bad retrieval is worse than "I don't know" |
| **Speculative RAG** | Pre-fetches potential follow-up chunks before the user asks | Proactive, predictive retrieval | Customer support, FAQ flows with predictable patterns |
| **Self-RAG** | Feeds generated responses back through retrieval iteratively | Iterative self-refinement cycle | Complex multi-part answers |
| **MEMO / Memory-Augmented RAG** | Uses long-term conversational memory as retrieval context | Persistent episodic memory | Multi-session agents, personalized assistants |
| **REALM-style RAG** | Retriever jointly pre-trained with LLM via masked LM | End-to-end retriever training | When retriever quality is the dominant bottleneck |
| **Cost-Constrained RAG** | Dynamically skips reranking, reduces k, or uses cheaper embeddings under budget | Explicit cost-quality trade-off | High-volume products with tight per-query cost budgets |
| **Adaptive RAG** | Adjusts retrieval strategy (k, chunk size, model) based on query complexity | Strategy adapts per-query | Long conversations where early turns are simple, later turns complex |
| **Streaming / Real-Time RAG** | Continuously ingests new data; index always fresh | Sub-second index freshness | News feeds, live financial data, incident response |

**When to choose each:**
- **CRAG** over Agentic RAG: when your retrieval quality is unreliable and a wrong context causes more harm than a fallback
- **Streaming RAG** over standard RAG: when a retrieval lag of even 5 minutes is unacceptable
- **MEMO-style RAG**: when users have many sessions and prior context should influence retrieval

---

## Q&A Review Bank

**Q: What's the difference between Advanced RAG and Modular RAG?** `[Medium]`

A: Advanced RAG improves a fixed pipeline at pre/retrieval/post stages but keeps the same structure. Modular RAG deconstructs the pipeline entirely into swappable components and adds a routing layer that selects different retrieval modules (web, SQL, graph, vector DB) based on query classification. Modular RAG is the generalization that subsumes Advanced RAG.

---

**Q: How does Self-RAG differ from standard RAG?** `[Medium]`

A: Standard RAG always retrieves before generating — one retrieval, then one generation. Self-RAG uses a fine-tuned model that generates special reflection tokens (`[Retrieve]`, `[IsRel]`, `[IsSup]`) to decide dynamically: should I retrieve at all? Is this retrieved document relevant? Does this generated claim have support from the retrieved context? Self-RAG retrieves only when needed, validates each retrieval, and checks factual support mid-generation — resulting in fewer hallucinations and unnecessary retrievals. The downside is requiring a specially fine-tuned model.

---

**Q: What is the core architectural difference between pipeline RAG and Agentic RAG?** `[Medium]`

A: Pipeline RAG has a fixed control flow — retrieve once, generate once. Agentic RAG gives an LLM agent the ability to dynamically decide when to retrieve, what query to use, and whether to retrieve again based on intermediate results. Pipeline RAG has predictable latency; Agentic RAG has variable latency but handles multi-hop and ambiguous queries naturally.

---

**Q: When would GraphRAG outperform dense vector retrieval?** `[Hard]`

A: Three scenarios where graph traversal wins: (1) Multi-entity relationship queries — "Find all companies that both person X and person Y have worked at" requires graph traversal, not vector similarity. (2) Global thematic synthesis — "Summarize the main trends across 10,000 earnings reports" — GraphRAG community summaries aggregate information across the entire corpus. (3) Causal chain queries — "What led to Event A?" — knowledge graph edges explicitly represent causal relationships that are only implicit in flat text.

---

**Q: What is FLARE and how does it decide when to retrieve?** `[Hard]`

A: FLARE monitors token-level generation probabilities during forward pass. When a generated token has probability below a threshold (e.g., 0.2), the model is uncertain about that fact. FLARE pauses generation, uses the uncertain span as a retrieval query, fetches relevant documents, then continues generation with the new context. This enables mid-generation retrieval rather than front-loading all retrieval before generation starts. Best for long-form generation where information needs emerge as the model generates.

---

**Q: What is Corrective RAG and why is it important for reliability?** `[Medium]`

A: CRAG adds a retrieval quality gate: after retrieving documents, an LLM evaluates whether they actually address the query. If not (`grade=INCORRECT`), it falls back to web search rather than forcing the generator to work with irrelevant context. This matters because standard RAG silently fails — irrelevant retrieval leads to hallucination without any signal. CRAG makes retrieval failure explicit and provides a recovery path. The trade-off: adds latency (one extra LLM grading call + possible web search).

---

**Q: Your multi-query RAG is adding too much latency. How do you optimize it?** `[Medium]`

A: Three optimizations: (1) **Parallelize retrievals** — run all N variant queries concurrently using `asyncio.gather()` instead of sequentially; N variants takes the same wall-clock time as 1. (2) **Cache embeddings** — if the same query or variant reappears, the embedding is already computed. (3) **Reduce N** — 2–3 variants often gives 80% of the benefit of 5; empirically test on your eval set. (4) **Diversify, don't duplicate** — generate variants using MMR on query embeddings to ensure they cover different semantic regions.

---

**Q: How does Contextual Compression help with the "lost in the middle" problem?** `[Medium]`

A: The "lost in the middle" effect means LLMs perform worse when relevant information is buried in the middle of a long context window. Contextual compression reduces each chunk to only its relevant sentences before assembly — fewer total tokens means the relevant information is proportionally more prominent, less total context to "get lost in," and relevant spans are more likely to land near the beginning or end of the assembled context.

---

**Q: Explain the trade-off between Agentic RAG and Pipeline RAG for a production system.** `[Hard]`

A: Pipeline RAG gives predictable sub-2 second latency, is easy to test and monitor — appropriate for 80% of queries that are straightforward factual lookups. Agentic RAG handles the remaining 20% that require multi-step reasoning but adds variable latency (2–15 seconds) and is harder to debug deterministically. The production pattern is often hybrid: fast pipeline RAG as the primary path, Agentic RAG triggered only when the pipeline's confidence score is low or the query classifier detects a multi-hop pattern.

---

**Q: How does ColPali differ from CLIP for image retrieval?** `[Hard]`

A: CLIP produces one embedding per image (a global vector), losing spatial and layout information. ColPali uses a Vision Language Model to produce per-patch embeddings (typically 1024 patches per page image), then scores (query, image) pairs using MaxSim — the max similarity over all patch-query pairs. This preserves layout information critical for document page retrieval (charts, tables, diagrams) and achieves significantly higher precision on document QA benchmarks without requiring OCR.

---

**Q: What would make you choose Naive RAG over Advanced RAG for a production system?** `[Easy]`

A: Latency constraints (Naive RAG is 3–5× faster), cost constraints (no reranking API calls), or when the corpus is small, clean, and queries are simple factual lookups where the extra precision of reranking provides negligible benefit. Naive RAG is also easier to debug and monitor. Start with Naive RAG, measure quality gaps, then add Advanced RAG components only where evaluation shows measurable improvement.
