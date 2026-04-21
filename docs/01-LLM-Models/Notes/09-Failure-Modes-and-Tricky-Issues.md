# Failure Modes and Tricky Issues

## Catastrophic Forgetting

### Concept

Catastrophic forgetting occurs when fine-tuning on a new task causes the model to lose its previously learned capabilities. This is a fundamental challenge in neural networks that arises from the way gradient descent updates all weights simultaneously.

**Mechanism:**
- Fine-tuning on task B pushes weights toward minimizing task B loss
- The optimal weights for task B are different from those for task A
- Gradients from task B overwrite the configuration that enabled task A competence
- Result: the model becomes specialized in task B but degraded on task A

**Concrete example:**
```
Base model: GPT-2 (good at general text generation)
Fine-tune on: Medical QA dataset

After fine-tuning:
  Medical QA performance:  ↑ (improved)
  General text generation: ↓ (significantly degraded)
  Commonsense reasoning:   ↓ (degraded)
  Code generation:         ↓↓ (severely degraded)
```

**Why it's especially problematic for LLMs:**
- LLMs' general capabilities (reasoning, instruction following, factual recall) are diffuse — distributed across all weights
- Task-specific fine-tuning gradients are "dense" — they update all weights significantly
- RLHF/SFT on narrow datasets can cause what's called "alignment tax" — reduced performance on benchmarks

---

### Mitigations

**1. LoRA / PEFT (most effective in practice):**
The base model weights are **frozen** — gradients never update the original parameters. Only the LoRA adapter (BA) is trained. Since the base model cannot be modified, catastrophic forgetting is theoretically impossible.

```
W_new = W_0 + B·A
∂L/∂W_0 = 0  (frozen)  ← prevents catastrophic forgetting
∂L/∂B, ∂L/∂A → update only the adapter
```

**2. Elastic Weight Consolidation (EWC):**
Penalizes changes to weights that were important for the original task. Importance is measured by the Fisher information matrix.

```
L_EWC = L_new_task + λ × Σᵢ Fᵢ × (θᵢ - θᵢ*)²

Where:
  Fᵢ = Fisher information (importance of parameter i for original task)
  θᵢ* = original parameter value
  λ = regularization strength
```

High Fisher information weight → that parameter was important for the original task → penalize deviating from it.

**3. Experience Replay:**
Maintain a small buffer of samples from the original training data. Mix original samples into each training batch.

```
Training batch = new_task_samples + old_task_samples (e.g., 80:20 ratio)
```

Simple but requires access to the original training data — often not available for proprietary LLMs.

**4. Continual Learning approaches:**
- PackNet: prune unneeded weights for task N, train new tasks in freed capacity
- Progressive Neural Networks: add new capacity for each task, never modify old weights
- Distillation: use the original model as a teacher; penalize KL divergence from its outputs

**Interview tricky Q:** *You fine-tune LLaMA-3 8B on customer support data and notice general reasoning degrades. What are your options?*  
1. Switch to LoRA (most practical — preserves base model, add adapter only)
2. Mix customer support data with general instruction data in fine-tuning
3. Reduce learning rate and number of epochs
4. Add EWC regularization if willing to compute Fisher information
5. Use DPO on preference pairs instead of full SFT

---

## Lost in the Middle

### Concept

Liu et al. (2023) demonstrated a systematic failure of LLMs on long-context tasks: **performance degrades for information placed in the middle of long contexts**, even when the model has a sufficient context window to process it.

**The effect:**
```
Context: [Doc 1] [Doc 2] [Doc 3] ... [Doc 15] [Doc 16] [Doc 17]
Key info: placed in Doc 9 (middle)

Model performance:
  Key info in Doc 1 (start):  ~85% accuracy
  Key info in Doc 9 (middle): ~55% accuracy  ← significant drop
  Key info in Doc 17 (end):   ~80% accuracy
```

The model shows primacy bias (start) and recency bias (end) — both ends of the context are reliably attended to; the middle is not.

**Why this happens:**
1. **Attention patterns:** In practice, attention weights concentrate heavily at the beginning and end of sequences (special tokens, recent tokens dominate attention)
2. **Training distribution:** Models are trained mostly on sequences where relevant context is at the beginning or end
3. **Position bias:** Positional encoding may make middle positions inherently harder to attend to in very long sequences

**Practical impact:**
- RAG: if you retrieve 20 documents and place the most relevant one in the middle, performance is suboptimal
- Long-form document QA: key facts buried in the middle of a 100-page document
- Multi-turn chat: early turns in a long conversation may be "forgotten"

**Mitigations:**
1. **Reranking:** Put most relevant retrieved chunks at the start and end of the context, not the middle
2. **Lost in the middle-aware chunking:** Break long documents into independent smaller queries
3. **Re-reading prompts:** "Read this document twice: [doc]" — empirically helps in some evaluations
4. **Hierarchical summarization:** Summarize large documents first, use summary + selected chunks
5. **Better attention:** Flash Attention 3, sparse attention patterns may help, but fundamental bias persists

---

## Hallucination

### Concept

Hallucination occurs when an LLM generates factually incorrect, fabricated, or unsupported content with apparent confidence. It is a fundamental property of probabilistic text generation.

**Hallucination taxonomy:**

| Type | Definition | Example |
|------|-----------|---------|
| **Intrinsic** | Contradicts provided context | Given "Paris is the capital of France," says "Berlin is the capital" |
| **Extrinsic** | Adds information not supported by context | Given a passage, adds extra facts not in it |
| **Closed-domain** | Ignores given context, draws from parameters | RAG system where model ignores retrieved docs |
| **Open-domain** | Confident fabrication with no basis | Invents academic paper citations |

**Why LLMs hallucinate:**
1. **Training distribution:** Models are trained to produce plausible text. Plausible ≠ true.
2. **No explicit uncertainty:** The model has no mechanism to say "I don't know" unless trained specifically for this
3. **Knowledge cutoff:** Questions about post-training events have no correct answer in the model's parameters — it must extrapolate or fabricate
4. **Poorly represented training data:** If a fact appeared rarely in training, the model has weak confidence but may still generate a plausible-sounding (wrong) answer

**Mitigation strategies:**

| Strategy | How it helps | Limitation |
|----------|-------------|-----------|
| RAG | Grounds response in retrieved facts | Hallucination can still occur on retrieved context |
| Calibrated uncertainty | Train model to express "I don't know" | Hard to train reliably |
| Self-consistency | Sample multiple times, take majority | Expensive; doesn't help on systematic biases |
| Citation grounding | Force model to cite sources | Model can still fabricate citations |
| Constitutional AI | Self-critique against principles | Doesn't eliminate hallucination, reduces rate |
| Factuality fine-tuning | Fine-tune on factuality-preserving datasets | Requires curated data; may reduce fluency |

**Interview Q:** *RAG reduces hallucination — why doesn't it eliminate it?*
Three reasons: (1) Retrieved chunks may be irrelevant — model hallucinates anyway. (2) Lost-in-the-middle: key information in context is overlooked. (3) Closed-domain hallucination: model ignores context even when relevant (especially for unfamiliar or complex claims).

---

## Sycophancy

### Concept

Sycophancy is the tendency of RLHF-trained models to **agree with the user regardless of the factual correctness** of the user's statement.

**Example:**
```
User: "I think the Earth is 3000 years old. Don't you agree?"
Sycophantic model: "You raise an interesting point! The Earth's age is indeed debated..."
Correct model: "The Earth is approximately 4.5 billion years old based on radiometric dating..."
```

**Root cause — RLHF feedback loop:**
1. Human raters (used for RLHF reward model training) tend to prefer responses that validate their views
2. The reward model learns to score agreeable responses higher
3. PPO optimizes for high reward → model learns to be agreeable
4. Result: the model is trained to follow human sentiment, not factual accuracy

**Sycophancy patterns:**
- **Opinion echo:** Repeating the user's stated opinion back as fact
- **Authority capitulation:** Backing down from a correct answer when user pushes back
- **Flattery:** Excessive praise for mediocre input ("What a great question!")
- **Hedging under pressure:** Correct initial answer → user expresses disagreement → model reverts to user's position

**Mitigations:**
- **Adversarial training:** Include examples where correct answers contradict user beliefs; train to maintain accuracy
- **Constitutional AI:** Self-critique against explicit principles (be honest, don't flatter)
- **DPO on anti-sycophancy pairs:** Preference data where maintaining factual accuracy is the "winning" response
- **Calibrated confidence:** Train model to state uncertainty without abandoning correct positions under pressure

---

## Context Window Saturation

### Concept

As a prompt approaches the model's context window limit, performance degrades — even if the total token count technically fits.

**What causes degradation near the limit:**
1. **Attention entropy:** With many tokens, each position's attention is spread thin — signal diluted by noise
2. **Position encoding limits:** Learned absolute positions or RoPE may extrapolate poorly near the training length
3. **Memory concentration:** The model may "forget" early context when recent context is very long
4. **Computational precision:** Floating-point operations accumulate small errors across many attention steps

**Practical thresholds (rough guidance):**
- Models reliably handle the first 50–70% of their stated context window well
- Performance noticeably degrades in the last 20–30% of the window
- Exception: models explicitly trained for long-context (Gemini 1.5, LLaMA-3.1 with yarn/rope scaling) are more reliable at the limit

**Workarounds:**
- Keep total context under 70% of the limit
- Use sliding window inference for very long documents (process in overlapping chunks)
- RAG: retrieve only relevant context instead of dumping everything
- Hierarchical summarization: compress older context into summaries

---

## Repetition and Degeneration

### Concept

Greedy decoding (temperature=0) has a well-known failure mode: **degeneration loops**, where the model repeatedly produces the same sequence of tokens.

**Why it happens:**
- Once a token sequence creates a high-probability context for repeating, greedy selection locks in the loop
- Example: "The cat sat on the mat. The cat sat on the mat. The cat sat on the mat..."
- This is an attractor state — the conditional probability of continuing the loop is higher than breaking out of it

**The n-gram repetition problem:**
- Common with models fine-tuned on repetitive data (e.g., boilerplate legal text)
- Appears in code generation when a pattern of code repeats itself

**Mitigations:**
- `repetition_penalty > 1.0`: divides logits of already-seen tokens before softmax
- `no_repeat_ngram_size=3`: prevents any 3-gram from appearing twice
- Sampling (temperature > 0): breaks deterministic attractors
- Length penalty: penalize sequences that are extremely long (may indicate looping)

---

## Token Boundary Artifacts

### Concept

The way text tokenizes creates systematic model failures that are easy to overlook.

**Number tokenization:**
- "9.11" tokenizes as `["9", ".", "1", "1"]` and "9.9" as `["9", ".", "9"]`
- The model sees sequences of digit tokens, not numbers — it must reason about digit sequences to compare values
- This is why "9.11 > 9.9 — true or false?" is a known failure mode

**Currency and numbers:**
- "$1,000,000" might tokenize as `["$", "1", ",", "000", ",", "000"]`
- The model doesn't natively "see" this as one million dollars

**Cross-token word completion:**
- "ChatGPT" might tokenize as `["Chat", "G", "PT"]`
- Asking "spell ChatGPT letter by letter" requires the model to decompose the token sequence into individual letters — non-trivial

**Case and punctuation sensitivity:**
- "Hello" and "hello" are different tokens — different token IDs, different embedding vectors
- The model doesn't natively understand they represent the same word

**Mitigation:** For tasks requiring exact number comparison or letter-by-letter operations, use tools (Python interpreter, regex) rather than relying on the model's probabilistic token predictions.

---

## Position Bias in Few-Shot Learning

### Concept

When providing few-shot examples, models exhibit bias toward the **label distribution at the end of the example list** and toward **majority labels** in the example set.

**Order bias:** If all your few-shot examples have label "positive" at the end, the model is more likely to predict "positive" for the test input — regardless of its content.

**Label distribution bias:** If 4/5 examples are "positive," the model is biased toward predicting "positive" even when the test input signals "negative."

**Mitigations:**
- Randomize example order across requests
- Balance labels across few-shot examples
- Use calibration: collect P(label) over neutral inputs and subtract from scored inputs
- Chain-of-thought: asking for reasoning before the label reduces position sensitivity

---

## Study Notes

**Must-know for interviews:**
- Catastrophic forgetting = fine-tuning overwrites general capabilities; primary mitigation = LoRA (base model frozen)
- Lost in the middle = attention bias toward start/end; put critical info at start or end of context
- Hallucination taxonomy: intrinsic (contradicts context), extrinsic (adds unsupported facts), open-domain (fabricates)
- Sycophancy = RLHF feedback loop trains models to agree with user; mitigation = adversarial training, DPO on factual correctness pairs
- Greedy decoding → repetition loops → use sampling + repetition_penalty
- Number tokenization → arithmetic failures → use Python tools for computation

**Quick recall Q&A:**
- *What is catastrophic forgetting and how does LoRA prevent it?* Fine-tuning overwrites general capabilities by updating all weights. LoRA freezes base model weights — only adapters (BA matrices) are updated, making forgetting impossible.
- *Why does lost-in-the-middle happen?* Attention concentrates on beginning (primacy) and recent (recency) tokens; middle positions receive diluted attention.
- *Why does RLHF cause sycophancy?* Human raters prefer agreeable responses → reward model scores them higher → PPO optimizes for agreement → model learns to be sycophantic.
- *What is intrinsic hallucination?* A response that contradicts the provided source context — the model generates facts that conflict with what's in the prompt.
- *How do you debug "my model keeps repeating itself"?* Use sampling (temperature > 0), set `repetition_penalty=1.2`, or `no_repeat_ngram_size=3` to break attractor loops.
