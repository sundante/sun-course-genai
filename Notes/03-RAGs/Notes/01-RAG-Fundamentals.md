# RAG Fundamentals

## What Is Retrieval-Augmented Generation

### Concept

Retrieval-Augmented Generation (RAG) is an architecture that enhances an LLM's responses by providing relevant external context at inference time, retrieved from a corpus you control. Instead of relying solely on knowledge encoded in the model's weights during training, the model reads a curated context window assembled from your documents before generating an answer.

The term was formally introduced by Lewis et al. (2020) at Facebook AI Research, where the generator (a sequence-to-sequence model) was conditioned on retrieved documents from a non-parametric memory (a Wikipedia dense passage index). The core insight: separating **parametric memory** (weights) from **non-parametric memory** (documents) gives you the best of both worlds.

**Three components:**
1. **Retriever** — takes a query, searches a document store, returns top-k relevant passages
2. **Augmentor** — assembles retrieved passages + original query into a structured prompt
3. **Generator** — an LLM that reads the augmented prompt and produces a grounded answer

**The fundamental contract:** The LLM is instructed (explicitly in the prompt) to answer using only the provided context. This constraint is what reduces hallucination — the model has less reason to fabricate when relevant facts are present in the context window.

```
Index phase (offline):
  Documents → chunk → embed → store in vector DB

Query phase (online):
  User query
      ↓
  Embed query (same model as indexing)
      ↓
  ANN search → top-k chunks
      ↓
  Build prompt: "Using the following context: {chunks}\n\nAnswer: {query}"
      ↓
  LLM generates answer grounded in context
```

---

## The Problem RAG Solves

### Concept

LLMs have three fundamental limitations that RAG addresses:

**1. Knowledge cutoff (staleness)**
Training data has a hard cutoff date. A model trained through April 2024 knows nothing about events after that date. In fast-moving domains (finance, news, product documentation, regulation), this renders the model unreliable. RAG bypasses the cutoff entirely — your vector DB is the source of truth, not the model weights.

**2. Hallucination (confabulation)**
LLMs generate plausible-sounding text by predicting tokens, not by retrieving facts. When a question touches knowledge the model has seen only sparsely, it will often generate confident-sounding wrong answers. Providing the correct passage in context dramatically reduces this — the model "reads" the answer rather than "inventing" it.

Caveat: RAG does not eliminate hallucination. If the retrieved chunks are irrelevant, the model still hallucinates. If the retrieved chunks are relevant but the model ignores them (the "lost in the middle" problem), hallucination persists. RAG reduces hallucination; it does not eliminate it.

**3. Private/proprietary knowledge**
You cannot fine-tune a public model on your private documents every time they change. Even if you could, the cost is prohibitive. RAG gives you zero-latency "updates" — add a document to the vector DB and it's immediately retrievable.

**What RAG does NOT solve:**
- Complex reasoning requiring multi-step chains of thought (mitigated by Agentic RAG)
- Numerical computation or structured data queries (use SQL/code tools instead)
- Questions where the answer requires synthesizing thousands of documents (partially mitigated by GraphRAG)

### Code

```python
# Demonstrating the "grounding" effect
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

# Without RAG — likely to hallucinate on proprietary/recent info
bare_answer = llm.invoke("What is the refund policy for Enterprise plan customers?")

# With RAG — grounded in actual policy document
context = """
Enterprise plan customers are eligible for a full refund within 30 days of initial purchase.
After 30 days, prorated refunds are available for unused months. Custom enterprise contracts
may have different terms as specified in the signed agreement.
"""
grounded_answer = llm.invoke(
    f"Using only the following context, answer the question.\n\n"
    f"Context: {context}\n\n"
    f"Question: What is the refund policy for Enterprise plan customers?\n\n"
    f"If the context does not contain the answer, say 'I don't have that information.'"
)
```

---

## RAG vs Fine-Tuning: When to Use Each

### Concept

This is one of the most common interview decision questions. The answer is nuanced — they address different problems, and sometimes you need both.

**Fine-tuning** teaches the model new behavior patterns, styles, or formats by updating its weights. It does NOT reliably inject factual knowledge — studies show fine-tuned models still hallucinate on facts from the fine-tuning corpus.

**RAG** injects factual knowledge at inference time without touching model weights. It does NOT teach the model new reasoning patterns or output styles.

| Dimension | RAG | Fine-Tuning |
|---|---|---|
| **Knowledge updates** | Instant (add to vector DB) | Requires retraining (hours/days) |
| **Factual grounding** | Strong (explicit context) | Weak (facts stored in weights, prone to hallucination) |
| **Cost per update** | Very low | High (compute + data) |
| **Behavior/style adaptation** | Poor | Excellent |
| **Domain-specific reasoning** | Depends on base model | Improved |
| **Traceability** | High (source chunk is known) | None |
| **Context length limit** | Yes (can't retrieve everything) | No (baked into weights) |
| **Private data** | Stays in your DB | Must be in training data |

**RAG wins when:**
- Knowledge changes frequently (support docs, news, regulations)
- You need source citations for auditability
- The corpus is large and diverse
- You can't afford fine-tuning compute

**Fine-tuning wins when:**
- You need a specific output format/style (JSON schemas, specialized language)
- Domain-specific reasoning patterns are important (medical differential diagnosis)
- Latency is critical and retrieval adds unacceptable overhead
- The knowledge is small and stable (e.g., company jargon mapping)

**Combined (RAG + Fine-Tuning):** Fine-tune for style and reasoning patterns, RAG for factual grounding. Example: a medical QA system where the fine-tuned model understands clinical reasoning patterns, and RAG provides specific drug information, guidelines, and patient records.

**RAG vs Prompting (few-shot):** Few-shot prompting works when examples fit in the context window (~10 examples). RAG is needed when the knowledge base has thousands of relevant patterns — you can't manually select which 10 to include.

### Code

```python
# Decision logic template for production
def choose_knowledge_strategy(use_case: dict) -> str:
    """
    Returns: "rag", "finetune", "both", or "prompting"
    """
    if use_case["knowledge_changes_weekly"]:
        if use_case["needs_citations"]:
            return "rag"
        return "rag"
    
    if use_case["needs_custom_reasoning_style"]:
        if use_case["knowledge_is_large_and_changing"]:
            return "both"
        return "finetune"
    
    if use_case["examples_fit_in_context_window"]:
        return "prompting"
    
    return "rag"  # default for most enterprise knowledge Q&A
```

---

## The Basic RAG Pipeline (Index → Retrieve → Augment → Generate)

### Concept

The RAG pipeline has two distinct phases with very different performance characteristics:

**Index Phase (offline, one-time + incremental updates)**
```
Raw Documents
    ↓ Document loader (PDF, HTML, DOCX, etc.)
Text
    ↓ Text splitter (chunking strategy)
Chunks
    ↓ Embedding model (e.g., text-embedding-004)
Vectors
    ↓ Upsert
Vector Database (Chroma, Pinecone, Vertex AI Vector Search)
```

**Query Phase (online, per-request)**
```
User Query
    ↓ Embedding model (same model used in index phase!)
Query Vector
    ↓ ANN search (k=4-8 typical)
Top-k Chunks + Metadata
    ↓ Prompt template
Augmented Prompt
    ↓ LLM (Gemini, GPT-4, Claude)
Answer
```

**Critical invariant:** The embedding model used at query time MUST be the same model used during indexing. Switching embedding models requires re-indexing the entire corpus.

**Component choices and their trade-offs:**

| Component | Options | Key Trade-off |
|---|---|---|
| **Chunker** | Fixed-size, semantic, hierarchical | Chunk size: larger = more context, lower precision |
| **Embedding model** | text-embedding-004, OpenAI ada-002, BGE-large | Quality vs cost vs latency |
| **Vector DB** | Chroma (local), Pinecone (managed), pgvector (SQL) | Scale vs complexity vs cost |
| **k (top-k)** | 3-8 typical | More chunks = more context, but also more noise |
| **LLM** | Gemini, GPT-4, Claude | Quality vs cost vs latency |

### Code

```python
import os
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

# --- INDEX PHASE ---
loader = DirectoryLoader("./docs", glob="**/*.pdf", loader_cls=PyPDFLoader)
raw_docs = loader.load()

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,       # characters (not tokens)
    chunk_overlap=50,     # overlap to avoid losing context at boundaries
    separators=["\n\n", "\n", ". ", " "]  # prefer semantic breaks
)
chunks = splitter.split_documents(raw_docs)

embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="./chroma_db"
)

# --- QUERY PHASE ---
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 4}
)

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

prompt = ChatPromptTemplate.from_template("""You are a helpful assistant. Answer the question using ONLY the provided context.
If the context does not contain the answer, say "I don't have that information in my knowledge base."

Context:
{context}

Question: {question}

Answer:""")

def format_docs(docs):
    return "\n\n---\n\n".join(doc.page_content for doc in docs)

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

answer = rag_chain.invoke("What are the key terms of the Enterprise SLA?")
print(answer)
```

---

## Naive RAG Limitations

### Concept

Even the basic pipeline above has well-documented failure modes. Knowing these is critical for interview discussions about why you'd adopt Advanced or Modular RAG:

**1. Retrieval failures**
- **Wrong k**: Too few chunks → missing information. Too many chunks → noise drowns signal.
- **Query-document mismatch**: User uses colloquial language ("price"), document uses formal language ("pricing schedule"). Semantic embeddings help but don't fully solve this.
- **Chunk boundary issues**: A key fact is split across two chunks; neither chunk alone contains the full answer.

**2. Context window failures**
- **Lost in the middle**: Studies (Liu et al., 2023) show LLMs perform significantly worse when relevant information is placed in the middle of a long context, not at the beginning or end.
- **Context overflow**: Even with 128K context windows, 50+ chunks degrade generation quality.

**3. Generation failures**
- **Ignoring context**: Models sometimes default to parametric memory even when the retrieved context contains the correct answer.
- **Over-reliance on context**: The model copies verbatim from context without synthesizing, producing answer "summaries" rather than answers.
- **Hallucinated citations**: Models may confidently cite chunks that don't say what the model claims.

**4. Index quality issues**
- **Stale index**: New documents aren't indexed promptly; users get outdated answers.
- **No de-duplication**: Near-duplicate chunks waste context window space and distort retrieval rankings.

---

## Interview Q&A

**Q: Why doesn't RAG fully eliminate hallucination?** `[Medium]`
A: RAG reduces hallucination by providing relevant context, but three failure paths remain: (1) the retrieval step fails to surface the relevant chunk, leaving the model without grounding, (2) the "lost in the middle" effect causes the model to ignore relevant context placed in the middle of a long context window, (3) the model still has strong parametric priors that can override the retrieved context, especially for popular misconceptions the model saw repeatedly in training.

**Q: When would you fine-tune a model instead of using RAG?** `[Easy]`
A: Fine-tune when you need to change the model's reasoning patterns, output format/style, or domain-specific language use — behaviors that can't be achieved by injecting context at inference time. Examples: teaching a model to output medical SOAP notes in a specific format, or adapting a model to use specialized jargon correctly. RAG cannot teach new behavior; it can only provide new facts.

**Q: What is the critical invariant in a RAG pipeline that, if violated, causes silent total failure?** `[Hard]`
A: Using a different embedding model at query time than at index time. Since vector similarity is only meaningful within the same embedding space, switching models (e.g., from `text-embedding-004` to `ada-002`) causes every query to retrieve semantically unrelated chunks. The system still returns results (no error), but every answer will be wrong. This is a silent failure — no exception is thrown, and basic integration tests won't catch it unless they check answer quality.

**Q: Explain the RAG pipeline to a non-technical stakeholder in one minute.** `[Easy]`
A: Think of RAG like giving your AI assistant a book before asking it a question. Instead of expecting it to know everything from training, you find the relevant pages first (retrieval), clip them to the question (augmentation), then have the AI answer using those pages (generation). This makes answers more accurate and lets you update the "book" without retraining the AI.

**Q: A RAG system has high retrieval recall but still produces wrong answers. What are the likely causes?** `[Hard]`
A: If retrieval is good (relevant chunks ARE being retrieved), the problem is in generation or augmentation: (1) **Faithfulness failure** — the LLM ignores retrieved context and uses parametric memory instead; diagnose by checking RAGAS faithfulness score. (2) **Lost in the middle** — relevant chunk is retrieved but placed in the middle of the context; fix by reordering chunks or using a cross-encoder reranker to place the highest-scoring chunks first. (3) **Context contradiction** — retrieved chunks contain conflicting information; the model may average or choose the wrong one; fix with better deduplication and source filtering. (4) **Prompt design** — the instruction to "use only the context" is not strong enough; strengthen the grounding instruction.

**Q: What's the difference between the index phase and query phase in terms of latency requirements?** `[Easy]`
A: The index phase is offline/batch — latency is not user-facing, so you can spend seconds per document on expensive embedding calls. The query phase is online/real-time — users are waiting, so p95 latency should be under 2-3 seconds total (including retrieval + reranking + LLM generation). This asymmetry means you can afford expensive but high-quality embedding models in the index phase (they run once per document) but must be more careful about what you add to the query-time path.

**Q: How would you handle a corpus with both English and Spanish documents in a RAG system?** `[Medium]`
A: Two approaches: (1) **Multilingual embeddings** — use a model like `multilingual-e5-large` or `text-multilingual-embedding-002` (Vertex AI) that projects both languages into the same embedding space; query in any language and retrieve across languages. (2) **Language-separated indices** — detect query language, route to the corresponding language's index; more complex but allows language-specific embedding models for higher quality. For most production systems, approach 1 is simpler and good enough; approach 2 is worth the complexity when per-language retrieval quality must be maximized.

**Q: The basic RAG pipeline retrieves k=4 chunks. A user complains answers are often incomplete. How do you debug this?** `[Medium]`
A: Instrument the retrieval step to log (query, retrieved chunks, answer) triples. Check: (1) Are the right chunks being retrieved at rank 1-4, or are they ranked lower? If yes, increase k temporarily to verify — if answer quality improves with k=10, the issue is retrieval ranking, not retrieval recall. (2) Are the right chunks in the index at all? Search the vector DB for the exact answer text — if it's not there, the issue is chunking (information is split across chunks) or missing documents. (3) If the right chunk is retrieved, is it being used in the answer? Compare retrieved context to answer; if the answer ignores the context, it's a faithfulness/generation issue.
