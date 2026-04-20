# Advanced RAG Patterns

## Multi-Query RAG

### Concept

Multi-query RAG addresses a fundamental limitation of single-query retrieval: a single embedding of the user's question represents one point in vector space, and relevant documents spread across multiple semantic dimensions may not be captured by that single point.

The pattern: use an LLM to generate 3-5 paraphrased or decomposed variants of the original query, retrieve separately for each variant, then deduplicate and merge the results.

**When it helps:**
- Ambiguous queries with multiple valid interpretations
- Complex questions that decompose into sub-questions
- Queries using informal language when documents use formal terminology

**When it doesn't help:**
- Precise technical queries (e.g., "error code E4013") — variants can't improve on the exact term
- Adds latency: N queries × embedding time + N × ANN searches + deduplication

**Deduplication strategy:**
De-duplicate by content hash before reranking. If two variants retrieve the same chunk, keep it once but boost its effective score (it was found by multiple independent queries → higher relevance signal).

### Code

```python
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import BaseOutputParser
import re

# Built-in LangChain multi-query
multi_query = MultiQueryRetriever.from_llm(
    retriever=vectorstore.as_retriever(search_kwargs={"k": 6}),
    llm=llm
)
# Internally generates 3 query variants and deduplicates results

# Custom multi-query with controlled prompting
query_gen_prompt = ChatPromptTemplate.from_template(
    """Generate {n} different versions of this question to improve document retrieval.
Each version should approach the question from a different angle.
Original question: {question}
Output one question per line, no numbering."""
)

class LineListParser(BaseOutputParser):
    def parse(self, text: str) -> list[str]:
        return [line.strip() for line in text.strip().split("\n") if line.strip()]

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
    # Sort by retrieval count (docs found by multiple queries rank higher)
    return [doc for doc, _ in sorted(all_docs.values(), key=lambda x: -x[1])]
```

---

## Contextual Compression

### Concept

Standard retrieval returns full document chunks regardless of whether every sentence in the chunk is relevant to the query. Contextual compression post-processes each retrieved chunk to extract only the sentences relevant to the query.

**The problem it solves:**
A 500-character chunk about "refund policy" might contain 4 sentences: one about refunds, one about exchanges, one about store credit, and one about contact information. A query about refunds only needs the first sentence. Returning all 4 wastes context window space and can confuse the LLM with irrelevant details.

**Two types of compressors:**

| Compressor | How | Cost | Quality |
|---|---|---|---|
| `LLMChainExtractor` | LLM extracts relevant sentences | High (LLM call per chunk) | Excellent |
| `LLMChainFilter` | LLM decides keep/discard per chunk | Medium (LLM call per chunk) | Good |
| `EmbeddingsFilter` | Embedding similarity between chunk and query | Very Low | Moderate |

**Practical choice:** `EmbeddingsFilter` with threshold=0.7 is fast and free; `LLMChainExtractor` is more precise but costs an LLM call per retrieved chunk (adds 4× LLM calls if k=4 — expensive).

### Code

```python
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import (
    LLMChainExtractor,
    LLMChainFilter,
    EmbeddingsFilter
)

# Option 1: LLM extraction (best quality, expensive)
extractor = LLMChainExtractor.from_llm(llm)
compression_retriever = ContextualCompressionRetriever(
    base_compressor=extractor,
    base_retriever=vectorstore.as_retriever(search_kwargs={"k": 8})
)

# Option 2: Embedding filter (fast, free, moderate quality)
embeddings_filter = EmbeddingsFilter(
    embeddings=embeddings,
    similarity_threshold=0.70  # discard chunks with cosine < 0.7 to query
)
fast_retriever = ContextualCompressionRetriever(
    base_compressor=embeddings_filter,
    base_retriever=vectorstore.as_retriever(search_kwargs={"k": 8})
)

# Option 3: Pipeline — filter first (cheap), then extract from remaining (precise)
from langchain.retrievers.document_compressors import DocumentCompressorPipeline
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

Self-RAG (Asai et al., 2023) teaches an LLM to adaptively retrieve and critique by training it to generate special reflection tokens alongside regular text. These tokens control the retrieval process.

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
3. LLM continues generating, producing `[IsRel]` to evaluate each retrieved doc
4. LLM generates answer segments, producing `[IsSup]` to verify each claim is supported
5. If `[IsNotSup]` → retrieve again with a refined query
6. Final `[IsUse]` rates the overall response utility

**Key insight:** Unlike standard RAG (always retrieves once before generating), Self-RAG retrieves only when needed and performs in-generation verification. This reduces unnecessary retrievals for questions the model can answer from parametric knowledge.

**Practical implementation without the fine-tuned model:**
Approximate Self-RAG behavior with a standard LLM using reflection prompts — the model assesses whether it needs retrieval, then whether retrieved content is relevant, then whether its generated claims are supported.

### Code

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

def self_rag(query: str) -> dict:
    # Step 1: Assess if retrieval is needed
    retrieval_decision_prompt = ChatPromptTemplate.from_template(
        """Should I retrieve documents to answer this question?
        If the answer requires specific facts, recent information, or private knowledge → RETRIEVE
        If it's general knowledge or reasoning I can do without context → NO_RETRIEVE
        
        Question: {query}
        Decision (RETRIEVE or NO_RETRIEVE):"""
    )
    decision = (retrieval_decision_prompt | llm | StrOutputParser()).invoke({"query": query}).strip()
    
    if "NO_RETRIEVE" in decision:
        answer = llm.invoke(query).content
        return {"answer": answer, "retrieved": False, "supported": "unknown"}
    
    # Step 2: Retrieve
    docs = retriever.invoke(query)
    context = "\n\n".join(doc.page_content for doc in docs)
    
    # Step 3: Assess document relevance
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
        # Re-retrieve with expanded query
        expanded_query = f"detailed information about {query}"
        docs = retriever.invoke(expanded_query)
        context = "\n\n".join(doc.page_content for doc in docs)
    
    # Step 4: Generate with grounding assessment
    grounded_gen_prompt = ChatPromptTemplate.from_template(
        """Answer using only the context. After the answer, rate support:
        FULLY_SUPPORTED, PARTIALLY_SUPPORTED, or NOT_SUPPORTED
        
        Context: {context}
        Question: {query}
        
        Answer:
        Support level:"""
    )
    response = (grounded_gen_prompt | llm | StrOutputParser()).invoke(
        {"context": context, "query": query}
    )
    
    # Parse answer and support level
    parts = response.split("Support level:")
    return {
        "answer": parts[0].replace("Answer:", "").strip(),
        "support_level": parts[1].strip() if len(parts) > 1 else "unknown",
        "retrieved": True
    }
```

---

## FLARE (Forward-Looking Active REtrieval)

### Concept

FLARE (Jiang et al., 2023) addresses a different problem from Self-RAG: during long-form generation, the model may need to retrieve additional information mid-generation to continue accurately.

**How it works:**
1. Model starts generating a response
2. At each generation step, it also generates a "tentative" next sentence with token probabilities
3. If any word in the tentative sentence has probability < threshold (e.g., 0.2), the model is uncertain about that fact
4. Trigger retrieval on the uncertain span
5. Continue generation using the newly retrieved context

**When FLARE excels:**
- Long-form generation (essays, reports) where the model needs fresh context mid-generation
- Multi-part questions where each sub-part needs different retrieval

**Key distinction from Self-RAG:**
Self-RAG retrieves at designated decision points; FLARE retrieves on-demand whenever the generation model becomes uncertain.

### Code

```python
def flare_generate(query: str, max_iterations: int = 5) -> str:
    generated_text = ""
    retrieval_contexts = []
    
    for iteration in range(max_iterations):
        # Generate next segment with the model, tracking token probabilities
        prompt = f"""Context: {chr(10).join(retrieval_contexts)}
        
Previous text: {generated_text}

Continue the response for: {query}
If you're uncertain about any fact, prefix that sentence with [UNCERTAIN]:"""
        
        next_segment = llm.invoke(prompt).content
        
        # Check if model signaled uncertainty
        if "[UNCERTAIN]" in next_segment:
            # Extract uncertain sentence for retrieval
            uncertain_part = next_segment.split("[UNCERTAIN]")[1].split(".")[0]
            new_docs = retriever.invoke(uncertain_part)
            retrieval_contexts.extend([doc.page_content for doc in new_docs[:2]])
            # Re-generate this segment with the new context
            continue
        
        generated_text += " " + next_segment
        
        # Stop if generation seems complete
        if next_segment.strip().endswith((".", "!", "?")):
            break
    
    return generated_text.strip()
```

---

## GraphRAG and Knowledge Graphs

### Concept

GraphRAG (Microsoft Research, 2024) replaces the flat vector index with a structured knowledge graph that captures entities, relationships, and hierarchical summaries. This fundamentally changes what kinds of questions can be answered well.

**Build pipeline (the expensive part):**
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

**Query pipeline:**
- **Local search**: entity detection in query → find relevant entities in graph → retrieve their neighborhood (related entities + relationships + community summaries) → generate answer
- **Global search**: generate answers from multiple community summaries at appropriate level → reduce/aggregate answers → final synthesis

**Why GraphRAG beats dense for relationship queries:**

Example: "Which employees worked at both Google and Apple?"

- Dense RAG: retrieves chunks mentioning Google or Apple, but can't traverse the relationship "employee of" across documents
- GraphRAG: entity "Alice Chen" is a node; edges "worked_at" connect to both "Google" and "Apple"; a graph traversal directly finds this

**Cost reality check:**
GraphRAG indexing costs ~$1-5 per 1M tokens in entity extraction (LLM calls per chunk). A 1M document corpus can cost $1,000-5,000 to index. Query costs are also higher (community summary tokens). Justified only when relationship traversal or global synthesis is a core query pattern.

### Code

```python
# Using the official Microsoft graphrag library
# pip install graphrag

# 1. Initialize settings
# graphrag.json: set model, embedding, storage settings

# 2. Build the index
# python -m graphrag.index --root ./corpus_dir

# 3. Query
import asyncio
from graphrag.query.cli import run_local_search, run_global_search

# Local search: best for specific entity questions
local_result = asyncio.run(run_local_search(
    config_dir="./corpus_dir",
    query="What products did Tesla announce in Q3 2024?"
))

# Global search: best for broad thematic questions
global_result = asyncio.run(run_global_search(
    config_dir="./corpus_dir",
    query="What are the recurring safety concerns mentioned across all reports?"
))

# Simple knowledge graph with NetworkX (DIY approach for smaller corpora)
import networkx as nx

def build_knowledge_graph(chunks: list[str], llm) -> nx.DiGraph:
    G = nx.DiGraph()
    for chunk in chunks:
        extract_prompt = f"""Extract entity-relationship triples from this text.
Format: entity1 | relation | entity2 (one per line)
Text: {chunk}
Triples:"""
        triples_text = llm.invoke(extract_prompt).content
        for line in triples_text.strip().split("\n"):
            parts = [p.strip() for p in line.split("|")]
            if len(parts) == 3:
                e1, rel, e2 = parts
                G.add_edge(e1, e2, relation=rel, source_chunk=chunk[:100])
    return G

def graph_retrieve(G: nx.DiGraph, query: str, k_hops: int = 2) -> list[str]:
    """Traverse graph to find relevant entity neighborhoods."""
    # Extract entities from query
    entities = llm.invoke(f"List named entities in: '{query}'. One per line.").content.split("\n")
    
    relevant_nodes = set()
    for entity in entities:
        entity = entity.strip()
        if entity in G:
            # Get k-hop neighborhood
            neighborhood = nx.ego_graph(G, entity, radius=k_hops)
            relevant_nodes.update(neighborhood.nodes())
    
    # Retrieve edge contexts for relevant nodes
    contexts = []
    for u, v, data in G.edges(data=True):
        if u in relevant_nodes or v in relevant_nodes:
            contexts.append(f"{u} {data['relation']} {v}: {data.get('source_chunk', '')}")
    
    return contexts[:k]
```

---

## Agentic RAG

### Concept

Agentic RAG moves beyond fixed pipelines. An LLM agent has tools including a retriever, and autonomously decides when to retrieve, what to retrieve, how many times to retrieve, and when it has enough information to answer.

**Key differences from pipeline RAG:**
- The agent can ask clarifying questions before retrieving
- The agent can decompose a complex question into sub-questions and retrieve for each
- The agent can evaluate retrieved results and decide to search differently
- The agent can combine retrieval with other tools (calculator, SQL, code execution)

**Architectures:**

**ReAct (Reason + Act):**
```
Thought: I need to find X
Action: retrieve("X")
Observation: [retrieved chunks]
Thought: I found X, but also need Y to complete the answer
Action: retrieve("Y")
Observation: [retrieved chunks about Y]
Thought: I now have enough information
Action: generate_final_answer
```

**Plan-and-Execute:**
```
Plan: [sub_question_1, sub_question_2, sub_question_3]
For each sub-question → retrieve independently
Synthesize: merge all contexts → generate answer
```

**When to use Agentic RAG:**
- Multi-hop questions requiring sequential information gathering
- Questions where the retrieval strategy isn't known in advance
- Complex reasoning combining facts from multiple documents

**Trade-offs:**
- Latency: variable, unpredictable (1-10+ seconds)
- Cost: multiple LLM calls per query
- Reliability: harder to test deterministically

### Code

```python
from langchain.tools.retriever import create_retriever_tool
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate

# Create retrieval as a tool
retriever_tool = create_retriever_tool(
    retriever=hybrid_retriever,
    name="knowledge_search",
    description="Search the knowledge base for relevant documents. "
                "Use this when you need specific facts, policies, or technical information."
)

# ReAct agent
react_prompt = PromptTemplate.from_template("""Answer the following questions using the available tools.

Tools:
{tools}

Use this format:
Question: the input question
Thought: what do I need to find?
Action: tool_name
Action Input: search query
Observation: tool result
... (repeat as needed)
Thought: I now have enough information
Final Answer: the answer

Question: {input}
Thought: {agent_scratchpad}""")

agent = create_react_agent(llm=llm, tools=[retriever_tool], prompt=react_prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=[retriever_tool],
    max_iterations=5,          # prevent infinite loops
    verbose=True,
    return_intermediate_steps=True
)

result = agent_executor.invoke({"input": "What was the revenue in Q3 and what caused the change from Q2?"})
```

---

## Corrective RAG (CRAG)

### Concept

CRAG (Yan et al., 2024) adds a quality gate after retrieval: evaluate whether the retrieved documents are actually relevant to the query. If they're not, fall back to web search instead of trying to generate an answer from irrelevant context.

**The problem it solves:**
Standard RAG always uses retrieved documents, even if they're irrelevant. The LLM then either hallucinates (uses parametric memory despite being told to use context) or says "I don't know" (wasting a query). CRAG detects retrieval failure and has a recovery strategy.

**CRAG states:**
- `CORRECT`: retrieved docs are highly relevant → use directly
- `INCORRECT`: retrieved docs are irrelevant → fall back to web search
- `AMBIGUOUS`: partial relevance → use retrieved docs + web search, merge

### Code

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional

class CRAGState(TypedDict):
    query: str
    retrieved_docs: list[str]
    retrieval_grade: str  # "CORRECT", "INCORRECT", "AMBIGUOUS"
    web_results: list[str]
    final_context: list[str]
    answer: Optional[str]

def grade_retrieval(state: CRAGState) -> CRAGState:
    grading_prompt = f"""Are these documents relevant to the query?
    Query: {state['query']}
    Documents: {state['retrieved_docs'][:2]}
    
    Answer: CORRECT (highly relevant), INCORRECT (not relevant), or AMBIGUOUS (partially relevant)"""
    
    grade = llm.invoke(grading_prompt).content.strip()
    return {"retrieval_grade": grade}

def web_search_node(state: CRAGState) -> CRAGState:
    # Use Tavily, Google Search API, or DuckDuckGo
    from langchain_community.tools import TavilySearchResults
    search = TavilySearchResults(k=3)
    results = search.invoke(state["query"])
    return {"web_results": [r["content"] for r in results]}

def assemble_context(state: CRAGState) -> CRAGState:
    if state["retrieval_grade"] == "CORRECT":
        return {"final_context": state["retrieved_docs"]}
    elif state["retrieval_grade"] == "INCORRECT":
        return {"final_context": state["web_results"]}
    else:  # AMBIGUOUS
        return {"final_context": state["retrieved_docs"] + state["web_results"]}

# Build CRAG graph
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

## Interview Q&A

**Q: How does Self-RAG differ from standard RAG?** `[Medium]`
A: Standard RAG always retrieves before generating — one retrieval, then one generation. Self-RAG uses a fine-tuned model that generates special reflection tokens (`[Retrieve]`, `[IsRel]`, `[IsSup]`) to decide dynamically: should I retrieve at all? Is this retrieved document relevant? Does this generated claim have support from the retrieved context? Self-RAG retrieves only when needed, validates each retrieval, and checks factual support mid-generation — resulting in fewer hallucinations and unnecessary retrievals. The downside is requiring a specially fine-tuned model.

**Q: When would GraphRAG outperform dense vector retrieval?** `[Hard]`
A: Three scenarios where graph traversal wins: (1) Multi-entity relationship queries: "Find all companies that both person X and person Y have worked at" — requires graph traversal, can't be done with vector similarity. (2) Global thematic synthesis: "Summarize the main trends across 10,000 earnings reports" — GraphRAG community summaries aggregate information across the entire corpus, which dense retrieval can't do without reading every document. (3) Causal chain queries: "What led to Event A?" — knowledge graph edges explicitly represent causal relationships that are only implicit in flat text.

**Q: What is FLARE and how does it decide when to retrieve?** `[Hard]`
A: FLARE monitors token-level generation probabilities during forward pass. When a generated token has probability below a threshold (e.g., 0.2), the model is uncertain about that fact. FLARE pauses generation, uses the uncertain span as a retrieval query, fetches relevant documents, then continues generation with the new context. This enables mid-generation retrieval rather than front-loading all retrieval before generation starts. Best for long-form generation where information needs emerge as the model generates.

**Q: Your multi-query RAG is adding too much latency. How do you optimize it?** `[Medium]`
A: Three optimizations: (1) **Parallelize retrievals** — run all N variant queries concurrently using `asyncio.gather()` instead of sequentially; N variants takes the same wall-clock time as 1. (2) **Cache embeddings** — if the same query or variant appears again, the embedding is already computed. (3) **Reduce N** — 2-3 variants often gives 80% of the benefit of 5 variants; empirically test on your eval set. (4) **Move deduplication upstream** — generate variants but retrieve only from the most semantically distant ones (MMR on query variants).

**Q: Explain the trade-off between Agentic RAG and Pipeline RAG for a production customer support system.** `[Hard]`
A: Pipeline RAG gives predictable sub-2 second latency, easy to test, monitor, and debug — it's appropriate for the 80% of customer support queries that are straightforward factual lookups. Agentic RAG handles the remaining 20% that require multi-step reasoning (e.g., "I bought product X on date Y, have I exceeded the warranty period?") but adds variable latency (2-15 seconds) and is harder to debug deterministically. The production pattern is often hybrid: fast pipeline RAG as the primary path, Agentic RAG triggered only when the pipeline's confidence score is low or the query classifier detects a multi-hop pattern.

**Q: What is Corrective RAG and why is it important for RAG reliability?** `[Medium]`
A: CRAG adds a retrieval quality gate: after retrieving documents, an LLM evaluates whether they actually address the query. If not (grade=INCORRECT), it falls back to web search rather than forcing the generator to work with irrelevant context. This is important because standard RAG silently fails — irrelevant retrieval leads to hallucination without any signal to the user. CRAG makes retrieval failure explicit and provides a recovery path. The trade-off: adds latency (one extra LLM call for grading + possible web search) and cost.

**Q: How does Contextual Compression help with the "lost in the middle" problem?** `[Medium]`
A: The "lost in the middle" effect means LLMs perform worse when relevant information is buried in the middle of a long context window. Contextual compression reduces each chunk to only its relevant sentences before assembly. Fewer total tokens in context means: (1) the relevant information is proportionally more prominent, (2) less total context to "get lost in," and (3) the relevant spans are more likely to be near the beginning or end of the assembled context. Use `LLMChainExtractor` to extract relevant sentences, or `EmbeddingsFilter` to discard chunks below a similarity threshold.
