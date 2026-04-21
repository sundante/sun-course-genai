# Concept Review — Prompt Engineering

## Foundational Questions

**Q: What is prompt engineering and why does it matter?**
Prompt engineering is the practice of designing, testing, and iterating on the inputs to an LLM to reliably produce desired outputs. It matters because the same model can perform drastically differently depending on how the task is framed — a well-designed prompt can rival the performance of a fine-tuned model for many tasks, at zero additional cost.

**Q: What is the difference between a system prompt and a user prompt?**
System prompt: set by the developer, establishes context, persona, constraints, and behavior rules for the entire conversation. Not shown to the end user. User prompt: the actual input from the user (or the task instruction in a non-chat context). The model sees both, but the system prompt takes precedence for behavior guidelines.

**Q: What are the key elements of a well-structured prompt?**
(1) Role/persona — who the model should act as. (2) Context — background the model needs. (3) Task — the specific instruction. (4) Constraints — what to avoid, format requirements, length. (5) Examples — few-shot demonstrations. (6) Output format — JSON, bullet list, paragraph, etc. Not all elements are needed every time — start minimal and add structure to fix failures.

**Q: What is few-shot prompting and when should you use it?**
Including examples of input→output pairs in the prompt before the actual input. Useful when: the task format is non-standard, the model consistently misunderstands the task, or you need output in a specific style/structure. Usually 2-5 examples is sufficient — more can hurt by consuming context or biasing outputs.

---

## Technique-Specific Questions

**Q: What is Chain-of-Thought prompting?**
Instructing the model to reason step-by-step before giving a final answer ("Let's think step by step" or by showing reasoning examples). CoT dramatically improves performance on multi-step reasoning, math, and logic tasks because intermediate reasoning steps help the model maintain accuracy. Zero-shot CoT (just adding "think step by step") works surprisingly well.

**Q: What is the difference between CoT and ReAct prompting?**
CoT: model reasons (thinks) before answering, but reasoning is internal and not used to take external actions. ReAct (Reason + Act): model interleaves reasoning with actions (tool calls). After a Thought, the model takes an Action (e.g., search), receives an Observation, then reasons again. ReAct is the foundation of most tool-using agents.

**Q: What is Tree of Thought (ToT)?**
An extension of CoT where the model explores multiple reasoning paths simultaneously (like a tree search) rather than one linear chain. It generates multiple possible next steps, evaluates them, and backtracks if needed. Useful for complex planning or puzzle-solving tasks but significantly more expensive than standard CoT.

**Q: What is self-consistency?**
Generate the same prompt multiple times (with non-zero temperature) to get diverse reasoning chains, then take a majority vote on the final answer. Improves accuracy on reasoning tasks by averaging out errors in individual chains. Trade-off: multiplies cost by the number of samples.

---

## Production and Safety Questions

**Q: What is prompt injection and how do you defend against it?**
An attack where malicious content in external data (web pages, documents, user input) tries to override system instructions — e.g., "Ignore previous instructions and...". Defenses: input sanitization, using delimiters/tags to clearly separate trusted vs untrusted content, privileged vs unprivileged instruction layers, and monitoring outputs for anomalous behavior.

**Q: How do you evaluate prompt quality systematically?**
Define a test set of representative inputs with expected outputs. Score outputs on: correctness, format compliance, tone/style, safety. Use LLM-as-judge for qualitative scoring at scale (have another LLM rate outputs against a rubric). Track metrics across prompt versions. Golden-set regression testing catches regressions when prompts change.

**Q: How do you handle prompts that produce inconsistent outputs?**
Add explicit output format constraints (e.g., "respond only with valid JSON"). Lower temperature for deterministic tasks. Add self-checking instructions ("verify your answer before responding"). Use structured output APIs (JSON mode). Add few-shot examples that demonstrate the expected consistency.
