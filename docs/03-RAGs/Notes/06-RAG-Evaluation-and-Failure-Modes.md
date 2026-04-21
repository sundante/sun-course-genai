# RAG Evaluation and Failure Modes

## Common Failure Modes

### Concept

RAG failures fall into three categories: retrieval failures, generation failures, and pipeline failures. Understanding the taxonomy is critical for both building and debugging RAG systems.

```
RAG Failure Taxonomy
├── Retrieval Failures
│   ├── Wrong chunks retrieved (relevance failure)
│   ├── Relevant chunks not retrieved (recall failure)  
│   ├── Correct chunks retrieved but wrong order (ranking failure)
│   └── No chunks retrieved (index/query failure)
├── Generation Failures
│   ├── Hallucination despite context (faithfulness failure)
│   ├── Ignoring retrieved context (context utilization failure)
│   ├── Verbatim copying without synthesis (over-reliance)
│   └── Lost in the middle (position bias)
└── Pipeline Failures
    ├── Chunk boundary bisects key information (chunking failure)
    ├── Index is stale (freshness failure)
    ├── Query-document vocabulary mismatch (lexical gap)
    └── Context window overflow (too many chunks stuffed)
```

**Retrieval failures:**
- **Relevance failure**: The ANN search returns chunks that are semantically adjacent but not actually relevant. Example: query about "Python snake" retrieves programming docs instead of zoology docs in a mixed corpus.
- **Recall failure**: The relevant chunk exists in the index but isn't in top-k. Fix: increase k, add hybrid search, improve embedding model, improve chunking.
- **Ranking failure**: Right chunks retrieved but ranked below irrelevant ones. Fix: add reranking.

**Generation failures:**
- **Faithfulness failure**: The LLM generates claims not supported by the retrieved context. Most insidious — the answer looks correct but contains invented details.
- **Context utilization failure**: The LLM has the right context but ignores it, preferring its parametric memory. Common with GPT-3.5 / older models on highly contested facts.
- **Lost in the middle**: Extensive research (Liu et al., 2023) shows performance degrades significantly for relevant content placed in the middle of a long context. Position 0 and position N (last) are best attended to.

---

## 8-Dimension RAG Evaluation Framework

### Concept

RAGAS covers the core four metrics, but production RAG evaluation requires a broader lens. This 8-dimension framework maps every failure mode to its measurement tool.

| Dimension | What It Measures | Tools | Key Metrics |
|---|---|---|---|
| **Retrieval Quality** | Are the right chunks being found? Covers precision, recall, and ranking order of retrieved context | RAGAS (`context_precision`, `context_recall`), custom Recall@k test sets | Context Precision, Context Recall, NDCG@k, MRR |
| **Groundedness / Faithfulness** | Are generated claims supported by retrieved context? Detects fabricated or unsupported assertions | RAGAS (`faithfulness`), TruLens, LangSmith, FactCC | Faithfulness score (0–1), Claim Support Rate |
| **Hallucination Detection** | Identifies model-generated content that contradicts the source or knowledge base | SelfCheckGPT (multi-sample consistency), GPTScore, NLI-based classifiers | Hallucination Rate, Contradiction Score |
| **Answer Quality** | Measures relevance, completeness, and clarity of the final answer | RAGAS (`answer_relevancy`), G-Eval / LLM-as-Judge, BERTScore, ROUGE-L | Answer Relevancy, ROUGE-L, BERTScore F1, Human BLEU |
| **Robustness** | How well does the system handle adversarial inputs, ambiguous queries, and out-of-distribution questions? | Adversarial test suites, perturbation testing | Accuracy under query paraphrase, accuracy under context noise |
| **End-to-End Task Metrics** | Task-specific correctness — F1, Exact Match, pass@k for code, accuracy for QA benchmarks | Dataset-specific (SQuAD F1, HotpotQA EM, HumanEval pass@k) | Exact Match, F1, pass@1, NDCG for ranking tasks |
| **Latency & Cost** | P50/P95 TTFT, tokens per query, embedding cost, rerank cost | Langfuse, LangSmith, Arize Phoenix, Cloud Trace | P95 latency, cost per query, cache hit rate |
| **User Feedback Loop** | Real-world quality signal — thumbs up/down, escalations, follow-up clarifications | Thumbs up/down UI, support ticket analysis, explicit feedback collection | Negative feedback rate, clarification rate, resolution rate |

**How to prioritize dimensions in practice:**

| Application Type | Primary Metric | Secondary Metric |
|---|---|---|
| Legal / Medical / Financial Q&A | Faithfulness (hallucination is catastrophic) | Retrieval Recall |
| Customer Support Chatbot | Answer Quality + User Feedback | Latency |
| Code Assistant | End-to-End Task (pass@k) | Robustness |
| Internal Knowledge Search | Retrieval Quality | Latency & Cost |
| Real-time Streaming RAG | Latency & Cost | Groundedness |

**Recommended evaluation stack per dimension:**
- **Retrieval**: RAGAS + hand-labeled golden test set (200–500 (q, expected_chunk) pairs)
- **Faithfulness**: RAGAS faithfulness + FactCC for claim-level verification
- **Hallucination**: SelfCheckGPT (sample 5 responses, check internal consistency)
- **Answer quality**: LLM-as-Judge (G-Eval) + human spot-checks for 5% of traffic
- **Latency**: Langfuse or Arize Phoenix for distributed tracing with per-stage spans
- **User feedback**: Thumbs up/down in UI → store to evaluation dataset → weekly RAGAS re-evaluation

---

## RAGAS Metrics

### Concept

RAGAS (Retrieval Augmented Generation Assessment) is the standard evaluation framework. It measures four dimensions, each using LLM-based scoring:

**1. Faithfulness** — Does the generated answer only contain claims that are supported by the retrieved context?

```
Faithfulness = (number of claims in answer supported by context) / (total claims in answer)
```

Implementation: extract all factual claims from the answer using an LLM, then for each claim, ask a judge LLM if the context supports it. Average across claims.

Score = 1.0: every claim in the answer is directly traceable to the context
Score = 0.0: answer is entirely fabricated or contradicts the context

**2. Answer Relevancy** — How relevant is the generated answer to the user's question?

```
Answer Relevancy = average cosine_similarity(original_question, reverse_generated_questions)
```

Implementation: prompt an LLM to generate N questions that the answer would answer, embed those generated questions, compute cosine similarity with the original question. If the answer is relevant to the question, the reverse-generated questions should be similar to the original.

**3. Context Precision** — Of the retrieved chunks, what fraction are actually relevant to the question?

```
Context Precision@k = (relevant_chunks_in_top_k / k) with position weighting
```

Measures retrieval precision. A high context precision means the retriever isn't adding noise.

**4. Context Recall** — Do the retrieved chunks cover all the information needed to answer the question?

```
Context Recall = (sentences in ground truth answer attributable to retrieved context) / (total sentences in ground truth)
```

Requires a ground truth answer. Measures whether retrieval "missed" any necessary information.

**Which metric matters most?**
- Faithfulness: most important for factual/legal/medical applications where hallucination has real consequences
- Context Recall: most important during development to diagnose retrieval gaps
- Answer Relevancy: important for conversational applications where the answer should stay on-topic
- Context Precision: important for cost optimization (fewer chunks = lower token cost)

### Code

```python
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall
)
from ragas.metrics.critique import harmfulness
from datasets import Dataset

# Build evaluation dataset
eval_data = {
    "question": ["What is the refund policy?", "How long is the warranty?"],
    "answer": ["Customers can get a full refund within 30 days.", "The warranty lasts 2 years."],
    "contexts": [
        ["Refunds are available within 30 days of purchase for all plans..."],  # retrieved chunks
        ["All products come with a 2-year limited warranty..."]
    ],
    "ground_truth": [
        "Customers are eligible for a full refund within 30 days.",  # optional: for recall
        "The product warranty covers 2 years from purchase date."
    ]
}

dataset = Dataset.from_dict(eval_data)
result = evaluate(
    dataset,
    metrics=[faithfulness, answer_relevancy, context_precision, context_recall]
)
print(result)
# Output: {'faithfulness': 0.95, 'answer_relevancy': 0.88, 'context_precision': 0.9, 'context_recall': 0.85}

# Manual faithfulness check (useful when RAGAS is overkill)
def check_faithfulness(answer: str, context: str, llm) -> float:
    prompt = f"""Extract all factual claims from the answer. For each claim, 
determine if it is SUPPORTED or NOT_SUPPORTED by the context.

Context: {context}
Answer: {answer}

For each claim, write: CLAIM: <claim> | VERDICT: <SUPPORTED/NOT_SUPPORTED>"""
    
    response = llm.invoke(prompt).content
    lines = [l for l in response.split("\n") if "VERDICT:" in l]
    if not lines:
        return 0.0
    supported = sum(1 for l in lines if "SUPPORTED" in l and "NOT_SUPPORTED" not in l)
    return supported / len(lines)
```

---

## LLM-as-Judge

### Concept

Beyond RAGAS's automated metrics, LLM-as-Judge uses an LLM to evaluate response quality on dimensions that are hard to formalize mathematically: clarity, completeness, tone, citation quality.

**G-Eval framework:**
Define evaluation criteria as natural language rubrics, then ask an LLM to score (1-5) on each criterion. More reliable when using chain-of-thought before scoring.

**Key considerations for LLM judges:**
- Use a stronger model as judge than the model being evaluated (use GPT-4o to judge GPT-3.5)
- Self-evaluation is biased — a model tends to prefer its own outputs
- Position bias: LLMs tend to favor the first response in pairwise comparison
- Verbosity bias: LLMs tend to prefer longer, more detailed answers

**When to use LLM-as-Judge vs RAGAS:**
- RAGAS: automated CI/CD gates on well-defined metrics (faithfulness, recall)
- LLM-as-Judge: qualitative human-preference-aligned evaluation, A/B testing new retrieval strategies

### Code

```python
def g_eval_rag(question: str, context: str, answer: str, judge_llm) -> dict:
    prompt = f"""You are evaluating a RAG system's response. Score each criterion 1-5.

Question: {question}
Retrieved Context: {context}
Generated Answer: {answer}

Evaluate:
1. Faithfulness (1=completely fabricated, 5=every claim supported by context)
2. Relevance (1=completely off-topic, 5=directly and completely answers the question)  
3. Completeness (1=major information missing, 5=all aspects addressed)
4. Clarity (1=confusing/misleading, 5=clear and precise)

First explain your reasoning for each, then provide scores in this format:
Faithfulness: X/5
Relevance: X/5
Completeness: X/5
Clarity: X/5"""
    
    response = judge_llm.invoke(prompt).content
    scores = {}
    for metric in ["Faithfulness", "Relevance", "Completeness", "Clarity"]:
        import re
        match = re.search(rf"{metric}: (\d)/5", response)
        if match:
            scores[metric.lower()] = int(match.group(1)) / 5.0
    return scores
```

---

## Tracing and Observability

### Concept

You cannot improve what you cannot measure. Production RAG systems need end-to-end tracing to diagnose latency, quality, and cost issues.

**What to instrument:**
```
Per request, trace:
├── query_id: unique ID for correlation
├── query: original user query
├── preprocessed_query: after rewriting/expansion
├── retrieval_latency: time to retrieve
├── retrieved_docs: {id, score, content_preview}[]
├── rerank_latency: if reranking used
├── reranked_docs: {id, score}[]
├── llm_latency: time to first token
├── total_tokens: prompt + completion tokens (cost tracking)
├── answer: final generated text
└── user_feedback: thumbs up/down if available
```

**Tools:**

| Tool | Type | Features |
|---|---|---|
| **LangSmith** | LangChain native | Full trace, LLM call inspection, eval datasets |
| **Arize Phoenix** | Open source | Local + cloud, RAGAS integration, drift detection |
| **Vertex AI Tracing** | GCP native | Integration with Cloud Trace, spans per service |
| **W&B Weave** | Weights & Biases | Experiment tracking + LLM tracing |
| **Langfuse** | Open source | EU-hosted option, RAGAS integration |

**Key metrics to monitor in production:**
- `retrieval_latency_p95`: alert if > 100ms
- `answer_quality_score`: sampled RAGAS faithfulness, alert if drops > 5% from baseline
- `cache_hit_rate`: alert if drops below 20% (indicates query distribution shift)
- `token_cost_per_query`: budget tracking
- `user_negative_feedback_rate`: thumbs down / complaint rate

### Code

```python
# LangSmith tracing (minimal setup)
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
os.environ["LANGCHAIN_PROJECT"] = "rag-production"

# All LangChain calls are now automatically traced — no code changes needed

# Custom structured logging for non-LangChain components
import structlog
import time

log = structlog.get_logger()

def traced_retrieve(query: str, retriever) -> tuple[list, float]:
    start = time.perf_counter()
    docs = retriever.invoke(query)
    latency = time.perf_counter() - start
    
    log.info("retrieval_complete",
        query=query[:100],
        num_docs=len(docs),
        latency_ms=round(latency * 1000, 2),
        top_doc_preview=docs[0].page_content[:100] if docs else None,
        doc_sources=[d.metadata.get("source") for d in docs]
    )
    return docs, latency

# Arize Phoenix (open source observability)
import phoenix as px
from phoenix.trace.langchain import LangChainInstrumentor

px.launch_app()  # starts local Phoenix server
LangChainInstrumentor().instrument()  # auto-instruments all LangChain calls
```

---

## A/B Testing RAG

### Concept

To improve a RAG system, you need to know when a change is actually better. A/B testing RAG requires:

**Offline evaluation (pre-deployment):**
Maintain a golden dataset of 100-500 (question, expected_answer, expected_source) tuples from production traffic. Before deploying a change, run both old and new pipelines against the golden set, compare RAGAS scores. Deploy only if new ≥ old on primary metric (typically faithfulness or Recall@5).

**Online evaluation (shadow mode):**
Run new pipeline in parallel with production pipeline but only log results (don't serve to users). Compare quality scores from the shadow pipeline vs production.

**Metric selection:**
Choose one primary metric for go/no-go decisions. Faithfulness for factual applications. Answer relevancy for conversational. Recall@5 for retrieval-focused improvements.

---

## When RAG Is NOT the Answer

### Concept

RAG is not always the right solution. Over-applying it wastes cost and latency.

| Scenario | Why RAG Fails | Better Approach |
|---|---|---|
| **Structured data queries** | "Show me all orders over $1000" — semantic search is wrong tool | SQL / text-to-SQL |
| **Real-time computation** | "What is 15% of $847?" — LLM should compute, not retrieve | Calculator tool, code execution |
| **Tiny static corpus** | 10 FAQ answers that never change | Stuff all FAQs into system prompt (no retrieval needed) |
| **Very low latency (< 200ms)** | RAG adds 100-500ms minimum | Fine-tuning or few-shot in system prompt |
| **All answers from one document** | A report that is always the full context | Summarization chain, not RAG |
| **Private numerical data** | Customer's account balance — lookup, not retrieval | Direct database query |

---

## Interview Q&A

**Q: What is RAGAS faithfulness and how is it computed?** `[Medium]`
A: Faithfulness measures what fraction of factual claims in the generated answer are supported by the retrieved context. Computation: (1) extract all factual claims from the answer using an LLM, (2) for each claim, prompt a judge LLM with both the claim and the context, asking if the context supports the claim, (3) faithfulness = supported claims / total claims. A score of 1.0 means the answer only contains claims directly traceable to retrieved context; 0.0 means the answer is entirely fabricated or contradicts the context.

**Q: How do you debug a RAG system where faithfulness is low (0.4) but context recall is high (0.9)?** `[Hard]`
A: High context recall means the retriever IS finding relevant documents (90% of needed information is present). Low faithfulness means the LLM is ignoring the retrieved context and generating unsupported claims. Diagnoses: (1) check if the LLM's system prompt instructs it strongly enough to use only the provided context — strengthen the grounding instruction. (2) Test if the model ignores context for specific topics it has strong parametric priors about — the model may "know" a wrong answer and prefer it. (3) Check position — is the relevant context placed in the middle of a long context? Try reordering so highest-scored chunks appear first. (4) Check if retrieved chunks contain contradictory information — the model may blend both versions.

**Q: You have no labeled data for evaluation. How do you set up a RAG evaluation pipeline?** `[Hard]`
A: Use synthetic ground truth generation: (1) take 200 random document chunks from your corpus, (2) for each chunk, use an LLM to generate 2-3 realistic questions a user might ask that the chunk can answer, (3) use the same LLM to generate the expected answer from the chunk alone — this becomes your "ground truth." You now have 400-600 (question, context, expected_answer) tuples. Run RAGAS on these. Caveat: synthetic test sets are biased toward content the LLM can answer from the chunks — test on real user queries as soon as you have production traffic.

**Q: What is the "lost in the middle" problem and how do you mitigate it?** `[Medium]`
A: Studies show that LLMs perform significantly worse when the relevant information is placed in the middle of a long context window, compared to beginning or end positions. With k=5 retrieved chunks, position 0 and position 4 are best attended; positions 1-3 are less reliably used. Mitigations: (1) **Reranking + ordering** — use a cross-encoder reranker, then place the highest-scored chunks at position 0 and 4 (top and bottom), lower-scored ones in the middle. (2) **Contextual compression** — reduce each chunk to only its relevant sentences, so total context is shorter and the problem is less severe. (3) **Fewer, higher-quality chunks** — k=3 with high-precision reranking often outperforms k=8 without it.

**Q: What's the difference between context precision and context recall in RAGAS?** `[Easy]`
A: Context precision measures the fraction of retrieved chunks that are relevant to the question — it's a retriever quality metric about noise. Context recall measures whether the retrieved chunks contain all the information needed to answer the question — it's a retriever quality metric about completeness. High context precision + low context recall: the retriever returns only relevant chunks but misses some necessary ones (try increasing k or improving hybrid search). Low context precision + high context recall: the retriever returns all necessary information but also a lot of noise (try better reranking or lower k).

**Q: When should you NOT use RAG?** `[Easy]`
A: RAG adds latency and cost unnecessarily when: (1) the entire knowledge base fits in a system prompt (10 FAQ entries — just include them all); (2) queries are computationally answerable (math, SQL queries over structured data — use tools, not retrieval); (3) latency requirements are very tight (<200ms) and the corpus is static and small enough to fine-tune; (4) every query needs the full document (legal contract review, financial report analysis — pass the full document, not retrieved snippets).
