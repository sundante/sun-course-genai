# Planning and Reasoning

## Why Planning Matters

A purely reactive agent takes one step at a time, deciding what to do based only on the most recent observation. This works for simple tasks. It breaks for complex ones.

Consider the task: "Prepare a comprehensive competitive analysis of EV battery manufacturers for our board presentation next Tuesday."

A reactive agent starts immediately — perhaps searching for "EV battery manufacturers" — without considering:
- What structure the analysis should have
- Which manufacturers to cover and why
- What data needs to be gathered for each manufacturer
- How the steps depend on each other (you need the list of manufacturers before you can research each one)
- What "comprehensive" and "board presentation" imply about depth and format

An agent with planning produces a structured plan first, validates it, then executes. The plan is the agent's theory of how to solve the problem. Execution tests that theory. Replanning corrects it when reality diverges.

The choice of planning strategy — whether to reason step-by-step, plan upfront, explore multiple approaches, or verify outputs — determines both the quality and cost of the result.

---

## Chain of Thought (CoT)

### What It Is

Chain of Thought is the simplest "planning" technique: prompt the model to reason through a problem step by step before giving an answer. The reasoning is not action — it's the model thinking out loud before committing.

```
Without CoT:
Q: "A store sells apples for $1.20 each and oranges for $0.80 each. 
    If I buy 3 apples and 5 oranges, how much do I spend?"
A: "$7.60"   ← may be wrong; no visible reasoning

With CoT:
Q: (same question) "Let's think step by step."
A: "First, the cost of 3 apples: 3 × $1.20 = $3.60
    Next, the cost of 5 oranges: 5 × $0.80 = $4.00
    Total: $3.60 + $4.00 = $7.60"  ← reasoning visible, answer grounded
```

### Variants

**Zero-shot CoT**: Add "Let's think step by step" to the prompt. No examples needed. Effective for many tasks.

```python
prompt = f"""
{user_question}

Let's think step by step before answering.
"""
```

**Few-shot CoT**: Provide examples that include reasoning chains. The model imitates the reasoning style.

```python
EXAMPLES = """
Q: If a train travels 120km in 2 hours, then 180km in 3 hours, what is its average speed?
A: Total distance = 120 + 180 = 300km. Total time = 2 + 3 = 5 hours. Average speed = 300/5 = 60 km/h.

Q: {user_question}
A: Let me work through this:
"""
```

**Self-consistency**: Generate multiple CoT reasoning chains (with higher temperature), take the majority answer. Improves accuracy on math and logic problems at the cost of multiple LLM calls.

```python
def self_consistent_answer(question: str, num_samples: int = 5) -> str:
    answers = []
    for _ in range(num_samples):
        response = llm.invoke(
            question + "\nLet's think step by step.",
            temperature=0.7
        )
        answers.append(extract_final_answer(response.content))
    
    # Return majority vote
    from collections import Counter
    return Counter(answers).most_common(1)[0][0]
```

### When to Use CoT

- Mathematical and logical reasoning tasks
- Multi-step problems where intermediate steps matter
- Tasks where you want visible reasoning for debugging or trust
- When the model consistently makes errors on a class of problem without explicit reasoning

**Limitation**: CoT is reasoning, not action. The model still cannot take actions, call tools, or observe external state. It's a thinking strategy, not an agent pattern.

---

## ReAct (Reason + Act)

### What It Is

ReAct is the most common agent reasoning pattern. It interleaves explicit reasoning traces with tool calls: **Thought → Action → Observation → Thought → ...**

```
Thought: The user wants to know the current CEO of Anthropic and their background.
         I should search for this.
Action: search_web("Anthropic CEO 2024")
Observation: Dario Amodei is the CEO of Anthropic. He was previously VP of Research at OpenAI.
Thought: I have the CEO's name and background. The user asked about educational background too.
         Let me check for more detail.
Action: search_web("Dario Amodei education background")
Observation: Dario Amodei has a PhD in computational neuroscience from Princeton University.
Thought: I now have both the position and educational background. I can answer.
Action: [FINAL ANSWER]
"Dario Amodei is the CEO of Anthropic. He holds a PhD in computational neuroscience from 
Princeton University and was previously VP of Research at OpenAI before co-founding Anthropic."
```

The "Thought" lines are not tool calls — they are the LLM reasoning out loud about what it knows and what it needs next. This makes the agent's logic visible and gives it the chance to self-correct before taking an action.

### ReAct System Prompt

```python
REACT_SYSTEM_PROMPT = """
You are a helpful assistant with access to tools.

For every task, follow this exact format:

Thought: Reason about the current situation and what you need to do next.
Action: Call the appropriate tool.
Observation: (This will be filled in with the tool result)
Thought: Reason about the observation and what to do next.
...repeat until done...

When you have enough information to answer, write:
Thought: I now have all the information needed to answer.
Final Answer: [your complete response to the user]

Rules:
- Always write a Thought before every Action
- Never make up tool results — wait for the real Observation
- If a tool call fails, reason about the failure and try a different approach
- Never call the same tool with identical arguments twice
"""
```

### Why ReAct Works

1. **Prevents premature action**: Writing out "Thought: I need X, so I will call tool Y with parameter Z" catches errors before execution. The LLM often corrects its own reasoning in the Thought step.

2. **Maintains goal awareness**: Each Thought step reconnects the agent to what it is ultimately trying to accomplish. Without this, agents drift toward solving the most recent subproblem and forget the original task.

3. **Makes debugging possible**: When the agent produces a wrong answer, you can read the Thought steps to find exactly where the reasoning went wrong — often before any tool was even called.

### ReAct Failure Modes

**Thought without grounding**
```
Thought: The CEO is probably Sarah Johnson.  ← fabrication
Action: [FINAL ANSWER] "The CEO is Sarah Johnson"
```
Prevention: Prompt the agent to only state facts it has observed. "Never state a fact unless it appeared in a tool result or was provided in the original context."

**Circular reasoning**
```
Thought: I need to find X. I'll search for X.
Action: search("X")
Observation: No results.
Thought: I need to find X. I'll search for X.  ← same thought, same action
```
Prevention: Track seen `(thought, action)` pairs. If the same pair repeats, force a new strategy: "You've tried this search. Try a different query or approach."

**Over-thinking without acting**
```
Thought: I need to find X. But first I should think about how to find X.
         To do that, I should think about what X is. X is related to...
         [20 lines of reasoning without any tool call]
```
Prevention: After N consecutive Thought lines without an Action, inject: "You've been reasoning for a while. Take an action now."

---

## Plan-and-Execute

### What It Is

Plan-and-Execute separates planning from execution into two distinct phases. Phase 1: the agent produces a complete, structured plan. Phase 2: the plan is executed step by step. If a step fails, the planner is re-invoked to update the remaining plan.

```python
# Phase 1: Planning
PLANNER_PROMPT = """
You are a planning agent. Given a goal, create a detailed execution plan.

Goal: {goal}

Produce a numbered list of concrete, executable steps. Each step should:
- Be specific enough that an agent can execute it without further clarification
- Have a clear, observable outcome
- Be ordered correctly (later steps may depend on earlier ones)
- Be achievable with the available tools: {tool_list}

Format each step as:
Step N: [action description]
Expected outcome: [what success looks like for this step]
Depends on: [step numbers that must complete first, or "none"]
"""

# Phase 2: Execution
EXECUTOR_PROMPT = """
You are an execution agent. Execute the following step and report the result.

Overall goal: {goal}
Current step: {step_description}
Expected outcome: {expected_outcome}
Context from previous steps: {context}

Execute this step using the available tools. Report:
- Whether the step succeeded
- The result
- Any issues encountered
"""
```

### Replanning on Failure

```python
async def plan_and_execute(goal: str) -> str:
    # Phase 1: Generate the plan
    plan = await generate_plan(goal)
    completed_steps = []
    
    for step in plan.steps:
        # Execute the step
        result = await execute_step(step, context=completed_steps)
        
        if result.success:
            completed_steps.append({"step": step, "result": result.output})
        else:
            # Step failed — replan from here
            updated_plan = await replan(
                goal=goal,
                completed=completed_steps,
                failed_step=step,
                failure_reason=result.error,
                remaining_steps=plan.steps[plan.steps.index(step):]
            )
            plan.steps = plan.steps[:plan.steps.index(step)] + updated_plan.steps
    
    return synthesize_results(goal, completed_steps)
```

### When to Use Plan-and-Execute

| Use Plan-and-Execute When | Use ReAct Instead When |
|--------------------------|----------------------|
| The full plan can be determined upfront | The right next step depends on the previous result |
| HITL review of the plan before execution is desired | Dynamic discovery is the core of the task |
| Steps have stable dependencies | Adaptation is more important than planning |
| Tracking progress against a plan matters to users | Speed is the primary concern |
| The task is a known workflow (research → write → review) | The task structure is unknown upfront |

### HITL Review of the Plan

One of Plan-and-Execute's biggest advantages: you can show the human the plan and get approval before any action is taken.

```python
async def plan_review_execute(goal: str) -> str:
    plan = await generate_plan(goal)
    
    # Present plan to human before execution
    approval = await request_hitl_approval(
        action_description="Execute the following plan",
        plan_preview=plan.to_markdown(),
        consequences="This will make real API calls and may take 5-10 minutes."
    )
    
    if approval.decision == "rejected":
        return f"Plan rejected: {approval.reason}"
    
    if approval.decision == "modified":
        plan = parse_modified_plan(approval.modified_plan)
    
    return await execute_plan(plan)
```

---

## Tree of Thoughts (ToT)

### What It Is

Tree of Thoughts models reasoning as a search tree. Instead of committing to a single line of reasoning, the agent explores multiple branches, evaluates each, and selects the most promising path.

```
Goal: Design a system for real-time fraud detection

                    [Goal]
                   /       \
          Branch A          Branch B
    (Rule-based system)  (ML-based system)
        /    \                /    \
    Branch A1  A2        Branch B1  B2
  (Fast, rigid) (Slow, flexible)  (Streaming)  (Batch)

Evaluate each branch:
  A1: score 5/10 (fast but brittle, can't adapt to new patterns)
  A2: score 4/10 (too slow for real-time)
  B1: score 8/10 (best fit: ML model + streaming, adapts over time)
  B2: score 6/10 (ML is right, but batch doesn't meet real-time req)

Select B1 → continue expanding from there
```

### BFS vs DFS for ToT

**Breadth-First Search (BFS)**: Explore all options at one level before going deeper. Best when you want to compare alternatives at the same level of abstraction before committing.

**Depth-First Search (DFS)**: Explore each branch fully before trying the next. Best when you have a strong prior that one branch is correct and want to verify it quickly.

**Beam Search**: Keep the top-K branches at each level (K = beam width). Balances exploration with efficiency. Most common in practice.

```python
async def tree_of_thoughts(
    problem: str,
    branching_factor: int = 3,
    max_depth: int = 3,
    beam_width: int = 2
) -> str:
    # Initialize: generate branching_factor initial thoughts
    thoughts = await generate_thoughts(problem, n=branching_factor)
    
    for depth in range(max_depth):
        # Evaluate all current thoughts
        scored_thoughts = []
        for thought in thoughts:
            score = await evaluate_thought(thought, problem)
            scored_thoughts.append((score, thought))
        
        # Keep top beam_width thoughts
        scored_thoughts.sort(reverse=True)
        thoughts = [t for _, t in scored_thoughts[:beam_width]]
        
        # Check if any thought is a final answer
        for thought in thoughts:
            if is_final_answer(thought):
                return thought.answer
        
        # Expand: generate next thoughts from each surviving branch
        next_thoughts = []
        for thought in thoughts:
            expansions = await generate_thoughts(thought, n=branching_factor)
            next_thoughts.extend(expansions)
        thoughts = next_thoughts
    
    # Return best answer found
    return max(thoughts, key=lambda t: t.score).answer
```

### When ToT Is Worth the Cost

ToT is expensive: generating N branches per step multiplies LLM calls by N, and evaluating each branch adds more. Use it only when:

- The problem has multiple non-obvious solution approaches
- Choosing the wrong approach early leads to dead ends
- Quality is far more important than speed and cost
- The problem is "creative" (writing, design, strategy) rather than factual retrieval

ToT is overkill for most information-retrieval tasks. It excels for complex design problems, strategic planning, and creative generation.

---

## FLARE (Forward-Looking Active Retrieval)

### What It Is

FLARE (Forward-Looking Active Retrieval Enhanced Generation) solves a specific problem: generating long documents where the LLM needs to retrieve information at multiple points, not just once at the start.

In standard RAG, retrieval happens once before generation. For a long document, the retrieved context may be relevant for the first few paragraphs but not the later ones.

FLARE retrieves iteratively: generate a bit, detect where you're uncertain, retrieve relevant information for that uncertainty, continue generating.

```
Task: "Write a detailed report on the current state of quantum computing"

Standard RAG:
1. Retrieve documents about quantum computing (once)
2. Generate the entire report from that context
Problem: Context retrieved at step 1 may not cover specific sections (e.g., quantum error correction details)

FLARE:
1. Generate paragraph 1 (introduction — no retrieval needed)
2. Detect uncertainty: "I need to write about the current state of IBM's quantum systems..."
3. Retrieve: search("IBM quantum computer 2024 qubits")
4. Generate paragraph 2 using retrieved context
5. Continue generating paragraph 3
6. Detect uncertainty: "I should discuss recent breakthroughs in error correction..."
7. Retrieve: search("quantum error correction recent advances 2024")
8. Generate paragraph 3 using new context
9. Continue...
```

### Implementation

```python
def flare_generate(task: str, retrieval_threshold: float = 0.5) -> str:
    output_so_far = ""
    
    while not is_complete(output_so_far, task):
        # Generate the next sentence or paragraph
        next_chunk = llm.generate(
            prompt=f"Task: {task}\n\nSo far:\n{output_so_far}\n\nContinue:",
            max_tokens=200
        )
        
        # Estimate confidence (look for hedging language or explicit uncertainty)
        confidence = estimate_generation_confidence(next_chunk)
        
        if confidence < retrieval_threshold:
            # Low confidence: retrieve before committing to this chunk
            query = generate_retrieval_query(task, output_so_far, next_chunk)
            retrieved_context = retrieve(query)
            
            # Regenerate the chunk with the retrieved context
            next_chunk = llm.generate(
                prompt=f"Task: {task}\n\nContext:\n{retrieved_context}\n\nSo far:\n{output_so_far}\n\nContinue:",
                max_tokens=200
            )
        
        output_so_far += next_chunk
    
    return output_so_far

def estimate_generation_confidence(text: str) -> float:
    # Simple heuristic: check for hedging language
    hedging_phrases = ["I think", "I believe", "probably", "I'm not sure", "approximately", "around"]
    hedge_count = sum(1 for phrase in hedging_phrases if phrase.lower() in text.lower())
    return max(0.0, 1.0 - (hedge_count * 0.25))
```

---

## Reflexion (Self-Evaluation + Revision)

### What It Is

Reflexion is a pattern where the agent evaluates its own output (or a separate evaluator agent evaluates it), generates a verbal "reflection" about what went wrong, and uses that reflection to improve the next attempt. This is different from simple Reflection (covered in Design Patterns) in that the feedback is stored as a "verbal reinforcement signal" that persists across attempts.

```
Attempt 1:
  Task: "Write a Python function to reverse a linked list"
  Output: [code with a bug — doesn't handle single-node lists]
  Test results: 3/5 tests pass
  
Reflection:
  "The function fails when the list has a single node because I didn't check 
   for self.next being None before setting next.prev. I should add a base case 
   check at the start: if head is None or head.next is None, return head."

Attempt 2: [uses the reflection as additional context]
  Output: [corrected code]
  Test results: 5/5 tests pass
```

### Implementation

```python
class ReflexionAgent:
    def __init__(self, max_attempts: int = 4):
        self.max_attempts = max_attempts
        self.reflections = []
    
    def solve(self, task: str) -> str:
        for attempt in range(self.max_attempts):
            # Build context with accumulated reflections
            context = task
            if self.reflections:
                context += "\n\nLessons from previous attempts:\n" + "\n".join(
                    f"- Attempt {i+1}: {r}" for i, r in enumerate(self.reflections)
                )
            
            # Generate solution
            solution = llm.invoke(context).content
            
            # Evaluate
            eval_result = self.evaluate(task, solution)
            
            if eval_result.success:
                return solution
            
            # Generate reflection for next attempt
            reflection = self.generate_reflection(
                task=task,
                solution=solution,
                failure_reason=eval_result.failure_reason,
                test_results=eval_result.test_results
            )
            self.reflections.append(reflection)
        
        return solution  # return best attempt after max attempts
    
    def generate_reflection(self, task: str, solution: str, 
                             failure_reason: str, test_results: dict) -> str:
        reflection_prompt = f"""
        Task: {task}
        My solution: {solution}
        Failure reason: {failure_reason}
        Test results: {test_results}
        
        What specifically did I do wrong? What should I do differently next time?
        Be specific and actionable. Focus on what to change, not what was right.
        """
        return llm.invoke(reflection_prompt).content
```

---

## Goal Decomposition

### Why Decomposition Is Hard

The right decomposition of a goal into subtasks is not obvious. Bad decomposition leads to:
- **Over-decomposition**: so many tiny tasks that coordination overhead dominates
- **Under-decomposition**: subtasks that are still too complex for a single agent
- **Wrong seams**: splitting at artificial boundaries instead of natural ones
- **Hidden dependencies**: step 3 needs the output of step 1, not step 2, but this isn't obvious

### Decomposition Strategies

**Functional decomposition**: Split by what each piece does (research, write, review). Natural for creative or analytical tasks.

```
Goal: "Write a market analysis report"
→ Research phase: gather data
→ Analysis phase: interpret data
→ Writing phase: produce report
→ Review phase: check quality
```

**Object decomposition**: Split by what entity each piece operates on. Natural for tasks that touch multiple independent entities.

```
Goal: "Summarize Q3 performance for all 5 regional teams"
→ Subtask 1: summarize Team A's Q3 performance
→ Subtask 2: summarize Team B's Q3 performance
→ ...parallel execution possible...
→ Subtask 6: synthesize all summaries
```

**Dependency-first decomposition**: Start by identifying what depends on what, then order from least to most dependent.

```python
def decompose_with_dependencies(goal: str) -> list[Subtask]:
    # Ask the LLM to identify tasks AND their dependencies
    decomposition_prompt = f"""
    Goal: {goal}
    
    List the subtasks needed to complete this goal. For each subtask:
    1. Give it a short ID (task_1, task_2, etc.)
    2. Describe what it does
    3. List which other tasks it depends on (must complete first)
    
    Format as JSON:
    [
      {{"id": "task_1", "description": "...", "depends_on": []}},
      {{"id": "task_2", "description": "...", "depends_on": ["task_1"]}},
      ...
    ]
    """
    raw = llm.invoke(decomposition_prompt).content
    subtasks_data = json.loads(extract_json(raw))
    return [Subtask(**data) for data in subtasks_data]
```

---

## Choosing the Right Strategy

| Strategy | Best For | Cost | Quality |
|----------|----------|------|---------|
| Chain of Thought | Math, logic, step-by-step reasoning | Low (1 call) | Medium |
| ReAct | General-purpose agentic tasks with tools | Medium | Medium-High |
| Plan-and-Execute | Known workflows, HITL plan review | Medium-High | High |
| Tree of Thoughts | Complex design, strategy, creative problems | High (N× branches) | Very High |
| FLARE | Long document generation, research reports | Medium (proportional to length) | High |
| Reflexion | Code generation, iterative refinement | Medium (proportional to attempts) | High |

**Decision rules:**

1. Start with ReAct — it handles the majority of tasks well
2. Use Plan-and-Execute when you need HITL approval before execution or when the task is a known workflow
3. Use Tree of Thoughts when the problem has multiple non-obvious solution approaches and quality outweighs cost
4. Use FLARE when generating long documents that require retrieval at multiple points
5. Use Reflexion when output quality on the first attempt is consistently insufficient and there's a clear evaluable quality criterion
6. Use CoT as a supporting technique inside any of the above when pure reasoning steps are needed

---

## Dynamic Replanning

Even well-designed plans fail when reality doesn't match assumptions. A robust agent detects failure and updates the plan without starting over.

```python
class PlanExecutor:
    def __init__(self, max_replan_attempts: int = 3):
        self.max_replan_attempts = max_replan_attempts
    
    async def execute(self, goal: str, initial_plan: Plan) -> Result:
        plan = initial_plan
        completed = []
        replan_count = 0
        
        while not plan.is_complete() and replan_count < self.max_replan_attempts:
            next_steps = plan.next_executable()
            
            for step in next_steps:
                result = await self.execute_step(step)
                
                if result.success:
                    completed.append({"step": step, "output": result.output})
                    plan.mark_done(step.id, result.output)
                else:
                    replan_count += 1
                    
                    # Replan: update remaining steps given the failure
                    updated_remaining = await self.replan(
                        goal=goal,
                        completed=completed,
                        failed_step=step,
                        failure_reason=result.error
                    )
                    plan.replace_remaining(updated_remaining)
                    break  # restart the step loop with new plan
        
        if not plan.is_complete():
            return Result.partial(completed, error="Replanning attempts exhausted")
        
        return Result.success(synthesize(goal, completed))
    
    async def replan(self, goal: str, completed: list, 
                     failed_step: Subtask, failure_reason: str) -> list[Subtask]:
        replan_prompt = f"""
        Goal: {goal}
        
        Completed steps:
        {format_completed(completed)}
        
        Failed step: {failed_step.description}
        Failure reason: {failure_reason}
        
        Given this failure, what is the best revised plan for the remaining work?
        Preserve as much completed work as possible.
        Account for the fact that {failed_step.description} failed and cannot be retried as-is.
        """
        return parse_plan(llm.invoke(replan_prompt).content)
```

---

## Study Notes

- **ReAct is the default.** Use it unless you have a specific reason for something more complex. It handles more tasks than you'd expect and is much easier to debug than elaborate planning strategies.
- **Plan-and-Execute's hidden superpower is HITL.** Being able to show a human the plan before executing anything — and getting approval or modification — is enormously valuable for high-stakes tasks. This alone often justifies the added complexity.
- **Tree of Thoughts is a premium tool.** The branching factor rapidly multiplies your LLM call count. Profile the cost before deploying. It's justified for one-time complex decisions, not for high-volume routine tasks.
- **Replanning is different from retrying.** Retrying is running the same step again. Replanning is reconsidering the remaining work given that the step failed. Retrying is for transient errors; replanning is for fundamental approach failures.
- **Decomposition quality determines everything downstream.** A bad decomposition — wrong seams, hidden dependencies, wrong granularity — will cause failures regardless of which reasoning strategy you use. Invest time in the decomposition prompt.

---

## Q&A Review Bank

**Q1: What is the difference between Chain of Thought and ReAct?** `[Easy]`
A: Chain of Thought is a reasoning technique where the model thinks step by step before producing an answer — it's pure text generation, no tool calls, no external actions. ReAct (Reason + Act) is an agent pattern that interleaves explicit reasoning traces (Thought) with tool calls (Action) and tool results (Observation). CoT gives the model more reasoning steps within a single LLM call; ReAct enables the agent to take actions and observe results across multiple LLM calls in a loop. CoT improves answers to complex questions; ReAct enables agents to retrieve information, execute code, and interact with external systems. In practice, ReAct uses CoT-style reasoning within each Thought step.

**Q2: When should you choose Plan-and-Execute over ReAct?** `[Medium]`
A: Choose Plan-and-Execute when: (1) the full task structure can be determined upfront — you know what the steps are before executing any of them; (2) HITL review of the plan before execution is required — you need a human to see and approve the approach before any action is taken; (3) the task is a known workflow (research → write → review) where the structure is predictable; (4) transparency and progress tracking matter — a plan with checkable steps is easier to report to users. Use ReAct when: the right next step depends on the result of the previous step (dynamic discovery), the task structure is unknown upfront, or speed is the primary concern and overhead of planning is not justified.

**Q3: What is Tree of Thoughts and what cost does it introduce?** `[Medium]`
A: Tree of Thoughts models reasoning as a search tree — instead of committing to one reasoning path, the agent generates multiple candidate thoughts (branches), evaluates each, and continues from the most promising. This allows exploring multiple solution approaches before committing. The cost is multiplicative: if the branching factor is 3, every step requires 3× the LLM calls of a linear approach plus additional evaluation calls. Across 3 depth levels with branching factor 3, that's roughly 27 leaf nodes + 9 + 3 = 39 LLM calls vs 3 for linear. ToT is justified only when: the problem has non-obvious solution paths, choosing the wrong path leads to dead ends, and quality significantly outweighs cost.

**Q4: What is FLARE and what specific problem does it solve that standard RAG does not?** `[Hard]`
A: FLARE (Forward-Looking Active Retrieval Enhanced Generation) solves iterative retrieval for long document generation. Standard RAG retrieves documents once at the start and generates the entire output from that context. For short answers this works; for long reports or documents, the initial retrieval may be relevant for the first few sections but not later sections that need different facts. FLARE retrieves iteratively: it generates incrementally, detects when it's uncertain (hedging language, unknown specifics), generates a retrieval query for that specific uncertainty, retrieves new context, and continues generation. This ensures every section of a long output is grounded in relevant, retrieved context — not hallucinated from model weights or extrapolated from context retrieved for a different section.

**Q5: What is the difference between retrying a failed step and replanning?** `[Medium]`
A: Retrying executes the same step again with the same approach — appropriate for transient failures (network timeout, rate limit, temporary service outage) where the step itself is correct and the failure was environmental. Replanning reconsidering the remaining work given that a step failed — appropriate for fundamental approach failures where the step cannot succeed as designed (the tool doesn't exist, the data isn't available, the approach was wrong). Retrying a fundamentally broken step wastes time and money. Replanning rethinks the remaining subtasks to achieve the goal through a different path, preserving all work completed before the failure. A robust agent classifies failures before retrying: transient errors → retry with backoff; fundamental errors → replan.

**Q6: Why is goal decomposition considered a critical skill and what are the three most common decomposition mistakes?** `[Hard]`
A: Decomposition quality determines the quality of everything downstream — a bad decomposition leads to coordination overhead, execution failures, and replanning that could have been avoided. The three most common mistakes: (1) Wrong seams — splitting at artificial boundaries rather than natural ones (e.g., splitting "write paragraph 1" and "write paragraph 2" as separate subtasks when the agent can't write paragraph 2 without knowing how paragraph 1 ends; the natural seam is between research/writing/review phases). (2) Hidden dependencies — creating subtasks that depend on each other in ways not captured in the dependency graph, causing deadlocks or incorrect ordering at execution time; uncovering dependencies requires explicitly asking the model to reason about what each task needs as inputs. (3) Wrong granularity — subtasks that are either so granular they add coordination overhead without benefit, or so coarse that each subtask is still too complex for a single agent to complete reliably.
