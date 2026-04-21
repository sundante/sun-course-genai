# GPU and Hardware Considerations

## VRAM Estimation

### Concept

Before deploying or training any LLM, you must know whether it fits in your GPU(s). VRAM estimation is a fundamental interview skill.

**Model weights memory:**
```
weights_GB = num_parameters × bytes_per_parameter / (1024³)

Bytes per precision:
  FP32:  4 bytes
  BF16:  2 bytes  ← standard for training and most inference
  FP16:  2 bytes
  INT8:  1 byte
  INT4:  0.5 bytes
  NF4:   0.5 bytes
```

**Quick mental math (BF16):**
- 7B model:   7 × 2 = 14 GB
- 13B model: 13 × 2 = 26 GB
- 70B model: 70 × 2 = 140 GB
- 405B model: 405 × 2 = 810 GB → needs 10+ A100-80GB

**Training overhead (Adam optimizer):**
Adam optimizer stores 3 copies per parameter: current weights (2 bytes BF16) + momentum (4 bytes FP32) + variance (4 bytes FP32) = 10 bytes per parameter.

```
Training VRAM ≈ 10 bytes × num_parameters
  7B model: 70 GB → needs 2× A100-40GB minimum with ZeRO
  70B model: 700 GB → needs 9+ A100-80GB
```

**Additional VRAM components:**

| Component | Size | Notes |
|-----------|------|-------|
| Model weights | params × bytes | Dominant |
| Optimizer states | 2× params (Adam FP32) | Training only |
| Gradients | 1× params | Training only |
| Activations | Seq_len × d_model × n_layers × batch | Cleared by grad checkpointing |
| KV cache | See formula in file 05 | Inference only |

**Worked example — 70B inference on A100-80GB:**
```
70B × 2 bytes (BF16) = 140 GB → needs 2× A100-80GB minimum
With 4-bit quantization: 70B × 0.5 bytes = 35 GB → fits on 1× A100-80GB
```

---

## Quantization

### Concept

Quantization reduces the numerical precision of model weights (and sometimes activations) to use fewer bits. The trade-off is reduced memory and compute cost vs potential quality degradation.

**Post-Training Quantization (PTQ):** Quantize a pretrained model without additional training. Fast and cheap; some quality loss.

**Quantization-Aware Training (QAT):** Simulate quantization during training so the model learns to compensate. Better quality but requires access to training pipeline.

---

### INT8 — LLM.int8()

**How it works:**
- Most weights are quantized to INT8 (1 byte)
- "Emergent outliers" — a small fraction of activations with very large magnitude that distort quantization — are kept in FP16 and computed separately
- This mixed-precision approach prevents the significant quality loss of naive INT8

**Results:**
- ~2× memory reduction vs FP16
- Minimal quality degradation (< 1% on most benchmarks)
- Some compute overhead from mixed-precision handling
- Library: `bitsandbytes` (`load_in_8bit=True`)

---

### GPTQ — GPU Post-Training Quantization

**How it works:**
- Weight-only quantization (weights to INT4 or INT8, activations remain FP16)
- Layer-by-layer quantization that minimizes the L2 reconstruction error of each layer's output
- Uses the inverse Hessian of the weight matrix (second-order information) to find optimal rounding

**Results:**
- INT4: ~4× memory reduction vs FP16
- Quality close to FP16 for most tasks
- Slightly slower than NF4 for inference
- Library: `auto-gptq`

---

### AWQ — Activation-Aware Weight Quantization

**How it works:**
- Observes that 1% of weight channels (those corresponding to large activation values) contribute disproportionately to reconstruction quality
- Protects those important channels by scaling them before quantization
- Result: better quality than GPTQ at the same bit-width

**Results:**
- Better quality than GPTQ at INT4, especially for instruction following
- Better inference speed than GPTQ (hardware-friendly kernel)
- Library: `autoawq`

---

### NF4 — NormalFloat4 (QLoRA)

**How it works:**
- 4-bit format with bins placed at equal probability intervals of the standard normal distribution N(0,1)
- LLM weights have a near-normal distribution → NF4 bins are optimally placed
- Used exclusively for QLoRA base model storage; combined with FP16/BF16 LoRA adapters

**Not intended for standalone inference** — primarily a training-efficiency format.

---

### Quantization Comparison Table

| Method | Bits | Memory reduction | Quality | Speed | Library | Best for |
|--------|------|-----------------|---------|-------|---------|----------|
| BF16 | 16 | 1× (baseline) | Best | Good | PyTorch | Training, production inference |
| LLM.int8 | 8 | ~2× | Near-lossless | Slightly slower | bitsandbytes | When 4-bit is too lossy |
| GPTQ | 4 | ~4× | Good | Fast (custom kernel) | auto-gptq | Production 4-bit inference |
| AWQ | 4 | ~4× | Better than GPTQ | Fastest | autoawq | Best 4-bit quality+speed |
| NF4 | 4 | ~4× | Good | Medium | bitsandbytes | QLoRA fine-tuning |
| GGUF/Q4_K_M | 4-5 | ~4× | Good | CPU-optimized | llama.cpp | Local/CPU inference |

**Interview Q:** *A 70B model in FP16 — minimum A100-80GB GPUs to run inference?*  
70B × 2 bytes = 140 GB. One A100-80GB has 80 GB → need at least **2 GPUs**. With INT4 quantization (70B × 0.5 = 35 GB) → fits on **1 GPU**.

---

## Parallelism Strategies

### Concept

For models that don't fit on a single GPU (or for faster training), you must distribute computation across multiple GPUs.

---

### Data Parallelism (DDP)

**How it works:**
- Each GPU holds a complete copy of the model
- Different batches of data are processed on different GPUs
- After the backward pass, gradients are averaged across all GPUs (all-reduce communication)
- Each GPU updates its local copy with the averaged gradient

```
GPU 0: Model copy A | Batch 1 → grad_1
GPU 1: Model copy A | Batch 2 → grad_2
GPU 2: Model copy A | Batch 3 → grad_3
                           ↓ All-reduce
All GPUs: grad = (grad_1 + grad_2 + grad_3) / 3
Update: W = W - lr × grad
```

**When to use:** Model fits on a single GPU; want to increase batch size or training speed.

**Communication cost:** One all-reduce per training step, proportional to model size.

---

### Tensor Parallelism (Megatron-LM style)

**How it works:**
- Split individual weight matrices across GPUs along one dimension
- Attention: Q, K, V, O projection matrices split along the head dimension
  - GPU 0: heads 1–16; GPU 1: heads 17–32
- FFN: split the intermediate dimension across GPUs
  - GPU 0: first half of d_ffn columns; GPU 1: second half

```
Linear(d_model, d_ffn):
  GPU 0: first d_ffn/2 columns → output_0
  GPU 1: last d_ffn/2 columns  → output_1
  All-reduce: output = concat(output_0, output_1)
```

**Communication cost:** One all-reduce per layer forward AND backward. High communication — requires NVLink for efficiency (PCIe is too slow).

**When to use:** Single layer too large for one GPU; NVLink interconnect available.

---

### Pipeline Parallelism

**How it works:**
- Split model layers across GPUs: GPU 0 runs layers 1–16, GPU 1 runs layers 17–32
- Each GPU processes its layers, passes activations to the next GPU
- Micro-batching: split the batch into M micro-batches to keep all GPUs busy

```
Layers 1–16: GPU 0
Layers 17–32: GPU 1

Step 1: GPU 0 processes micro-batch 1, sends activations to GPU 1
Step 2: GPU 0 processes micro-batch 2 (while GPU 1 processes micro-batch 1)
...
```

**"Bubble" problem:** At the start and end of a batch, some GPUs are idle waiting for data. The bubble size = (num_GPUs - 1) / (num_micro_batches + num_GPUs - 1). More micro-batches = smaller bubble.

**When to use:** Very deep models; layer-granularity parallelism needed; lower communication bandwidth requirement than tensor parallelism (only activations cross GPU boundaries, not gradients).

---

### ZeRO — Zero Redundancy Optimizer

### Concept

ZeRO (Rajbhandari et al., 2019) eliminates redundant copies of optimizer states, gradients, and parameters across GPUs in data-parallel training. Three stages:

```
Stage 1 — Optimizer State Partitioning:
  Each GPU stores only 1/N of optimizer states (momentum, variance)
  Parameters and gradients: still replicated on all GPUs
  Memory reduction: 4× (optimizer states are typically 2× weights in Adam)

Stage 2 — Gradient Partitioning:
  Each GPU stores only 1/N of gradients during backward pass
  Parameters: still replicated
  Memory reduction: 8× vs DDP

Stage 3 — Parameter Partitioning:
  Each GPU stores only 1/N of parameters
  Parameters are gathered via all-gather as needed during forward/backward
  Memory reduction: 16× or more vs DDP — enables training models far larger than single-GPU memory
```

**ZeRO-Infinity:** Extends ZeRO-3 to offload to CPU RAM and NVMe SSDs — can train trillion-parameter models on limited GPU clusters.

| ZeRO Stage | What's partitioned | Memory reduction | Communication overhead |
|------------|-------------------|-----------------|----------------------|
| 0 (DDP) | Nothing | 1× | 1 all-reduce |
| 1 | Optimizer states | ~4× | 1 all-reduce + scatter |
| 2 | + Gradients | ~8× | Same as 1 |
| 3 | + Parameters | ~16× | Higher (all-gather) |

**DeepSpeed** is the primary library implementing ZeRO.

---

## Flash Attention as Hardware Optimization

### Concept

Flash Attention is primarily a hardware (GPU memory hierarchy) optimization — see [Attention Mechanisms](03-Attention-Mechanisms.md) for the algorithm. Here is the hardware context:

**GPU memory hierarchy:**
```
Registers: ~256 KB, fastest (no latency)
L1 cache:  ~128 KB per SM
SRAM:      ~192 KB per SM on A100, ~20 TB/s bandwidth
HBM:       80 GB on A100, ~2 TB/s bandwidth — 10× slower than SRAM
```

Standard attention writes the n×n attention matrix to HBM (slow), reads it back for softmax (slow), writes softmax output (slow), reads for ×V (slow). Flash Attention keeps all intermediate results in SRAM by tiling — eliminates the HBM round-trips.

**Why this matters at scale:**
- For 128K tokens: attention matrix = 128K × 128K × 2 bytes = 32 GB — impossible to hold in SRAM, Flash Attention never materializes it
- Flash Attention makes long-context models practical, not just mathematically possible

---

## PCIe vs NVLink

### Concept

GPU-to-GPU communication speed determines how well parallelism strategies scale.

| Interconnect | Bandwidth | Latency | Use |
|-------------|-----------|---------|-----|
| PCIe 4.0 ×16 | ~32 GB/s (bidirectional) | Medium | Consumer GPUs, budget clusters |
| NVLink 4.0 | ~900 GB/s (bidirectional) | Low | A100, H100 — production AI clusters |
| NVSwitch | ~3.6 TB/s (all-to-all) | Very low | H100 SXM clusters |

**Practical impact:**
- Tensor parallelism requires all-reduce after every layer: high bandwidth demand. PCIe is the bottleneck — tensor parallelism scales poorly without NVLink.
- Pipeline parallelism only passes activations at layer boundaries: lower bandwidth requirement — viable with PCIe.
- A100 SXM4 (NVLink) vs A100 PCIe: tensor-parallel scaling efficiency drops from ~95% to ~50% at 8 GPUs.

---

## Code

```python
# VRAM estimation utility
def estimate_vram(
    num_params_billions,
    precision="bf16",
    mode="inference",
    kv_cache_tokens=4096,
    n_layers=32,
    n_kv_heads=8,
    d_head=128,
    batch_size=1
):
    """Estimate VRAM requirements in GB."""
    bytes_per_param = {"fp32": 4, "bf16": 2, "fp16": 2, "int8": 1, "int4": 0.5, "nf4": 0.5}
    bpp = bytes_per_param[precision]
    
    weight_gb = num_params_billions * 1e9 * bpp / 1e9
    
    if mode == "training":
        # Adam: weights (bpp) + momentum (4B) + variance (4B) = bpp + 8
        optimizer_factor = (4 + 4) / bpp  # extra FP32 copies
        total = weight_gb * (1 + optimizer_factor)
        return {"weights": weight_gb, "total_approx": total}
    else:
        kv_gb = (n_layers * kv_cache_tokens * 2 * n_kv_heads * d_head * 2 * batch_size) / 1e9
        return {"weights": weight_gb, "kv_cache": kv_gb, "total_approx": weight_gb + kv_gb}

# Examples
print("LLaMA-3 8B inference (BF16, 4K context):")
print(estimate_vram(8, "bf16", "inference"))

print("\nLLaMA-3 70B inference (INT4, 4K context):")
print(estimate_vram(70, "int4", "inference"))

print("\nLLaMA-3 7B training (BF16):")
print(estimate_vram(7, "bf16", "training"))

# BitsAndBytes quantization
from transformers import AutoModelForCausalLM, BitsAndBytesConfig
import torch

config_8bit = BitsAndBytesConfig(load_in_8bit=True)
config_4bit = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True
)

# Load in 8-bit (comment out when running, requires GPU + large model)
# model_8bit = AutoModelForCausalLM.from_pretrained(
#     "meta-llama/Llama-3.2-1B",
#     quantization_config=config_8bit
# )
# print(f"8-bit model memory: {model_8bit.get_memory_footprint() / 1e9:.2f} GB")

# GPU memory profiling
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name()}")
    print(f"Total VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    print(f"Available: {torch.cuda.memory_reserved(0) / 1e9:.2f} GB reserved")
```

---

## Study Notes

**Must-know for interviews:**
- VRAM for weights = params × bytes_per_precision (BF16=2, INT8=1, INT4=0.5)
- Training VRAM ≈ 10× params in bytes (Adam optimizer stores FP32 momentum + variance + weights)
- 70B in FP16 = 140 GB → needs 2× A100-80GB for inference; INT4 = 35 GB → 1 GPU
- Quantization hierarchy: BF16 (best quality) → INT8 (near-lossless) → AWQ INT4 (recommended 4-bit) → NF4 (QLoRA only)
- Data parallelism: replicate model, split batch; Tensor parallelism: split weight matrices; Pipeline: split layers
- ZeRO-3: partition optimizer + gradients + parameters → 16× memory reduction, enables single-node training of very large models
- NVLink is required for efficient tensor parallelism (PCIe is 28× slower than NVLink)

**Quick recall Q&A:**
- *A 13B model in BF16 — how much VRAM for inference?* 13 × 2 = 26 GB → needs 1× A100-40GB or more.
- *What 3 things does Adam store per parameter?* Current weights (BF16), first moment/momentum (FP32), second moment/variance (FP32).
- *What is the key difference between GPTQ and AWQ?* AWQ uses activation statistics to identify and protect important weight channels before quantization — better quality at the same bit-width.
- *What does ZeRO Stage 3 partition?* Optimizer states + gradients + parameters (model weights themselves).
- *Why does tensor parallelism require NVLink?* It requires all-reduce communication after every layer (forward and backward) — PCIe bandwidth is a severe bottleneck at this frequency.
