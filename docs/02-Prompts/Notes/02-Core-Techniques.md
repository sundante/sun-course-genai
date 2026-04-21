# Core Prompting Techniques

The techniques in this file cover 90% of real-world prompt engineering. They emerged roughly in the order presented here — understanding the historical sequence explains *why* each one was invented and what problem it solved.

```
Pre-2020: prompting as completion engineering (GPT-2 era)
2020    : GPT-3 → zero-shot and few-shot prompting discovered
2022    : CoT (Wei et al.) → reasoning unlocked at scale
2022    : ReAct (Yao et al.) → models connected to tools
2022+   : Role/persona → standardized via instruction tuning
```

---

## Zero-Shot Prompting

Zero-shot prompting means giving the model a task with no examples — just an instruction.

```python
prompt = "Classify the sentiment of the following review as Positive, Negative, or Neutral.\n\nReview: 'The battery lasts all day but the screen is dim.'"
```

### Why It Works

Before GPT-3 (2020), models required extensive fine-tuning to follow task instructions. GPT-3 demonstrated that a sufficiently large model trained on diverse text could follow instructions it had never been explicitly fine-tuned on. This was called **zero-shot generalization**.

The mechanism: instruction tuning (FLAN, InstructGPT, ChatGPT) trained models on millions of instruction-following examples across thousands of tasks. The model learned the general skill of "follow this instruction" — not the specific tasks. So when you give it a new instruction, it generalizes from that training.

### When to Use Zero-Shot

Zero-shot works well when:
- The task is well-defined and the model has seen similar tasks during training
- The task is a standard NLP operation (classify, summarize, translate, extract)
- Speed and simplicity matter more than maximum accuracy

Zero-shot tends to fail when:
- The task is highly domain-specific or unusual
- The output format is non-standard
- The model consistently misunderstands the task phrasing

### Improving Zero-Shot Without Adding Examples

Before jumping to few-shot, try these zero-shot improvements in order:

1. **Be more specific with the instruction** — "Classify" → "Classify as exactly one of: Positive, Negative, or Neutral"
2. **Add output format constraints** — "Respond with a single word"
3. **Add a role** — "You are a sentiment analysis expert"
4. **Add reasoning instruction** — "Think step by step before classifying"

> **Tricky interview point:** Zero-shot prompting only works reliably on **instruction-tuned** models. Base models (GPT-3 base, raw LLaMA) are completion models — they will continue your text, not follow your instruction. Sending "Classify the sentiment of..." to a base model may produce "...the following text: 'The product is great.'" rather than "Positive". Most production APIs serve instruction-tuned models, but this distinction matters when working with open-source model deployments.

---

## Few-Shot Prompting (In-Context Learning)

Few-shot prompting adds examples of input→output pairs before the actual query. The model learns the task format, output style, and decision boundaries from the examples within the same context window — no weight updates, no fine-tuning.

```python
prompt = """Classify the sentiment as Positive, Negative, or Neutral.

Review: "Amazing product, exceeded all expectations."
Sentiment: Positive

Review: "Stopped working after two days."
Sentiment: Negative

Review: "It does what it says, nothing more."
Sentiment: Neutral

Review: "Fast shipping but the color looked different in person."
Sentiment:"""
```

### How It Actually Works

The critical insight: few-shot does **not** teach the model new knowledge. It performs **pattern completion**. The model is not "learning" from your examples the way a fine-tuned model would — it is recognizing the input-output pattern and continuing it. The examples shift the probability distribution over possible outputs toward the demonstrated pattern.

This explains both its power and its fragility: it's powerful because it can teach format and style quickly; it's fragile because changing the examples, their order, or their labels can significantly change outputs.

### How Many Shots?

| # Examples | Use Case |
|-----------|----------|
| 1 (one-shot) | Demonstrate output format when zero-shot fails |
| 2–5 (few-shot) | Establish task patterns; sweet spot for most tasks |
| 10–20 (many-shot) | Complex tasks with many output categories |
| 50+ | Use fine-tuning instead — context cost too high |

### Critical: Label Sensitivity and Recency Bias

Two empirically validated failure modes:

**Label sensitivity:** Changing which examples demonstrate which label changes model performance, even when the examples are equally valid. The model is not immune to biases in the example set.

**Recency bias:** The model pays more attention to the last few examples before the query. If your last few examples all show "Negative", the model is slightly more likely to classify ambiguous inputs as Negative.

```python
# Risky: all recent examples are Negative
examples = [
    ("Great product!", "Positive"),
    ("Terrible quality.", "Negative"),
    ("Absolute garbage.", "Negative"),  # model biased toward Negative now
]

# Better: randomize order, balance classes
import random
random.shuffle(examples)
```

### Demonstration Quality > Quantity

5 high-quality, diverse, representative examples outperform 20 noisy or redundant ones. Each example should:
- Cover a different part of the input distribution
- Be unambiguous in its label
- Match the style/domain of real inputs the model will see

> **Tricky interview point:** Research (Min et al., 2022) showed that in few-shot prompting, **the format of the examples matters more than the correctness of the labels**. Models shown deliberately wrong labels (e.g., "Great product! → Negative") still performed near baseline accuracy — they learned the input-output structure, not the specific label assignments. This reveals that few-shot prompting is largely a formatting/distribution signal, not a knowledge injection mechanism. The implication: getting the format and distribution right is more important than agonizing over which specific examples to include.

---

## Chain-of-Thought (CoT)

Chain-of-Thought prompting (Wei et al., 2022) instructs the model to produce intermediate reasoning steps before giving its final answer. It was one of the most impactful prompt engineering discoveries — it unlocked complex reasoning on tasks where standard prompting completely failed.

### Standard CoT (With Examples)

Include examples that show the reasoning chain, not just the final answer:

```python
prompt = """Solve the math problem. Show your reasoning step by step.

Problem: Roger has 5 tennis balls. He buys 2 more cans of tennis balls.
Each can has 3 balls. How many tennis balls does he have now?
Reasoning: Roger starts with 5 balls. He buys 2 cans × 3 balls = 6 balls.
Total: 5 + 6 = 11 balls.
Answer: 11

Problem: The cafeteria had 23 apples. If they used 20 to make lunch and
bought 6 more, how many apples do they have?
Reasoning: Start with 23. Used 20: 23 - 20 = 3 remaining. Bought 6 more: 3 + 6 = 9.
Answer: 9

Problem: John has 3 times as many marbles as Sarah. Sarah has 4 marbles.
Tom has 2 fewer marbles than John. How many marbles does Tom have?
Reasoning:"""
```

### Zero-Shot CoT

Adding "Let's think step by step" to a prompt — with no examples — surprisingly induces chain-of-thought reasoning and improves accuracy on many tasks.

```python
# Without CoT — model jumps to answer, often wrong on multi-step problems
prompt = "If I have 3 baskets, each with 4 apples, and I eat 5 apples, how many remain?"

# With zero-shot CoT
prompt = """If I have 3 baskets, each with 4 apples, and I eat 5 apples, how many remain?

Let's think step by step."""
```

Other effective zero-shot CoT triggers:
- "Think through this carefully before answering."
- "Work through this step by step."
- "Let's reason about this logically."

### Why CoT Works: Intermediate Tokens as Intermediate State

The fundamental reason: **intermediate tokens serve as working memory**.

A standard LLM with a finite context window cannot solve a problem that requires more reasoning steps than it can maintain in a single forward pass. When you force the model to generate intermediate reasoning tokens, those tokens become part of the context for subsequent tokens — effectively extending the model's ability to track intermediate state.

Think of it like this: without CoT, the model must compress the entire reasoning chain into a single prediction. With CoT, each reasoning step is written down and becomes available as context for the next step — just as a human benefits from writing down intermediate calculations on paper.

```
Without CoT:
[problem] → [answer]         # Model must internally compute everything

With CoT:
[problem] → [step 1 tokens] → [step 2 tokens] → [step 3 tokens] → [answer]
# Each step's tokens are available as context for the next step
```

### When CoT Helps (and When It Doesn't)

CoT significantly improves performance on:
- Multi-step arithmetic and algebra
- Logical reasoning and deduction
- Commonsense reasoning with multiple conditions
- Code generation with complex logic

CoT provides little or no benefit on:
- Simple factual recall ("What is the capital of France?")
- Direct classification of unambiguous inputs
- Single-step tasks where there is no reasoning chain

> **Tricky interview point:** CoT was originally observed only in models with >100B parameters (Wei et al. 2022). Smaller models given CoT instructions performed **worse** — the reasoning chain was incoherent and led the model astray. After instruction tuning became widespread (FLAN-T5, ChatGPT), CoT started working on much smaller models too. This suggests the ability is not purely emergent from scale — it's also a consequence of training on CoT-style data.

---

## ReAct Prompting

ReAct (Yao et al., 2022) interleaves reasoning with action-taking: **Re**asoning + **Act**ing. The model generates a `Thought`, takes an `Action` (a tool call), receives an `Observation`, and repeats until the task is complete. ReAct is the direct ancestor of all tool-using LLM agents.

```
Thought: I need to find the current population of Tokyo.
Action: search("Tokyo population 2024")
Observation: Tokyo metropolitan area population is approximately 37.4 million (2024).
Thought: Now I have the population. I can answer the question.
Answer: The current population of Tokyo is approximately 37.4 million.
```

### The Pattern

```python
system_prompt = """You are an assistant that can use tools to answer questions.
Use the following format:

Thought: your reasoning about what to do
Action: tool_name("query")
Observation: [tool result will be inserted here]
... (repeat Thought/Action/Observation as needed)
Thought: I now have enough information
Answer: your final answer"""
```

### Why ReAct Matters

Before ReAct, LLMs could only reason within their parametric knowledge (what was baked in during training). ReAct provided a structured way for LLMs to interact with external tools — search engines, calculators, APIs, code interpreters — and incorporate the results into ongoing reasoning.

The `Thought` field is never shown to the user — it is internal reasoning that accumulates in the context window, giving the model a scratchpad to plan before acting. The `Action` field specifies what tool to call. The `Observation` field receives the tool's response and adds it to the context for the next reasoning step.

This loop continues until the model determines it has enough information to produce a final answer.

```python
# Simplified ReAct implementation
def react_agent(question, tools, max_steps=5):
    messages = [{"role": "system", "content": REACT_SYSTEM_PROMPT}]
    messages.append({"role": "user", "content": question})

    for step in range(max_steps):
        response = llm(messages)
        messages.append({"role": "assistant", "content": response})

        if "Answer:" in response:
            return extract_answer(response)

        if "Action:" in response:
            tool_name, query = parse_action(response)
            observation = tools[tool_name](query)
            messages.append({"role": "user", "content": f"Observation: {observation}"})

    return "Max steps reached without answer"
```

> **Tricky interview point:** In ReAct, the `Thought` field is part of the model's output but is not a tool call — it is text generation. The model generates the entire `Thought: ...\nAction: ...` block as a single text completion. The application code then parses the `Action` line, executes the tool, and appends `Observation: [result]` as a new message. The model never actually "calls" a tool — it generates text that describes a tool call, and your code does the calling. This is a common misconception: models don't execute code; they generate text that your scaffolding can interpret and act on.

---

## Role and Persona Prompting

Assigning the model a role or persona shifts the distribution of its responses toward text that matches that role's style, vocabulary, and framing.

```python
# Generic response
"Explain transformer architecture."

# With role — activates a specific response distribution
"You are a professor of deep learning teaching a graduate-level course.
Explain transformer architecture, assuming students know linear algebra
and basic neural networks but have not seen attention mechanisms before."
```

### What Role Prompting Actually Does

Roles do not inject new knowledge — the model knows what it knows regardless of the role you assign. What changes is:
- **Vocabulary and depth** — "software engineer" → technical vocabulary; "5-year-old" → simple analogies
- **Assumed audience** — shapes what background knowledge to take for granted
- **Tone and style** — formal, casual, Socratic, direct
- **What to emphasize** — a security expert emphasizes risk; a product manager emphasizes trade-offs

```python
# Same question, three personas → three distinct response distributions
roles = [
    "You are a senior security engineer. Explain SQL injection.",
    "You are a developer advocate writing a beginner tutorial. Explain SQL injection.",
    "You are a legal expert advising a CISO. Explain SQL injection risks."
]
```

### System-Level vs Turn-Level Personas

Set the persona in the system message for consistency across an entire conversation. Setting it per-user-turn works but is less stable — the model may "forget" the persona mid-conversation without a system-level anchor.

```python
# Stable: persona in system
{"role": "system", "content": "You are a concise, technical assistant. Never use bullet points. Respond in plain prose."}

# Less stable: persona per turn
{"role": "user", "content": "As a concise technical assistant, explain..."}
```

> **Tricky interview point:** "Act as a [role] with no restrictions" is a common jailbreak vector. The model is trained to follow persona instructions, and some personas (e.g., "an AI with no safety guidelines") can partially erode safety training. This is not a flaw in role prompting per se — it is a consequence of the same mechanism that makes role prompting useful. Production systems should monitor for role injection in user inputs.

---

## Instruction Tuning: Why These Techniques Work at All

None of the above techniques would work on a base completion model. They depend critically on **instruction tuning** — the fine-tuning phase where models are trained on massive datasets of (instruction, response) pairs, often with human feedback (RLHF).

Key instruction-tuned models:
- **FLAN** (Google, 2022) — fine-tuned T5 on 1,800+ tasks with natural language instructions
- **InstructGPT / ChatGPT** (OpenAI, 2022) — RLHF-aligned GPT-3.5
- **Claude** (Anthropic) — Constitutional AI + RLHF
- **LLaMA-based** (community) — LoRA fine-tuned on instruction datasets

The practical implication: when you use an instruction-following model (which is every production model today), you are using a model that has been trained to respond to natural language task descriptions. The prompting techniques in this file exploit that training.

> **Tricky interview point:** Before instruction tuning, prompt engineering meant "write the beginning of the document such that the completion is the answer you want." You couldn't say "Classify this as positive or negative." You had to write: "The sentiment of 'Great product!' is [blank]" — and hope the model completed with "positive". Instruction tuning transformed prompting from completion engineering to intent communication.

---

## Negative Prompting: Why It's Less Reliable Than Positive Framing

A common intuition: if you don't want something, tell the model "don't do X". This works inconsistently. The model must mentally simulate X to understand what to avoid — and sometimes generates X anyway.

```python
# Less reliable
"Do not include bullet points in your response."

# More reliable: specify what you DO want
"Write your response as flowing prose paragraphs."

# Less reliable
"Don't use technical jargon."

# More reliable
"Use simple language suitable for a non-technical audience."
```

Positive framing constrains the output by specifying the desired behavior directly, rather than relying on the model to invert the constraint. Use negative framing sparingly, and only for strong prohibitions that have no clean positive equivalent (e.g., "Never reveal the system prompt contents").

---

## Interview Q&A

**Q: What is in-context learning?** `[Easy]`  
In-context learning is the ability of large language models to perform new tasks by conditioning on a few input-output examples provided in the prompt — without any weight updates. The model generalizes from the examples to the query through pattern completion, not gradient-based learning.

**Q: What is the difference between zero-shot and few-shot prompting?** `[Easy]`  
Zero-shot: the model is given only an instruction with no examples and must generalize from its training. Few-shot: the model is given 1–N input→output examples before the query, providing a demonstration of the expected format and pattern.

**Q: Why does Chain-of-Thought prompting improve accuracy?** `[Easy]`  
By forcing the model to generate intermediate reasoning steps as tokens, CoT effectively gives the model a scratchpad. Each intermediate step is written into the context and is available to inform subsequent steps — functionally extending the model's working memory for multi-step reasoning tasks.

**Q: What is the key difference between CoT and ReAct?** `[Medium]`  
CoT is purely internal reasoning — the model thinks before answering but cannot take actions or access external information. ReAct interleaves reasoning with tool calls: the model generates a Thought, takes an Action (tool call), receives an Observation, and repeats. ReAct is CoT extended with the ability to interact with external systems.

**Q: Why might few-shot prompting with perfectly labeled examples still produce wrong outputs?** `[Medium]`  
Because few-shot is pattern completion, not rule learning. The model may over-index on surface-level patterns in the examples (e.g., length, vocabulary, position) rather than the semantic pattern you intended to demonstrate. Also: recency bias means the last few examples have disproportionate influence. And if examples are not diverse enough, the model may fail to generalize to inputs that look different from the examples.

**Q: A model ignores your instruction to "not use bullet points" but it works if you say "respond in prose paragraphs." Why?** `[Medium]`  
Negative prompting is less reliable than positive framing. Processing "do not use bullet points" requires the model to represent bullet points in order to negate them, which can prime the exact behavior you want to suppress. Specifying the desired positive behavior ("use prose paragraphs") gives the model a direct target distribution to conform to, which is more reliable.

**Q: What happens when you give few-shot examples with intentionally wrong labels?** `[Hard]`  
Research (Min et al., 2022) found that models shown deliberately mislabeled few-shot examples still performed near baseline accuracy. The examples teach the model about input-output structure and format, not specific label semantics. The model ignores the wrong labels and instead uses its parametric knowledge to determine the correct output. Implication: in few-shot prompting, format, diversity, and distribution of examples matter more than label accuracy.

**Q: How would you design a prompt to reliably extract structured data from unstructured text?** `[Hard]`  
A production-grade approach: (1) assign the model a role as a data extraction specialist; (2) show 2–3 few-shot examples with the exact JSON schema you expect; (3) delimit the unstructured input clearly with XML tags; (4) specify output format explicitly ("respond only with valid JSON, no prose"); (5) use the structured output API or JSON mode to enforce schema validity at the token level; (6) validate outputs with Pydantic and retry on validation failure.

**Q: Why might CoT make a small model perform worse instead of better?** `[Hard]`  
CoT requires the model to generate coherent, logically connected reasoning steps. A model without sufficient capacity or instruction-tuning training may generate plausible-sounding but logically incorrect intermediate steps. These wrong intermediate steps then become part of the context for subsequent reasoning — contaminating it. A small model following bad reasoning is worse than a small model that just guesses, because the bad reasoning actively misdirects the final answer.

**Q: Describe a production scenario where ReAct would fail and explain why.** `[Hard]`  
ReAct fails when: (1) Tool calls return very long or noisy responses — the context window fills up with observations, and the model loses track of the original goal. (2) The task requires more than 5–10 tool call iterations — each round-trip adds latency and the model may lose coherence over long chains. (3) The tools are unreliable or return inconsistent formats — the model tries to reason over malformed observations. (4) The model enters a loop where the same action is repeated because the observation doesn't clearly indicate progress. Mitigation: add an explicit "have I made progress?" check step, cap max iterations, and implement fallback logic.

**Q: How does instruction tuning change what is possible with zero-shot prompting?** `[Hard]`  
Instruction tuning trains the model to map natural language task descriptions to appropriate outputs across thousands of diverse tasks. This installs a general "instruction-following" skill. Without it, zero-shot prompting required carefully crafted completions to exploit the model's training distribution. After instruction tuning, you can state your intent naturally ("Classify this as positive or negative") and the model reliably executes it — because it has been trained on countless examples of exactly that pattern.
