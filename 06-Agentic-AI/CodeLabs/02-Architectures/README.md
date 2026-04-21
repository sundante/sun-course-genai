# 02 — Agentic AI Architectures

## What This Section Teaches

How multiple agents coordinate to solve problems too complex for a single agent. Each pattern is implemented in all four frameworks using the **same mock task** — making the cross-framework comparison explicit.

---

## The Patterns

```
01 SEQUENTIAL           02 PARALLEL              03 HIERARCHICAL
─────────────           ───────────              ───────────────
[A]→[B]→[C]            [O]→[A1]                 [Manager]
                             →[A2] →[Merge]       ↙        ↘
                             →[A3]              [Lead1]   [Lead2]
                                                ↙  ↘      ↙   ↘
                                              [W1][W2]  [W3] [W4]

04 ORCHESTRATOR          05 PIPELINE             06 ADVERSARIAL
───────────────          ───────────             ──────────────
    [Plan]               [Extract]              [Proposer]
   /  |  \                  ↓                       ↓
[S1][S2][S3]            [Transform]            [Critic]
                            ↓                       ↓
                         [Load]                  [Judge]

07 REFLEXION
────────────
[Agent] → [Evaluator] → score < threshold → [Agent] (retry)
                      → score ≥ threshold → done
```

---

## Pattern Reference

| # | Pattern | When to Use | Key Mechanism |
|---|---|---|---|
| 01 | Sequential | Tasks with strict ordering/dependencies | Output of one = input of next |
| 02 | Parallel | Independent subtasks, need speedup | Fan-out + aggregation |
| 03 | Hierarchical | Large tasks with nested decomposition | Multi-level orchestration |
| 04 | Orchestrator-Subagent | Dynamic task delegation | Planner decides who does what |
| 05 | Pipeline | Pure data transformation chains | Stateless stages, no coordination |
| 06 | Adversarial/Debate | Need critical analysis or red-teaming | Opposing agents + judge |
| 07 | Reflexion | Quality-sensitive output, iterative improvement | Self-critique + retry loop |

---

## The Mock Task (same across all frameworks per pattern)

Each pattern uses a simple, consistent task so you can focus on the **architecture**, not the domain:

| Pattern | Mock Task |
|---|---|
| Sequential | Research topic → Summarize → Format as report |
| Parallel | 3 agents each research a different angle, 1 merges |
| Hierarchical | PM assigns to Dev subteam + QA subteam |
| Orchestrator | Planner delegates to Search agent, Code agent, Write agent |
| Pipeline | Extract raw data → Transform → Load into structured output |
| Adversarial | Proposer argues claim, Critic refutes, Judge decides |
| Reflexion | Agent writes answer, Evaluator scores, Agent retries if < 8/10 |

---

## Folder Structure

```
02-Architectures/
├── 01-Sequential/
│   ├── README.md          pattern explanation + ASCII diagram
│   ├── LangChain/         sequential.ipynb + sequential.py
│   ├── LangGraph/
│   ├── CrewAI/
│   └── ADK/
├── 02-Parallel/           same structure
├── 03-Hierarchical/
├── 04-Orchestrator-Subagent/
├── 05-Pipeline/
├── 06-Adversarial-Debate/
└── 07-Reflexion/
```

---

## Recommended Path

1. Start with **Sequential** (simplest coordination pattern)
2. Move to **Parallel** (introduces concurrency)
3. Then **Orchestrator-Subagent** (the most common production pattern)
4. Work through the rest in order
5. For each pattern, read all four framework implementations side-by-side
