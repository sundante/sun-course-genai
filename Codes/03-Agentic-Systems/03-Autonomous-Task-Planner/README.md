# Autonomous Task Planner System

An agentic system that takes a high-level goal, decomposes it into a structured plan, executes each subtask, monitors results, and replans when subtasks fail — until the goal is achieved or the system hits its limits.

## Architecture

```
Goal Input
    ↓
[Planner Agent] → Task Ledger (list of subtasks)
    ↓
[Executor] → Execute next ready subtask
    ↓
[Monitor Agent] → Check result quality
    ↓
  Result OK?
  ├── YES → Mark complete → next subtask
  └── NO  → [Replanner] → Update remaining plan → retry
    ↓ (all subtasks done)
[Synthesizer] → Final output
```

## Patterns Used

| Pattern | Where It Appears |
|---------|-----------------|
| Plan-and-Execute | Planner generates full task list before execution begins |
| Hierarchical | Planner → Monitor → Replanner forms a management layer above executors |
| Feedback Loop | Monitor evaluates each result and triggers replanning on failure |

## Agent Roles

| Agent | Role |
|-------|------|
| Planner | Decomposes goal into ordered, executable subtasks with dependencies |
| Executor | Executes one subtask at a time using available tools |
| Monitor | Evaluates subtask results for quality and goal alignment |
| Replanner | Updates the remaining plan when a subtask fails or the situation changes |
| Synthesizer | Assembles all subtask outputs into the final deliverable |

## Task Ledger

Each subtask has: `id`, `description`, `dependencies`, `status` (pending/done/failed), `output`, `tool_hint`.

```json
{
  "subtasks": [
    {"id": "1", "description": "Research current state", "status": "done"},
    {"id": "2", "description": "Analyze gaps", "status": "done", "depends_on": ["1"]},
    {"id": "3", "description": "Write recommendations", "status": "pending", "depends_on": ["2"]}
  ]
}
```

## What This Demonstrates

1. Explicit upfront planning (plan before executing)
2. Task dependency management (only execute when dependencies are met)
3. Monitor agent as quality gate between steps
4. Dynamic replanning when steps fail
5. Task ledger as resilient state (survives context compression)

## Implementations

- [LangChain](LangChain/system.py) — Plan-and-execute loop with conditional replanning
- [LangGraph](LangGraph/system.py) — State graph with planner → execute → monitor → replan loop
- [CrewAI](CrewAI/system.py) — Hierarchical crew with manager, executors, and quality reviewer
- [ADK](ADK/system.py) — SequentialAgent with feedback loop
