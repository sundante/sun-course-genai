# Interview Q&A — LLM Models

## Foundational Concepts

**Q: What is a Large Language Model?**
A language model trained on massive text corpora to predict the next token. "Large" refers to both parameter count (billions) and training data scale. LLMs learn grammar, facts, reasoning patterns, and world knowledge implicitly through next-token prediction.

**Q: What is a token and how does it relate to cost?**
A token is a chunk of text — roughly 4 characters or ¾ of a word in English. LLMs process and generate text token by token. API pricing is per token (input + output), so longer prompts and responses cost more. Context window limits are also measured in tokens.

**Q: What is a context window?**
The maximum number of tokens an LLM can process in a single forward pass — both the input prompt and the generated output. Beyond this limit, earlier content is not visible to the model. Common sizes: 8K (older GPT-4), 128K (GPT-4o, Claude 3), 1M+ (Gemini 1.5 Pro).

**Q: What is the difference between temperature and top-p?**
Both control output randomness. Temperature scales the probability distribution before sampling — higher = more random, 0 = greedy (always picks the highest probability token). Top-p (nucleus sampling) limits sampling to the smallest set of tokens whose cumulative probability exceeds p. In practice, set one and leave the other at its default.

**Q: What is the difference between open-source and proprietary LLMs?**
Proprietary models (GPT-4, Claude, Gemini) are API-only, offer best-in-class performance, but you have no control over weights, training data, or deployment. Open-source models (Llama 3, Mistral, Gemma) give you full control — fine-tune, self-host, inspect — but require infrastructure and expertise. Best performance-per-dollar often favors open models for specific, well-defined tasks.

---

## Classification Questions

**Q: How are LLM models classified?**
LLMs can be classified across 8 dimensions:
- **Architecture** → decoder-only / encoder-only / encoder-decoder / MoE / SSM / multimodal
- **Training stage** → base / SFT / RLHF / reasoning-optimized
- **Modality** → text / vision / audio / code
- **Scale** → frontier / mid-tier / SLM / edge
- **Access** → proprietary / open-weights / open-source
- **Domain** → general / coding / science / embeddings
- **Generation** → GPT-2 era → instruction era → multimodal era → agentic era
- **Context window** → standard (4K–32K) / extended (128K–200K) / long-context (1M+)

**Q: What are the 7 functional types of LLM models?**

| Model Type | Key Characteristic | Core Use Case |
|---|---|---|
| **Base Models** | Trained on raw, unlabeled data via next-token prediction | Foundation for all other models; lacks instruction-following |
| **Instruction-Tuned** | Fine-tuned (SFT/RLHF) to follow specific user commands | Powering assistants like ChatGPT, Gemini, Claude |
| **Mixture of Experts (MoE)** | Sparse architecture — only "expert" sub-networks activate | Scaling to trillions of parameters with faster inference |
| **Reasoning Models** | Optimized for multi-step thought (Chain-of-Thought) | Complex math, coding, logical problem-solving |
| **Multimodal (MLLM)** | Processes text, images, audio, and video simultaneously | Document parsing, visual Q&A, rich data interpretation |
| **Hybrid Models** | Dynamically switches between fast and deep reasoning paths | Adaptive AI balancing cost and performance on-the-fly |
| **Deep Research Agents** | Autonomous agents that iterate via web browsing and tools | In-depth investigation and structured report generation |

---

## Architecture Questions

**Q: Explain the transformer architecture.**
Transformers process entire sequences in parallel (unlike RNNs which are sequential). Input tokens are converted to embeddings, passed through stacked attention + feed-forward layers, and each layer refines the representation. The key innovation is self-attention: each token can directly attend to every other token, capturing long-range dependencies efficiently.

**Q: What is the attention mechanism?**
Attention computes a weighted sum of values (V) where weights are determined by the similarity between a query (Q) and keys (K): `Attention(Q,K,V) = softmax(QKᵀ / √d_k)V`. This lets the model focus on relevant parts of the context when processing each token. Multi-head attention runs this in parallel with different learned projections.

**Q: What is the difference between decoder-only and encoder-decoder models?**
Decoder-only (GPT, Llama, Claude): processes a single sequence left-to-right, used for generation tasks. Masked self-attention — each token only attends to previous tokens. Encoder-decoder (T5, BART): encoder processes the full input bidirectionally, decoder generates output attending to encoder outputs. Better for translation/summarization; decoder-only has won for general-purpose LLMs at scale.

**Q: Why did transformers replace RNNs/LSTMs?**
RNNs process tokens sequentially — slow to train (can't parallelize) and struggle with very long-range dependencies (vanishing gradients). Transformers process all tokens in parallel and use attention to directly connect any two positions, making them faster to train and better at long-range reasoning.

---

## Training and Fine-Tuning Questions

**Q: What is RLHF and why is it used?**
Reinforcement Learning from Human Feedback. After pre-training (next-token prediction on web data), RLHF trains the model to be helpful, harmless, and honest. Steps: (1) supervised fine-tuning on human-written responses, (2) train a reward model on human preference rankings, (3) use PPO to optimize the LLM to maximize reward. Without RLHF, LLMs complete text patterns rather than follow instructions.

**Q: What is the difference between pre-training and fine-tuning?**
Pre-training: train from scratch on massive unlabeled text (next-token prediction). Produces a base model with broad world knowledge but no instruction-following behavior. Fine-tuning: continue training a pre-trained model on a smaller, task-specific dataset. Much cheaper than pre-training. SFT (supervised fine-tuning) is the most common form.

**Q: What is LoRA / QLoRA?**
Low-Rank Adaptation. Instead of updating all model weights during fine-tuning (expensive), LoRA freezes the original weights and adds small trainable rank-decomposition matrices alongside them. The update ΔW = BA where B and A are low-rank. This reduces trainable parameters by 10,000x with minimal quality loss. QLoRA adds quantization (4-bit weights) to further reduce GPU memory requirements.

---

## Practical Application Questions

**Q: When should you fine-tune vs use RAG vs use prompt engineering?**
Start with prompt engineering — it's free and fast. Add RAG when you need external, up-to-date, or proprietary knowledge at inference time. Fine-tune when you need the model to consistently follow a specific style/format, exhibit domain-specific behavior, or when latency/cost of long prompts is a concern. Fine-tuning does not reliably add factual knowledge — use RAG for that.

**Q: What causes hallucinations and how do you mitigate them?**
LLMs generate plausible-sounding text, not factually correct text — there's no grounding to reality in the base training objective. Mitigations: RAG (ground responses in retrieved documents), asking the model to cite sources, chain-of-thought reasoning, self-consistency sampling, grading/validation steps, and choosing models with better calibration.
