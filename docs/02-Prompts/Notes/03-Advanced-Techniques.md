# Advanced Prompting Techniques

The core techniques (zero-shot, few-shot, CoT, ReAct) get you most of the way. But they share a common limitation: they all commit to a single reasoning path or a single prompt formulation. The advanced techniques in this file either **explore multiple paths** (ToT, self-consistency), **compose prompts programmatically** (chaining, least-to-most), or **use the model to improve itself** (meta-prompting, generated knowledge).

The historical arc:
```
2021: Generated Knowledge (Liu et al.) — augment with model-generated facts
2022: Self-Consistency (Wang et al.)   — sample many paths, vote on best
2022: Least-to-Most (Zhou et al.)     — decompose before solving
2023: Tree of Thought (Yao et al.)    — systematic search over reasoning space
2023: Meta-prompting                  — model improves its own prompts
```

---

## Why Core Techniques Have Limits

**The single-path problem:** Standard CoT generates one reasoning chain. If the model takes a wrong turn on step 3 of a 10-step problem, the entire chain is corrupted — and it arrives at a confident wrong answer with apparently coherent reasoning.

**The format generalization problem:** Few-shot provides examples, but examples are finite. Novel inputs that fall outside the distribution of your examples may not be handled correctly.

**The decomposition problem:** Some tasks are too complex for a single prompt. "Research this topic, synthesize the findings, and write a 5-page report" is not a single-step task — it requires breaking down into manageable sub-tasks.

Advanced techniques address these limits systematically.

---

## Tree of Thought (ToT)

Tree of Thought (Yao et al., 2023) generalizes CoT from a linear chain to a **tree search**. Instead of one reasoning path, the model generates multiple candidate "thoughts" at each step, evaluates them, and explores the most promising branches — backtracking when a branch leads to a dead end.

```
Standard CoT:
Problem → Step1 → Step2 → Step3 → Answer  (one path)

Tree of Thought:
                    ┌── Branch A1 → A2 → [dead end, backtrack]
Problem → Root ─── ┼── Branch B1 → B2 → B3 → Answer ✓
                    └── Branch C1 → [evaluated as low quality, pruned]
```

### How It Works

ToT requires three components:
1. **Thought generator:** Produce multiple candidate next steps (typically 2–5)
2. **State evaluator:** Score each candidate — "is this on the right track?" The evaluator is also an LLM call
3. **Search algorithm:** BFS (explore all nodes at each depth) or DFS (go deep on one branch, backtrack on failure)

```python
def tree_of_thought(problem, breadth=3, depth=4):
    """Simplified BFS implementation."""
    thoughts = [problem]  # root

    for step in range(depth):
        candidates = []
        for thought in thoughts:
            # Generate multiple next steps from current thought
            next_steps = generate_thoughts(thought, n=breadth)
            candidates.extend(next_steps)

        # Evaluate all candidates and keep top-k
        scored = [(t, evaluate_thought(t)) for t in candidates]
        thoughts = [t for t, score in sorted(scored, key=lambda x: -x[1])[:breadth]]

    # Return highest-scoring final thought
    return max(thoughts, key=evaluate_thought)

def generate_thoughts(context, n=3):
    prompt = f"""Given this reasoning so far:
{context}

Generate {n} different possible next reasoning steps. Each should explore a different angle.
Output as a numbered list."""
    return parse_numbered_list(llm(prompt))

def evaluate_thought(thought):
    prompt = f"""Rate this reasoning path from 1-10 for correctness and progress:
{thought}

Score (just the number):"""
    return int(llm(prompt).strip())
```

### When ToT Is Worth the Cost

Cost: ToT makes O(breadth × depth) LLM calls for a problem that CoT solves in 1 call. A breadth=3, depth=4 search makes ~12 calls plus evaluation calls — roughly 20–30× the cost of CoT.

ToT is worth it when:
- The problem requires creative exploration (planning, puzzle-solving, code architecture design)
- Single-path CoT consistently fails on a specific class of problems
- The problem has well-defined intermediate evaluation criteria

ToT is overkill when:
- The task is a straightforward reasoning chain with no branching decision points
- Cost and latency matter more than accuracy
- The problem is solvable with CoT 90%+ of the time

> **Tricky interview point:** ToT requires a good **evaluator function** — the component that scores each reasoning branch. If the evaluator is unreliable (which it often is, since it's also an LLM), ToT may systematically explore the wrong branches and perform worse than CoT. The evaluator is the hardest part to get right, and it adds its own hallucination risk. In practice, ToT works best when the evaluation criterion is verifiable (e.g., code that runs, math with checkable answers) rather than subjective.

---

## Self-Consistency

Self-Consistency (Wang et al., 2022) is a decoding strategy, not a prompting technique per se. Instead of generating one CoT chain and trusting it, generate **N diverse chains** and take a majority vote on the final answer.

```
Prompt (same each time, temperature > 0)
    → Chain 1 → Answer: 42
    → Chain 2 → Answer: 42
    → Chain 3 → Answer: 40  ← outlier
    → Chain 4 → Answer: 42
    → Chain 5 → Answer: 42

Majority vote → 42 ✓
```

```python
from collections import Counter

def self_consistent_answer(prompt, n_samples=5, temperature=0.7):
    answers = []
    for _ in range(n_samples):
        response = llm(prompt, temperature=temperature)
        answer = extract_final_answer(response)
        answers.append(answer)

    # Majority vote
    vote_counts = Counter(answers)
    return vote_counts.most_common(1)[0][0]
```

### Why High Temperature Is Intentional

Self-consistency requires **diverse** chains, not identical ones. High temperature (0.7–1.0) introduces variation in the reasoning paths. If you use temperature=0, all chains are identical and the vote adds nothing. The diversity is the mechanism — different paths may take different wrong turns, and the correct answer is more likely to be in the majority.

### When Self-Consistency Helps (and When It Doesn't)

**Works well:** Tasks with a single verifiable correct answer — math problems, factual questions, classification. The majority vote is meaningful because "correct" is well-defined.

**Does not work:** Open-ended generation tasks (writing, summarization, creative tasks). If you ask for a summary and get 5 different summaries, there is no "majority vote" — they're all different. Self-consistency requires an answer space where multiple responses can be compared and votes can be counted.

> **Tricky interview point:** Self-consistency multiplies your API cost by N. For a task where standard CoT is correct 85% of the time, self-consistency with N=5 might push that to 94% — but costs 5× as much. The question for a production system is whether that 9% accuracy improvement justifies the 5× cost. In most cases, it does not — use it selectively for high-stakes or high-confidence tasks where accuracy justifies cost.

---

## Prompt Chaining

Prompt chaining decomposes a complex task into a **pipeline of prompts** where the output of each step becomes the input to the next. Rather than one large monolithic prompt, you write multiple focused prompts.

```
[Prompt 1: Extract key claims]
    ↓ (list of claims)
[Prompt 2: Verify each claim against source]
    ↓ (claim + verified/unverified)
[Prompt 3: Write balanced summary using only verified claims]
    ↓ (final output)
```

```python
def chain_prompts(document):
    # Step 1: Extract
    claims = llm(f"Extract all factual claims from this document as a numbered list:\n\n{document}")

    # Step 2: Verify
    verified = llm(f"""For each claim below, mark it as SUPPORTED or UNSUPPORTED
based on the original document.

Claims:
{claims}

Document:
{document}""")

    # Step 3: Synthesize
    summary = llm(f"""Write a 2-paragraph summary using only SUPPORTED claims:

{verified}""")

    return summary
```

### Benefits

- **Debuggable:** Each intermediate output can be inspected and evaluated independently
- **Composable:** Steps can be reused across pipelines
- **Reliable:** Smaller, focused prompts are easier for the model to execute correctly
- **Parallelizable:** Independent steps can run concurrently

### Pitfalls

**Error propagation:** A mistake in step 1 propagates to all subsequent steps. Build validation and error-handling between steps.

**Context loss:** Information present in step 1's input may not be available in step 3 unless explicitly passed. Be intentional about what context flows through the chain.

**Token cost:** Each step is a separate API call. N steps = N × (input + output) tokens.

---

## Meta-Prompting

Meta-prompting uses the LLM to **generate or improve prompts** rather than to directly complete a task. The model is applied to the prompt itself.

### Self-Refinement Loop

Generate an initial output, critique it, and revise based on the critique. This is a mini-optimization loop that can run for 1–3 iterations before diminishing returns.

```python
def self_refine(task, n_iterations=2):
    # Initial attempt
    draft = llm(f"Complete the following task:\n\n{task}")

    for i in range(n_iterations):
        # Critique
        critique = llm(f"""You are a critical editor. Identify weaknesses in this response:

Task: {task}
Response: {draft}

List specific problems and improvements needed:""")

        # Revise
        draft = llm(f"""Revise the response to address these issues:

Original task: {task}
Previous response: {draft}
Critique: {critique}

Revised response:""")

    return draft
```

### Automatic Prompt Generation

Use the LLM to generate improved prompt formulations for a given task:

```python
def improve_prompt(original_prompt, task_description):
    return llm(f"""You are a prompt engineering expert.
Given this task: {task_description}
And this current prompt that underperforms: {original_prompt}

Write an improved prompt that will produce better outputs. Focus on:
- Clarity of instruction
- Output format specification
- Appropriate context
- Failure mode prevention

Improved prompt:""")
```

> **Tricky interview point:** Meta-prompting can create **prompt brittleness** — prompts that are highly optimized for a narrow distribution of inputs but fail on anything slightly different. The model that generates the improved prompt is also the model that will use it — so the improvements are biased toward what the model finds easy to follow, not necessarily what produces correct outputs for your actual evaluation criteria. Always evaluate generated prompts against a held-out test set.

---

## Least-to-Most Prompting

Least-to-Most Prompting (Zhou et al., 2022) solves the **decomposition challenge** in complex tasks by explicitly breaking a problem into sub-problems, solving the simplest first, and using each solution as context for harder sub-problems.

```
Stage 1 — Decompose:
"To solve [hard problem], I first need to solve: [sub-problem 1], then [sub-problem 2], then..."

Stage 2 — Sequential solving:
Solve sub-problem 1 → add solution to context
Solve sub-problem 2 using sub-problem 1's answer as context
...
Solve original problem using all sub-problem answers as context
```

```python
def least_to_most(problem):
    # Stage 1: Decompose into sub-problems
    decomposition = llm(f"""Break this problem into simpler sub-problems that must be solved first.
List them from simplest to most complex.

Problem: {problem}

Sub-problems (simplest first):""")

    sub_problems = parse_list(decomposition)

    # Stage 2: Solve each sub-problem, carry context forward
    context = f"Original problem: {problem}\n\n"
    for sub in sub_problems:
        solution = llm(f"{context}Sub-problem to solve: {sub}\n\nSolution:")
        context += f"Sub-problem: {sub}\nSolution: {solution}\n\n"

    # Final answer using all sub-solutions
    answer = llm(f"{context}Now solve the original problem using the sub-solutions above:")
    return answer
```

Least-to-most is particularly effective for:
- Math word problems with multiple steps
- Multi-hop question answering
- Code generation with complex logic that builds on itself

---

## Generated Knowledge Prompting

Generated Knowledge Prompting (Liu et al., 2021) was an early technique for improving model accuracy on knowledge-intensive tasks — a predecessor to RAG. The idea: before answering a question, ask the model to generate relevant background knowledge, then use that knowledge to answer.

```python
def generated_knowledge(question):
    # Step 1: Generate relevant knowledge
    knowledge = llm(f"""Generate 5 relevant facts that would help answer this question accurately:

Question: {question}

Facts:""")

    # Step 2: Answer using the generated knowledge
    answer = llm(f"""Use the following facts to answer the question accurately:

Facts:
{knowledge}

Question: {question}

Answer:""")

    return answer
```

### Relationship to RAG

Generated Knowledge is "pre-retrieval from the model's own weights." It forces the model to surface relevant knowledge explicitly before reasoning, which can improve accuracy by making that knowledge available in the context window rather than requiring the model to recall it implicitly during answer generation.

The critical limitation: the model can hallucinate the generated facts. A fabricated "relevant fact" that is added to the context will be treated as ground truth in step 2, potentially generating a confident, coherent, but wrong answer. This is why RAG (retrieving real external documents) superseded Generated Knowledge for production knowledge-intensive tasks.

> **Tricky interview point:** Generated Knowledge can actually **amplify hallucinations** in a failure mode: the model generates a plausible-sounding but incorrect fact in step 1, and that incorrect fact becomes the primary basis for the step 2 answer. The final output is confident and coherent because it correctly applied the "facts" — they just weren't real. Always verify generated knowledge against a ground truth source for high-stakes tasks.

---

## Directional Stimulus Prompting

Directional Stimulus Prompting adds a **hint or nudge** at the end of the prompt to steer the model's generation without providing a full example. It is lighter than few-shot (no full examples required) but provides more guidance than zero-shot.

```python
# Standard zero-shot
prompt = "Summarize the following article:\n\n{article}"

# With directional stimulus
prompt = """Summarize the following article:\n\n{article}

Focus especially on the economic implications and any policy recommendations made."""
```

Other effective stimuli:
- "Pay particular attention to any numerical evidence provided."
- "Consider both the benefits and risks before concluding."
- "The key tension in this text involves..."

Directional stimuli work by shifting the probability distribution at the point in generation where the model is deciding what to focus on. They are cheap, easy to apply, and underused.

---

## Evolution Summary: Which Technique Solves What

| Technique | Core Problem Solved | Year | Cost vs Baseline | Best For |
|-----------|-------------------|------|-----------------|---------|
| Zero-shot CoT | Single-step reasoning fails | 2022 | 1× | Math, logic |
| Few-shot | Output format/style inconsistency | 2020 | 1× | Formatting, rare patterns |
| Self-Consistency | Single CoT chain can be wrong | 2022 | N× | Math, factual Q&A |
| Least-to-Most | Task too complex for single prompt | 2022 | N-step | Multi-hop reasoning |
| Generated Knowledge | Model doesn't surface relevant facts | 2021 | 2× | Knowledge-intensive Q&A |
| Tree of Thought | Single path misses best solution | 2023 | 20-30× | Planning, creative tasks |
| Prompt Chaining | Single prompt too complex to debug | 2022+ | N-step | Long pipelines |
| Meta-Prompting | Manual prompt optimization too slow | 2023 | 2-3× | Prompt improvement |

---

## Interview Q&A

**Q: What problem does self-consistency solve that CoT alone cannot?** `[Easy]`  
CoT generates a single reasoning chain — if it takes a wrong turn, the final answer is wrong. Self-consistency generates multiple diverse chains and takes a majority vote. Individual chains may err in different places, but the correct answer tends to appear in the majority, improving aggregate accuracy.

**Q: When should you choose Tree of Thought over Chain-of-Thought?** `[Medium]`  
When the task requires exploring multiple solution approaches simultaneously — planning problems, creative design, complex puzzles. ToT is 20-30× more expensive than CoT, so only use it when (a) CoT consistently fails on the specific task class and (b) the improved accuracy justifies the cost. For most tasks, CoT is sufficient.

**Q: What is the key risk of meta-prompting (using an LLM to improve its own prompts)?** `[Medium]`  
The model generates prompts that are easy for *it* to follow, not necessarily prompts that produce correct outputs on your actual evaluation criteria. Generated prompts can be highly optimized for a narrow input distribution and brittle on anything different. Always evaluate generated prompts against a held-out test set rather than trusting the improvement intuitively.

**Q: How does Generated Knowledge Prompting differ from RAG, and why was RAG an improvement?** `[Medium]`  
Generated Knowledge asks the model to produce relevant facts from its parametric memory, then uses those facts to answer. RAG retrieves real documents from an external knowledge base. The critical difference: generated knowledge can hallucinate; retrieved documents contain ground-truth information. RAG eliminates the hallucination risk in the knowledge-gathering step, at the cost of requiring a retrieval infrastructure.

**Q: Explain error propagation in prompt chaining and how to mitigate it.** `[Hard]`  
Each step in a prompt chain uses the previous step's output as input. An error in step 1 (wrong extraction, missed information) propagates to step 2, which builds on it, producing step 3 output that is incorrect in a compounding way. Mitigation: (1) validate intermediate outputs — use a separate "checker" prompt to verify each step's output before proceeding; (2) include error recovery logic that retries or falls back; (3) design chains so each step is independently evaluable against a known schema or constraint; (4) pass the original source document through the entire chain so later steps can cross-reference it.

**Q: Self-consistency doesn't work for "what is the best marketing slogan for our product?" Why?** `[Hard]`  
Self-consistency requires a verifiable correct answer that can be determined by majority vote. Slogans are subjective and open-ended — 5 diverse outputs will be 5 completely different slogans. There is no "majority vote" mechanism applicable to open-ended creative outputs. Self-consistency is a technique for tasks with convergent answers (math, factual questions, classification), not divergent creative tasks.

**Q: A customer asks you to build a prompt that achieves 95% accuracy on a medical QA benchmark. You're currently at 85% with standard CoT. Walk through your approach.** `[Hard]`  
Step 1: Analyze the 15% errors — are they systematic (specific topics, question types) or random? Systematic errors suggest the need for domain-specific few-shot examples or a specialized system prompt. Random errors suggest self-consistency might help. Step 2: Test self-consistency with N=5 (costs 5×, expected gain ~5–8%). Step 3: For systematic errors in specific topics, build a dynamic few-shot retrieval system that selects the most relevant examples per question. Step 4: Test Generated Knowledge or chain a "recall relevant medical facts first" step before answering. Step 5: Evaluate each intervention independently against a held-out test set. Step 6: If still below 95%, the gap may require RAG with a medical knowledge base rather than prompt engineering alone — parametric knowledge has limits.

**Q: Why might Directional Stimulus Prompting outperform explicit instruction for steering model focus?** `[Hard]`  
Explicit instructions ("Focus on X") operate at the beginning of generation and may be partially "forgotten" over long outputs due to attention decay across position. A directional stimulus at the end of the prompt is placed close to where generation begins, exploiting the recency effect in attention. It's closer to showing the model what to do than telling it at a distance. Additionally, stimuli that are framed as observations ("The key tension involves...") can activate relevant knowledge representations more strongly than instructions ("Please focus on...").
