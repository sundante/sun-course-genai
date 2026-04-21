# 01 — LLM Models

## What You Will Learn

- What large language models are, how they predict tokens, and how sampling works
- Transformer architecture internals: embeddings, positional encoding (RoPE/ALiBi), residuals, FFN
- Attention mechanisms: scaled dot-product, multi-head, Flash Attention, GQA
- Model architecture types: encoder-only (BERT), decoder-only (GPT/LLaMA), encoder-decoder (T5)
- KV caching, paged attention, speculative decoding, and inference optimization
- How LLMs are pretrained and how scaling laws shape model design decisions
- Fine-tuning: SFT, RLHF, DPO, LoRA, QLoRA, and multi-head fine-tuning
- GPU/hardware considerations: VRAM estimation, quantization, parallelism, ZeRO
- Failure modes: catastrophic forgetting, lost in the middle, hallucination, sycophancy
- Production deployment: serving frameworks, latency optimization, context window workarounds
- Interview-ready answers on all LLM topics with 68+ Q&A pairs

## Chapter Map

| # | File | Topic | Difficulty |
|---|------|-------|-----------|
| 1 | [LLM Fundamentals](Notes/01-LLM-Fundamentals.md) | Tokens, sampling parameters, context window, model types | Beginner |
| 2 | [Transformer Architecture](Notes/02-Architecture.md) | Embeddings, positional encoding, Pre-LN, residuals, SwiGLU FFN | Intermediate |
| 3 | [Attention Mechanisms](Notes/03-Attention-Mechanisms.md) | Q/K/V math, multi-head, Flash Attention, GQA, causal masking | Intermediate |
| 4 | [Model Architecture Types](Notes/04-Model-Architecture-Types.md) | Encoder-only, Decoder-only, Encoder-Decoder, MoE, model comparison table | Intermediate |
| 5 | [KV Cache & Inference Optimization](Notes/05-KV-Cache-and-Inference-Optimization.md) | KV cache math, MQA/GQA, paged attention, speculative decoding, continuous batching | Advanced |
| 6 | [Training & Pretraining](Notes/06-Training-and-Pretraining.md) | Data curation, BPE, CLM/MLM objectives, scaling laws, distributed training | Intermediate |
| 7 | [Fine-Tuning](Notes/07-Fine-Tuning.md) | SFT, RLHF, DPO, LoRA math, QLoRA, multi-head fine-tuning | Advanced |
| 8 | [GPU & Hardware](Notes/08-GPU-and-Hardware.md) | VRAM estimation, quantization (INT8/INT4/AWQ/NF4), tensor/pipeline/ZeRO parallelism | Advanced |
| 9 | [Failure Modes & Tricky Issues](Notes/09-Failure-Modes-and-Tricky-Issues.md) | Catastrophic forgetting, lost in the middle, hallucination, sycophancy, repetition | Advanced |
| 10 | [Production Deployment](Notes/10-Production-Deployment.md) | vLLM/TGI, latency budgets, prefix caching, token window workarounds, cost optimization | Advanced |
| 11 | [Prompting Strategies](Notes/04-Prompting-Strategies.md) | Chat templates, CoT mechanics, system prompts, structured output, prompt injection | Intermediate |
| 12 | [Interview Q&A Bank](Notes/12-Interview-QA-Bank.md) | 68+ Q&A pairs tagged Easy/Medium/Hard across all topics | All levels |

## Recommended Learning Paths

### Path A: Beginner → Conceptual Understanding
1. [LLM Fundamentals](Notes/01-LLM-Fundamentals.md) — understand what LLMs are and how they generate text
2. [Transformer Architecture](Notes/02-Architecture.md) — understand the building blocks
3. [Attention Mechanisms](Notes/03-Attention-Mechanisms.md) — understand the core operation
4. [Model Architecture Types](Notes/04-Model-Architecture-Types.md) — understand the landscape
5. [Prompting Strategies](Notes/04-Prompting-Strategies.md) — understand how to interact with models

### Path B: Interview Preparation (Accelerated)
1. [LLM Fundamentals](Notes/01-LLM-Fundamentals.md) + [Transformer Architecture](Notes/02-Architecture.md) in parallel
2. [Attention Mechanisms](Notes/03-Attention-Mechanisms.md) — very common in technical interviews
3. [KV Cache & Inference](Notes/05-KV-Cache-and-Inference-Optimization.md) — increasingly asked in production roles
4. [Fine-Tuning](Notes/07-Fine-Tuning.md) — LoRA math, RLHF vs DPO
5. [GPU & Hardware](Notes/08-GPU-and-Hardware.md) — VRAM estimation questions are common
6. [Interview Q&A Bank](Notes/12-Interview-QA-Bank.md) — drill all 68 questions

### Path C: Production Engineering (Advanced)
1. [KV Cache & Inference Optimization](Notes/05-KV-Cache-and-Inference-Optimization.md)
2. [GPU & Hardware](Notes/08-GPU-and-Hardware.md)
3. [Production Deployment](Notes/10-Production-Deployment.md)
4. [Failure Modes & Tricky Issues](Notes/09-Failure-Modes-and-Tricky-Issues.md)

## Resources

- [Gemma Handbook](../Resources/01-LLM-Models/Gemma-Handbook.pdf) — Google's Gemma open model reference
- [Interview Q&A Bank](Notes/12-Interview-QA-Bank.md) — 68+ Q&A pairs in this module
- [Cross-topic Interview Questions](../Interview-Questions/01-LLM-Models.md)

## Key Cross-References

- KV cache and attention variants → [Attention Mechanisms](Notes/03-Attention-Mechanisms.md) + [KV Cache](Notes/05-KV-Cache-and-Inference-Optimization.md)
- Catastrophic forgetting → [Failure Modes](Notes/09-Failure-Modes-and-Tricky-Issues.md) + [Fine-Tuning](Notes/07-Fine-Tuning.md) (LoRA)
- Token window limits → [Failure Modes](Notes/09-Failure-Modes-and-Tricky-Issues.md) + [Production Deployment](Notes/10-Production-Deployment.md)
- VRAM and parallelism → [GPU & Hardware](Notes/08-GPU-and-Hardware.md)
- RAG as a complement to LLM capabilities → [03-RAGs module](../03-RAGs/INDEX.md)

## Next Topic

[02 — Prompt Engineering](../02-Prompts/INDEX.md)
