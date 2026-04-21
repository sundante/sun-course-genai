# Attention Mechanisms

## Scaled Dot-Product Attention

### Concept

Attention is the core operation that allows each token to "look at" every other token and decide what information to incorporate. The mechanism is elegant: **the more similar a query is to a key, the more the corresponding value contributes to the output**.

**Formal definition:**

```
Attention(Q, K, V) = softmax( Q·Kᵀ / √d_k ) · V
```

Where:
- **Q** (Queries): "What am I looking for?" — derived from the current token
- **K** (Keys): "What do I have to offer?" — derived from all tokens
- **V** (Values): "What do I actually provide?" — derived from all tokens
- **d_k**: dimension of the key/query vectors (used for scaling)

**Step-by-step forward pass:**

```
Input X: [seq_len, d_model]

1. Project to Q, K, V:
   Q = X · W_Q    [seq_len, d_k]
   K = X · W_K    [seq_len, d_k]
   V = X · W_V    [seq_len, d_v]

2. Compute attention scores (raw):
   scores = Q · Kᵀ / √d_k     [seq_len, seq_len]
   # Each entry scores[i,j] = how much token i attends to token j

3. (Optional) Apply causal mask:
   scores[i,j] = -inf  for all j > i   (future masking)

4. Normalize with softmax (per row):
   weights = softmax(scores)     [seq_len, seq_len]
   # Each row sums to 1; weights[i] is token i's attention distribution

5. Weighted sum of values:
   output = weights · V          [seq_len, d_v]
   # Each token's output = weighted average of all values
```

**Why scale by √d_k?**

As d_k grows, the dot product Q·K grows in variance (its magnitude scales as √d_k for random vectors). Without scaling, large dot products push softmax into regions of extremely small gradients (near-zero everywhere except the argmax). Dividing by √d_k keeps the dot product variance at ~1, keeping softmax in its useful gradient range.

**Tricky Q:** *Why does large Q·K variance cause softmax to become "spiky"?*  
Softmax is `exp(x_i) / Σ exp(x_j)`. With large magnitude differences, one term dominates the denominator exponentially — the distribution collapses to a one-hot. The gradient of softmax at this extreme is near-zero → training stalls.

---

## Multi-Head Attention

### Concept

A single attention computation attends to the sequence with one "perspective." Multi-head attention runs **h parallel attention operations** with different learned projections, then concatenates the results.

**Why multiple heads?**

Each head learns to attend based on different relationships:
- Head 1 might focus on syntactic dependencies (subject-verb agreement)
- Head 2 might track coreference (pronoun → noun)
- Head 3 might focus on local context (adjacent words)
- Head 4 might attend to the beginning of the sequence (topic sentence)

No single set of Q/K/V projections can capture all these simultaneously — different projections reveal different structure.

**Formal definition:**

```
MultiHead(Q, K, V) = Concat(head_1, ..., head_h) · W_O

where head_i = Attention(Q · W_Qi, K · W_Ki, V · W_Vi)
```

- Each head has its own W_Q, W_K, W_V of shape [d_model, d_k]
- d_k = d_model / h (so total compute is similar to single large attention)
- Output projection W_O: [h × d_v, d_model] recombines head outputs

**Parameter count per attention layer:**
```
W_Q, W_K, W_V each: d_model × d_model = 4096² ≈ 16.8M (for d_model=4096)
W_O:                 d_model × d_model = 4096² ≈ 16.8M
Total per layer:     4 × d_model² ≈ 67M (for 4096)
```

**Tricky Q:** *Why use separate projection matrices per head rather than just splitting the embedding dimension?*  

Simply splitting d_model/h gives each head a different slice of the same embedding — the slices are not independent because the preceding LayerNorm and FFN computed them jointly. Separate W_Q/W_K/W_V projections allow each head to compute a **different linear transformation** of the full embedding, giving each head a genuinely different "view" of the input. This is the critical distinction.

---

## Self-Attention vs Cross-Attention

### Concept

**Self-attention:** Q, K, and V all come from the **same** input sequence. Used in both encoder and decoder (for attending within a sequence).

```
# Self-attention in a decoder block
Q = K = V = hidden_states  (same source)
output = MultiHead(Q, K, V)
```

**Cross-attention:** Q comes from one sequence (e.g., the decoder), while K and V come from another (e.g., encoder output). This is how encoder-decoder models condition the decoder on the encoded input.

```
# Cross-attention in encoder-decoder
Q = decoder_hidden_states
K = V = encoder_output
output = MultiHead(Q, K, V)  # decoder attends to encoder
```

Cross-attention is absent in decoder-only models (LLaMA, GPT) — they have no separate encoder to cross-attend to.

---

## Causal (Autoregressive) Masking

### Concept

Decoder-only models generate tokens left-to-right. During training, the model sees the full sequence but must not be allowed to "cheat" by attending to future tokens when predicting position i.

**The causal mask:** A lower-triangular boolean matrix applied to attention scores before softmax:

```
For seq_len=4:
Mask:
  [1, 0, 0, 0]    token 0 can only attend to itself
  [1, 1, 0, 0]    token 1 can attend to 0 and 1
  [1, 1, 1, 0]    token 2 can attend to 0, 1, 2
  [1, 1, 1, 1]    token 3 can attend to all
```

Masked positions get score = -inf → softmax produces probability ≈ 0 for those positions.

**Causal masking enables parallel training:** Even though generation is sequential, training can process the entire sequence in parallel by applying the mask. The model simultaneously predicts token 1 from token 0, token 2 from tokens 0–1, token 3 from tokens 0–2, etc. — all in a single forward pass.

---

## Attention Complexity: The Quadratic Bottleneck

### Concept

Standard self-attention is O(n²) in both memory and compute for sequence length n:
- The attention score matrix is [n × n] — n² entries
- Computing Q·Kᵀ requires n × n × d_k multiply-adds

**Practical implications:**

| Sequence length | Attention matrix size | At d_model=4096 |
|-----------------|----------------------|-----------------|
| 2K | 4M entries | ~16 MB per layer (FP16) |
| 32K | 1B entries | ~2 GB per layer |
| 128K | 16B entries | ~32 GB per layer |
| 1M | 1T entries | ~2 TB per layer — impossible to materialize |

This is why long-context models need specialized attention implementations.

---

## Efficient Attention Variants

### Flash Attention

### Concept

Flash Attention (Dao et al., 2022) achieves the *same mathematical result* as standard attention but avoids materializing the full n×n attention matrix in GPU HBM (High Bandwidth Memory). Instead, it tiles the computation to fit in fast on-chip SRAM.

**Why this matters — GPU memory hierarchy:**
```
GPU SRAM (on-chip): ~192 KB per SM, ~20 TB/s bandwidth
GPU HBM (off-chip):  80 GB on A100, ~2 TB/s bandwidth
```

Standard attention writes the full [n,n] attention matrix to HBM and reads it back → bottlenecked by the 10× slower HBM. Flash Attention fuses the attention operations into a single kernel that keeps everything in SRAM:

```
Standard: QKᵀ → write to HBM → read from HBM → softmax → write → read → ×V
Flash:    Tile(Q,K,V) → compute entire attention within SRAM → write only output to HBM
```

**Results:**
- 2–4× faster wall-clock time on long sequences
- Memory usage: O(n) instead of O(n²) — enables much longer contexts
- Numerically identical to standard attention (not an approximation)

**Flash Attention 2 (2023):** Improved parallelism across GPU thread blocks, better work partitioning. ~2× faster than Flash Attention 1.

**Flash Attention 3 (2024):** Exploits H100 tensor core pipelining, asynchronous execution. Another 1.5–2× speedup on H100.

---

### Multi-Query Attention (MQA) and Grouped-Query Attention (GQA)

### Concept

Both are modifications of multi-head attention that **share key and value projections across heads**, reducing KV cache memory (critical for inference — see [KV Cache](05-KV-Cache-and-Inference-Optimization.md)).

**Multi-Head Attention (MHA):** Each head has its own K and V projections.
```
h heads × (d_k + d_v) × d_model = full KV memory
```

**Multi-Query Attention (MQA):** All heads share a single K and V.
```
1 shared K + 1 shared V — KV memory reduced by h×
Quality trade-off: slightly worse, especially for complex tasks
Used by: Falcon, some early efficient models
```

**Grouped-Query Attention (GQA):** G groups of heads, each group shares one K/V.
```
G groups, h/G heads per group
KV memory reduced by h/G×
Best of both worlds: quality close to MHA, memory close to MQA
Used by: LLaMA-3 (h=32 heads, G=8 groups), Gemma, Mistral
```

```
MHA:  [Q1 K1 V1] [Q2 K2 V2] [Q3 K3 V3] [Q4 K4 V4]  (4 KV pairs)
GQA:  [Q1 Q2 K1 V1]  [Q3 Q4 K2 V2]                  (2 KV pairs, G=2)
MQA:  [Q1 Q2 Q3 Q4  K  V ]                           (1 KV pair)
```

| Variant | KV cache size | Quality | Used by |
|---------|--------------|---------|---------|
| MHA | Full (h KV pairs) | Best | BERT, early GPT |
| GQA | h/G KV pairs | Near-MHA | LLaMA-3, Gemma, Mistral |
| MQA | 1 KV pair | Slightly lower | Falcon, Gemma-1 |

---

### Sliding Window Attention (Mistral)

### Concept

Instead of attending to all past tokens, each token attends only to the W nearest tokens (window size W). Long-range information propagates through multiple layers.

```
Standard: token 100 attends to all 100 previous tokens
Sliding:  token 100 attends only to tokens 95–100 (W=5)
After L layers: receptive field = L × W
```

Mistral 7B uses W=4096 with a 32K context — each token's effective receptive field grows with depth. Reduces attention compute from O(n²) to O(n×W).

**Trade-off:** Cannot directly attend to distant context within a single layer. Works well for most generation tasks; less effective for tasks requiring precise recall of distant facts.

---

## Code

```python
import numpy as np
import torch
import torch.nn.functional as F

# Manual scaled dot-product attention (NumPy for clarity)
def scaled_dot_product_attention(Q, K, V, mask=None):
    """
    Q: [batch, heads, seq, d_k]
    K: [batch, heads, seq, d_k]
    V: [batch, heads, seq, d_v]
    """
    d_k = Q.shape[-1]
    scores = np.matmul(Q, K.transpose(-2, -1)) / np.sqrt(d_k)

    if mask is not None:
        scores = np.where(mask == 0, scores, -1e9)

    weights = np.exp(scores - scores.max(axis=-1, keepdims=True))
    weights /= weights.sum(axis=-1, keepdims=True)  # softmax

    output = np.matmul(weights, V)
    return output, weights

# Demo
seq_len, d_k, d_v = 4, 8, 8
Q = np.random.randn(1, 1, seq_len, d_k)
K = np.random.randn(1, 1, seq_len, d_k)
V = np.random.randn(1, 1, seq_len, d_v)

# Causal mask (lower triangular)
causal_mask = np.triu(np.ones((seq_len, seq_len)), k=1).astype(bool)

output, weights = scaled_dot_product_attention(Q, K, V, mask=causal_mask)
print("Attention weights (causal):")
print(weights.squeeze().round(3))
# Should show upper triangle ≈ 0 (masked future positions)

# PyTorch Flash Attention (requires PyTorch >= 2.0)
# torch.nn.functional.scaled_dot_product_attention uses Flash Attention when available
Q_t = torch.randn(2, 8, 512, 64)  # batch, heads, seq, d_k
K_t = torch.randn(2, 8, 512, 64)
V_t = torch.randn(2, 8, 512, 64)

# is_causal=True automatically applies causal masking with Flash Attention backend
with torch.backends.cuda.sdp_kernel(enable_flash=True, enable_math=False):
    output_flash = F.scaled_dot_product_attention(Q_t, K_t, V_t, is_causal=True)

print(f"\nFlash Attention output shape: {output_flash.shape}")
```

---

## Study Notes

**Must-know for interviews:**
- Attention(Q,K,V) = softmax(QKᵀ/√d_k) · V — know this formula by heart
- Scale by √d_k to prevent softmax from collapsing to one-hot with large dot products
- Multi-head attention: different projection matrices per head give genuinely different "views," not just embedding slices
- Causal masking sets future positions to -inf before softmax → enables parallel training of autoregressive models
- Standard attention is O(n²) memory and compute — Flash Attention achieves same result in O(n) memory via SRAM tiling
- GQA (Grouped-Query) shares K/V across head groups — standard in LLaMA-3, Gemma, Mistral for KV cache efficiency

**Quick recall Q&A:**
- *Why does multi-head attention use separate W_Q/W_K/W_V per head?* To give each head a different linear projection of the full embedding, not just a slice — independent "views" of the input.
- *What does Flash Attention optimize?* IO between GPU HBM and SRAM — not the math, just where it happens. Same output, O(n) memory.
- *What is GQA?* Grouped-Query Attention — G groups of heads share K/V projections, reducing KV cache by h/G× with minimal quality loss.
- *What does the causal mask do during training?* Forces position i to predict from only positions 0..i-1, while still processing the full sequence in parallel.
- *Why scale Q·K by √d_k and not d_k?* The standard deviation of the dot product of two random d_k-dimensional unit vectors grows as √d_k, so dividing by √d_k normalizes variance to 1.
