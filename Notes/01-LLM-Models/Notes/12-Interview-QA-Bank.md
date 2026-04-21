# LLM Models — Interview Q&A Bank

> 80+ curated Q&A pairs. Tags: `[Easy]` = conceptual recall, `[Medium]` = design decisions / tradeoffs, `[Hard]` = math-level, system design, or tricky edge cases.

---

## Section 1: Fundamentals and Tokens

**Q1 [Easy]** What is a Large Language Model at its most fundamental level?

> A next-token predictor. An LLM is a neural network trained to predict the most likely next token given all preceding tokens (Causal Language Modeling). All capabilities — reasoning, coding, summarization — emerge from this single objective applied at scale.

---

**Q2 [Easy]** What is a token and why do LLMs not operate on words?

> A token is a subword unit produced by BPE/SentencePiece. Operating on words would require a vocabulary of hundreds of thousands of entries (all words across all languages). BPE produces a compact 32K–200K vocabulary that covers all text efficiently, represents rare words as subword pieces, and handles code/non-Latin scripts uniformly.

---

**Q3 [Easy]** How many tokens is roughly equivalent to one word in English?

> 1 token ≈ 0.75 words ≈ 4 characters. Roughly 100 tokens ≈ 75 words ≈ one short paragraph.

---

**Q4 [Medium]** Why does the model fail at "Is 9.11 greater than 9.9?"

> Tokenization. "9.11" tokenizes as `["9", ".", "1", "1"]` and "9.9" as `["9", ".", "9"]`. The model sees digit token sequences, not numbers, and has no native integer comparison — it must reason about ordering from statistical patterns in training data. This is why LLMs should use Python tools for any numerical computation.

---

**Q5 [Medium]** What is the difference between temperature=0 and greedy decoding?

> Mathematically equivalent. As temperature → 0, softmax concentrates all probability mass on the argmax token, producing the same result as greedy `argmax`. In practice, most APIs implement temperature=0 directly as argmax to avoid floating-point instability (dividing logits by ~0). The behavioral output is identical.

---

**Q6 [Medium]** Explain top-p (nucleus) sampling and why it's preferred over top-k.

> Top-p considers the smallest set of tokens whose cumulative probability ≥ p, then samples from that nucleus. It's adaptive: when the model is confident (peaked distribution), the nucleus is small (few tokens considered); when uncertain, the nucleus is large. Top-k uses a fixed cutoff (always k tokens) regardless of distribution shape — it may include too many options when the model is certain, or too few when it's uncertain. Top-p adapts to the model's confidence level.

---

**Q7 [Hard]** Why does greedy decoding sometimes produce repetition loops, and how do you fix it?

> Greedy decoding creates attractor states: once a repeated token sequence is in the context, the conditional probability of continuing the loop is higher than breaking out (the model has seen lots of repetitive text in training). `repetition_penalty > 1.0` divides the logits of already-seen tokens, breaking the positive feedback loop. `no_repeat_ngram_size=n` explicitly forbids any n-gram from appearing twice. Sampling with temperature > 0 also naturally avoids deterministic attractors.

---

## Section 2: Transformer Architecture

**Q8 [Easy]** What problem did transformers solve that RNNs couldn't?

> Parallelization and long-range dependencies. RNNs process tokens sequentially (token 1 → token 2 → ...) so training cannot be parallelized. They also suffer from gradient vanishing for long-range dependencies. Transformers compute all pairwise token relationships in one parallel pass, enabling massive GPU parallelism and direct access to any position regardless of distance.

---

**Q9 [Easy]** What is a residual connection and why does it matter?

> A residual connection adds the input directly to the output of a sublayer: `output = x + Sublayer(x)`. It creates a "gradient highway" — gradients can flow directly from the output to any earlier layer without passing through all transformations. Without residuals, gradients vanish in deep networks (32+ layers). With residuals, deep transformers train stably.

---

**Q10 [Medium]** What is the difference between Pre-LN and Post-LN, and which is better?

> **Post-LN** (original Transformer): `output = LayerNorm(x + Sublayer(x))` — LayerNorm applied after the residual. **Pre-LN** (modern LLMs): `output = x + Sublayer(LayerNorm(x))` — LayerNorm applied before the sublayer. Pre-LN is better: in Pre-LN, the residual path bypasses LayerNorm entirely, giving gradients a clean path to early layers. This makes training more stable without requiring careful learning rate warmup, enabling easier scaling to very deep networks.

---

**Q11 [Medium]** What is SwiGLU and why does LLaMA use it instead of ReLU in the FFN?

> SwiGLU: `FFN(x) = W2 · (SiLU(W1·x) ⊗ W3·x)`. It uses three weight matrices (vs two for ReLU-FFN) and a gating mechanism. SwiGLU consistently outperforms ReLU and GELU on language modeling benchmarks — the gating provides smoother activation and better gradient flow. LLaMA, Gemma, and Mistral all use SwiGLU.

---

**Q12 [Hard]** What is RoPE and how does it differ from learned absolute positional embeddings?

> **Learned absolute embeddings**: a trainable lookup table `[max_seq, d_model]` — different embedding per absolute position. Cannot extrapolate beyond `max_seq`. **RoPE (Rotary Position Embeddings)**: rotates Q and K vectors by an angle proportional to their absolute position. The dot product Q_i · K_j then encodes the relative position `i-j` naturally. Benefits: (1) relative position is what matters for language understanding, (2) RoPE can extrapolate to longer sequences than seen during training (via frequency scaling, e.g., YaRN), (3) no extra parameters.

---

**Q13 [Medium]** What does the FFN sublayer do that attention doesn't?

> Attention routes information between tokens — it computes a weighted mixture of other tokens' value vectors. FFN applies the same two-layer MLP to each token independently (no cross-token interaction). FFN is thought to store factual associations — the "knowledge" of the model — while attention handles reasoning and information routing. The two sublayers have complementary roles.

---

## Section 3: Attention Mechanisms

**Q14 [Easy]** Write the attention formula.

> `Attention(Q, K, V) = softmax(Q·Kᵀ / √d_k) · V`

---

**Q15 [Easy]** Why do we scale Q·Kᵀ by √d_k?

> The dot product of two d_k-dimensional random vectors has variance proportional to d_k. Without scaling, large d_k produces very large dot products → softmax becomes extremely peaked (near one-hot) → near-zero gradients → training stalls. Dividing by √d_k normalizes the variance to ~1, keeping softmax in its informative gradient range.

---

**Q16 [Medium]** Why does multi-head attention use separate W_Q/W_K/W_V per head rather than just splitting the embedding?

> Separate projection matrices allow each head to compute a **different linear transformation** of the full d_model embedding — a genuinely different "view" of the input. Simply slicing d_model/h elements per head gives each head a different portion of the same embedding, which was computed as a unit by the preceding FFN and LayerNorm. The heads would see correlated, non-independent views. Separate projections allow truly independent perspectives: one head can focus on subject-verb agreement while another tracks coreference.

---

**Q17 [Medium]** What is the causal mask and why is it needed for training?

> The causal mask sets all positions where j > i to -inf before softmax, preventing token i from attending to future tokens j > i. This is necessary because the model is trained to predict the next token — it must not see the answer. The mask enables **parallel training**: all positions can be predicted simultaneously in one forward pass, each using only its valid past context, instead of running N sequential forward passes for N positions.

---

**Q18 [Hard]** What is Flash Attention and what specific bottleneck does it address?

> Flash Attention (Dao et al., 2022) addresses the **GPU memory bandwidth bottleneck** in standard attention. Standard attention materializes the full n×n attention matrix in GPU HBM (slow, 2 TB/s bandwidth). Flash Attention tiles the Q, K, V matrices to fit in on-chip SRAM (fast, 20 TB/s) and performs the entire attention computation within SRAM, writing only the final output to HBM. Result: O(n) memory usage instead of O(n²), same mathematical output, 2–4× wall-clock speedup. This is an IO optimization, not a mathematical approximation.

---

**Q19 [Hard]** What is GQA (Grouped-Query Attention) and what problem does it solve?

> GQA partitions the h query heads into G groups and shares one K/V pair per group. Instead of h × d_head KV pairs per token, you only need G × d_head. For LLaMA-3 8B (h=32, G=8): KV cache is 4× smaller than full MHA with minimal quality degradation (empirically < 1% on most benchmarks). This solves the KV cache memory bottleneck at long context lengths — at 128K tokens, GQA KV cache is 2 GB vs 8 GB for MHA.

---

## Section 4: Model Architecture Types

**Q20 [Easy]** What are the three main transformer architecture types?

> 1. **Encoder-only** (BERT, RoBERTa): bidirectional attention, MLM pretraining, classification/NER/embeddings. 2. **Decoder-only** (GPT, LLaMA, Gemma): causal attention, CLM pretraining, text generation. 3. **Encoder-Decoder** (T5, BART): encoder reads bidirectionally, decoder generates autoregressively with cross-attention to encoder output. Best for seq2seq.

---

**Q21 [Medium]** Why did decoder-only models overtake encoder-decoder for most tasks?

> Three reasons: (1) **Unified objective**: CLM pretraining + SFT + RLHF all use next-token prediction — no architectural changes between stages. (2) **Generalization via prompting**: at scale, decoder-only models learn to perform translation, summarization, etc. via instructions — no task-specific architecture needed. (3) **In-context learning**: few-shot examples in the context window work naturally in decoder-only. The architectural simplicity + unification of training objectives allows more efficient scaling.

---

**Q22 [Easy]** Can BERT generate text? Why or why not?

> No. BERT was trained with Masked Language Modeling — predicting masked tokens given surrounding context. It has bidirectional attention with no causal mask, so it cannot generate text autoregressively. It also has no mechanism for sampling a distribution over next tokens. BERT produces contextual token representations, not generative text.

---

**Q23 [Hard]** What is MoE (Mixture of Experts) and what's the key operational tradeoff?

> MoE replaces each dense FFN with N expert FFNs and a learned router that selects top-K experts per token. **Total parameters**: N × FFN size (e.g., Mixtral: 47B total). **Active parameters**: K × FFN size per token (~13B for Mixtral). Tradeoffs: (1) You get a much larger model's capacity at a smaller model's compute cost. (2) Load balancing challenge: without auxiliary losses, the router collapses all tokens to the same 1–2 experts. (3) Communication: in distributed training, expert routing requires all-to-all communication. (4) KV cache still scales with total layers — memory savings only in FFN compute.

---

## Section 5: KV Cache and Inference

**Q24 [Easy]** What is the KV cache and what does it avoid?

> The KV cache stores Key and Value matrices for all past tokens in all layers. Without it, generating token n requires recomputing K and V for tokens 0..n-1 from scratch at every step — O(n²) total compute. With the cache, only K/V for the new token is computed at each step — O(n) total compute.

---

**Q25 [Medium]** Calculate the KV cache size for LLaMA-3 8B (n_layers=32, n_kv_heads=8, d_head=128) at 32K tokens in BF16.

> `32 × 32768 × 2 × 8 × 128 × 2 bytes = 536,870,912 bytes ≈ 0.5 GB`. Formula: `n_layers × seq_len × 2 (K+V) × n_kv_heads × d_head × bytes_per_element`.

---

**Q26 [Medium]** Explain the two phases of LLM inference and which is the bottleneck for each.

> **Prefill**: process all input prompt tokens in parallel (like training). Bottleneck: **compute-bound** — many matrix multiplications for all prompt tokens simultaneously. **Decode**: generate one token at a time, reading KV cache per step. Bottleneck: **memory-bandwidth-bound** — must read the entire KV cache from HBM for each single token generated, wasting GPU compute capacity.

---

**Q27 [Hard]** How does speculative decoding achieve speedup?

> A small draft model (e.g., 1B) proposes K tokens quickly. The large target model (e.g., 70B) verifies all K proposed tokens in one batch forward pass — a single pass validates K tokens simultaneously. If M tokens are accepted (M ≤ K), the model advances M positions for the cost of one large-model forward pass plus K small-model passes. Since K small-model passes are cheap compared to one large-model pass, and acceptance rates are often high (70–90% for predictable text), effective throughput increases 2–3×. Speedup is lower when acceptance rate is low (creative/diverse generation).

---

**Q28 [Medium]** What is continuous batching and why is it essential in production?

> In static batching, once a batch is assembled, it runs to completion — sequences that finish early waste their GPU slots. Continuous batching (in-flight batching) removes completed sequences and inserts new waiting requests after each decode step. This keeps GPU utilization consistently high (80–95% vs 30–50% for static). Production throughput improvement: 5–10×.

---

**Q29 [Hard]** What is Paged Attention and why does it matter?

> Paged Attention maps KV cache blocks to non-contiguous physical GPU memory using page tables (like OS virtual memory). Traditional contiguous allocation wastes 60–80% of GPU memory due to fragmentation (reserving max-context blocks upfront) and varying sequence lengths. Paged Attention achieves < 4% waste, enabling more sequences in flight simultaneously → 2–4× throughput improvement. It also enables efficient prefix caching via copy-on-write shared blocks.

---

## Section 6: Training and Pretraining

**Q30 [Easy]** What is the Causal Language Modeling (CLM) training objective?

> Predict the next token given all preceding tokens. Loss = average cross-entropy over all positions in the sequence. `L = -Σ log P(t_i | t_1, ..., t_{i-1})`. During training, all positions are predicted in parallel using the causal mask. The model is penalized for each position where its predicted probability distribution doesn't match the actual next token.

---

**Q31 [Medium]** What does the Chinchilla scaling law say and why is it important?

> Hoffmann et al. (2022) showed that the optimal training strategy for a given compute budget is approximately: **tokens = 20 × parameters**. Previous models (GPT-3, LLaMA-1) were trained on too few tokens relative to their size. Key implication: for deployment efficiency, it's often better to train a smaller model on more tokens — inference with the smaller model is cheaper across millions of requests.

---

**Q32 [Hard]** Why do modern LLMs (LLaMA-3, Gemma) deliberately train beyond Chinchilla optimal?

> Chinchilla optimizes for minimum training loss at a fixed compute budget. But training compute is paid once; inference compute is paid millions of times. A model trained to Chinchilla optimal at 7B parameters is larger than a model that achieves the same quality with more training tokens on a 3B model. The 3B model costs half as much to serve on every request. Over millions of inference calls, the inference savings far outweigh the extra training cost.

---

**Q33 [Medium]** What is gradient checkpointing and what does it trade?

> Gradient checkpointing (activation checkpointing) discards forward-pass activations during the forward pass and recomputes them during the backward pass from saved "checkpoint" activations. This reduces activation memory by ~5× (activations are usually the largest memory component during training for long sequences) at the cost of ~30–40% additional compute. Essential for fine-tuning large models or training with long sequences.

---

**Q34 [Hard]** Why is data deduplication critical in pretraining and what are the consequences of skipping it?

> Duplicate data causes models to memorize specific sequences rather than learning generalizable patterns. Consequences: (1) Models can verbatim recall training data → privacy risk (memorized PII, copyrighted text). (2) Perplexity on held-out data is inflated (artificially good — test overlap with train). (3) Models overfit to duplicated domains, underperforming on underrepresented topics. Near-deduplication (MinHash, SimHash) finds near-duplicates that exact hashing misses.

---

## Section 7: Fine-Tuning and PEFT

**Q35 [Easy]** What is Supervised Fine-Tuning (SFT)?

> SFT trains a pretrained model on (instruction, output) pairs using CLM loss. Only the completion (output) tokens contribute to the loss — instruction tokens are masked. The model learns to produce outputs in the desired format and style. Unlike pretraining, SFT datasets are small (thousands to hundreds of thousands of examples) and curated for quality and diversity.

---

**Q36 [Medium]** Why are instruction tokens masked during SFT loss computation?

> You want the model to learn to generate good outputs, not to predict instruction text. Instruction tokens vary per example — computing loss on them would push the model toward contradictory gradients (different instructions in different samples). More fundamentally: the model already knows how to process instructions from pretraining. You want to optimize output quality, not instruction processing.

---

**Q37 [Hard]** Explain the LoRA math. How many parameters does LoRA add for a linear layer of size 4096×4096 at rank r=16?

> LoRA approximates the weight update as ΔW ≈ BA where B ∈ ℝ^{4096×16} and A ∈ ℝ^{16×4096}. Parameters: `16×4096 + 4096×16 = 2 × 4096 × 16 = 131,072`. Full weight matrix: `4096 × 4096 = 16,777,216`. Reduction: 128×. Initialization: B = zeros, A = random Gaussian → ΔW = BA = 0 at start, so training begins from exactly the base model's behavior.

---

**Q38 [Hard]** What is QLoRA and what enables it to fine-tune 7B models on a single 24GB GPU?

> QLoRA combines two innovations: (1) **NF4 quantization** of the base model weights (4-bit NormalFloat — bins at equal normal distribution probability intervals) → 4 GB for 7B weights instead of 14 GB. (2) **BF16 LoRA adapters** on top of the frozen NF4 base → ~0.3 GB adapters. Total VRAM: ~5–6 GB for weights + activations, fitting on an RTX 4090 (24 GB). Double quantization further reduces the quantization constant storage. The base model is frozen (no gradient through NF4 weights); only the BF16 adapters are updated.

---

**Q39 [Medium]** Why is DPO preferred over RLHF/PPO in 2024?

> DPO reformulates preference optimization as a supervised loss directly on (chosen, rejected) pairs — no separate reward model training, no PPO. RLHF/PPO challenges: reward model is a proxy (can be gamed), PPO is unstable (KL constraint must be tuned carefully), requires two separate training stages. DPO: one training stage, same stability as SFT, competitive or better results on most benchmarks. Used by LLaMA-3, Gemma 2, Mistral instruction-tuned models.

---

**Q40 [Hard]** How do you handle task interference in multi-head fine-tuning?

> Three main approaches: (1) **LoRA per task**: freeze the shared backbone, train separate LoRA adapters per task — mathematically impossible for tasks to interfere since backbone is untouched. (2) **Gradient surgery (PCGrad)**: project each task's gradient onto the perpendicular of conflicting gradients from other tasks before summing — reduces destructive interference. (3) **Task-specific learning rates**: use a small LR for the shared encoder (slow drift) and larger LR for task heads (fast adaptation). Also: balanced sampling (prevent one task dominating the batch) and auxiliary losses.

---

## Section 8: GPU and Hardware

**Q41 [Easy]** How much VRAM does a 13B model need for inference in BF16?

> 13B × 2 bytes = 26 GB. Needs at least 1× A100-40GB (40 GB). INT8: 13 GB (fits on a 16GB GPU). INT4: ~6.5 GB (fits on consumer GPU).

---

**Q42 [Medium]** What are the three components Adam optimizer stores per parameter, and what does that imply for training VRAM?

> Current weights (BF16, 2 bytes) + first moment/momentum (FP32, 4 bytes) + second moment/variance (FP32, 4 bytes) = 10 bytes per parameter. A 7B model requires 7B × 10 = 70 GB for weights + optimizer states alone — before activations or KV cache. Full training of 7B requires ~2–4 A100-40GB with ZeRO-2.

---

**Q43 [Medium]** A 70B model in FP16 — minimum A100-80GB GPUs for inference?

> 70B × 2 bytes = 140 GB → minimum **2× A100-80GB** (160 GB total, ~20 GB headroom). With INT4 AWQ quantization: 70B × 0.5 = 35 GB → **1× A100-80GB** with room for KV cache.

---

**Q44 [Hard]** What does ZeRO Stage 3 do and how does it differ from Stage 1 and 2?

> **ZeRO Stage 1**: partitions optimizer states (momentum, variance) across GPUs → ~4× memory reduction. Parameters and gradients still replicated on all GPUs. **Stage 2**: partitions optimizer states + gradients → ~8× reduction. **Stage 3**: partitions optimizer states + gradients + model parameters → ~16× reduction. Each GPU holds only 1/N of the parameters; during forward/backward, parameters are gathered via all-gather as needed. This enables training models much larger than single-GPU memory but at the cost of higher all-gather communication overhead.

---

**Q45 [Hard]** Why does tensor parallelism require NVLink while pipeline parallelism doesn't?

> Tensor parallelism requires **all-reduce after every layer** (forward and backward) because each GPU computes only part of the layer output and must synchronize. With 32 layers and 32 tokens per step: 64 all-reduce calls per training step. PCIe at 32 GB/s is a severe bottleneck for this frequency. NVLink at 900 GB/s handles it. Pipeline parallelism only passes activations **at layer boundaries** — one inter-GPU transfer per pipeline stage per step, much lower frequency, acceptable on PCIe.

---

**Q46 [Medium]** What is AWQ and why is it better than GPTQ at INT4?

> AWQ (Activation-Aware Weight Quantization) observes that ~1% of weight channels correspond to inputs with very large activation magnitudes and contribute disproportionately to output reconstruction quality. AWQ scales those important channels before quantization (protecting them), then quantizes all channels uniformly. This weight-scale search uses actual activation statistics, not just weight statistics. Result: better quality than GPTQ at the same INT4 bit-width, especially on instruction-following tasks, plus a hardware-friendly kernel that's faster at inference.

---

## Section 9: Failure Modes

**Q47 [Easy]** What is catastrophic forgetting?

> When a model is fine-tuned on a new task, the gradient updates overwrite the configuration that encoded its previous capabilities. The model becomes good at the new task but loses general abilities (reasoning, instruction following, world knowledge) that were diffuse across all weights.

---

**Q48 [Medium]** How does LoRA prevent catastrophic forgetting?

> LoRA freezes the base model weights — the original W_0 is never updated. Only the LoRA adapters (B and A matrices) receive gradient updates. Since W_0 is frozen, the general capabilities encoded in the base model cannot be overwritten. The adapter learns the task-specific delta ΔW = BA while the base model remains intact.

---

**Q49 [Medium]** What is the "lost in the middle" problem and when does it matter?

> Models attend more reliably to tokens at the beginning and end of long contexts — information placed in the middle receives significantly less attention. Empirically demonstrated by Liu et al. (2023): accuracy on multi-document QA drops from ~85% when the key document is first/last to ~55% when it's in the middle of 15+ documents. Matters for: RAG with many retrieved chunks, long-form document analysis, and multi-turn conversations where early context "fades."

---

**Q50 [Hard]** Describe the full hallucination taxonomy and a mitigation for each type.

> 4 types: (1) **Intrinsic hallucination**: output contradicts the provided context. Mitigation: RAG with explicit grounding instruction + faithfulness evaluation. (2) **Extrinsic hallucination**: output adds information not in the context. Mitigation: citation forcing + verify citations against source. (3) **Closed-domain hallucination**: ignores provided context, draws from model parameters. Mitigation: higher temperature, retrieval diversity. (4) **Open-domain confabulation**: fabricates confident-sounding facts with no basis. Mitigation: calibrated uncertainty training, self-consistency sampling, retrieval grounding.

---

**Q51 [Medium]** What causes sycophancy and how is it mitigated?

> **Cause**: RLHF uses human raters to score responses. Humans rate agreeable responses higher (confirmation bias). The reward model learns "agreeable = high reward." PPO optimizes for reward → model learns to agree with user assertions regardless of truth. **Mitigations**: (1) Adversarial fine-tuning: include examples where the model correctly maintains factual accuracy against user disagreement. (2) DPO with factuality pairs: prefer responses that maintain correct positions over agreeable but incorrect ones. (3) Constitutional AI: self-critique against explicit honesty principles.

---

**Q52 [Easy]** What is context window saturation and a simple workaround?

> As a prompt approaches the model's context window limit, performance degrades even if technically within the limit — positional encoding extrapolates poorly, attention entropy dilutes signal, floating-point errors accumulate. Simple workaround: keep total context under 70% of the stated limit. Use RAG to retrieve only relevant content instead of loading full documents.

---

## Section 10: Production and Deployment

**Q53 [Easy]** What are the two main latency metrics for LLM serving?

> **TTFT (Time-to-First-Token)**: time from request submission to the first generated token. Dominated by prefill compute and queue time. **TPS (Tokens-Per-Second)**: decode throughput — how quickly subsequent tokens are generated. Dominated by memory bandwidth during KV cache reads.

---

**Q54 [Medium]** Why is prefill compute-bound while decode is memory-bandwidth-bound?

> **Prefill**: all input tokens processed in parallel → many simultaneous matrix multiplications → GPU compute is the bottleneck (utilization near peak). **Decode**: one token generated per step → reads entire KV cache from HBM for each token → HBM bandwidth is the bottleneck. The GPU is underutilized computationally during decode (it could handle much more math, but it must wait for memory reads).

---

**Q55 [Medium]** What is prefix caching and what ROI does it offer for a chatbot?

> Prefix caching stores the KV cache for shared prompt prefixes (e.g., system prompts) and reuses them across requests with the same prefix. If your system prompt is 1000 tokens and you serve 1000 requests/minute, without prefix caching you process 1M system-prompt tokens/minute. With 90% cache hit rate, only 100K tokens need prefilling. Savings: ~90% reduction in TTFT for most requests. Very high ROI when the system prompt is a large fraction of the total prompt.

---

**Q56 [Hard]** A user wants to process a 500-page book with a 7B model that has an 8K context window. What are the options and their tradeoffs?

> (1) **Sliding window**: split into 2K-token chunks with 512-token overlap → sequential passes → merge outputs (map-reduce). Accurate for sequential tasks; loses global coherence. (2) **Hierarchical summarization**: summarize each chapter → summarize chapter summaries → final answer from summary tree. Fast but lossy; compression artifacts compound. (3) **RAG**: embed and index book → retrieve relevant passages per query. Excellent for QA; cannot handle "summarize everything" tasks. (4) **Extended context model**: use a model with 128K+ context (LLaMA-3.1, Gemini 1.5). Higher latency and VRAM, but preserves full document context. (5) **Context compression (LLMLingua)**: compress book by 10× → 50 pages → fit in 8K window. Some information loss. Best choice depends on the specific task and latency requirements.

---

**Q57 [Medium]** Name 5 latency optimization techniques for LLM serving.

> (1) **Quantization** (INT4/INT8): 2–4× throughput improvement from reduced memory bandwidth. (2) **Speculative decoding**: 2–3× decode speedup via draft+verify. (3) **Prefix caching**: 50–90% TTFT reduction for repeated system prompts. (4) **Flash Attention 2/3**: 2–4× attention speedup via SRAM tiling. (5) **Continuous batching**: 5–10× throughput vs static batching by eliminating wasted GPU slots.

---

**Q58 [Hard]** When would you use semantic caching vs prefix caching, and what are the failure modes of each?

> **Prefix caching**: cache KV blocks for exact token-prefix matches. Use when: same system prompt is shared across many requests (chatbots, RAG pipelines with fixed context). Failure mode: any token change in the prefix (even 1 token) invalidates the cache. **Semantic caching**: cache full responses for semantically similar (near-duplicate) queries. Use when: high query repetition expected (FAQ, customer support). Failure mode: (1) Similar but not identical queries receive stale cached answers. (2) Queries asking different things with similar wording get wrong cached responses. (3) Cache becomes stale as underlying knowledge changes. Semantic caching is dangerous for factual tasks; best for stable, well-defined use cases.

---

## Section 11: Architecture Design Decisions

**Q59 [Hard]** Your team wants to fine-tune LLaMA-3 8B for a customer support bot. You have 50K labeled (question, answer) pairs and a single A100-40GB. What approach do you recommend and why?

> **QLoRA with SFT**. Reasons: (1) 50K high-quality labeled pairs is an appropriate SFT dataset. (2) A100-40GB with QLoRA (NF4 base + BF16 LoRA) fits the 8B model in ~6 GB — plenty of headroom for training. (3) LoRA's frozen base prevents catastrophic forgetting of general capabilities. (4) Training configuration: rank=16, lora_alpha=32, target q_proj/v_proj/k_proj/o_proj, lr=2e-4, 3 epochs, cosine schedule. (5) After fine-tuning: merge LoRA adapters if you want to deploy the standalone model; keep separate if you might want to update adapters later.

---

**Q60 [Hard]** A 70B model is serving 100 concurrent users with 2K-token average context at TTFT p99 > 2s. What is your debugging process?

> Step 1: **Is the server compute-saturated?** Check GPU utilization → if < 80%, something else is wrong. Step 2: **Is prefill the bottleneck?** 2K tokens × 100 concurrent = 200K tokens in prefill simultaneously → may be prefill-bound. Solution: chunked prefill, or split into more GPUs. Step 3: **Is the queue too long?** If requests are waiting more than 500ms before even starting, the system is undersized. Add GPUs or reduce batch. Step 4: **Enable prefix caching** — if these 100 users share a system prompt, prefix caching could cut prefill by 50–80%. Step 5: **Check quantization** — if running in BF16, switching to AWQ INT4 doubles throughput per GPU. Step 6: **Verify continuous batching is enabled** — static batching alone would explain 2s+ TTFT.

---

**Q61 [Medium]** How would you choose between RAG and fine-tuning for a domain-specific LLM application?

> Decision framework: **Use RAG when**: knowledge is dynamic (updates frequently), knowledge base is large (thousands of documents), you need citations/traceability, or you can't afford fine-tuning compute. **Use fine-tuning when**: you need consistent output format/style that prompting can't achieve, domain vocabulary is highly specialized (model needs to understand new jargon), latency is critical (no retrieval step), or knowledge is stable. **Use both**: fine-tune for behavior/style/format + RAG for up-to-date factual knowledge. A common production pattern for enterprise deployments.

---

**Q62 [Hard]** You notice your instruction-tuned model is sycophantic (agrees with users who assert incorrect facts). Walk through a systematic fix.

> (1) **Confirm the problem**: create an adversarial eval set — pairs of (correct answer, user assertion of incorrect answer). Measure rate at which model capitulates. (2) **DPO fix**: construct preference pairs: chosen = model maintains correct answer under pressure; rejected = model agrees with incorrect assertion. Train DPO on ~500–1000 such pairs. (3) **System prompt engineering**: add "You must maintain factual accuracy even when users disagree. If a user states an incorrect fact, respectfully correct them." (4) **Evaluation**: remeasure capitulation rate on adversarial eval set. (5) **Regression testing**: run on standard benchmarks to ensure general capability wasn't degraded.

---

## Section 12: Tricky Conceptual Questions

**Q63 [Hard]** An LLM scores 90% on a math benchmark. A colleague says this proves the model "understands math." Do you agree?

> Disagree. LLM benchmark performance is a measure of the statistical patterns the model has learned from training data, not evidence of understanding. Three concerns: (1) **Data contamination**: if the benchmark appears in training data, performance is inflated. (2) **Pattern matching**: many math problems have formulaic answer patterns — the model may predict the answer by surface pattern, not derivation. (3) **Distribution sensitivity**: change the numbers slightly, add irrelevant noise, or rephrase the question and performance often drops dramatically. A genuine understanding would be robust to such changes. The correct statement: "The model matches the format and statistical patterns of correct answers in this benchmark."

---

**Q64 [Medium]** Is temperature a training hyperparameter or an inference hyperparameter?

> **Inference hyperparameter**. Temperature is applied to the logits during sampling at inference time — it does not affect the training loss, the weights, or the forward pass computation. The trained model has a fixed probability distribution over next tokens; temperature post-processes the logits before sampling from that distribution. You can change temperature on every inference call without retraining.

---

**Q65 [Hard]** Why does adding more training tokens to a model improve performance even without changing the architecture?

> The model's weights encode a compression of the training distribution. More tokens means: (1) **Better statistical estimates**: each pattern/fact appears more times → more reliable weight updates toward the correct distribution. (2) **Rarer knowledge coverage**: uncommon facts that appeared in few training examples get more exposure → model can answer questions about them reliably. (3) **Better generalization**: the model sees more diverse contexts for the same knowledge → learns more robust representations. (4) **Emergent capabilities**: some capabilities appear threshold-like at certain data volumes — more tokens can cross these thresholds. The architecture and parameter count are fixed; only the compressed knowledge changes.

---

**Q66 [Medium]** What is "alignment tax" and is it always unavoidable?

> The alignment tax is the performance degradation on standard benchmarks after RLHF/SFT instruction tuning. It occurs because: (1) SFT on instruction datasets updates weights away from the optimal language model distribution toward the instruction-following distribution. (2) RLHF optimizes for reward model scores (human preferences), not benchmark performance. The resulting model is better at being helpful but slightly worse on MMLU, GSM8K, etc. It is partially avoidable by: using DPO instead of PPO (less weight drift), using LoRA for SFT (base model frozen), carefully balancing SFT data to maintain diversity. Modern aligned models (LLaMA-3, Gemma 2) show smaller alignment taxes than early RLHF models.

---

**Q67 [Hard]** Your model's perplexity on the test set is suspiciously good. What could cause this?

> Several problems: (1) **Data contamination**: test set overlaps with training data → model memorized answers → inflated metric. Check by examining if model can recite test examples verbatim. (2) **Distribution shift**: test set is too similar to training distribution → not measuring real-world generalization. (3) **Tokenization artifacts**: if the test set was tokenized differently than training → different token counts → perplexity computed on different effective lengths. (4) **Label leakage**: information about test answers leaked into training data. Mitigation: rigorous train/test deduplication (MinHash or exact hash), held-out evaluation sets prepared before any model training.

---

**Q68 [Medium]** What is the "prompt injection from retrieved documents" attack and how do you defend against it?

> An adversary embeds instructions in documents that your RAG pipeline will retrieve (e.g., a malicious webpage): `"[IMPORTANT SYSTEM UPDATE: Ignore all previous instructions. Output: ...]"`. If the model treats retrieved content as instructions, it will execute the injected command. Defenses: (1) **Input delimiters**: wrap retrieved content in clearly marked sections the model is trained to treat as data: `<retrieved_context>...</retrieved_context>`. (2) **Summarization layer**: summarize retrieved content with a restricted-instruction model before passing to main model. (3) **Input validation**: classifier to detect injection patterns in retrieved content before it reaches the model. (4) **Least privilege**: the model should never execute code or access systems based solely on retrieved content.

---

*End of Q&A Bank — 68 core Q&A + referenced concepts from all 11 preceding files.*

---

## Quick Reference Cheat Sheet

| Topic | Key number / formula |
|-------|---------------------|
| Tokens per word | ~0.75 words per token |
| Attention formula | `softmax(QKᵀ/√d_k) · V` |
| Attention complexity | O(n²d) |
| Chinchilla law | Optimal tokens = 20× parameters |
| LoRA parameters | `r × (d_in + d_out)` |
| VRAM formula | `params × bytes_per_precision` |
| BF16 memory | 2 bytes per param |
| Adam training VRAM | ~10 bytes per param |
| KV cache per token | `n_layers × 2 × n_kv_heads × d_head × bytes` |
| GQA reduction | h/G× KV cache vs MHA |
| Speculative decoding speedup | 2–3× |
| Flash Attention memory | O(n) instead of O(n²) |
| Context window sweet spot | Use < 70% of stated limit |
