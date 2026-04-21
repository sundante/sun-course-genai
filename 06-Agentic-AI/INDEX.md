# 06 — Agentic AI

## What Is Agentic AI

Agentic AI refers to systems designed to pursue goals autonomously over extended horizons — combining planning, memory, tool use, and multi-agent coordination to solve complex, open-ended tasks.

## Scope of This Section

This section focuses on the *system-level* view: architectural patterns, design principles, and multi-agent coordination. For framework-specific implementations, see [05 — Agents](../05-Agents/INDEX.md). For end-to-end system design code examples, see [Code Labs — Agentic Systems](CodeLabs/03-Agentic-Systems.md).

## Chapter Map

| # | File | Topic | Difficulty |
|---|------|-------|------------|
| 1 | [Agentic Concepts](Notes/01-Agentic-Concepts.md) | Core vocabulary, autonomy spectrum, properties | ★★☆ |
| 2 | [Architectural Patterns](Notes/02-Architectural-Patterns.md) | 8 patterns, HITL, feedback loops, pattern selection | ★★★ |
| 3 | [Design Patterns](Notes/03-Design-Patterns.md) | Tool-use, reflection, planning, routing | ★★★ |
| 4 | [Multi-Agent Systems](Notes/04-Multi-Agent-Systems.md) | Coordination, communication, state, resilience | ★★★ |
| 5 | [Agentic System Design](Notes/05-Agentic-System-Design.md) | Production architecture, reliability, security, cost | ★★★ |
| 6 | [Evaluation and Observability](Notes/06-Evaluation-and-Observability.md) | Trajectory eval, metrics, tracing, debugging | ★★★ |
| 7 | [Interview Q&A](../Interview-Questions/06-Agentic-AI.md) | Conceptual, architecture, system design, evaluation | ★★★ |

## Relationship to Other Sections

- **05 — Agents**: How to build agents using specific frameworks (LangChain, LangGraph, CrewAI, ADK)
- **06 — Agentic AI**: How to design agentic *systems* — patterns, flows, failure modes, production engineering
- **[Code Labs — Architecture Patterns](CodeLabs/02-Architectures.md)**: Framework implementations of each architectural pattern
- **[Code Labs — Agentic Systems](CodeLabs/03-Agentic-Systems.md)**: End-to-end system designs combining multiple patterns

## Learning Paths

### Path A — Full Progression (recommended for interview prep)
Read chapters 1 → 2 → 3 → 4 → 5 → 6 in order, then do the Q&A. ~4–6 hours.

### Path B — Accelerated (familiar with agents already)
Skip chapter 1, read 2 → 3 → 4, skim 5 and 6. ~2 hours.

### Path C — System Design Focus
Read chapter 1 (vocabulary) → 5 (system design) → 2 (patterns to reference). ~1.5 hours.

### Path D — Code First
Browse [Code Labs — Agentic Systems](CodeLabs/03-Agentic-Systems.md), then read notes for concepts you encounter.

## Resources

- [Agentic Architectural Patterns](../Resources/06-Agentic-AI/Agentic_Architectural_Patterns_for_Building_Agent.pdf)
- [Agentic Design Patterns](../Resources/06-Agentic-AI/Agentic_Design_Patterns.pdf)
- [AI Agents vs Agentic AI](../Resources/06-Agentic-AI/AI_Agents_vs_Agentic_AI.pdf)

## Navigation

[Previous: 05 — Agents](../05-Agents/INDEX.md) | [Back to Master Index](../INDEX.md)
