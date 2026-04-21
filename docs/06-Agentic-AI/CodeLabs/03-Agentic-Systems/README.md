# 03 — Agentic Systems

End-to-end system designs that combine multiple architectural and design patterns into complete, production-like agentic applications. Each system is implemented in all four frameworks.

## What Makes These Different from 02-Architectures

| 02-Architectures | 03-Agentic-Systems |
|-----------------|-------------------|
| Demonstrates one pattern in isolation | Combines multiple patterns into a complete system |
| Minimal, focused examples | Full workflows with realistic agents and tasks |
| Shows HOW a pattern works | Shows HOW to build a system that solves a real problem |

## Systems

| # | System | Patterns Used | Complexity |
|---|--------|--------------|------------|
| [01-Research-Assistant](01-Research-Assistant/README.md) | Multi-topic research → synthesis → critique → report | Orchestrator-Subagent + Parallel + Reflexion | ★★★ |
| [02-Document-Processor](02-Document-Processor/README.md) | Classify → extract → validate → route + HITL gate | Pipeline + Conditional Routing + HITL | ★★★ |
| [03-Autonomous-Task-Planner](03-Autonomous-Task-Planner/README.md) | Goal decomposition → execute → monitor → replan | Plan-and-Execute + Hierarchical + Feedback Loop | ★★★ |
| [04-Code-Review-System](04-Code-Review-System/README.md) | Parallel specialized reviews → aggregate → prioritized report | Parallel Fan-out + Aggregation + Reflexion | ★★★ |

## Framework Implementations

Each system is implemented in all four frameworks:

| Framework | File | Notes |
|-----------|------|-------|
| LangChain | `LangChain/system.py` + `system.ipynb` | LCEL composition, AgentExecutor |
| LangGraph | `LangGraph/system.py` + `system.ipynb` | State graph, native parallelism, checkpointing |
| CrewAI | `CrewAI/system.py` + `system.ipynb` | Role-based agents, crew orchestration |
| ADK | `ADK/system.py` + `system.ipynb` | Google Cloud-native, SequentialAgent / ParallelAgent |

## Setup

```bash
cd setup/
pip install -r requirements.txt
cp .env.example .env
# Add your GOOGLE_API_KEY to .env
```

## How to Read These Examples

1. Read the system's `README.md` first — it explains the architecture, agent roles, and data flow
2. Run the LangGraph version for the clearest state visibility (state transitions are explicit)
3. Compare the CrewAI version to see the role-based approach to the same problem
4. The ADK version shows Google Cloud-native patterns

## Related Notes

- [06-Agentic-AI Notes](../../INDEX.md) — architectural patterns and system design concepts
- [02-Architectures](../02-Architectures/README.md) — individual pattern implementations
