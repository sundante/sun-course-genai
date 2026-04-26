# LLM Fundamentals

## What Is a Large Language Model

<div class="audience-biz" markdown="1">

Think of an LLM as an incredibly well-read assistant. It has absorbed a significant fraction of all text ever written — books, articles, code, research papers, conversations — and learned the statistical patterns of how ideas connect and how language flows.

When you ask it something, it doesn't search a database or look facts up. It generates a response one word at a time, predicting what should come next based on those learned patterns. Every capability you see — summarizing contracts, writing code, answering questions, translating languages — emerges from this single mechanism running at massive scale.

**What this means in practice:**

- LLMs are generative, not retrieval-based — they can confidently state things that are wrong (hallucination). If you need reliable facts, pair the LLM with a retrieval system (see [RAG](../../03-RAGs/INDEX.md)).
- "Large" means trained on a lot of data with a lot of parameters — more scale generally means better results, but also more cost.
- An LLM is not a knowledge base with citations. It encodes patterns, not verified facts.

</div>

<div class="audience-tech" markdown="1">

### Concept

A Large Language Model is a neural network trained to predict the next token given a sequence of preceding tokens. That is the *entire* job description. Every capability — summarization, coding, reasoning, translation — emerges from doing this one thing at massive scale on diverse data.

This framing matters for interviews. An LLM is **not**:
- A knowledge base (it encodes statistical patterns, not facts with citations)
- A reasoning engine (it simulates reasoning by predicting tokens that *look like* reasoning)
- A retrieval system (it cannot look things up unless given tools or RAG)

The correct mental model: **an LLM is a compressed probabilistic model of human text**. It has processed a significant fraction of human-written text and learned what tokens tend to follow other tokens across contexts. When you prompt it, you are sampling from that distribution conditioned on your input.

**Why "large"?** The term is relative. In 2018, BERT-large (340M parameters) was "large." By 2024, the baseline is 7B–70B+ parameters. What scale provides:
- More parameters → more capacity to memorize patterns and relationships
- More training tokens → better generalization and knowledge coverage
- The relationship is governed by scaling laws (see [Training and Pretraining](06-Training-and-Pretraining.md))

**Autoregressive generation:** At inference time, the model generates one token at a time, appending each new token to the context and re-running the forward pass. This is why generation is slow — you cannot parallelize sequential token production.

```
Input:  "The capital of France is"
Step 1: model predicts " Paris" (highest probability) → appended
Step 2: model predicts "." → appended
Step 3: model predicts end-of-sequence token → stop
Output: "The capital of France is Paris."
```

</div>

---

## Key Concepts: Tokens, Context, Temperature

### Tokens

<div class="audience-biz" markdown="1">

AI models don't read text the way you do. They break everything into small chunks called **tokens** — roughly 3–5 characters each, about ¾ of an English word.

This matters for two practical reasons:

**1. Cost.** APIs bill per token. A 10-page document is roughly 3,000–5,000 tokens. A back-and-forth conversation accumulates fast. Understanding token counts helps you budget API costs accurately.

**2. Quirky behavior.** Because the model sees token patterns — not actual characters or numbers — it can struggle with tasks that seem trivial:

- Counting letters in a word ("How many r's in 'strawberry'?") — it never sees individual characters
- Comparing numbers like 9.11 vs 9.9 — digits are tokenized individually, not as numeric values
- Spelling unusual names — rare words get split into pieces the model hasn't seen combined

When an AI gives a surprisingly bad answer to a simple question, token boundaries are often the culprit.

</div>

<div class="audience-tech" markdown="1">

### Concept

LLMs operate on **tokens** — subword units produced by a tokenizer — not characters or words. Understanding tokens is critical for cost estimation, context window management, and debugging unexpected model behavior.

**How BPE tokenization works:**
1. Start with all individual characters as the vocabulary
2. Repeatedly merge the most frequent adjacent pair into a single new token
3. Continue until vocabulary reaches the target size (typically 32K–200K tokens)
4. The result: common words become single tokens; rare words split into subword pieces

**Practical rules of thumb:**
- English text: ~1 token ≈ 4 characters ≈ 0.75 words
- Code: more tokens per line (brackets, indentation, symbols are expensive)
- Non-Latin scripts (Chinese, Arabic): often 1–3 characters per token (less efficient)
- Numbers: each digit is often a separate token — source of arithmetic failures

**Why tokenization causes reasoning failures:**
- "9.11 > 9.9": the model sees `["9", ".", "1", "1"]` and `["9", ".", "9"]` as token sequences, not numbers — it cannot easily do digit-wise comparison
- "50,000" vs "50000" may tokenize differently, causing inconsistency
- Words split across tokens can confuse rhyming and spelling tasks

**Token boundary quiz (common interview trap):**
- Q: *How many tokens is "ChatGPT is great"?*  
  A: 5 tokens: `["Chat", "G", "PT", " is", " great"]` — "ChatGPT" splits because it was rare at training time

### Code

```python
import tiktoken
from transformers import AutoTokenizer

# GPT-4 / Claude-family tokenizer
enc = tiktoken.get_encoding("cl100k_base")
text = "The tokenization of language models is surprisingly tricky."
tokens = enc.encode(text)
print(f"Token count: {len(tokens)}")
print(f"Tokens: {[enc.decode([t]) for t in tokens]}")

# Show the arithmetic problem
number_text = "Is 9.11 greater than 9.9?"
print(f"\n'{number_text}'")
print(f"Tokens: {[enc.decode([t]) for t in enc.encode(number_text)]}")
# Output shows digits tokenized individually

# Compare across model families
llama_tok = AutoTokenizer.from_pretrained("meta-llama/Llama-3.2-1B")
sample = "Tokenization affects everything downstream."
print(f"\nLLaMA-3 tokens: {llama_tok.tokenize(sample)}")
print(f"LLaMA-3 count: {len(llama_tok.encode(sample))}")
```

</div>

---

### Context Window

<div class="audience-biz" markdown="1">

Every AI model has a working memory limit called the **context window**. Think of it as a whiteboard: everything you want the AI to consider — your question, the document you uploaded, the conversation history so far — must fit on that whiteboard.

**What this means in practice:**

- **Long documents need special handling.** A 200-page legal contract won't fit in most context windows. You either need to summarize sections, split the document, or use a retrieval system (RAG) to pull in only the relevant parts.
- **Cost scales with size.** The AI has to compare every piece of information against every other piece — so a larger context window costs significantly more to run. This is why large-context API calls are priced higher.
- **Memory doesn't persist between sessions.** Each new conversation starts blank. The AI has no memory of past conversations unless you explicitly provide them in the prompt.

Context window sizes vary widely — from a few thousand words (small chatbots) to over a million words (Gemini 2.5 Pro). Bigger isn't always better; very long contexts can cause the model to lose focus on information buried in the middle.

</div>

<div class="audience-tech" markdown="1">

### Concept

The context window is the maximum number of tokens an LLM can process in a single forward pass — input + output combined. It is a hard architectural limit.

**Why context windows are bounded:**
- Self-attention computes pairwise relationships between every pair of tokens: **O(n²) memory and compute**
- A 128K-token context requires 128K × 128K = 16.4 billion attention weight computations per layer
- This is why extending context is expensive; Flash Attention and architectural tricks mitigate but don't eliminate this

**Context window sizes (representative, 2024):**

| Model | Context Window |
|-------|---------------|
| GPT-3.5-turbo | 16K |
| GPT-4 Turbo / GPT-4o | 128K |
| Claude 3.5 Sonnet | 200K |
| LLaMA-3.1 8B/70B | 128K |
| Gemini 1.5 Pro | 1M |
| Gemma 2 | 8K |
| Mistral 7B | 32K |

**The dirty secret:** A large context window ≠ uniform retrieval quality. The "lost in the middle" problem (see [Failure Modes](09-Failure-Modes-and-Tricky-Issues.md)) means models attend poorly to tokens buried in the middle of very long contexts. Putting the most important information at the beginning or end of the context is a practical mitigation.

**Context is shared between input and output.** A 128K window with a 100K-token prompt leaves only 28K tokens for the response.

**Context window scaling approaches — how modern models extend context:**

| Approach | Description | Used by |
|----------|-------------|---------|
| Fixed Context | Choose max tokens at model design time (e.g., 2K, 8K) | Early GPTs, BERT |
| Sliding Window / Chunking | Split input into overlapping windows (e.g., 512 tokens with 128 overlap) | RAG / long-doc QA |
| Adaptive Context | Dynamically select relevant chunks based on task | Attention routing systems |
| Sparse Attention | Fixed-size context but sparsified heads — reduces O(n²) cost | Longformer, BigBird, FlashAttention |
| Memory-efficient Transformers | Linear attention or recurrent state instead of full attention | Performer, RWKV, Mamba |
| Recurrence / Caching | Reuse past hidden states or token representations | LLaMA 2/3, RWKV, Gemini, GPT Turbo |
| Retriever-Augmented (RAG) | Retrieve external chunks to keep active context short and focused | All RAG systems |
| Compressed Context | Summarize long text, feed a compact version to the model | Hybrid long-doc systems |
| RoPE Interpolation | Rescale rotary position embeddings to extend native context window | GPT-NeoX, Mistral 7B, Claude 3, LLaMA 2/3 |

**Context window sizes in current models (2025/2026):**

| Model | Context Length | How it's achieved |
|-------|---------------|-------------------|
| GPT-3.5 | 4K / 16K | Naive Transformer |
| GPT-4 / GPT-4.1 | 128K / 1M | FlashAttention + chunking |
| Claude 3 / Sonnet 4 | 200K | Sparse attention + retrieval + caching |
| Gemini 2.5 Pro | 1M | Memory compression + long-context training |
| LLaMA 4 Scout | 10M | MoE + extreme context training |
| Mistral 7B | 32K (tested 64K) | RoPE interpolation |
| Longformer | 4K–16K | Sparse local + global attention |
| RWKV | Infinite (streaming) | RNN-like with token recurrence |
| Mamba | Sub-quadratic | Attention-free state-space model |

**Practical guidelines — choosing context window strategy:**

| Use Case | Recommended Strategy |
|----------|---------------------|
| Small chatbot (FAQ, support) | 2K–4K context is sufficient |
| Long documents (legal, medical, policy) | 8K–32K + retrieval or summarization |
| Summarization of books or legal docs | RAG + chunking + re-ranking |
| Code generation | 8K–16K (code needs larger context for multi-file awareness) |
| Training from scratch | Trade off context size vs GPU memory (O(n²) attention cost) |
| Local inference on laptop | Prefer 2K–4K with quantization |

</div>

---

### Sampling Parameters

<div class="audience-biz" markdown="1">

When you build or configure an AI product, you can tune how predictable or creative its responses are. The main dial is called **temperature**.

| Temperature setting | Effect | When to use |
|---------------------|--------|-------------|
| Low (0.0–0.3) | Consistent, focused, predictable | Customer support, factual Q&A, data extraction |
| Medium (0.5–0.8) | Balanced | General chat, writing assistance |
| High (1.0+) | Creative, varied, unpredictable | Brainstorming, creative writing, idea generation |

Most consumer AI products expose this as a "creativity" or "randomness" slider. For business applications, you almost always want low-to-medium temperature — predictability and consistency matter more than creativity in production.

There are a few other dials engineers tune (top-p, top-k, repetition penalty), but temperature is the one with the most direct business impact.

</div>

<div class="audience-tech" markdown="1">

### Concept

When the model predicts the next token, it produces a probability distribution over its entire vocabulary (e.g., 32K–200K tokens). Sampling parameters control how you draw from that distribution.

**Temperature** scales the logits before softmax:

```
P(token_i) = softmax(logits / T)[i]
```

| Temperature | Effect | Use case |
|-------------|--------|----------|
| 0.0 | Greedy: always pick argmax | Deterministic tasks, factual QA |
| 0.1–0.5 | Sharp, conservative | Code generation, structured output |
| 0.7–1.0 | Balanced creativity | General chat, creative writing |
| 1.5–2.0 | Very random, often incoherent | Brainstorming, diversity sampling |

**Tricky Q:** *Is temperature=0 identical to greedy decoding?*  
Mathematically yes — as T→0, softmax concentrates all mass on the argmax. In practice, `temperature=0` in most APIs is implemented as `argmax`, producing deterministic results. True floating-point `softmax(logits/0)` would divide by zero.

**Top-p (Nucleus Sampling):** Consider only the smallest set of tokens whose cumulative probability ≥ `p`, then renormalize and sample from that nucleus.

```
Sort tokens by P descending: [0.4, 0.2, 0.15, 0.1, 0.05, ...]
top_p=0.9: include tokens until cumulative sum ≥ 0.9 → [0.4, 0.2, 0.15, 0.1, 0.05] (sum=0.9)
Sample from these 5 tokens (renormalized)
```

Top-p adapts: when the model is confident (peaked distribution), the nucleus is tiny; when uncertain, it's larger.

**Top-k:** Restrict to the `k` highest-probability tokens before sampling. Less adaptive than top-p.

**Repetition penalty:** Divides the logit of tokens that have already appeared:
```
logit[token] /= repetition_penalty  (if token appeared before)
```
Values > 1.0 penalize repetition. Without this, greedy decoding often collapses into loops.

| Parameter | Effect | Typical Range |
|-----------|--------|---------------|
| `temperature` | Distribution sharpness | 0.0–2.0 |
| `top_p` | Nucleus size | 0.7–1.0 |
| `top_k` | Hard token cutoff | 10–100 |
| `repetition_penalty` | Loop prevention | 1.0–1.3 |
| `max_new_tokens` | Output length cap | task-specific |

</div>

---

## Types of LLMs

<div class="audience-biz" markdown="1">

There are three main families of language models, each built for different tasks:

| Type | What it does | Real-world examples | Best for |
|------|-------------|---------------------|----------|
| **Generator** | Produces free-form text, answers questions, writes code | ChatGPT, Claude, Gemini | Chat, writing, coding, Q&A, summarization |
| **Classifier** | Labels or categorizes text — doesn't generate new text | BERT (used inside Google Search) | Sentiment analysis, content moderation, search ranking |
| **Translator** | Converts one format of text to another | Translation engines, document summarizers | Language translation, structured extraction |

**Generators have largely won** for general-purpose AI products. When evaluating AI vendors or choosing a model for a specific business use case, the type matters more than the brand name. A classifier is orders of magnitude cheaper than a generator for tasks like "is this review positive or negative?"

The emerging pattern is **Mixture of Experts (MoE)** — a way to make very large models cheaper to run by only activating a fraction of their capacity per request. This is why some models can have 400B+ parameters but still run at reasonable cost.

</div>

<div class="audience-tech" markdown="1">

### Concept

LLMs are categorized by their training architecture and objective. Three core types exist, with a clear market winner in 2024.

**1. Decoder-Only (Causal LM)**
- Architecture: transformer with causal (left-to-right) attention masking
- Training objective: predict next token (Causal Language Modeling, CLM)
- Examples: GPT family, LLaMA, Gemma, Mistral, Phi, Falcon
- Best for: text generation, chat, reasoning, code, general-purpose tasks
- **Dominant in production** — has displaced other architectures for most tasks

**2. Encoder-Only (Masked LM)**
- Architecture: transformer with bidirectional attention (sees full context)
- Training objective: predict masked tokens (Masked Language Modeling, MLM)
- Examples: BERT, RoBERTa, DeBERTa, DistilBERT
- Best for: text classification, NER, semantic similarity, embeddings
- **Not generative** — cannot produce free-form text, only classify or embed

**3. Encoder-Decoder (Seq2Seq)**
- Architecture: encoder produces context representations; decoder attends to encoder output via cross-attention
- Training objective: span corruption (T5), denoising (BART)
- Examples: T5, BART, mT5, FLAN-T5, mBART
- Best for: translation, summarization, structured prediction (document → output)
- Still used for seq2seq tasks but decoder-only models have largely caught up via prompting

**Why decoder-only won:**
1. Unified training objective (CLM) — no need for masked prediction or denoising design choices
2. Generation is natural — the architecture is designed for it
3. Instruction fine-tuning (SFT + RLHF) works exceptionally well on top of CLM pretraining
4. Emergent in-context learning scales with model size

**Mixture of Experts (MoE) — a fourth category:**
Not a separate architecture but a modification: instead of one dense FFN per layer, use N "expert" FFNs and a router that selects 1–2 experts per token. Result: large total parameters but only a fraction active per token (Mixtral-8x7B: 47B total, ~13B active).

Full architecture deep dive: see [Transformer Architecture](02-Architecture.md) and [Model Architecture Types](04-Model-Architecture-Types.md).

</div>

---

## Open Source vs Proprietary

| Dimension | Open Source (LLaMA-3, Gemma, Mistral) | Proprietary (GPT-4o, Claude 3.5, Gemini 1.5) |
|-----------|---------------------------------------|-----------------------------------------------|
| **Per-token cost at scale** | Infrastructure cost only | Provider billing (can be high at volume) |
| **Data privacy** | Runs on your infra; no data leaves | Data sent to provider API |
| **Customization** | Full fine-tuning, quantization, architecture changes | Limited fine-tuning API at extra cost |
| **Frontier capability** | Lags by ~6–12 months | Cutting-edge models |
| **Ops burden** | You manage GPUs, scaling, updates, failures | Zero ops — just call an API |
| **Latency control** | Full control; can optimize aggressively | Variable, dependent on provider load |
| **Compliance/audit** | Can inspect weights and pipeline | Black box; trust provider's policies |

**Choose open source when:**
- Strict data residency (GDPR, HIPAA, SOC 2, financial PII)
- High-volume workloads where per-token cost dominates
- Fine-tuning on proprietary data you cannot share with an external provider
- Research requiring reproducibility or custom modifications

**Choose proprietary when:**
- Rapid prototyping where GPU ops is not your core competency
- Tasks requiring frontier-quality reasoning (frontier open models are ~6–12 months behind)
- Low-volume usage where managed reliability > cost optimization
- Multimodal tasks (vision, audio) where open models still lag

---

## Study Notes

**Must-know for interviews:**
- LLM = next-token predictor; all capabilities emerge from this at scale
- ~1 token ≈ 4 characters / 0.75 words in English; code and non-Latin scripts use more tokens
- Context window = hard O(n²) limit; large windows exist but quality degrades in the middle
- Temperature=0 ≈ greedy; top-p nucleus sampling is preferred for creative tasks
- Three architecture types: decoder-only (dominant, generative), encoder-only (BERT, classification), encoder-decoder (seq2seq)
- Open source = data control + cost at scale; proprietary = ops simplicity + frontier capability

**Quick recall Q&A:**
- *What does temperature=0 produce?* Deterministic greedy output — always the highest-probability next token.
- *Why can't LLMs reliably do arithmetic?* Digits tokenize individually; no native integer arithmetic, only learned statistical patterns over digit sequences.
- *What limits context window size?* Attention is O(n²) — quadratic memory and compute in sequence length.
- *What is a token?* A subword unit produced by BPE/SentencePiece; typically 3–5 characters in English.
- *Why did decoder-only win?* Unified CLM objective, natural generation, instruction fine-tuning works well, scales with emergent in-context learning.
