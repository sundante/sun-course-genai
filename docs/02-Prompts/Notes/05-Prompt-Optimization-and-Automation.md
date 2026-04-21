# Prompt Optimization and Automation

Manual prompt engineering has a fundamental problem: it does not scale. Expert prompt engineers are scarce, prompt quality depends heavily on individual intuition, and the search space of possible prompts is effectively infinite. A prompt that achieves 87% accuracy could potentially achieve 94% with better wording — but finding that wording through manual iteration is slow, expensive, and non-reproducible.

The field response: **automate the search over prompt space**. This file covers the techniques, frameworks, and mental models that emerged from 2022–2025 to automate what was previously artisanal.

```
2022: Manual prompt engineering is the norm
2023: APE, OPRO — LLMs propose and evaluate prompt candidates
2023: DSPy — paradigm shift from writing prompts to writing programs
2024: LLM-as-Judge matures as an evaluation standard
2025: Reasoning models change what prompts need to do
```

---

## The Scaling Problem

Consider a production system with 20 different prompts (classification, extraction, summarization, routing, etc.). Each prompt:
- Was written by one engineer based on intuition
- Has not been systematically evaluated against an adversarial test set
- Will silently degrade when the model is updated
- May perform significantly better with different wording

Manual optimization of 20 prompts is a full-time job. Optimizing them continuously as models update is impossible at human scale. This is the problem that automated prompt optimization solves.

The three levers for automated optimization:
1. **Generate** diverse candidate prompts
2. **Evaluate** each candidate against a metric
3. **Select or improve** based on evaluation results

---

## Automatic Prompt Engineer (APE)

Automatic Prompt Engineer (Zhou et al., 2023) was an early demonstration that LLMs can be used to generate and evaluate prompt candidates — treating prompt optimization as a program synthesis problem.

### How APE Works

```
Phase 1 — Instruction Induction:
  Given a set of (input, output) demonstration pairs, ask an LLM to
  infer what instruction would produce those outputs.

Phase 2 — Scoring:
  Run each candidate instruction on a held-out evaluation set.
  Score each candidate by accuracy or the target metric.

Phase 3 — Selection:
  Pick the highest-scoring candidate.
  Optionally, use it as a seed for a second round.
```

```python
def ape_generate_candidates(demonstrations: list, n_candidates: int = 10) -> list:
    """Ask LLM to infer the instruction from input-output pairs."""
    demo_text = "\n".join([f"Input: {d['input']}\nOutput: {d['output']}" for d in demonstrations])

    prompt = f"""Here are some input-output pairs that follow a specific instruction.
Infer {n_candidates} different possible instructions that would produce these outputs.

{demo_text}

Possible instructions (one per line):"""

    candidates_text = llm(prompt)
    return candidates_text.strip().split("\n")

def ape_select_best(candidates: list, eval_set: list) -> str:
    """Evaluate candidates and return the best one."""
    scores = {}
    for candidate in candidates:
        results = evaluate_prompt(candidate, eval_set)
        scores[candidate] = results["accuracy"]

    return max(scores, key=scores.get)
```

### Limitations of APE

- The LLM generating candidates is biased toward prompts that are easy for *it* to follow
- Candidate quality is bounded by what the LLM can imagine
- Does not iteratively improve — it's generate-once, evaluate, select
- Overfits to small eval sets

> **Tricky interview point:** APE selects the best prompt from a generated set — but "best on the eval set" is not the same as "best on production inputs." If your eval set is small or unrepresentative, APE will select a prompt that is overfit to the eval set distribution. Always validate APE-selected prompts on a held-out test set that was not used in the optimization loop.

---

## OPRO: Optimization by Prompting

OPRO (Yang et al., 2023, Google DeepMind) treats prompt optimization as a meta-learning problem. The optimizer LLM reads a history of (prompt, score) pairs and uses that history to propose an improved prompt. This is iterative, not one-shot.

### The OPRO Meta-Prompt

```
You are optimizing a text instruction for a task. 
Below is the history of instructions tried so far, with their scores:

Instruction: "Classify the sentiment."
Score: 0.71

Instruction: "Determine if the following review is Positive, Negative, or Neutral."
Score: 0.84

Instruction: "You are a sentiment analysis expert. Classify the customer review as 
Positive, Negative, or Neutral. Respond with a single word."
Score: 0.89

Based on this history, propose a new instruction that might achieve a higher score:
```

The optimizer LLM reads the trajectory and uses it to propose increasingly better prompts — much like a gradient descent optimizer reads the loss history to update weights, but using language instead of calculus.

```python
def opro_optimize(task_description: str, eval_set: list, n_iterations: int = 10) -> str:
    history = []

    # Initialize with a simple prompt
    current_prompt = f"Complete this task: {task_description}"
    score = evaluate_prompt(current_prompt, eval_set)["accuracy"]
    history.append({"prompt": current_prompt, "score": score})

    for iteration in range(n_iterations):
        # Build meta-prompt from history
        history_text = "\n\n".join([
            f'Instruction: "{h["prompt"]}"\nScore: {h["score"]:.3f}'
            for h in sorted(history, key=lambda x: x["score"])
        ])

        meta_prompt = f"""You are optimizing an instruction for this task: {task_description}

History of instructions and their accuracy scores:
{history_text}

Based on this history, propose a new instruction that might achieve a higher score.
Output only the instruction text, nothing else:"""

        new_prompt = llm(meta_prompt).strip()
        new_score = evaluate_prompt(new_prompt, eval_set)["accuracy"]
        history.append({"prompt": new_prompt, "score": new_score})

        print(f"Iteration {iteration + 1}: {new_score:.3f} — {new_prompt[:80]}...")

    # Return best prompt found
    return max(history, key=lambda x: x["score"])["prompt"]
```

### OPRO Convergence Behavior

OPRO tends to converge within 5–20 iterations. The trajectory often resembles a hill-climbing search: rapid early improvement, diminishing gains, occasional backtracking, convergence to a local optimum.

> **Tricky interview point:** OPRO can overfit to the eval set used during optimization. The optimizer LLM learns what *pattern* of prompt correlates with high scores on that specific eval set — if the eval set is small, it finds prompts that happen to work well on those N examples, not prompts that generalize. Use a separate validation set to check for eval set overfitting. Budget at least 100 eval examples for OPRO to work reliably.

---

## DSPy: From Prompts to Programs

DSPy (Khattab et al., 2023, Stanford) is the most significant paradigm shift in prompt engineering since CoT. Instead of writing prompts, you write **programs** using LM calls as primitives. DSPy then **compiles** those programs into optimized prompts automatically.

### The Core Insight

In traditional prompt engineering:
```
You write the prompt → model executes → you evaluate → you edit the prompt
```

In DSPy:
```
You write the program logic → DSPy generates and optimizes the prompt
```

The prompt is an implementation detail, not something you write by hand.

### DSPy Program Example

```python
import dspy

# Configure the LM
lm = dspy.LM("anthropic/claude-sonnet-4-6")
dspy.configure(lm=lm)

# Define a DSPy module — the LOGIC, not the prompt
class SentimentAnalyzer(dspy.Module):
    def __init__(self):
        # Declare the signature: what goes in, what comes out
        self.classify = dspy.Predict("review -> sentiment")

    def forward(self, review: str) -> str:
        return self.classify(review=review).sentiment

# Multi-hop RAG example
class RAGAnswerer(dspy.Module):
    def __init__(self, num_passages=3):
        self.retrieve = dspy.Retrieve(k=num_passages)
        self.generate = dspy.ChainOfThought("context, question -> answer")

    def forward(self, question: str) -> str:
        context = self.retrieve(question).passages
        return self.generate(context=context, question=question).answer
```

### DSPy Compilation (Prompt Optimization)

The compiler optimizes the program by finding the best prompt (and few-shot examples) for each module:

```python
# Define a metric
def accuracy_metric(example, prediction, trace=None):
    return example.sentiment == prediction.sentiment

# Create a teleprompter (optimizer)
from dspy.teleprompt import BootstrapFewShot

optimizer = BootstrapFewShot(
    metric=accuracy_metric,
    max_bootstrapped_demos=4,   # Max few-shot examples to inject
    max_labeled_demos=16        # Training data to bootstrap from
)

# Compile: DSPy searches for the best prompt/examples
compiled_analyzer = optimizer.compile(
    SentimentAnalyzer(),
    trainset=train_examples
)

# The compiled module now has optimized prompts baked in
print(compiled_analyzer.classify.demos)   # Auto-selected few-shot examples
```

### Key DSPy Modules

| Module | Equivalent Manual Approach |
|--------|--------------------------|
| `dspy.Predict` | Direct zero-shot or few-shot |
| `dspy.ChainOfThought` | Chain-of-thought prompting |
| `dspy.ReAct` | ReAct with tools |
| `dspy.Retrieve` | RAG retrieval step |
| `dspy.ProgramOfThought` | Code-based reasoning |

### DSPy Optimizers

| Optimizer | Strategy |
|-----------|----------|
| `BootstrapFewShot` | Label training data, bootstrap examples |
| `MIPRO` | Bayesian optimization over prompt space |
| `BootstrapFineTune` | Uses bootstrapped demos to fine-tune the model |

### When to Use DSPy vs Manual Prompting

| Situation | Use DSPy? |
|-----------|----------|
| Complex multi-step pipeline with many LM calls | Yes |
| You have a metric and labeled training data | Yes |
| Rapid one-off prompt for a simple task | No |
| You need full control over the exact prompt text | No |
| The pipeline changes frequently | No — DSPy recompilation is expensive |
| Production system with stability requirements | Maybe — test thoroughly |

> **Tricky interview point:** DSPy requires a **metric function** — a programmatic way to evaluate whether an output is good. Writing a good metric is often harder than writing a good prompt. If your metric is wrong (penalizes good outputs, rewards bad ones), the compiler will optimize toward bad behavior. The quality of DSPy outputs is fundamentally bounded by the quality of your metric. "I can't write a metric" is a signal that the task itself is underspecified.

---

## LLM-as-Judge

LLM-as-Judge is the practice of using a strong language model to evaluate the outputs of another (or the same) model. It enables scalable, automated evaluation for tasks where "correct" is not binary — summarization, writing quality, reasoning coherence, instruction-following.

### Evaluation Modes

**Criteria-based (absolute):** Score a single output against a rubric.

```python
JUDGE_CRITERIA_PROMPT = """Evaluate this response on a 1-5 scale for each criterion.

Task: {task}
Response: {response}

Criteria:
- Accuracy (1-5): Does it correctly answer the task?
- Completeness (1-5): Does it cover all key aspects?  
- Conciseness (1-5): Is it appropriately brief?
- Format (1-5): Does it follow any format requirements?

Output JSON only: {{"accuracy": N, "completeness": N, "conciseness": N, "format": N}}"""
```

**Pairwise comparison:** Given two responses, choose the better one.

```python
JUDGE_PAIRWISE_PROMPT = """You will be shown two responses to the same task. 
Choose which is better overall.

Task: {task}
Response A: {response_a}
Response B: {response_b}

Which response is better? Answer with just "A" or "B", then explain why in one sentence."""
```

**Reference-based:** Compare against a gold standard answer.

```python
JUDGE_REFERENCE_PROMPT = """Compare this response to the reference answer.
Score 1-5: how closely does the response match the reference in accuracy and coverage?

Reference: {reference}
Response to evaluate: {response}

Score (1-5) and brief reasoning:"""
```

### Known Biases and Mitigations

| Bias | Evidence | Mitigation |
|------|----------|-----------|
| **Position bias** | Judge prefers Response A ~60% of the time | Swap A/B and average scores |
| **Verbosity bias** | Prefers longer, more detailed responses | Rubric must include conciseness; penalize unnecessary length |
| **Self-preference** | GPT-4 rates GPT-4 outputs higher | Use a different model as judge; use multiple judges |
| **Sycophancy** | Agrees when told "the first answer is better" | Blind evaluation; no hints about preference |
| **Format bias** | Prefers well-formatted (Markdown) responses regardless of content | Use plain text for both candidates |

### Calibration

LLM judges must be calibrated against human labels periodically. An uncalibrated judge may have systematic offset (always scores 0.5 points too high) or poor discrimination (scores everything between 3 and 4, regardless of quality).

```python
def calibrate_judge(human_labels: list, judge_labels: list) -> dict:
    """Compute calibration metrics."""
    import numpy as np
    from scipy.stats import pearsonr, spearmanr

    human = np.array([h["score"] for h in human_labels])
    judge = np.array([j["score"] for j in judge_labels])

    return {
        "pearson_r": pearsonr(human, judge)[0],
        "spearman_rho": spearmanr(human, judge)[0],
        "mean_offset": np.mean(judge - human),
        "std_error": np.std(judge - human),
    }
```

> **Tricky interview point:** LLM-as-Judge is most reliable for **relative** comparisons (A is better than B) and least reliable for **absolute** scores (this response is a 4.2/5.0). Humans and LLM judges agree on pairwise comparisons ~80% of the time (comparable to human-human agreement), but absolute scores have low inter-rater reliability. Use pairwise evaluation when possible; use absolute scores only for coarse binning (acceptable vs not acceptable).

---

## Reasoning Models and the New Prompting Paradigm

OpenAI o1 (2024), o3, Claude 3.7 Sonnet with extended thinking, and DeepSeek R1 introduced a new class of model: **reasoning models** that perform internal chain-of-thought before generating an output. This changes what prompts need to do.

### What Changes

| Traditional Models (GPT-4, Claude 3.5) | Reasoning Models (o1, R1, Claude 3.7 Extended) |
|----------------------------------------|------------------------------------------------|
| Need "think step by step" to reason | Reason internally by default |
| Benefit from CoT few-shot examples | CoT examples often unnecessary or harmful |
| Instruction complexity matters greatly | Can handle complex instructions natively |
| Benefit from explicit decomposition | Self-decompose the task |
| Temperature controls output variation | Extended thinking "budget" controls reasoning depth |

### What Still Matters

Reasoning models don't eliminate the need for prompt engineering — they shift what matters:

```python
# For reasoning models: focus on these
prompt = """
# Task
Extract all action items from this meeting transcript.

# Output Format
JSON array: [{"action": "...", "owner": "...", "deadline": "..."}]
Include only items with explicit owners. Omit general discussion.

# Input
{transcript}
"""

# What to stop worrying about for reasoning models:
# - "Think step by step" (they do this internally)
# - Detailed reasoning examples (they generate their own)
# - Extensive CoT demonstrations (often counterproductive)
```

**What still matters with reasoning models:**
- **Task framing** — clear description of what success looks like
- **Output format** — explicit schema, still needs to be specified
- **Constraints and scope** — what to include/exclude
- **Context quality** — garbage in, garbage out still applies
- **Evaluation** — you still need to measure whether outputs are correct

> **Tricky interview point:** Reasoning models can be "overthought" — they perform extensive internal reasoning even when the task is trivial, adding latency and cost. For simple tasks (classification, extraction of obvious information), a standard model with a direct prompt will be faster and cheaper. Use reasoning models selectively for genuinely complex tasks: multi-step planning, complex code generation, research synthesis, math-heavy problems.

### Prompting Differences in Practice

```python
# Traditional model: need explicit step-by-step guidance
traditional_prompt = """
Solve this problem step by step:
1. First identify all constraints
2. Then enumerate possible solutions
3. Evaluate each against the constraints
4. Select the optimal solution

Problem: {problem}
"""

# Reasoning model: just describe the task and output format
reasoning_model_prompt = """
Solve this optimization problem. Return your answer as JSON with fields:
"solution" (the recommended approach) and "reasoning" (2-3 sentence justification).

Problem: {problem}
"""
```

---

## Interview Q&A

**Q: What is the fundamental difference between APE and OPRO?** `[Medium]`  
APE is a one-shot approach: generate N candidates, evaluate them, select the best. OPRO is iterative: it maintains a history of (prompt, score) pairs and uses an optimizer LLM to propose improvements based on that history, converging over multiple rounds. OPRO is closer to gradient descent in spirit — it uses the optimization history to improve each successive candidate.

**Q: Why does DSPy require a metric function, and what happens if the metric is wrong?** `[Medium]`  
DSPy optimizes the prompt by running the program on training examples and using the metric to score the outputs. The optimizer searches for prompts that maximize the metric score. If the metric is wrong — rewards incorrect outputs, penalizes correct ones — DSPy will converge on prompts that produce the wrong behavior. The metric is the ground truth signal that guides the entire optimization. Getting the metric right is often harder than writing the prompt manually and is the most common failure mode in DSPy adoption.

**Q: What is position bias in LLM-as-Judge and how do you correct for it?** `[Medium]`  
Position bias: when presented with Response A and Response B, LLM judges tend to prefer whichever response appears first (~60% of the time). Correction: run the evaluation twice, swapping the order of A and B in the second run. Average the scores from both orderings. If one response is preferred in both orderings, it is a robust win. If the "preferred" response flips with the ordering, the difference is not statistically meaningful.

**Q: When should you use self-consistency instead of OPRO for improving accuracy?** `[Hard]`  
Self-consistency: use at inference time for specific high-stakes queries where you need higher confidence on a single answer and can afford N× cost. It improves accuracy per-query without changing the prompt. OPRO: use during development to find a better prompt that performs well across the entire evaluation set. OPRO improves accuracy globally by finding a better prompt; self-consistency improves accuracy locally for a specific query by sampling multiple answers. They are complementary: an OPRO-optimized prompt + self-consistency at inference time gives both benefits.

**Q: A team wants to migrate from manual prompting to DSPy. What are the three main risks?** `[Hard]`  
(1) **Metric risk:** DSPy quality is bounded by metric quality. If the team can't write a programmatic metric that correctly captures "good output," the compiled prompts will be optimized toward the wrong objective. (2) **Brittleness risk:** DSPy-compiled prompts are often long and specific — they're optimized for the training distribution but may perform worse on distribution shift. They also break when models update. (3) **Observability risk:** The prompt is generated by the compiler, not written by an engineer. When a compiled system fails, it's harder to diagnose because you can't read and reason about "why did this prompt produce that output" as easily as with a hand-crafted prompt.

**Q: How do reasoning models change the way you evaluate prompts?** `[Hard]`  
With traditional models, prompt quality is directly testable through output quality on an eval set — you change the prompt and run the eval. With reasoning models, the model's internal chain-of-thought is not always visible (o1's thinking is hidden; extended thinking models may expose it). This means you're evaluating a black box — you see the final answer but not the intermediate reasoning that produced it. Evaluation must focus more on output quality and less on reasoning trace quality. Additionally, reasoning model outputs are inherently more variable (longer, more exploratory) — evaluation rubrics must account for this. Pass/fail metrics work well; fine-grained "reasoning quality" scores are harder to compute and interpret.
