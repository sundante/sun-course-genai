# LLM Fundamentals

## What Is a Large Language Model

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

---

## Key Concepts: Tokens, Context, Temperature

### Tokens

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

---

### Context Window

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

---

### Sampling Parameters

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

---

## Types of LLMs

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

Full architecture deep dive: see [Transformer Architecture](02-Transformer-Architecture.md) and [Model Architecture Types](04-Model-Architecture-Types.md).

---

## Open Source vs Proprietary

### Concept

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
