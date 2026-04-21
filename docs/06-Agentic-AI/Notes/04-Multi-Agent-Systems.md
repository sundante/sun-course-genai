# Multi-Agent Systems

## Why Multi-Agent

A single agent has hard limits. When a task pushes past those limits, the solution is to split the work across multiple agents. There are four distinct reasons to go multi-agent, each with different implications for system design.

### 1. Task Decomposition

Some tasks are too complex to reason about holistically. A single agent trying to "build a full market analysis" will produce worse results than one agent that researches, one that structures findings, and one that writes — because each subtask requires focused attention.

The key question: does the task have natural seams where it can be split? If splitting is forced and artificial, multi-agent adds overhead with no benefit.

### 2. Specialization

Different agents can be optimized for different tasks through prompt engineering, model selection, or tool sets.

| Agent | Specialization |
|-------|--------------|
| Research Agent | Prompt tuned for systematic web search; access to search tools |
| Code Agent | Prompt tuned for Python; access to code execution sandbox |
| Critic Agent | Prompt tuned for adversarial analysis; no action tools |
| Summarizer | Uses a smaller, faster model (cost optimization) |

Specialization improves quality: a focused agent outperforms a generalist on its specific task.

### 3. Parallelism

Independent subtasks can run concurrently, reducing total wall-clock time. A system that runs 5 research agents in parallel completes in 1/5 the time of running them sequentially.

This only applies to **genuinely independent** subtasks. Tasks with dependencies must still be sequential.

### 4. Fault Isolation

When one agent fails, it fails in isolation. The orchestrator can retry that agent, substitute a fallback, or skip the subtask — without the whole system crashing. This is fundamentally different from a single agent where any failure terminates the entire task.

---

## Coordination Strategies

Coordination answers: how do agents decide what to do and in what order?

### Centralized (Orchestrator-Controlled)

A single orchestrator holds the plan and assigns tasks to agents. Agents are workers — they execute assigned tasks and report results. They have no knowledge of the broader plan.

```
Orchestrator (has the plan)
    → assigns task_A to Agent_1
    → assigns task_B to Agent_2 (in parallel)
    → waits for both results
    → assigns task_C to Agent_3 (using results from A and B)
    → synthesizes final output
```

**Advantages:**
- Easy to reason about — one place holds the plan state
- Easy to debug — trace the orchestrator's decisions
- Easy to add HITL — insert approval gate in the orchestrator

**Disadvantages:**
- Orchestrator is a single point of failure
- Orchestrator bottleneck — all coordination flows through one LLM
- Doesn't scale to very large agent counts

**Best for:** Most production systems. Orchestrator-Subagent is the default pattern.

### Decentralized (Peer-to-Peer)

No orchestrator. Agents observe the shared state, determine what needs to be done, and execute. Coordination emerges from agent behavior, not explicit assignment.

```
Shared State: {todo: [task_A, task_B, task_C], done: [], results: {}}

Agent_1 sees task_A unclaimed → claims it → executes → writes result
Agent_2 sees task_B unclaimed → claims it → executes → writes result
Agent_3 waits for A and B → both done → executes task_C → writes result
```

**Advantages:**
- No single point of failure
- Self-organizing — agents pick up work without assignment
- Scales to many agents naturally

**Disadvantages:**
- Harder to reason about — behavior emerges from agent interactions
- Race conditions if agents don't use proper locking when claiming tasks
- Difficult to implement HITL
- Debugging is much harder

**Best for:** Distributed systems where fault tolerance is critical; research settings.

### Hybrid

Most large systems use a hybrid: a centralized orchestrator at the top level, with decentralized coordination within each team (a team lead delegates to its workers, who coordinate P2P).

---

## Communication Protocols Between Agents

How do agents pass information to each other?

### Message Passing

Each agent communicates via explicit message objects. The orchestrator routes messages between agents.

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class AgentMessage:
    sender: str
    recipient: str
    task_id: str
    content: dict
    message_type: str  # "task_assignment", "result", "error", "query"
    timestamp: str
```

**Advantages:** Explicit interfaces, auditable, typed
**Disadvantages:** Verbose, requires message routing infrastructure

### Shared State

All agents read from and write to a shared state object. The state is the communication channel.

```python
# LangGraph uses this approach — the state is the "graph state"
class WorkflowState(TypedDict):
    goal: str
    research_results: list[str]
    draft: str
    critique: str
    final_output: str
    current_step: str
    errors: list[str]
```

**Advantages:** Simple to implement, natural for sequential pipelines
**Disadvantages:** Requires careful design to prevent agents from overwriting each other; less explicit than message passing

### Event-Driven (Pub/Sub)

Agents publish events and subscribe to events produced by other agents. No direct coupling between agents.

```
Research Agent publishes: ResearchCompleted(results=[...])
Writing Agent subscribes to: ResearchCompleted → triggers when research is done
Critic Agent subscribes to: DraftCompleted → triggers when writing is done
```

**Advantages:** Highly decoupled, good for asynchronous long-running systems
**Disadvantages:** Complex to reason about, event ordering issues, harder to debug

**Best for:** Long-running background systems, async processing pipelines.

---

## State Management

State is what enables an agentic system to do more than a single-turn agent. Without persistent state, every step starts from scratch.

### What State Needs to Contain

| State Component | Purpose |
|----------------|---------|
| Conversation history | Context for the LLM — what has been said and done |
| Tool results | Outputs from previous tool calls |
| Task ledger | List of planned subtasks + their status (pending/done/failed) |
| Intermediate outputs | Partial results from each agent |
| Error log | What has failed and why (for replanning) |
| Metadata | Task ID, timestamp, agent IDs, cost counter |

### Checkpointing

Checkpointing serializes the full agent state to persistent storage at each step (or at defined intervals). If the system crashes, it restores from the last checkpoint and continues.

```python
import json
from pathlib import Path

def save_checkpoint(state: dict, task_id: str, step: int):
    checkpoint = {"task_id": task_id, "step": step, "state": state}
    Path(f"checkpoints/{task_id}_step{step}.json").write_text(json.dumps(checkpoint))

def load_latest_checkpoint(task_id: str) -> dict | None:
    checkpoints = sorted(Path("checkpoints").glob(f"{task_id}_step*.json"))
    if not checkpoints:
        return None
    return json.loads(checkpoints[-1].read_text())
```

LangGraph has built-in checkpointing via `MemorySaver` and `SqliteSaver` backends.

### Context Summarization

Long-running agents accumulate conversation history that eventually exceeds the context window. Summarize older history to prevent this.

```
Step 1-10: Full history in context
Step 11: Summarize steps 1-5 into a compact summary; keep steps 6-11 in full
Step 16: Summarize steps 6-10 into a compact summary; keep steps 11-16 in full
```

The summary must preserve the key facts, decisions, and tool results — not just "some work was done."

### Task Ledger

A task ledger is a structured record of planned subtasks, their status, and their outputs. It survives context summarization because it's a separate data structure, not embedded in conversation history.

```python
@dataclass
class Subtask:
    id: str
    description: str
    status: str  # "pending", "in_progress", "done", "failed"
    dependencies: list[str]  # ids of subtasks that must complete first
    output: dict | None = None
    error: str | None = None

@dataclass
class TaskLedger:
    task_id: str
    goal: str
    subtasks: list[Subtask]

    def next_executable(self) -> list[Subtask]:
        done_ids = {t.id for t in self.subtasks if t.status == "done"}
        return [t for t in self.subtasks if t.status == "pending"
                and all(dep in done_ids for dep in t.dependencies)]
```

---

## Failure Modes and Resilience

Multi-agent systems fail in ways that single agents don't. Understanding the failure modes is prerequisite to building resilient systems.

### Failure Mode Taxonomy

**Cascading failure**
Agent A fails → passes error output to Agent B → Agent B produces bad output → Agent C receives bad input → system produces wrong final answer with no indication of failure.

*Prevention:* Each agent validates its inputs. Propagate errors explicitly, not silently. Have the orchestrator detect error outputs and halt or reroute.

**Infinite loop**
Agent A produces output → Critic rejects it → Agent A revises → Critic rejects again → ... forever.

*Prevention:* Always set `max_iterations`. Track iteration count in state and terminate with a "max iterations reached" output rather than silently looping.

**Context drift**
As conversation history grows, the agent starts losing track of the original goal. Later reasoning contradicts earlier reasoning.

*Prevention:* Keep the goal statement in a fixed position in the prompt (system message or beginning of each user message). Use a task ledger as the source of truth for what remains to be done.

**Tool call hallucination**
Agent calls a tool with incorrect arguments (hallucinated parameter values), gets an error or unexpected result, and doesn't recognize that the tool result is wrong.

*Prevention:* Validate tool arguments before execution. Return structured errors that describe what went wrong. Log the actual tool call and result for debugging.

**Agent deadlock**
Agent A is waiting for Agent B's output; Agent B is waiting for Agent A's output. Neither proceeds.

*Prevention:* Define a strict dependency graph upfront. Circular dependencies should be caught at design time. Each agent should have a timeout that triggers an error if its dependencies don't complete in time.

**Conflicting agents**
Two agents independently reach different conclusions and both write to the same output field, with one overwriting the other.

*Prevention:* Use append-only state for intermediate results. Have the orchestrator or a synthesis agent explicitly merge conflicting outputs rather than last-write-wins.

### Resilience Patterns

**Bounded autonomy**

```python
AGENT_LIMITS = {
    "max_steps": 20,
    "max_time_seconds": 300,
    "max_cost_usd": 0.50,
    "max_retries": 3,
}
```

**Idempotent actions**

Design tools so that calling the same tool with the same arguments multiple times is safe.

```python
@tool
def create_user(email: str) -> dict:
    """Create a user. Safe to retry — returns existing user if already exists."""
    existing = db.users.find_one({"email": email})
    if existing:
        return {"user_id": existing["id"], "created": False}
    new_user = db.users.insert({"email": email})
    return {"user_id": new_user["id"], "created": True}
```

**Fallback agents**

```python
def get_research_results(query: str) -> dict:
    try:
        return primary_research_agent.run(query)
    except AgentError:
        return fallback_research_agent.run(query)  # simpler, more reliable
```

**Graceful degradation**

Return a partial result with metadata about what succeeded and failed, rather than returning nothing.

```python
final_output = {
    "research": research_result or "Research failed — see errors",
    "analysis": analysis_result or "Analysis skipped due to research failure",
    "errors": [str(e) for e in errors],
    "completeness": "partial" if errors else "complete"
}
```

---

## Study Notes

- Multi-agent is not always better. The overhead of coordination (extra LLM calls, state management, error handling) is real. Measure whether the multi-agent version actually outperforms a well-designed single agent for your specific task.
- Start with **centralized coordination** (orchestrator-subagent). It's much easier to debug and reason about. Move to decentralized only if you have a specific reason.
- The task ledger pattern is underused. It gives you replanning capability for free — if the orchestrator knows what's been done and what remains, it can update the plan when something goes wrong.
- Every multi-agent system needs **structured communication interfaces** (typed outputs from each agent). Unstructured handoffs (agent A just returns a paragraph that agent B has to parse) are a major source of bugs.
- Design for failure from the start. Cascading failures are the most common production issue in multi-agent systems, and they're cheap to prevent if the defensive patterns are built in from day one.

---

## Interview Questions

**Q1: What are the four reasons to go multi-agent, and what mistake do teams most often make when choosing this architecture?** `[Medium]`
A: The four reasons are: Task Decomposition (the task has natural seams that benefit from focused sub-tasks), Specialization (different agents optimized with different prompts, models, and tools outperform a generalist), Parallelism (independent subtasks running concurrently reduce wall-clock time), and Fault Isolation (one agent's failure doesn't crash the whole system). The most common mistake is choosing multi-agent because it sounds more capable, without checking whether the overhead of coordination — extra LLM calls, state management, structured communication, error handling — actually produces better results than a well-designed single agent. Always measure whether the multi-agent version outperforms the single-agent version on your specific task before committing to the complexity.

**Q2: What is cascading failure in multi-agent systems and what are the two primary defenses?** `[Hard]`
A: Cascading failure is when Agent A fails and passes a bad output silently to Agent B, which produces a worse output, which is passed to Agent C — resulting in a wrong final answer with no visible error. The system appears to complete successfully while all downstream results are garbage. The two primary defenses are: (1) explicit error propagation — each agent validates its inputs and returns a typed error if they are malformed, rather than trying to process bad data; (2) orchestrator error detection — the orchestrator compares each subagent's output against expected structure before passing it downstream, halting or rerouting rather than blindly continuing. These defenses are cheap to implement at design time and expensive to retrofit after a production incident.

**Q3: Compare centralized (orchestrator) vs decentralized (peer-to-peer) coordination.** `[Medium]`
A: Centralized: one orchestrator holds the plan and assigns tasks; agents are stateless workers with no knowledge of the broader plan. Advantages — easy to reason about, easy to debug (single trace), easy to add HITL gates. Disadvantages — orchestrator is a single point of failure and a bottleneck. Decentralized: agents observe shared state and self-assign work; coordination emerges from agent behavior. Advantages — no single point of failure, scales to many agents, self-organizing. Disadvantages — race conditions, harder to add HITL, much harder to debug. Use centralized for almost all production systems; use decentralized only when you have a specific fault-tolerance requirement and the team has experience debugging distributed systems.

**Q4: What is a task ledger and why is it critical for long-running agentic systems?** `[Hard]`
A: A task ledger is a structured, external-to-context-window record of all planned subtasks, their status (pending/in-progress/done/failed), their dependencies, and their outputs. It's critical because conversation history eventually exceeds the context window and gets summarized or truncated — the task ledger is never summarized, so the agent always knows exactly what remains to be done and what has been completed. It also enables replanning: if a subtask fails, the orchestrator reads the ledger to determine what was completed, updates the remaining plan, and continues — without losing work done so far. The ledger is the difference between an agent that can recover from failure and one that has to start over from scratch.

**Q5: What is an idempotent action and give an example of making a non-idempotent tool idempotent?** `[Medium]`
A: An idempotent action produces the same result whether executed once or multiple times with the same inputs. It's critical for agentic systems because agents retry on failure — if a tool creates a duplicate record each time it's called, retries cause data corruption. Example: a `create_user(email)` tool is non-idempotent by default (multiple calls create duplicate users). To make it idempotent: before inserting, check if a user with that email already exists; if yes, return the existing user record; if no, create and return the new user. The check-then-act pattern, upserts, and idempotency keys (unique per task+step token sent with each API request) are the standard implementation approaches.

**Q6: Why do agents using event-driven (pub/sub) communication need special care compared to shared state?** `[Hard]`
A: Event-driven communication is highly decoupled — agents publish events and subscribe to events from others, with no direct coupling. This is ideal for long-running async systems and horizontal scaling. However, it introduces event ordering challenges (an agent may receive events out of order), duplicate event delivery (message brokers guarantee at-least-once delivery, not exactly-once), and complex debugging (there's no single trace to follow — you must reconstruct the sequence from distributed logs). You also lose the natural barrier checking of shared state (where you can easily see what's been written). Use event-driven when you need async processing, true decoupling, or need to fan out to many consumers; use shared state for simpler synchronous pipelines where debuggability is more important than decoupling.
