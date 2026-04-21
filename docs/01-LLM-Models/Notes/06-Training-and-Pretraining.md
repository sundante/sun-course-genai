# Training and Pretraining

## Pre-Training

### Concept

Pretraining is the large-scale phase where a model learns general language understanding from massive unlabeled text corpora. It requires enormous compute and data but is done only once — the resulting base model is then fine-tuned for specific tasks.

**The three stages of an LLM's life:**
```
1. Pretraining   → Base model (knows language, world knowledge, no instruction following)
2. Fine-tuning   → Instruction-tuned model (follows instructions, behaves as assistant)
3. Alignment     → RLHF / DPO (safe, helpful, honest — reduced harmful outputs)
```

**Scale of pretraining:**
- LLaMA-3 8B: trained on ~15 trillion tokens (15T), >2M GPU-hours on H100
- GPT-4: estimated 10T+ tokens, undisclosed compute
- Rule of thumb: 1B GPU-hours on modern H100s costs ~$1M–$3M at cloud prices

---

## Dataset Curation

### Concept

The quality of pretraining data is at least as important as model architecture. "Garbage in, garbage out" applies at trillion-token scale.

**Data sources:**
- **Common Crawl:** Web scrapes of the entire internet — petabytes of raw text; requires aggressive filtering
- **Books:** Project Gutenberg, BooksCorpus, Books3 — high-quality, diverse language
- **Wikipedia:** Clean, factual, structured — high signal-to-noise
- **Code:** GitHub — improves reasoning capabilities, not just coding
- **Academic papers:** ArXiv — improves scientific understanding
- **Curated datasets:** Refinedweb, RedPajama, SlimPajama, Dolma

**Data processing pipeline:**
```
Raw web text
    ↓
URL/domain filtering (block adult content, spam, known low-quality domains)
    ↓
Language detection (keep target languages)
    ↓
Exact deduplication (MinHash, exact hash) — removes copy-pasted content
    ↓
Near-deduplication (SimHash, n-gram overlap) — removes near-duplicates
    ↓
Quality filtering:
  - Perplexity filtering (low-perplexity text from a reference model → good quality)
  - Heuristic rules (min/max token counts, symbol ratio, etc.)
  - Classifier-based quality scoring
    ↓
PII removal (personal email, phone numbers, SSNs)
    ↓
Final tokenization + storage
```

**Why deduplication matters:** Training on duplicate data memorizes specific text rather than learning generalizable patterns. Deduplication also reduces privacy risk (memorized PII).

**Data mixture ratios** (approximate, from public information):
```
LLaMA-3 8B training mix:
~50% general web (filtered Common Crawl)
~15% code
~10% curated/academic
~25% other high-quality sources
```

---

## Tokenization

### Concept

Before training, all text is converted to token sequences using a fixed vocabulary tokenizer built from the training data.

**Byte-Pair Encoding (BPE) — step by step:**

```
Initial vocabulary: all individual bytes (256 symbols)

Training procedure:
1. Split all training text into characters/bytes
2. Count frequency of all adjacent symbol pairs
3. Merge the most frequent pair into a new symbol
4. Repeat until vocabulary reaches target size (e.g., 32K)

Example:
  Text: "low lower lowest"
  Initial: [l,o,w] [l,o,w,e,r] [l,o,w,e,s,t]
  Most frequent pair: (l,o) → merge to (lo)
  → [lo,w] [lo,w,e,r] [lo,w,e,s,t]
  Most frequent pair: (lo,w) → merge to (low)
  → [low] [low,e,r] [low,e,s,t]
  ...continues until target vocab size
```

**Comparing tokenizers:**

| Tokenizer | Algorithm | Used by | Vocab size |
|-----------|-----------|---------|------------|
| tiktoken (cl100k) | BPE | GPT-4, Claude | 100K |
| SentencePiece BPE | BPE | LLaMA, Gemma | 32K–256K |
| WordPiece | Greedy likelihood | BERT, DistilBERT | 30K |
| Unigram | Probabilistic | T5, ALBERT | 32K |

**SentencePiece (LLaMA, Gemma):** Works on raw bytes without pre-tokenization — handles all languages and code uniformly; no whitespace issues.

**tiktoken (GPT-4):** Uses cl100k_base with a 100K vocabulary — larger vocab reduces token counts, improving efficiency for English and code.

---

## Training Objectives

### Concept

**Causal Language Modeling (CLM) — Decoder-only:**
```
Input:   "The cat sat on the mat"
Targets: "cat sat on the mat <EOS>"
Loss:    CrossEntropy(logits, targets) averaged over all non-padding positions
```

The model sees tokens 0..t-1 and predicts token t. This is why causal masking is applied during training — the model must predict each position without seeing future tokens. The loss is the average cross-entropy over all predicted positions in the sequence.

**Masked Language Modeling (MLM) — Encoder-only (BERT):**
```
Input:   "The [MASK] sat on the [MASK]"
Targets: "cat" and "mat"
Loss:    CrossEntropy only on masked positions
```

15% of tokens are replaced: 80% with [MASK], 10% with a random token, 10% kept unchanged (this mix helps the model generalize beyond just masked positions).

**Span Corruption — Encoder-Decoder (T5):**
```
Input:   "The <X> on the mat. The <Y> is fluffy."  (spans replaced by sentinels)
Target:  "<X> cat sat <Y> cat"
Loss:    CrossEntropy on the decoder's output
```

---

## Scaling Laws

### Concept

Neural scaling laws describe how model performance improves predictably with scale. Kaplan et al. (2020, OpenAI) and Hoffmann et al. (2022, DeepMind/Chinchilla) are the key papers.

**Kaplan scaling laws (original):**
- Loss scales as a power law in compute, parameters, and data independently
- For a fixed compute budget: larger model + less data tends to be better
- This led to GPT-3 (175B) being undertrained — not enough tokens for the model size

**Chinchilla scaling law (the correction):**
Hoffmann et al. showed the Kaplan law overweighted parameters. Their revised finding:
```
Optimal: tokens = 20 × parameters
```

- A 7B model should train on 140B tokens for "compute-optimal" training
- LLaMA-1's 65B model was trained on only 1.4T tokens — compute-optimal would be 1.3T, so roughly right
- **LLaMA-2 and LLaMA-3 deliberately overtrain** beyond Chinchilla optimal because the serving cost of a smaller model is more valuable than training efficiency at a fixed compute budget

**The inference-aware scaling insight (LLaMA philosophy):**
Chinchilla optimizes for minimum training loss. But in practice, you want a model that's as good as possible *after serving millions of requests*. Training a smaller model on more tokens → smaller model → cheaper inference × millions of requests. So "compute-optimal training" ≠ "deployment-optimal training."

**Key scaling law takeaways for interviews:**
- Performance scales predictably as a power law in N (parameters), D (tokens), C (compute)
- Doubling parameters gives diminishing returns unless you also double training data
- Chinchilla: optimal token count ≈ 20× parameter count
- Modern LLMs (LLaMA-3, Gemma) train well beyond Chinchilla optimal for inference efficiency

---

## Distributed Training

### Concept

A 70B model in BF16 requires 140 GB of VRAM just for weights — that's more than any single GPU. Training is even worse (4× for optimizer states — see [GPU and Hardware](08-GPU-and-Hardware.md)). Distributed training splits work across many GPUs.

**Data Parallelism (DDP — DistributedDataParallel):**
- Replicate the full model on each GPU
- Split the batch across GPUs (different data, same model)
- After each backward pass, average gradients across all GPUs (all-reduce)
- Simplest strategy; works when model fits on one GPU

**Tensor Parallelism (Megatron-LM style):**
- Split individual weight matrices across GPUs
- Attention heads split across GPUs: head 1–8 on GPU 1, head 9–16 on GPU 2, etc.
- FFN layers split across GPUs: first half of d_ffn on GPU 1, second half on GPU 2
- Requires all-reduce after each layer — high communication overhead
- Essential for models too large to fit on one GPU

**Pipeline Parallelism:**
- Split layers (not weights) across GPUs: layers 1–16 on GPU 1, layers 17–32 on GPU 2
- Micro-batching: split the batch into micro-batches so GPUs overlap computation ("bubble" reduction)
- Communication: only activations at layer boundaries cross GPU — less bandwidth than tensor parallelism
- Bubble overhead: GPUs still idle when waiting for previous stage — mitigated by micro-batching

**ZeRO (Zero Redundancy Optimizer) — covered in detail in [GPU and Hardware](08-GPU-and-Hardware.md):**
- Shards optimizer states, gradients, and parameters across GPUs
- Eliminates redundant copies present in pure DDP
- ZeRO-3: full parameter sharding — enables training models much larger than per-GPU memory

**Practical training setup for 7B model:**
- 8× A100-80GB: enough for BF16 training with ZeRO-2
- Gradient checkpointing: trade 30% compute for 5× memory reduction on activations
- Mixed precision (BF16): 2× memory reduction vs FP32, similar training stability

### Code

```python
# Minimal CLM training loop (conceptual)
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR

model_name = "gpt2"  # small, runnable locally
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

tokenizer.pad_token = tokenizer.eos_token

# Sample training data
texts = [
    "The transformer architecture revolutionized NLP.",
    "Scaling laws predict model performance from compute.",
]

def tokenize(texts, max_length=64):
    return tokenizer(
        texts, 
        truncation=True, 
        padding="max_length", 
        max_length=max_length,
        return_tensors="pt"
    )

optimizer = AdamW(model.parameters(), lr=1e-4, weight_decay=0.01)
scheduler = CosineAnnealingLR(optimizer, T_max=100)

model.train()
for step in range(10):
    batch = tokenize(texts)
    input_ids = batch["input_ids"]
    attention_mask = batch["attention_mask"]
    
    # Labels = input_ids shifted by 1 (CLM: predict next token)
    # HuggingFace handles the shift internally when labels == input_ids
    labels = input_ids.clone()
    labels[attention_mask == 0] = -100  # ignore padding in loss

    outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
    loss = outputs.loss

    optimizer.zero_grad()
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)  # gradient clipping
    optimizer.step()
    scheduler.step()

    print(f"Step {step}: loss={loss.item():.4f}")

# BPE tokenizer training demo (SentencePiece)
from tokenizers import Tokenizer
from tokenizers.models import BPE
from tokenizers.trainers import BpeTrainer
from tokenizers.pre_tokenizers import Whitespace

tokenizer_bpe = Tokenizer(BPE(unk_token="[UNK]"))
tokenizer_bpe.pre_tokenizer = Whitespace()
trainer = BpeTrainer(vocab_size=1000, special_tokens=["[UNK]", "[CLS]", "[PAD]", "[MASK]"])
# trainer.train(["corpus.txt"])  # train on your corpus
print("BPE tokenizer configured (needs corpus file to actually train)")
```

---

## Learning Rate and Training Stability

### Concept

**Warmup + cosine decay:** The standard schedule for transformer training.

```
Warmup (0 → max_lr over first T_warmup steps):
  lr = max_lr × (step / T_warmup)

Cosine decay (T_warmup → T_total):
  lr = min_lr + 0.5 × (max_lr - min_lr) × (1 + cos(π × t / T_decay))
```

**Why warmup?** At the start of training, gradients are large and inconsistent — high learning rates cause instability. Warmup gradually increases lr while the model's parameter estimates stabilize.

**Gradient clipping:** Clips the global gradient norm to a maximum value (typically 1.0):
```
if ||g|| > max_norm:
    g = g × max_norm / ||g||
```
Prevents gradient explosions from occasional bad batches. Essential for stable pretraining.

**Gradient checkpointing:** Instead of storing all activations from the forward pass (needed for backpropagation), discard them and recompute from saved checkpoints during backward. Reduces activation memory by ~5× at the cost of ~30% more compute. Standard for training large models.

---

## Study Notes

**Must-know for interviews:**
- Pretraining = learn language from massive unlabeled data; fine-tuning = specialize for tasks
- Data quality matters enormously: deduplication, quality filtering, and PII removal are critical
- BPE builds subword vocabulary by merging frequent adjacent pairs iteratively
- CLM loss: cross-entropy on next-token prediction; label shifting handled by the framework
- Chinchilla: compute-optimal training = 20× tokens per parameter
- Modern LLMs deliberately overtrain beyond Chinchilla because smaller models are cheaper to serve
- Distributed training: data parallelism (batch split), tensor parallelism (weight split), pipeline parallelism (layer split)

**Quick recall Q&A:**
- *What is the Chinchilla scaling law?* Optimal token count ≈ 20× parameter count for compute-efficient training.
- *Why does LLaMA-3 overtrain beyond Chinchilla?* Inference cost dominates training cost over millions of requests — a smaller, well-trained model costs less to serve.
- *What is gradient checkpointing?* Trading compute for memory by discarding and recomputing activations during backward pass.
- *Why is data deduplication critical?* Duplicate data causes memorization of specific text rather than learning generalizable patterns; also reduces privacy risk.
- *What is the CLM training objective?* Predict the next token given all preceding tokens; minimize cross-entropy averaged over all positions.
