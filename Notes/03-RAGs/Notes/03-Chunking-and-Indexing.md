# Chunking and Indexing Strategies

## Why Chunking Matters

### Concept

Chunking is the most underappreciated quality lever in RAG. A perfect retriever can't save you if the answer is split across two chunks. A perfect embedding model can't save you if your chunks contain too much noise. **Chunking quality sets the ceiling of retrieval quality.**

The core tension: chunk size creates a fundamental precision/recall trade-off.

**Small chunks (100-300 chars):**
- Higher semantic precision — the retrieved chunk is tightly focused on one idea
- Lower contextual completeness — the surrounding context needed to understand the answer may be in adjacent chunks
- More chunks in the index → higher storage and retrieval cost
- Better for factoid Q&A: "What is the capital of France?"

**Large chunks (1000-2000 chars):**
- More context per chunk — surrounding sentences provide interpretive context
- Lower retrieval precision — a large chunk about "pricing" also contains unrelated terms that dilute the embedding
- Fewer chunks in index → lower storage cost
- Better for summarization and nuanced questions

**Rule of thumb starting points:**
- Customer support / FAQ: 256-512 chars, 50 char overlap
- Technical documentation: 512-1000 chars, 100 char overlap
- Legal / regulatory documents: 1000-2000 chars, 200 char overlap (legal context matters)
- Code: function-level chunking (not character-based)

**The overlap parameter:** Overlap ensures information at chunk boundaries doesn't get lost. If chunk N ends mid-sentence, overlap means chunk N+1 starts 50 characters into chunk N, preserving the boundary context.

---

## Fixed-Size Chunking

### Concept

The simplest strategy: split text into chunks of N characters (or tokens) with M character overlap. LangChain's `RecursiveCharacterTextSplitter` is the standard implementation — it tries to split on paragraph breaks first, then sentence breaks, then word breaks, only falling back to hard character splits if necessary.

**Character-based vs token-based:**
- Character-based: faster to compute, but chunks may vary in token count. A 500-char chunk in English averages ~125 tokens; in German or CJK languages, character-to-token ratio differs.
- Token-based: more predictable context window usage. Use `tiktoken` or the model's tokenizer. Preferred when you're close to the LLM's context window limit.

**Recursive separators (in priority order):**
1. `"\n\n"` — paragraph break (strongest semantic boundary)
2. `"\n"` — line break
3. `". "` — sentence end
4. `" "` — word boundary
5. `""` — character boundary (last resort)

This priority ensures chunks are split at the most meaningful boundaries available.

### Code

```python
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    TokenTextSplitter
)
from langchain_community.document_loaders import PyPDFLoader

# Character-based (most common)
char_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", ". ", " ", ""],
    length_function=len  # len() counts characters
)

# Token-based (use when LLM context window is a concern)
token_splitter = TokenTextSplitter(
    chunk_size=128,     # tokens, not characters
    chunk_overlap=10,
    encoding_name="cl100k_base"  # GPT-4 / Gemini compatible
)

# Load and split
loader = PyPDFLoader("policy.pdf")
docs = loader.load()
chunks = char_splitter.split_documents(docs)

# Inspect chunk quality
for i, chunk in enumerate(chunks[:3]):
    print(f"Chunk {i}: {len(chunk.page_content)} chars")
    print(f"  Preview: {chunk.page_content[:100]!r}")
    print(f"  Metadata: {chunk.metadata}\n")
```

---

## Semantic and Recursive Chunking

### Concept

Fixed-size chunking is blind to content structure. A 500-character hard split might bisect a key sentence or merge two unrelated topics. Semantic chunking analyzes the content and splits at points of semantic change.

**Semantic chunking algorithm (LangChain `SemanticChunker`):**
1. Split text into sentences
2. Embed each sentence (or a sliding window of 3 sentences for stability)
3. Compute cosine similarity between consecutive sentence groups
4. Split where cosine similarity drops significantly (semantic breakpoint)
5. Optionally set a minimum and maximum chunk size

**Benefits:**
- Each chunk is semantically coherent — about one topic
- Splits happen at natural topic boundaries, not arbitrary character counts
- Embeddings of semantic chunks have higher semantic purity → better retrieval precision

**Drawbacks:**
- Slower to build (requires embedding every sentence)
- Produces variable-size chunks (hard to predict token budget)
- Slightly worse recall for facts at topic boundaries

**When to prefer semantic chunking:**
- Long-form documents with multiple distinct topics (annual reports, research papers)
- When retrieval precision is more important than build-time speed
- When chunk sizes vary dramatically (some topics are brief, others extensive)

### Code

```python
from langchain_experimental.text_splitter import SemanticChunker
from langchain_google_genai import GoogleGenerativeAIEmbeddings

embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

# Percentile breakpoint: split where similarity drop is in bottom 5th percentile
semantic_splitter = SemanticChunker(
    embeddings=embeddings,
    breakpoint_threshold_type="percentile",  # "percentile", "standard_deviation", "interquartile"
    breakpoint_threshold_amount=95,           # split at top 5% sharpest drops
)

chunks = semantic_splitter.split_documents(docs)

# Compare chunk sizes: semantic vs fixed
fixed_chunks = RecursiveCharacterTextSplitter(chunk_size=500).split_documents(docs)
print(f"Fixed: {len(fixed_chunks)} chunks, avg {sum(len(c.page_content) for c in fixed_chunks)//len(fixed_chunks)} chars")
print(f"Semantic: {len(chunks)} chunks, avg {sum(len(c.page_content) for c in chunks)//len(chunks)} chars")

# Custom semantic chunking for domain-specific documents
def semantic_chunk_by_section(text: str) -> list[str]:
    """Chunk research papers by section headers."""
    import re
    section_pattern = r'^#{1,3}\s+.+$'  # Markdown headers
    parts = re.split(section_pattern, text, flags=re.MULTILINE)
    headers = re.findall(section_pattern, text, flags=re.MULTILINE)
    return [f"{h}\n{p}" for h, p in zip(headers, parts[1:]) if p.strip()]
```

---

## Hierarchical and Parent-Child Chunking

### Concept

Hierarchical chunking solves a fundamental retrieval-generation tension:
- **Small chunks** → better retrieval precision (focused semantic content)
- **Large chunks** → better generation quality (more context for the LLM)

Parent-child chunking provides both by maintaining two levels of granularity:
- **Small child chunks** (100-200 chars) are stored in the vector index and used for retrieval
- **Large parent chunks** (1000-2000 chars) are stored separately and returned for generation

At query time:
1. Embed query → ANN search against small child chunk index
2. Identify which child chunks matched
3. Return their parent chunks (much richer context) to the LLM

**Result:** Retrieval precision of small chunks + generation quality of large chunks.

**Variants:**

| Variant | Index | Return |
|---|---|---|
| Parent-child (standard) | Small children (~200 chars) | Parent (~1000 chars) |
| Sentence window | Individual sentences | ±3 surrounding sentences |
| Document-level | Paragraph-level chunks | Full document |

### Code

```python
from langchain.retrievers import ParentDocumentRetriever
from langchain.storage import InMemoryStore
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Parent chunks (large, for generation context)
parent_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)

# Child chunks (small, for precise retrieval)
child_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20)

# Storage: vector store for child embeddings, docstore for parent text
from langchain_community.vectorstores import Chroma
child_vectorstore = Chroma(embedding_function=embeddings, collection_name="children")
parent_docstore = InMemoryStore()  # use Redis or GCS for production

parent_retriever = ParentDocumentRetriever(
    vectorstore=child_vectorstore,
    docstore=parent_docstore,
    child_splitter=child_splitter,
    parent_splitter=parent_splitter,
)

# Index: adds both parent and child chunks
parent_retriever.add_documents(docs)

# Query: searches small children, returns large parents
results = parent_retriever.invoke("What is the quarterly revenue growth rate?")
# results contain parent chunk text (1500 chars), not child chunk (200 chars)

# Sentence window retriever (manual implementation)
def sentence_window_retrieve(query: str, window: int = 2) -> list[str]:
    """Retrieve by sentence, return sentence + surrounding window."""
    results = sentence_vectorstore.similarity_search(query, k=5)
    enriched = []
    for result in results:
        source_doc_id = result.metadata["doc_id"]
        sentence_idx = result.metadata["sentence_idx"]
        all_sentences = sentence_index[source_doc_id]
        
        start = max(0, sentence_idx - window)
        end = min(len(all_sentences), sentence_idx + window + 1)
        enriched.append(" ".join(all_sentences[start:end]))
    return enriched
```

---

## Metadata and Filtering

### Concept

Metadata pre-filtering is one of the most impactful but least discussed RAG optimizations. By filtering on structured attributes BEFORE the ANN search, you:
1. Reduce the search space → faster ANN search and better recall within the relevant subset
2. Enforce access control → prevent retrieving unauthorized documents
3. Improve answer quality → answers from the relevant date/category/source

**Types of metadata to capture at ingest:**
- `source_type`: "policy", "faq", "legal", "technical"
- `department`: "hr", "legal", "engineering"
- `date`: document creation/update date (for time-windowed queries)
- `author`: useful for attribution
- `language`: for multilingual corpora
- `security_level`: "public", "internal", "confidential"
- `product`: "enterprise", "starter", "all"

**Pre-filter vs post-filter:**
- **Pre-filter** (database-level): filters applied INSIDE the ANN search. The search only considers matching vectors. Fast, but some vector DBs implement this imperfectly (lower recall for pre-filtered HNSW).
- **Post-filter** (application-level): run ANN search on all vectors, then filter results. Fast ANN, but may return too few results after filtering if k is small.

**Best practice:** Pre-filter for large exclusions (e.g., department isolation = exclude 80% of docs). Use a larger k (k=50 instead of k=5) when post-filtering to ensure enough results survive the filter.

### Code

```python
from langchain_community.vectorstores import Chroma

# Add metadata during indexing
from langchain.schema import Document

def create_chunk_with_metadata(text: str, source_file: str, page: int, 
                                 department: str, date: str) -> Document:
    return Document(
        page_content=text,
        metadata={
            "source": source_file,
            "page": page,
            "department": department,
            "date": date,
            "content_hash": hashlib.md5(text.encode()).hexdigest()
        }
    )

# Query with pre-filtering (Chroma)
results = vectorstore.similarity_search(
    query="refund policy",
    k=5,
    filter={
        "department": "legal",
        "$and": [
            {"date": {"$gte": "2023-01-01"}},  # Chroma filter syntax
            {"source_type": {"$eq": "policy"}}
        ]
    }
)

# Pinecone metadata filtering
from langchain_pinecone import PineconeVectorStore

pinecone_vs = PineconeVectorStore(index=index, embedding=embeddings)
results = pinecone_vs.similarity_search(
    query="refund policy",
    k=5,
    filter={
        "department": {"$eq": "legal"},
        "date": {"$gte": "2023-01-01"}
    }
)

# Qdrant payload filtering (most expressive filter syntax)
from qdrant_client.http.models import Filter, FieldCondition, MatchValue, Range

qdrant_filter = Filter(
    must=[
        FieldCondition(key="department", match=MatchValue(value="legal")),
        FieldCondition(key="year", range=Range(gte=2023))
    ]
)
```

---

## Document-Type Specific Strategies

### Concept

Different document types need different chunking approaches. Using a generic text splitter on all document types is a common production mistake.

**PDFs:**
- Challenge: headers, footers, page numbers, multi-column layouts, tables
- Tool: `pymupdf` (`fitz`) for complex PDFs, or Google Document AI for scanned PDFs
- Strategy: extract text page-by-page, strip page numbers/headers, then split semantically

**HTML / Web pages:**
- Challenge: navigation bars, ads, sidebars contain noise
- Tool: `trafilatura` extracts main content and discards nav/footer/ads
- Strategy: extract main content first, then split on HTML headers (`<h1>`, `<h2>`)

**Code:**
- Challenge: semantic meaning depends on function/class boundaries, not sentences
- Tool: `RecursiveCharacterTextSplitter` with code-specific separators
- Strategy: split by function/class definitions; include docstrings with the function body

**Tables:**
- Challenge: tabular data loses meaning when text-serialized and split mid-row
- Strategy: serialize as Markdown tables (each row as one chunk), or use specialized table parsers
- Alternatively: store tables in a structured database, query with SQL

### Code

```python
# PDF with complex layout
import fitz  # pymupdf

def extract_pdf_clean(pdf_path: str) -> list[dict]:
    doc = fitz.open(pdf_path)
    pages = []
    for page_num, page in enumerate(doc):
        blocks = page.get_text("blocks")
        # Filter out headers/footers by y-position
        content_blocks = [
            b[4] for b in blocks
            if b[1] > 50 and b[3] < page.rect.height - 50  # exclude top/bottom 50 pts
            and len(b[4].strip()) > 20  # skip short noise strings
        ]
        pages.append({"page": page_num + 1, "content": "\n".join(content_blocks)})
    return pages

# HTML content extraction
from trafilatura import fetch_url, extract

html = fetch_url("https://example.com/policy")
clean_text = extract(html, include_tables=True, no_fallback=False)

# Code chunking
code_splitter = RecursiveCharacterTextSplitter.from_language(
    language="python",
    chunk_size=1000,
    chunk_overlap=100
)
# Uses Python-specific separators: class defs, function defs, decorators

# Table serialization
def table_to_chunks(df) -> list[str]:
    """Convert DataFrame to searchable text chunks (one row per chunk for precision)."""
    chunks = []
    for _, row in df.iterrows():
        row_text = " | ".join([f"{col}: {val}" for col, val in row.items()])
        chunks.append(row_text)
    return chunks

# Or as markdown (better for LLM generation)
def df_to_markdown_chunks(df, chunk_rows: int = 20) -> list[str]:
    """Chunk DataFrame as Markdown tables."""
    chunks = []
    for i in range(0, len(df), chunk_rows):
        chunks.append(df.iloc[i:i+chunk_rows].to_markdown(index=False))
    return chunks
```

---

## Interview Q&A

**Q: What is the retrieval precision/recall trade-off in chunk sizing, and how do you decide?** `[Medium]`
A: Smaller chunks have higher retrieval precision — the retrieved text is tightly focused on the relevant topic with less noise. But smaller chunks may miss surrounding context needed to answer the question, reducing generation quality. Larger chunks include more context but their embeddings are "diluted" by multiple topics, reducing retrieval precision. The right chunk size depends on query type: factoid Q&A benefits from small precise chunks; synthesis and analysis questions need larger contextual chunks. Parent-child chunking resolves the tension: retrieve with small chunks, generate with their larger parents.

**Q: Why does RecursiveCharacterTextSplitter outperform simple split-by-N-characters?** `[Easy]`
A: RecursiveCharacterTextSplitter applies a priority list of separators, attempting to split at paragraph boundaries first, then sentence boundaries, then word boundaries, only falling back to hard character splits as a last resort. This ensures chunks respect semantic and syntactic boundaries where possible. A naive N-character split often bisects sentences mid-word, creating chunks with incomplete sentences and poor embeddings.

**Q: How does parent-child chunking improve RAG quality over standard chunking?** `[Medium]`
A: Parent-child chunking decouples retrieval granularity from generation context. Small child chunks (100-200 chars) produce focused, high-precision embeddings — ANN search finds the right topic. But the LLM receives the larger parent chunk (1000-2000 chars) containing the full section context, improving answer completeness. Without this pattern, you face a dilemma: small chunks = good retrieval, poor generation; large chunks = poor retrieval, good generation. Parent-child gives both.

**Q: You're building a RAG system over a legal document corpus. What chunking strategy would you use and why?** `[Hard]`
A: Legal documents require large chunks with substantial overlap because: (1) legal meaning is highly context-dependent — a definition in section 2 affects clause interpretation in section 8; (2) legal language is precise and formal, so semantic chunking on topic shifts works well; (3) cross-references between sections mean that a 200-char chunk often lacks the context to be understood alone. Strategy: semantic chunking with a minimum chunk size of 800 chars and maximum 2000 chars, with 20% overlap. Add rich metadata: section number, clause type (definition, obligation, exception), contract type, effective date. For retrieval, use parent-child: retrieve by clause (semantic unit), return the surrounding article (broader legal context) to the LLM.

**Q: How do you handle metadata filtering in a system where users have fine-grained access controls (e.g., user can access marketing docs from 2022-2024 but not HR docs)?** `[Hard]`
A: Model access control as metadata attributes at ingest time: tag every chunk with `department`, `classification_level`, and `date`. At query time, compute the user's permission set from their IAM/RBAC role, translate to a metadata filter: `filter={"department": {"$in": allowed_departments}, "date": {"$range": [user_start, user_end]}, "classification_level": {"$lte": user_max_level}}`. This filter is applied at the vector DB layer — even if application code has a bug, the filter prevents unauthorized vectors from entering results. Critical: this must be enforced server-side (in the query service), never client-side. Audit log every (user_id, query, filter_applied, returned_doc_ids) for forensic capability.

**Q: What are the specific chunking challenges for code repositories?** `[Medium]`
A: Three key challenges: (1) **Semantic unit is function/class**, not paragraph — a function definition should never be split mid-body; use `RecursiveCharacterTextSplitter.from_language("python")` which splits on class/function boundaries. (2) **Context dependency** — a function's meaning depends on its docstring, imports, and class context; include function signatures and docstrings together. (3) **Long functions** — a 300-line function exceeds any reasonable chunk size; strategy: chunk at method level (include the class definition and method signature as context in metadata), or use a code-specific parser (ast module in Python) to extract logical units. Also index function names and docstrings separately for keyword-based retrieval.
