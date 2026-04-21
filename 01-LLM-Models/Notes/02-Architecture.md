# Transformer Architecture

## Transformer Architecture Overview

### Concept

The transformer architecture, introduced in "Attention Is All You Need" (Vaswani et al., 2017), replaced recurrent networks (LSTMs, GRUs) as the dominant architecture for sequence modeling. Its key insight: replace sequential recurrence with **parallel attention** — compute relationships between all positions simultaneously.

**Why transformers displaced RNNs:**
- RNNs process tokens sequentially → cannot parallelize → slow training
- RNNs struggle with long-range dependencies (gradient vanishing over many steps)
- Transformers compute all pairwise relationships in one pass → fully parallelizable on GPUs
- Self-attention has direct access to any position in the sequence, regardless of distance

**The original architecture** had two components:
1. **Encoder** — reads the full input with bidirectional attention, produces context representations
2. **Decoder** — generates output tokens autoregressively, attends to encoder output via cross-attention

Modern LLMs (GPT, LLaMA, Gemma) use **decoder-only** — the encoder is dropped. See [Model Architecture Types](04-Model-Architecture-Types.md) for why.

**High-level decoder-only forward pass:**

```
Input tokens
    ↓
Token Embedding  (token_id → dense vector, vocab_size × d_model)
    ↓
+ Positional Encoding  (adds position information)
    ↓
┌─────────────────────────────────────┐
│  Transformer Block × N layers       │
│                                     │
│  ┌─────────────────────────────┐   │
│  │  LayerNorm (pre-norm)       │   │
│  │  Multi-Head Self-Attention  │   │
│  │  + Residual Connection      │   │
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │  LayerNorm (pre-norm)       │   │
│  │  Feed-Forward Network       │   │
│  │  + Residual Connection      │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
    ↓
Final LayerNorm
    ↓
Linear projection (d_model → vocab_size)
    ↓
Softmax → probability distribution over next token
```

---

## Input Embedding and Positional Encoding

### Concept

**Token Embedding:** Maps each token ID to a learnable dense vector of size `d_model` (512–8192 depending on model). This is a lookup table — a matrix of shape `[vocab_size, d_model]` — learned during training.

**The positional encoding problem:** Self-attention is permutation-invariant by design — the same tokens in different orders produce the same attention outputs without positional information. You must inject position explicitly.

**Three approaches, each with different trade-offs:**

### 1. Sinusoidal Positional Encoding (original Transformer)

Fixed (not learned), uses sine/cosine at different frequencies:

```
PE(pos, 2i)   = sin(pos / 10000^(2i/d_model))
PE(pos, 2i+1) = cos(pos / 10000^(2i/d_model))
```

- Advantage: works for any sequence length (extrapolates to unseen lengths)
- Disadvantage: performance degrades for lengths not seen during training; no adaptation

### 2. Learned Absolute Positional Embeddings (GPT-2, BERT)

A trainable embedding table of shape `[max_seq_len, d_model]`, just like token embeddings.

- Advantage: the model optimizes position representations for the task
- Disadvantage: hard limit at `max_seq_len` — cannot extrapolate to longer sequences

### 3. Rotary Position Embeddings — RoPE (LLaMA, Gemma, Mistral)

Instead of adding position to the embedding, RoPE **rotates** the query and key vectors in attention by an angle proportional to position. The dot product Q·K then naturally encodes relative position.

```
Q_rotated = Q * rotation_matrix(pos_q)
K_rotated = K * rotation_matrix(pos_k)
Q·K encodes relative position (pos_q - pos_k)
```

- Advantage: encodes **relative** position → generalizes better to longer sequences; enables techniques like YaRN for context extension
- Used by: LLaMA-2/3, Gemma, Mistral, Phi, Falcon
- RoPE with scaling (YaRN, LongRoPE) allows extending context beyond the training length

### 4. ALiBi — Attention with Linear Biases (MPT, BLOOM)

Adds a position-dependent bias directly to attention scores (not embeddings):
```
attention_score = Q·K / sqrt(d_k) - m * |i - j|
```
Where `m` is a per-head slope and `|i-j|` is the distance between positions.

- Advantage: zero extra parameters; strong length generalization beyond training length
- Disadvantage: doesn't encode exact position, only proximity — can hurt tasks needing absolute position

| Encoding | Model examples | Extrapolates? | Relative position? |
|----------|----------------|---------------|--------------------|
| Sinusoidal | Original Transformer | Poorly | No |
| Learned absolute | GPT-2, BERT | No | No |
| RoPE | LLaMA, Gemma, Mistral | With scaling | Yes |
| ALiBi | MPT, BLOOM | Yes, naturally | Proximity only |

---

## Layer Normalization and Residual Connections

### Concept

Two techniques that make deep transformers trainable: residual connections and layer normalization.

**Residual connections (He et al., 2016):**
```
output = LayerNorm(x + Sublayer(x))  # Post-LN (original)
output = x + Sublayer(LayerNorm(x))  # Pre-LN (modern)
```

Why they matter: in a 32-layer network without residuals, gradients must flow through 32 multiplicative transformations and easily vanish to zero or explode. Residuals create a "highway" — gradients can flow directly from the output to any layer without passing through all the transformations.

**Layer Normalization:** Normalizes across the feature dimension (d_model) for each token independently:
```
LayerNorm(x) = γ * (x - μ) / (σ + ε) + β
```
Where γ, β are learned scale and shift parameters; μ, σ are computed per-token across features.

**Pre-LN vs Post-LN — a critical difference:**

| | Post-LN (original "Attention is All You Need") | Pre-LN (modern LLMs: LLaMA, GPT-3) |
|--|----------------------------------------------|-------------------------------------|
| Formula | `x + Sublayer(LayerNorm(x))` (LN after residual) | `x + Sublayer(LayerNorm(x))` (LN before sublayer) |
| Training stability | Requires careful learning rate warmup; can diverge | Much more stable; easier to train without warmup |
| Final layer | Needs no extra LN | Needs final LN before the output projection |
| Gradient flow | Gradients pass through LN at every layer | LN is bypassed by the residual path |

**Why modern LLMs use Pre-LN:** More stable training dynamics, easier to scale to very deep networks, less sensitive to learning rate choice.

---

## Feed-Forward Network (FFN)

### Concept

Each transformer block has an FFN that applies the same two-layer MLP to each token **independently** (no cross-token interaction — that's attention's job):

**Original FFN (ReLU):**
```
FFN(x) = W2 · ReLU(W1 · x + b1) + b2
```
- Dimensions: `d_model → 4 * d_model → d_model` (the 4× expansion is the original choice)
- This creates a "wide" intermediate layer that stores fact-like associations

**SwiGLU variant (LLaMA, Gemma, Mistral):**
```
FFN(x) = W2 · (SiLU(W1 · x) ⊗ (W3 · x))
```
Where SiLU(x) = x · sigmoid(x) and ⊗ is element-wise multiplication (gating).

SwiGLU uses **three** weight matrices (W1, W2, W3) but the intermediate dimension is scaled down to compensate (~2/3 × 4 × d_model). Empirically outperforms ReLU and GELU variants.

**Why the FFN matters as much as attention:**
- Attention routes information between tokens
- FFN stores and recalls knowledge — "factual associations" are often thought to live in FFN weights
- The 4× intermediate dimension is why transformers are computationally expensive: for a 7B model with d_model=4096, each FFN layer is 4096 → 16384 → 4096 = 2 × (4096 × 16384) = 134M parameters per layer

---

## Key Architectural Hyperparameters

### Concept

Understanding model shape hyperparameters is essential for VRAM estimation (see [GPU and Hardware](08-GPU-and-Hardware.md)) and for interpreting model cards.

| Hyperparameter | Meaning | Typical values |
|----------------|---------|----------------|
| `d_model` (hidden size) | Embedding and residual stream dimension | 2048–8192 |
| `n_layers` | Number of transformer blocks | 24–80 |
| `n_heads` | Number of attention heads | 16–64 |
| `d_head` | Dimension per head = d_model / n_heads | 64–128 |
| `n_kv_heads` | KV heads (< n_heads for GQA) | 8–n_heads |
| `d_ffn` | FFN intermediate dimension | 4× d_model (or ~2.67× for SwiGLU) |
| `vocab_size` | Number of tokens in vocabulary | 32K–200K |
| `max_position` | Maximum sequence length | 4K–1M |

**Example — LLaMA-3 8B:**
- `d_model = 4096`, `n_layers = 32`, `n_heads = 32`, `n_kv_heads = 8` (GQA), `d_ffn = 14336` (SwiGLU)

**Parameter count estimation:**
```
Embedding:       vocab_size × d_model = 128K × 4096 ≈ 0.5B
Attention/layer: 4 × d_model² = 4 × 4096² = 67M (per layer, 32 layers)
FFN/layer:       3 × d_model × d_ffn = 3 × 4096 × 14336 = 176M (per layer)
Total ≈ 8B ✓
```

### Code

```python
import torch
import torch.nn as nn
import math

class TransformerBlock(nn.Module):
    """Minimal decoder-only transformer block (Pre-LN, no attention for brevity)."""
    def __init__(self, d_model=512, n_heads=8, d_ffn=2048, dropout=0.1):
        super().__init__()
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.attn = nn.MultiheadAttention(d_model, n_heads, batch_first=True)
        self.ffn = nn.Sequential(
            nn.Linear(d_model, d_ffn),
            nn.GELU(),
            nn.Linear(d_ffn, d_model),
            nn.Dropout(dropout),
        )

    def forward(self, x, causal_mask=None):
        # Pre-LN + residual
        normed = self.norm1(x)
        attn_out, _ = self.attn(normed, normed, normed, attn_mask=causal_mask)
        x = x + attn_out          # residual
        x = x + self.ffn(self.norm2(x))  # residual
        return x

class MiniDecoder(nn.Module):
    def __init__(self, vocab_size=1000, d_model=512, n_layers=6, n_heads=8):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, d_model)
        self.pos_embed = nn.Embedding(2048, d_model)  # learned absolute
        self.blocks = nn.ModuleList([
            TransformerBlock(d_model, n_heads) for _ in range(n_layers)
        ])
        self.norm = nn.LayerNorm(d_model)
        self.head = nn.Linear(d_model, vocab_size, bias=False)

    def forward(self, token_ids):
        B, T = token_ids.shape
        positions = torch.arange(T, device=token_ids.device).unsqueeze(0)
        x = self.embed(token_ids) + self.pos_embed(positions)

        # Causal mask: upper triangle = -inf
        causal_mask = torch.triu(
            torch.full((T, T), float('-inf'), device=x.device), diagonal=1
        )
        for block in self.blocks:
            x = block(x, causal_mask)

        x = self.norm(x)
        logits = self.head(x)  # [B, T, vocab_size]
        return logits

# Quick sanity check
model = MiniDecoder(vocab_size=1000, d_model=256, n_layers=4)
tokens = torch.randint(0, 1000, (2, 16))  # batch=2, seq_len=16
logits = model(tokens)
print(f"Input shape: {tokens.shape}")
print(f"Output shape: {logits.shape}")  # [2, 16, 1000]
print(f"Parameters: {sum(p.numel() for p in model.parameters()):,}")
```

---

## Study Notes

**Must-know for interviews:**
- Transformers replaced RNNs by computing all pairwise token relationships in parallel (no sequential bottleneck)
- Decoder-only = causal attention mask, autoregressive generation; encoder-only = bidirectional, no generation
- Pre-LN is more stable than Post-LN and is used by all modern LLMs (LLaMA, Gemma, GPT-3+)
- Residual connections prevent gradient vanishing in deep networks
- RoPE encodes relative position via rotation → enables context extension; used by LLaMA, Gemma, Mistral
- FFN stores factual associations; SwiGLU variant outperforms ReLU and is used in LLaMA/Gemma
- d_model, n_layers, n_heads, d_ffn are the four key hyperparameters for parameter count estimation

**Quick recall Q&A:**
- *Why can't you just add more layers to improve a model without residuals?* Gradients vanish through deep multiplicative transformations — residuals provide a gradient highway.
- *What is the role of the FFN in a transformer?* Stores and recalls learned associations per-token (independent of cross-token interaction, which is attention's job).
- *Why does RoPE generalize better than learned absolute embeddings?* It encodes relative position in the attention dot product, not absolute position in embeddings — relative patterns seen at shorter contexts extend to longer ones.
- *What is Pre-LN and why does it matter?* LayerNorm is applied before the sublayer, not after; makes training stable without requiring careful warmup schedules.
