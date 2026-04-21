# Code Labs — 02: Architecture Patterns

Seven multi-agent coordination patterns, each implemented in all four frameworks using the same mock task. Builds directly on [01 — Agent Types](../../05-Agents/CodeLabs/01-Agent-Types.md).

← **Back to Concepts:** [Architectural Patterns](../Notes/02-Architectural-Patterns.md)

---

## Pattern Overview

```
Sequential          Parallel            Hierarchical
A → B → C           A ─┬─ B             Orchestrator
(pipeline)            └─ C               ├── SubAgent-1
                        ↓                └── SubAgent-2
                      Aggregate               ↓
                                        SubAgent-3

Orchestrator-       Pipeline            Adversarial         Reflexion
Subagent            (data-flow)         Debate              (self-critique)
Planner             Stage1→Stage2       Proposer            Agent
  ├── Worker-1      (no shared state)   vs Critic           ↓ critique
  └── Worker-2                          → Judge             ↓ revise
                                                            ↓ done?
```

---

## Pattern Reference Table

| # | Pattern | Key Concept | When to Use | Notes Link |
|---|---------|------------|-------------|-----------|
| 01 | Sequential | A→B→C pipeline, output feeds next | Linear multi-step workflows | [Architectural Patterns](../Notes/02-Architectural-Patterns.md) |
| 02 | Parallel | Fan-out + aggregate | Independent subtasks, reduce latency | [Architectural Patterns](../Notes/02-Architectural-Patterns.md) |
| 03 | Hierarchical | Nested orchestration tiers | Complex delegation, team-of-teams | [Architectural Patterns](../Notes/02-Architectural-Patterns.md) |
| 04 | Orchestrator-Subagent | Planner + specialized workers | Dynamic task decomposition | [Architectural Patterns](../Notes/02-Architectural-Patterns.md) |
| 05 | Pipeline | Data-flow, no shared state | ETL-style transformation chains | [Architectural Patterns](../Notes/02-Architectural-Patterns.md) |
| 06 | Adversarial Debate | Proposer vs Critic vs Judge | High-stakes decisions, quality gates | [Architectural Patterns](../Notes/02-Architectural-Patterns.md) |
| 07 | Reflexion | Self-critique + iterative revision | Output quality, agentic planning | [Design Patterns](../Notes/03-Design-Patterns.md) |

---

## Files by Pattern and Framework

Each pattern lives in `06-Agentic-AI/CodeLabs/02-Architectures/<pattern-name>/<Framework>/`:

| Pattern | LangChain | LangGraph | CrewAI | ADK |
|---------|-----------|-----------|--------|-----|
| Sequential | `sequential.py` + `.ipynb` | same | same | same |
| Parallel | `parallel.py` + `.ipynb` | same | same | same |
| Hierarchical | `hierarchical.py` + `.ipynb` | same | same | same |
| Orchestrator-Subagent | `orchestrator.py` + `.ipynb` | same | same | same |
| Pipeline | `pipeline.py` + `.ipynb` | same | same | same |
| Adversarial-Debate | `debate.py` + `.ipynb` | same | same | same |
| Reflexion | `reflexion.py` + `.ipynb` | same | same | same |

**28 total implementations** — every pattern × every framework.

---

## Recommended Order

1. **Sequential** — start here; simplest pattern, clear A→B→C structure
2. **Parallel** — fan-out to multiple agents, then aggregate results
3. **Orchestrator-Subagent** — dynamic planning; the most commonly used pattern in production
4. **Hierarchical** — nested orchestration; builds on Orchestrator-Subagent
5. **Pipeline** — data-flow style; useful for ETL and document processing
6. **Adversarial-Debate** — quality through disagreement; challenging but powerful
7. **Reflexion** — self-improvement loop; combines with most other patterns

---

## Pattern Selection Guide

| Requirement | Recommended Pattern |
|------------|-------------------|
| Fixed sequence of steps | Sequential or Pipeline |
| Reduce wall-clock time | Parallel |
| Dynamic task decomposition | Orchestrator-Subagent |
| Multiple teams/layers | Hierarchical |
| High-quality output required | Adversarial-Debate or Reflexion |
| Iterative refinement | Reflexion |

---

## Getting Started

```bash
# Start with Sequential in LangGraph (most readable)
jupyter notebook 06-Agentic-AI/CodeLabs/02-Architectures/01-Sequential/LangGraph/sequential.ipynb

# Then compare the same pattern in CrewAI
jupyter notebook 06-Agentic-AI/CodeLabs/02-Architectures/01-Sequential/CrewAI/sequential.ipynb
```

---

## What to Read Alongside

- [Architectural Patterns](../Notes/02-Architectural-Patterns.md) — conceptual deep-dive on all 8 patterns
- [Design Patterns](../Notes/03-Design-Patterns.md) — tool-use, reflection, planning, routing
- [Multi-Agent Systems](../Notes/04-Multi-Agent-Systems.md) — coordination, state management, failure modes

---

## Next: Agentic Systems

After mastering individual patterns, see how they combine in [03 — Agentic Systems](03-Agentic-Systems.md) — full end-to-end production system designs.
