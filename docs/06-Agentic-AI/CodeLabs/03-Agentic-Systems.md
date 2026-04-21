# Code Labs — 03: Agentic Systems

Four complete, end-to-end production-grade agentic systems. Each system combines multiple architectural patterns from [02 — Architecture Patterns](02-Architectures.md) into a realistic use case, implemented across all four frameworks.

**Notes companion:** [06 — Agentic AI: System Design](../Notes/05-Agentic-System-Design.md) · [Evaluation & Observability](../Notes/06-Evaluation-and-Observability.md)

---

## Systems Overview

```
01-Research-Assistant          02-Document-Processor
──────────────────────         ──────────────────────
Orchestrator-Subagent          Pipeline
+ Parallel fan-out             + Conditional Routing
+ Reflexion (quality gate)     + HITL (human approval)

↓ Use case:                    ↓ Use case:
Deep research with             Ingest, classify, extract,
multiple sub-researchers       and route documents

03-Autonomous-Task-Planner     04-Code-Review-System
──────────────────────────     ─────────────────────
Plan-and-Execute               Parallel fan-out
+ Feedback loop                + Aggregation
+ Dynamic replanning           + Reflexion

↓ Use case:                    ↓ Use case:
Break goals into plans,        Multi-perspective code
execute, and adapt             review with synthesis
```

---

## System Details

### 01 — Research Assistant

| Property | Detail |
|----------|--------|
| Patterns | Orchestrator-Subagent + Parallel + Reflexion |
| Use case | Given a research question, spawn specialist sub-researchers in parallel, aggregate findings, reflect on quality, produce final report |
| Complexity | Advanced |
| Files | `06-Agentic-AI/CodeLabs/03-Agentic-Systems/01-Research-Assistant/<Framework>/system.py` |

**Architecture flow:**
```
User query
    ↓
Orchestrator (plans sub-tasks)
    ├── Researcher-A (parallel) ── search + synthesize
    ├── Researcher-B (parallel) ── search + synthesize
    └── Researcher-C (parallel) ── search + synthesize
         ↓ aggregate
    Quality-Critic (Reflexion)
         ↓ revise if needed
    Final Report
```

---

### 02 — Document Processor

| Property | Detail |
|----------|--------|
| Patterns | Pipeline + Conditional Routing + HITL gate |
| Use case | Ingest documents, classify by type, extract structured data, route to appropriate workflow, pause for human approval on low-confidence cases |
| Complexity | Advanced |
| Files | `06-Agentic-AI/CodeLabs/03-Agentic-Systems/02-Document-Processor/<Framework>/system.py` |

**Architecture flow:**
```
Document input
    ↓
Stage 1: Ingestion + OCR
    ↓
Stage 2: Classification (contract / invoice / email / other)
    ↓
Stage 3: Conditional routing
    ├── High confidence → auto-process
    └── Low confidence → HITL approval gate
         ↓
Stage 4: Structured extraction
    ↓
Output store
```

---

### 03 — Autonomous Task Planner

| Property | Detail |
|----------|--------|
| Patterns | Plan-and-Execute + Feedback loop + Dynamic replanning |
| Use case | Accept a high-level goal, decompose into an executable plan, run each step, evaluate results, and replan when steps fail or produce unexpected output |
| Complexity | Advanced |
| Files | `06-Agentic-AI/CodeLabs/03-Agentic-Systems/03-Autonomous-Task-Planner/<Framework>/system.py` |

**Architecture flow:**
```
Goal input
    ↓
Planner (decompose into steps)
    ↓
Executor loop:
    ├── Execute step N
    ├── Evaluate output
    ├── If failed → Replanner → new sub-plan
    └── If done → next step
         ↓
Goal achieved / report
```

---

### 04 — Code Review System

| Property | Detail |
|----------|--------|
| Patterns | Parallel fan-out + Aggregation + Reflexion |
| Use case | Submit code for review; multiple specialist reviewers (security, performance, readability, correctness) run in parallel; results aggregated; Reflexion loop ensures completeness |
| Complexity | Advanced |
| Files | `06-Agentic-AI/CodeLabs/03-Agentic-Systems/04-Code-Review-System/<Framework>/system.py` |

**Architecture flow:**
```
Code submission
    ↓
Fan-out to reviewers (parallel):
    ├── Security-Reviewer
    ├── Performance-Reviewer
    ├── Readability-Reviewer
    └── Correctness-Reviewer
         ↓ aggregate findings
    Synthesis-Agent
         ↓ Reflexion (gap check)
    Final Review Report
```

---

## Framework Implementations

All 4 systems × all 4 frameworks = **16 total implementations**:

| System | LangChain | LangGraph | CrewAI | ADK |
|--------|-----------|-----------|--------|-----|
| Research Assistant | `system.py` | `system.py` | `system.py` | `system.py` |
| Document Processor | `system.py` | `system.py` | `system.py` | `system.py` |
| Autonomous Task Planner | `system.py` | `system.py` | `system.py` | `system.py` |
| Code Review System | `system.py` | `system.py` | `system.py` | `system.py` |

---

## Prerequisites

These systems assume familiarity with individual patterns. Complete these first:

1. [01 — Agent Types](../../05-Agents/CodeLabs/01-Agent-Types.md) — at least the Complex level
2. [02 — Architecture Patterns](02-Architectures.md) — at minimum: Parallel, Orchestrator-Subagent, Reflexion

---

## Getting Started

```bash
# Start with Research Assistant in LangGraph (cleanest state model for this use case)
python 06-Agentic-AI/CodeLabs/03-Agentic-Systems/01-Research-Assistant/LangGraph/system.py

# Or Code Review System in CrewAI (role-based structure fits naturally)
python 06-Agentic-AI/CodeLabs/03-Agentic-Systems/04-Code-Review-System/CrewAI/system.py
```

---

## What to Read Alongside

- [Agentic System Design](../Notes/05-Agentic-System-Design.md) — production architecture, HITL design, reliability, cost
- [Multi-Agent Systems](../Notes/04-Multi-Agent-Systems.md) — coordination protocols, shared state, failure modes
- [Evaluation and Observability](../Notes/06-Evaluation-and-Observability.md) — how to evaluate these systems end-to-end
