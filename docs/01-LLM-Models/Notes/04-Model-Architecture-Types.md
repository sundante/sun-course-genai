# Model Architecture Types

## Encoder-Only Architecture

### Concept

Encoder-only models use **bidirectional self-attention** — each token can attend to all other tokens simultaneously. There is no causal mask; the model sees the full context in both directions.

**Training objective — Masked Language Modeling (MLM):**
- Randomly mask 15% of tokens in the input
- Train the model to predict the masked tokens from context
- This forces the model to understand bidirectional context

**Architecture specifics:**
- Input sequence → bidirectional attention → contextual representations per token
- No autoregressive generation — the model produces a fixed-size representation for each token, not new tokens
- Classification and span-extraction heads are added on top of the final hidden states

**When to use encoder-only:**
- **Text classification** (sentiment analysis, intent detection): take the [CLS] token embedding → linear head
- **Named Entity Recognition (NER)**: classify each token's hidden state → per-token labels
- **Semantic similarity / embeddings**: mean pool or [CLS] embedding → similarity search
- **Extractive QA** (SQuAD): predict start/end token positions within the context

**Key models:**

| Model | Parameters | Context | Key innovation |
|-------|-----------|---------|----------------|
| BERT-base | 110M | 512 | Bidirectional MLM + NSP |
| BERT-large | 340M | 512 | Larger BERT |
| RoBERTa | 125M/355M | 512 | Removed NSP, more data, better MLM |
| DeBERTa-v3 | 183M | 512 | Disentangled attention, ELECTRA pretraining |
| DistilBERT | 66M | 512 | 40% smaller, 60% faster, 97% of BERT quality |
| BGE-M3 | ~560M | 8K | Multi-function embedding model |

**Tricky Q:** *Can a BERT-family model generate text?*  
No — BERT was never trained to autoregressively predict the next token. Its output is a contextual representation, not a probability distribution over the next token. You can build a seq2seq encoder-decoder on top of a BERT encoder, but the encoder alone cannot generate.

---

## Decoder-Only Architecture

### Concept

Decoder-only models use **causal (left-to-right) self-attention** — each token can only attend to itself and all preceding tokens. The model is trained to predict the next token.

**Training objective — Causal Language Modeling (CLM):**
- Given tokens t₁, t₂, ..., tₙ₋₁, predict tₙ
- Loss is cross-entropy on the predicted next-token distribution vs the actual next token
- The simplicity of this objective is a key reason for the architecture's dominance

**Why decoder-only won:**

1. **Unified objective:** CLM pretraining + instruction fine-tuning (SFT) + RLHF all use the same token prediction framework — no architectural changes between stages
2. **Natural generation:** The architecture is inherently designed to generate; no adapter or cross-attention bridge needed
3. **Emergent reasoning:** At scale, decoder-only models develop chain-of-thought reasoning by learning to produce intermediate "thinking" tokens
4. **In-context learning:** Few-shot prompting works naturally by prepending examples before the query
5. **Scalability:** Simple objective → easy to scale to trillions of training tokens

**Architecture flow:**
```
Input: "The cat sat on the"
→ Tokenize → Embed → [Transformer Block × N with causal mask] → Final LN → Linear → Softmax
→ P(next token) → sample → append → repeat
```

**Key models:**

| Model | Params | Context | Key innovation |
|-------|--------|---------|----------------|
| GPT-2 | 1.5B | 1024 | First large-scale CLM demo |
| GPT-3 | 175B | 2048 | In-context learning at scale |
| GPT-4 / GPT-4o | ~1.8T (MoE, est.) | 128K | Multimodal, top-tier reasoning |
| LLaMA-2 | 7B–70B | 4K | Open weights, commercial license |
| LLaMA-3.1 | 8B–405B | 128K | GQA, strong open weights |
| Gemma 2 | 2B–27B | 8K | Google open, KV-cache sliding window |
| Mistral 7B | 7B | 32K | GQA + sliding window attention |
| Phi-3-mini | 3.8B | 128K | High quality from small size |
| Falcon | 7B–180B | 2K–8K | Multi-Query Attention |

---

## Encoder-Decoder Architecture

### Concept

Encoder-decoder models have two components:
1. **Encoder:** reads the input with bidirectional attention → produces context representations
2. **Decoder:** generates output tokens autoregressively, attending to both its own output (causal self-attention) and the encoder output (**cross-attention**)

**Cross-attention:**
```
Q = decoder hidden states (what the decoder wants to know)
K = V = encoder output    (what the input provides)
cross_attention_output = softmax(Q·Kᵀ / √d_k) · V
```

This allows the decoder to directly "look up" relevant parts of the input at each generation step.

**Training objectives:**

- **T5 (Span Corruption):** Mask contiguous spans of input tokens (replace with single mask token), train decoder to reconstruct the spans
- **BART (Denoising):** Corrupt input via masking, shuffling, deletion; train decoder to reconstruct the clean sequence

**When to use encoder-decoder:**
- **Machine translation:** long input → long output with reordering
- **Abstractive summarization:** input document → shorter summary (not extractive)
- **Document-to-structured output:** parse a document into a structured format
- **Question generation:** answer + context → question

**Key models:**

| Model | Parameters | Key innovation |
|-------|-----------|----------------|
| T5-base/large | 220M/770M | Text-to-text unified framework |
| FLAN-T5 | 80M–11B | Instruction fine-tuned T5 |
| BART | 140M/400M | Denoising pretraining |
| mT5 | 300M–13B | Multilingual T5 |
| mBART | 610M | Multilingual denoising |

**Tricky Q:** *Why did decoder-only models overtake encoder-decoder for summarization and translation?*  

Two reasons: (1) At sufficient scale, decoder-only models learn to produce appropriate-length summaries and translations via instruction fine-tuning, without the architectural inductive bias of cross-attention. (2) A single decoder-only model can handle many tasks via prompting, while encoder-decoder models require task-specific fine-tuning to perform well. Operational simplicity wins.

---

## Architecture Comparison

### Concept

| Dimension | Encoder-Only | Decoder-Only | Encoder-Decoder |
|-----------|-------------|-------------|-----------------|
| Attention direction | Bidirectional | Causal (left-to-right) | Encoder: bi; Decoder: causal + cross |
| Training objective | MLM / ELECTRA | CLM (next token) | Denoising / span corruption |
| Can generate text? | No | Yes | Yes |
| Best for | Classification, NER, embeddings | Generation, reasoning, chat | Seq2seq tasks |
| In-context learning | Poor | Excellent | Moderate |
| Instruction fine-tuning | Awkward | Natural | Possible |
| Production dominance | Embedding models | General LLMs | Niche seq2seq |

---

## Mixture of Experts (MoE)

### Concept

MoE is an architectural modification to the FFN layer, not a new architecture class. Instead of one dense FFN per layer, the model has N "expert" FFNs and a learned **router** that selects top-K experts per token.

```
Standard FFN:
  token → single FFN → output

MoE FFN:
  token → router (softmax over N experts)
         → select top-K experts by router score
         → weighted sum of selected expert outputs
```

**Key MoE concept: sparse activation**
- Total parameters: N × (d_model × d_ffn) — much larger than a dense model
- Active parameters per token: only K experts are used — much smaller computation
- Example: Mixtral-8x7B has 8 experts of 7B each ≈ 47B total parameters, but activates 2 experts per token ≈ 13B active parameters

**MoE advantages:**
- Scale model capacity without proportional compute increase
- Different experts can specialize in different domains/languages/task types
- Efficient at inference for large models (only K/N of FFN is computed per token)

**MoE challenges:**
- Load balancing: without constraints, router collapses all tokens to the same 1–2 experts
- Communication overhead in distributed training (all-to-all for expert routing)
- KV cache still scales with total layers — memory savings only in FFN compute

**Models:**
- Mixtral-8x7B: 8 experts, top-2 routing, 47B total / 13B active
- GPT-4: estimated to be a large MoE (not officially confirmed)
- Switch Transformer (Google): pioneered MoE at scale with top-1 routing

---

## Model Family Comparison Table

### Concept

A reference table for major model families you'll encounter in interviews and production:

| Model Family | Org | Type | Context | Architecture innovations |
|-------------|-----|------|---------|--------------------------|
| GPT-2 | OpenAI | Decoder | 1K | First demo of large CLM |
| GPT-3 | OpenAI | Decoder | 2K | 175B in-context learning |
| GPT-4 / 4o | OpenAI | Decoder (MoE est.) | 128K | Multimodal, top-tier |
| LLaMA-2 | Meta | Decoder | 4K | Open weights, GQA (70B) |
| LLaMA-3 / 3.1 | Meta | Decoder | 8K / 128K | GQA all sizes, 405B |
| Gemma | Google | Decoder | 8K | Multi-query attention |
| Gemma 2 | Google | Decoder | 8K | GQA + local+global attn |
| Mistral 7B | Mistral | Decoder | 32K | GQA + sliding window |
| Mixtral 8x7B | Mistral | Decoder (MoE) | 32K | Top-2 MoE, 47B/13B active |
| Phi-3-mini | Microsoft | Decoder | 128K | 3.8B, textbook-quality data |
| BERT-base | Google | Encoder | 512 | MLM + NSP, bidirectional |
| RoBERTa | Meta | Encoder | 512 | Better BERT training |
| DeBERTa-v3 | Microsoft | Encoder | 512 | Disentangled attention |
| T5 / FLAN-T5 | Google | Enc-Dec | 512–2K | Text-to-text, instruction |
| BART | Meta | Enc-Dec | 1K | Denoising pretraining |

---

## When to Choose Which Architecture

### Concept

**Use encoder-only (BERT/DeBERTa/BGE) when:**
- Task is purely classification, NER, or span extraction
- You need high-quality fixed-size embeddings for search/RAG
- Inference must be very fast (smaller models, no generation overhead)
- Labels are sentence-level or token-level — not generative

**Use decoder-only (LLaMA/Gemma/GPT) when:**
- Task requires free-form text generation
- You want a single model for multiple tasks via prompting
- You need in-context learning (few-shot examples in prompt)
- You plan to instruction fine-tune for custom tasks

**Use encoder-decoder (T5/FLAN-T5/BART) when:**
- Task is explicitly seq2seq with fixed input and output schemas
- You have limited compute — smaller fine-tuned encoder-decoder can beat large decoder-only for specific structured tasks
- Translation or summarization at scale where encoder-decoder efficiency matters

**Practical rule of thumb (2024):** Default to decoder-only for new projects. Switch to encoder-only if you need embeddings or fast token classification. Encoder-decoder is a niche choice for legacy systems or very specific seq2seq workloads.

### Code

```python
from transformers import (
    AutoTokenizer, AutoModelForSequenceClassification,  # Encoder-only
    AutoModelForCausalLM,                               # Decoder-only
    AutoModelForSeq2SeqLM,                             # Encoder-Decoder
    pipeline
)

# --- Encoder-only: text classification ---
classifier = pipeline(
    "text-classification",
    model="distilbert-base-uncased-finetuned-sst-2-english"
)
result = classifier("This movie was absolutely fantastic!")
print(f"Encoder-only classification: {result}")

# --- Decoder-only: text generation ---
generator = pipeline(
    "text-generation",
    model="gpt2",  # small, runs locally
    max_new_tokens=50,
    temperature=0.7
)
result = generator("The transformer architecture revolutionized AI because")
print(f"\nDecoder-only generation: {result[0]['generated_text']}")

# --- Encoder-Decoder: summarization ---
summarizer = pipeline(
    "summarization",
    model="facebook/bart-large-cnn",
    max_length=60,
    min_length=20
)
article = """
The transformer architecture, introduced in the paper "Attention Is All You Need" by Vaswani 
et al. in 2017, revolutionized natural language processing. It replaced recurrent neural 
networks with a self-attention mechanism that could process all tokens simultaneously, 
enabling much faster training and better handling of long-range dependencies.
"""
result = summarizer(article)
print(f"\nEncoder-Decoder summary: {result[0]['summary_text']}")

# --- Checking architecture type programmatically ---
from transformers import AutoConfig

for model_name in ["bert-base-uncased", "gpt2", "facebook/bart-large"]:
    config = AutoConfig.from_pretrained(model_name)
    print(f"{model_name}: {config.model_type} — {config.architectures}")
```

---

## Study Notes

**Must-know for interviews:**
- Three architecture families: encoder-only (bidirectional, MLM, classification), decoder-only (causal, CLM, generation), encoder-decoder (cross-attention, seq2seq)
- Decoder-only dominates production for general LLMs — simple CLM objective + instruction fine-tuning = powerful general purpose model
- BERT uses bidirectional attention — cannot generate; best for embeddings and classification
- MoE: sparse routing selects top-K experts per token → large total params, small active params
- LLaMA-3, Gemma, Mistral all use GQA for efficient KV caching
- When in doubt in 2024: reach for decoder-only (LLaMA-3, Gemma)

**Quick recall Q&A:**
- *Why can BERT not generate text?* BERT was trained with MLM (predict masked tokens), not CLM (predict next token) — it has no autoregressive generation mechanism.
- *What is MoE and what is the key tradeoff?* Multiple expert FFNs with sparse routing — scales capacity without proportional compute, but requires load balancing and has communication overhead in distributed settings.
- *Why did decoder-only beat encoder-decoder for summarization?* At scale + instruction fine-tuning, decoder-only generalizes across tasks without architectural inductive bias; operational simplicity wins.
- *Name 3 decoder-only models and their context lengths.* LLaMA-3.1 (128K), Gemma 2 (8K), Mistral 7B (32K).
