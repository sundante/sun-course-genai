# Concept Review — RAG (Retrieval-Augmented Generation)

## Conceptual Questions

**Q: What is RAG and what problem does it solve?**
Retrieval-Augmented Generation. LLMs have a fixed knowledge cutoff and limited context windows — they can't know about recent events or proprietary internal data. RAG solves this by retrieving relevant documents at query time and injecting them into the prompt, grounding the model's response in real, up-to-date sources without changing model weights.

**Q: What is the difference between RAG and fine-tuning?**
RAG injects knowledge at inference time through retrieved context. Fine-tuning bakes knowledge into model weights during training. RAG is better for: frequently changing data, verifiable citations, large knowledge bases that won't fit in a prompt, and privacy-sensitive data. Fine-tuning is better for: consistent tone/style/format, domain-specific behavior, and reducing inference latency from long prompts. They are complementary, not mutually exclusive.

**Q: Walk me through the basic RAG pipeline.**
(1) Indexing: chunk documents, embed each chunk, store vectors in a vector database. (2) Retrieval: embed the user query, search the vector DB for the top-k nearest chunks. (3) Augmentation: inject retrieved chunks into the prompt alongside the query. (4) Generation: LLM generates a response grounded in the retrieved context.

**Q: What are embeddings and why are they central to RAG?**
Embeddings are dense vector representations of text that capture semantic meaning — similar texts map to nearby vectors in high-dimensional space. They enable semantic search: you retrieve chunks that are *meaning-similar* to the query, not just keyword-matching. The quality of your embedding model directly determines retrieval quality.

---

## Architecture and Design Questions

**Q: What is hybrid search in RAG?**
Combining dense retrieval (embedding similarity) with sparse retrieval (keyword matching, e.g., BM25). Dense search finds semantically related content even with different words. Sparse search excels at exact matches (product IDs, names, technical terms). Hybrid search scores are merged (e.g., Reciprocal Rank Fusion). Usually outperforms either method alone.

**Q: What is re-ranking and why does it help?**
The initial retrieval returns top-k candidates quickly using approximate nearest-neighbor search. A re-ranker (typically a cross-encoder model) then scores each candidate more precisely against the query and reorders them. Re-ranking improves precision at the cost of latency. The pipeline: retrieve top-20 → re-rank → pass top-5 to the LLM.

**Q: What is query transformation / HyDE?**
Hypothetical Document Embedding: instead of embedding the query directly, ask the LLM to generate a hypothetical answer to the query, then embed *that* and use it for retrieval. The hypothetical answer looks more like the target documents than the question does, improving retrieval. Other transformations: query decomposition (split complex queries), step-back prompting (abstract the query to find background knowledge).

**Q: What is agentic RAG?**
Rather than a fixed retrieve-then-generate pipeline, the LLM decides when and what to retrieve, can issue multiple retrieval queries, evaluate whether retrieved content is sufficient, and re-retrieve if needed. The agent treats the knowledge base as a tool. Enables iterative research but adds latency and complexity.

---

## Retrieval and Chunking Questions

**Q: Why does chunking strategy matter so much?**
Chunks that are too large: retrieve irrelevant content alongside relevant content, diluting the signal and wasting context window. Chunks that are too small: lose surrounding context needed to interpret a sentence. The goal is chunks that are semantically self-contained. Chunk boundaries should respect semantic units (paragraphs, sections) rather than arbitrary character counts.

**Q: What is parent-child chunking?**
Index small chunks (child) for precise retrieval, but when a child chunk is retrieved, pass its larger parent chunk to the LLM for context. Solves the tension between retrieval precision (small chunks) and generation context quality (large chunks). Implementation: store parent-child relationships in metadata.

---

## Evaluation Questions

**Q: How do you evaluate a RAG system?**
Two dimensions: retrieval quality and generation quality. Retrieval metrics: recall@k (was the relevant chunk retrieved?), precision@k (were the retrieved chunks relevant?). Generation metrics: faithfulness (does the answer contradict the retrieved context?), answer relevance (does the answer address the question?), context utilization. RAGAS is a popular framework that measures all of these with LLM-as-judge.

**Q: What are the main failure modes of RAG?**
(1) Retrieval failure: relevant chunks not retrieved — caused by poor embeddings, bad chunking, or query-document mismatch. (2) Context poisoning: irrelevant chunks retrieved and hallucinated into the answer. (3) Lost in the middle: LLMs ignore context in the middle of long retrieved passages — put the most relevant chunk first or last. (4) Faithfulness failure: model uses its parametric knowledge instead of the retrieved context. (5) Chunking boundary: answer spans a chunk boundary, so it's never fully retrieved.
