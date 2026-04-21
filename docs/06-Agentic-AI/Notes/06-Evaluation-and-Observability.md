# Evaluation and Observability

## Why Agent Evaluation Is Different

Evaluating a single-turn LLM is straightforward: does the output match what you expect? You can measure BLEU scores, factual accuracy, or user ratings on individual responses.

Evaluating an agentic system is fundamentally harder because **the path matters, not just the destination**.

| Dimension | Single-Turn LLM | Agentic System |
|-----------|----------------|----------------|
| What to evaluate | Final output | Each step + final output |
| Failure modes | Hallucination, refusal | Wrong tool, bad arguments, infinite loop, cascading error |
| Success criteria | Output quality | Task completion + efficiency + safety |
| Ground truth | Expected answer | Expected trajectory (hard to define) |
| Side effects | None | Real-world actions taken (emails sent, files written) |
| Cost | Per-call cost | Cumulative cost over potentially many calls |

An agent can produce the right final answer via a completely wrong path — and that wrong path might have taken 3× longer and cost 5× more than it should have. Or it might have taken a correct shortcut that happens to fail in edge cases. Final answer alone tells you nothing.

---

## Trajectory Evaluation

Trajectory evaluation assesses the quality of the agent's execution path, not just the final answer.

### What a Trajectory Contains

```
Task: "Find the current CEO of OpenAI and their educational background"

Trajectory:
  Step 1: search_web("OpenAI CEO 2024")           → "Sam Altman, CEO of OpenAI"
  Step 2: search_web("Sam Altman education")       → "Stanford, dropped out"
  Step 3: [LLM reasons: I have enough information]
  Step 4: [LLM generates final answer]

Final answer: "Sam Altman is the CEO of OpenAI. He attended Stanford University 
              before dropping out to start businesses."
```

A good trajectory:
- Calls the right tools at the right time
- Uses appropriate arguments (not hallucinated)
- Doesn't make unnecessary tool calls
- Doesn't repeat failed approaches
- Terminates when the task is complete (doesn't loop)

### Trajectory Evaluation Approaches

**Golden trajectory comparison**
Define a "golden" trajectory for each test case (the ideal path), then compare the agent's actual trajectory against it.

```python
golden = {
    "task": "Find OpenAI CEO's educational background",
    "expected_tools": ["search_web", "search_web"],
    "expected_tool_args": [{"query": "OpenAI CEO"}, {"query": "Sam Altman education"}],
    "expected_steps": 2,
    "expected_final_answer_contains": ["Sam Altman", "Stanford"]
}
```

**Limitation:** Golden trajectories are brittle — there are usually multiple valid paths to the same answer.

**LLM-as-Judge for trajectories**
Use a strong LLM to evaluate whether the trajectory was reasonable, even if it differed from the golden path.

```python
judge_prompt = """
Evaluate this agent trajectory for a task. Rate each dimension 1-5:

Task: {task}
Trajectory: {trajectory}
Final Answer: {final_answer}

Dimensions to rate:
1. Tool selection accuracy: Were the right tools called?
2. Argument quality: Were tool arguments correct and reasonable?
3. Efficiency: Were there unnecessary or repeated steps?
4. Answer correctness: Is the final answer accurate?
5. Safety: Did the agent avoid any problematic actions?

Provide a score and brief justification for each.
"""
```

**Automated step-level checks**
For each step in the trajectory, run automated assertions:

```python
def check_trajectory(trajectory: list[Step]) -> EvalResult:
    issues = []

    for i, step in enumerate(trajectory):
        # Check: no hallucinated tool arguments
        if step.tool_call and not is_valid_tool_args(step.tool_call):
            issues.append(f"Step {i}: invalid tool arguments")

        # Check: no repeated identical tool calls
        if i > 0 and step.tool_call == trajectory[i-1].tool_call:
            issues.append(f"Step {i}: duplicate tool call")

        # Check: tool result was used in subsequent reasoning
        if step.tool_result and not is_referenced_in_next_step(step, trajectory[i+1:]):
            issues.append(f"Step {i}: tool result ignored")

    return EvalResult(issues=issues, score=1.0 - len(issues) / len(trajectory))
```

---

## Key Metrics

### Task-Level Metrics

| Metric | Definition | How to Measure |
|--------|-----------|----------------|
| Task completion rate | % of tasks that produce a valid final output | Pass/fail per task in evaluation set |
| Steps to completion | Number of LLM calls + tool calls per task | Count from trajectory |
| Cost per task | Total token cost for the task | Token counts × model pricing |
| Time to completion | Wall-clock time from start to final output | Timestamp delta |
| Safety violation rate | % of tasks where agent attempted a prohibited action | Audit log analysis |

### Step-Level Metrics

| Metric | Definition |
|--------|-----------|
| Tool call accuracy | % of tool calls with correct arguments |
| Tool selection accuracy | % of tool choices that were appropriate for the current reasoning step |
| Hallucination rate | % of tool arguments that were hallucinated (not grounded in context) |
| Retry rate | % of steps that required a retry after failure |
| Context utilization | Did the agent use the available context, or ignore it? |

### Quality Metrics

| Metric | Definition |
|--------|-----------|
| Final answer accuracy | % of final answers that are factually correct |
| Answer completeness | Does the answer address all parts of the task? |
| Instruction following | Did the agent follow the format/style requirements? |
| Groundedness | Is the final answer grounded in tool results vs hallucinated? |

---

## Evaluation Approaches

### Simulated Environments

Run the agent against mock tools that return predefined responses. This allows deterministic, reproducible evaluation without real API calls or side effects.

```python
# Mock tool that returns predefined responses based on query
class MockSearchTool:
    def __init__(self, fixtures: dict[str, str]):
        self.fixtures = fixtures  # query → response mapping

    def __call__(self, query: str) -> str:
        # Find best matching fixture
        for pattern, response in self.fixtures.items():
            if pattern.lower() in query.lower():
                return response
        return "No results found"

fixtures = {
    "OpenAI CEO": "Sam Altman is the CEO of OpenAI as of 2024",
    "Sam Altman education": "Sam Altman attended Stanford University and dropped out",
}
mock_search = MockSearchTool(fixtures)
```

**Advantages:** Fast, cheap, reproducible, no external dependencies
**Limitations:** Can't test the agent's behavior on novel inputs

### Real Environment Testing

Run the agent against real tools in a staging environment. Captures real-world behavior but is slower, more expensive, and has side effects.

Use real environment testing for:
- Pre-production validation
- Edge case testing for known failure scenarios
- Cost and latency benchmarking

### A/B Evaluation

Compare two agent versions (or two model versions) on the same task set. Measures relative improvement rather than absolute quality.

```python
results_v1 = evaluate_agent(agent_v1, test_tasks)
results_v2 = evaluate_agent(agent_v2, test_tasks)

# Compare on key metrics
compare_metrics(results_v1, results_v2, ["completion_rate", "steps_to_completion", "cost_per_task"])
```

### Human Evaluation

For tasks where automated metrics are insufficient (subjective quality, nuanced correctness), have humans rate agent outputs.

Use a structured rubric:
- Is the answer factually correct?
- Is it complete?
- Is the reasoning sound?
- Would you trust this output in production?

---

## Observability Stack

Observability means you can understand what the system did at any point in time. For agentic systems, this requires tracing every LLM call, tool call, and state transition.

### What to Instrument

Every significant event should be logged with enough context to reconstruct what happened:

```python
@dataclass
class AgentEvent:
    event_type: str        # "llm_call", "tool_call", "state_update", "hitl_trigger", "error"
    task_id: str
    agent_id: str
    step: int
    timestamp: str
    
    # For LLM calls
    model: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None
    
    # For tool calls
    tool_name: str | None = None
    tool_args: dict | None = None
    tool_result: dict | None = None
    tool_latency_ms: int | None = None
    
    # For errors
    error_type: str | None = None
    error_message: str | None = None
    stack_trace: str | None = None
```

### Observability Tools

| Tool | What It Does | Best For |
|------|-------------|----------|
| **LangSmith** | Full LLM call + chain tracing, built for LangChain/LangGraph | LangChain/LangGraph projects |
| **Langfuse** | Open-source LLM observability, works with any framework | Framework-agnostic, self-hosted option |
| **Weights & Biases (W&B)** | ML experiment tracking + LLM tracing | Teams already using W&B for ML |
| **OpenTelemetry + Jaeger** | General distributed tracing, framework-agnostic | Custom instrumentations, microservices |

### Setting Up LangSmith Tracing

```python
import os
from langsmith import traceable

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "your-api-key"
os.environ["LANGCHAIN_PROJECT"] = "agentic-system-prod"

# All LangChain/LangGraph calls are traced automatically once env vars are set
# For custom functions, use the @traceable decorator:
@traceable(name="research_step")
def run_research(query: str) -> dict:
    # ... your research logic
    return results
```

### Setting Up Langfuse

```python
from langfuse import Langfuse
from langfuse.decorators import observe

langfuse = Langfuse(
    public_key="pk-...",
    secret_key="sk-...",
    host="https://cloud.langfuse.com"
)

@observe()  # auto-traces this function and all nested calls
def run_agent_task(goal: str) -> str:
    # all LLM calls made within this function are traced
    return agent.run(goal)
```

### Dashboards and Alerts

Set up monitoring dashboards that track:
- Task completion rate over time
- Average steps per task (efficiency)
- Error rate by agent and error type
- Cost per task (total and by model)
- P50 / P95 / P99 task duration

Set alerts for:
- Task completion rate drops below 90%
- Error rate spikes above 5%
- Any safety violation
- Daily cost exceeds budget threshold

---

## Debugging Agentic Systems

Debugging a multi-agent system is harder than debugging a single function because the failure may have happened several steps before the visible error.

### Step 1: Find the First Wrong Step

Don't start from the error message — start from the beginning of the trajectory and find the first step where something went wrong.

```
Task: "Send a summary of the Q3 earnings report to the CFO"

Step 1: search("Q3 earnings report")    → [correct: found the report]
Step 2: read_file("Q3_earnings.pdf")    → [correct: extracted text]
Step 3: summarize(text)                 → [FIRST ERROR: summary missed key figures]
Step 4: get_email("CFO")                → [correct: found email, but summary was already wrong]
Step 5: send_email(summary, to=CFO)     → [symptom: wrong content sent]
```

The error is at step 3, not step 5. Fix the summarization step.

### Step 2: Replay from Checkpoint

Most agentic frameworks support replaying execution from a checkpoint. This lets you:
1. Stop execution at the problematic step
2. Modify the agent prompt or tool behavior
3. Resume from that checkpoint to verify the fix

```python
# LangGraph: replay from checkpoint
config = {"configurable": {"thread_id": "task-123", "checkpoint_id": "step-3"}}
for event in graph.stream(None, config, stream_mode="values"):
    print(event)
```

### Step 3: Inspect State at Each Step

Check the full agent state (conversation history, tool results, intermediate outputs) at each step, not just the final state.

### Step 4: Check Tool Call Arguments

The most common failure mode is a hallucinated tool argument. Log and verify every tool call's arguments, not just whether the tool succeeded.

```python
# Log exactly what was sent to the tool
logger.debug(f"Tool call: {tool_name}({json.dumps(tool_args, indent=2)})")
logger.debug(f"Tool result: {json.dumps(tool_result, indent=2)}")
```

### Step 5: Trace Context Usage

Did the agent actually use the information it was given? Check whether the final answer references facts from the tool results, or whether it was generated from model weights (hallucinated).

---

## Failure Mode Taxonomy

| Failure Mode | Symptom | Root Cause | Fix |
|-------------|---------|-----------|-----|
| Hallucinated tool args | Tool returns unexpected result | Agent invents arguments not grounded in context | Improve tool descriptions; validate args before calling |
| Wrong tool selected | Task fails or takes too long | Agent misunderstands when to use each tool | Clarify tool descriptions; add routing logic |
| Infinite retry loop | Task runs forever; cost spikes | No max_iterations; evaluator always rejects | Set max_iterations; improve evaluator rubric |
| Context window exhaustion | Agent loses track of goal | History too long | Add summarization; reduce verbose tool outputs |
| Cascade failure | Downstream agents produce garbage | Upstream error not caught and propagated | Validate each agent's output; propagate errors explicitly |
| Context drift | Agent contradicts its earlier work | Goal lost in long conversation | Pin goal in system prompt; use task ledger |
| HITL timeout | Task stuck | Human didn't respond; no timeout handler | Define timeout policy; add escalation path |
| Prompt injection | Agent takes unauthorized actions | Malicious content in external data | Input sanitization; role separation; action validation |

---

## Study Notes

- **Evaluate before you optimize.** Build your evaluation harness before tuning prompts or adding complexity. Without measurement, you can't tell if changes improve or degrade behavior.
- **Trajectory evaluation is the most important investment** in agent eval. Final answer quality is easy to measure and easy to game; trajectory quality is what actually reflects system health.
- **LangSmith or Langfuse from day one.** Instrumenting after the fact is 10× harder. Start tracing on the first day of development.
- **Simulated environments enable fast iteration.** Running against mock tools lets you test thousands of scenarios quickly and cheaply. Build a good test fixture library.
- **Debugging: always find the first wrong step.** Symptoms appear downstream; root causes are upstream. Don't fix the symptom.
- **The hardest failure mode to catch is context drift.** The agent's final answer looks reasonable; only comparison against the original task reveals that it answered a slightly different question than the one asked.

---

## Q&A Review Bank

**Q1: Why is trajectory evaluation more important than final-answer evaluation for agentic systems?** `[Medium]`
A: A final answer alone tells you almost nothing about system health. An agent can produce the right answer via a completely wrong path — one that took 3× longer, cost 5× more, and would fail on any variation of the input. Conversely, an agent can follow a perfect path and still get a wrong answer due to an out-of-date knowledge source. Trajectory evaluation — assessing tool selection, argument quality, step count, and absence of loops — reveals the real system behavior. It's also essential for catching context drift: the final answer looks reasonable, but only the trajectory reveals that the agent answered a slightly different question than the one asked.

**Q2: What are the three categories of metrics for evaluating agentic systems?** `[Easy]`
A: Task-level metrics (completion rate, steps to completion, cost per task, time to completion, safety violation rate — these measure the overall task outcome), Step-level metrics (tool call accuracy, tool selection accuracy, hallucination rate in tool arguments, retry rate — these measure the quality of individual decisions within a trajectory), and Quality metrics (final answer accuracy, answer completeness, instruction following, groundedness — these measure the value of the output to the user). All three categories are needed: task-level metrics can mask step-level inefficiency, and quality metrics can mask trajectory inefficiency.

**Q3: What is LLM-as-judge for trajectory evaluation and what is its key limitation?** `[Medium]`
A: LLM-as-judge uses a strong LLM (the judge) to evaluate a trajectory on defined dimensions — tool selection accuracy, argument quality, efficiency, answer correctness, and safety — producing a score and justification for each. It's used instead of golden trajectory comparison because there are usually multiple valid paths to the same answer, and golden trajectories are brittle. The key limitation is that LLM judges introduce their own biases and are inconsistent: the same trajectory may receive different scores on different runs (due to temperature), and the judge may share blind spots with the generating model. Calibrate LLM judges by comparing their scores to human annotators on a subset of trajectories before relying on them.

**Q4: Why are simulated environments preferred for most agentic evaluation runs?** `[Medium]`
A: Simulated environments use mock tools with predefined responses, enabling fast (no API latency), cheap (no API costs), reproducible (same response every run), and side-effect-free (no emails sent, no records written) evaluation. This allows running thousands of test scenarios in minutes. Real environment testing is reserved for pre-production validation, edge case testing, and cost/latency benchmarking — situations where the real behavior of external services matters. The key to making simulated evaluation valuable is building comprehensive fixture libraries that cover both happy-path and failure-mode scenarios.

**Q5: What is context drift, why is it the hardest failure mode to catch, and how do you prevent it?** `[Hard]`
A: Context drift occurs when an agent's accumulated conversation history grows so long that later reasoning starts to contradict earlier reasoning, and the agent gradually loses track of the original goal — answering a subtly different question than the one it was asked. It's the hardest to catch because the final answer looks reasonable in isolation; only comparison against the original task reveals the drift. Automated metrics won't flag it; trajectory evaluation is required. Prevention: pin the goal statement in a fixed position in every prompt (system message or beginning of each user turn), maintain a task ledger as the external source of truth for what remains to be done, and use context summarization that preserves the original goal explicitly.

**Q6: Describe the five-step debugging process for a multi-agent system.** `[Hard]`
A: Step 1 — Find the first wrong step: don't start from the error message, start from the beginning of the trajectory and find the earliest step where something went wrong; symptoms appear downstream of root causes. Step 2 — Replay from checkpoint: most frameworks (LangGraph, etc.) support replaying execution from a saved state, letting you modify the agent and resume from the problem point without rerunning the whole task. Step 3 — Inspect state at each step: examine the full agent state (conversation history, tool results, intermediate outputs) at the problem step, not just the final state. Step 4 — Check tool call arguments: the most common failure is hallucinated arguments — log and verify every call's exact input, not just whether the tool returned a success code. Step 5 — Trace context usage: verify whether the final answer actually references facts from tool results, or whether it was generated from model weights (hallucinated context).
