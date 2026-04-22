# 06 — Agentic AI

**Level:** Beginner to Advanced  
**Format:** Prose + code + Q&A pairs tagged `[Easy]` `[Medium]` `[Hard]`

---

## What You Will Learn

- What an AI agent actually is and how it differs from a chatbot or workflow
- How the agent loop works at the API level — what the LLM sees at every step
- How function calling works, how to design good tools, and how to handle failures
- The four memory types and how to manage context across long-horizon tasks
- Planning and reasoning strategies: ReAct, Plan-and-Execute, Tree of Thoughts, Reflexion
- The 8 architectural patterns and how to choose between them
- The 5 core design patterns used across virtually all production agents
- How multi-agent systems coordinate, communicate, and fail
- The four major agent frameworks (LangGraph, ADK, CrewAI, AutoGen) and when to use each
- Production system design: reliability, security, HITL, cost management
- Trajectory evaluation and observability — how to measure and debug agent behavior
- 40+ curated Q&A pairs covering all domains

---

## Chapter Map

| # | File | Topic | Level |
|---|------|-------|-------|
| 1 | [What Is an AI Agent](Notes/01-Agentic-Concepts.md) | Agent vs chatbot, autonomy spectrum, core properties, key vocabulary | ★★☆ Beginner |
| 2 | [The Agent Loop](Notes/02-The-Agent-Loop.md) | The core loop mechanics, what the LLM sees, ReAct, context growth, termination | ★★☆ Beginner |
| 3 | [Tool Use & Function Calling](Notes/03-Tool-Use-and-Function-Calling.md) | Function calling API, schema design, tool chaining, parallel calls, security | ★★★ Intermediate |
| 4 | [Memory & State](Notes/04-Memory-and-State.md) | 4 memory types, working memory, checkpointing, semantic memory, context management | ★★★ Intermediate |
| 5 | [Planning & Reasoning](Notes/05-Planning-and-Reasoning.md) | CoT, ReAct, Plan-and-Execute, Tree of Thoughts, FLARE, Reflexion, replanning | ★★★ Intermediate |
| 6 | [Architectural Patterns](Notes/06-Architectural-Patterns.md) | 8 patterns, HITL architectures, feedback loops, hybrid patterns, selection guide | ★★★ Intermediate |
| 7 | [Design Patterns](Notes/07-Design-Patterns.md) | Tool-use, Reflection, Planning, Coordination, Routing — behavior within patterns | ★★★ Intermediate |
| 8 | [Multi-Agent Systems](Notes/08-Multi-Agent-Systems.md) | Coordination strategies, communication protocols, state, failure modes, resilience | ★★★ Advanced |
| 9 | [Agent Frameworks](Notes/09-Agent-Frameworks.md) | LangGraph, ADK, CrewAI, AutoGen — internals, code examples, comparison matrix | ★★★ Intermediate |
| 10 | [Agentic System Design](Notes/10-Agentic-System-Design.md) | Production architecture, reliability engineering, security, cost, scalability | ★★★★ Advanced |
| 11 | [Evaluation & Observability](Notes/11-Evaluation-and-Observability.md) | Trajectory eval, LLM-as-judge, metrics, observability stack, debugging | ★★★ Advanced |
| 12 | [Q&A Review Bank](Notes/12-Interview-QA-Bank.md) | 40 questions across 8 domains — concepts through production engineering | ★★★ |

---

## Recommended Learning Paths

### Path A — Full Progression (beginner to interview-ready)
Read chapters in order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11, then work through [12-Interview-QA-Bank.md](Notes/12-Interview-QA-Bank.md). ~6–8 hours.

### Path B — Accelerated (already understand LLM basics)
1. [What Is an AI Agent](Notes/01-Agentic-Concepts.md) — vocabulary (30 min)
2. [The Agent Loop](Notes/02-The-Agent-Loop.md) — the mechanics (45 min)
3. [Tool Use & Function Calling](Notes/03-Tool-Use-and-Function-Calling.md) — building blocks (45 min)
4. [Architectural Patterns](Notes/06-Architectural-Patterns.md) — structure (45 min)
5. [Agentic System Design](Notes/10-Agentic-System-Design.md) — production (60 min)
6. [Q&A Review Bank](Notes/12-Interview-QA-Bank.md) — all 40 questions (90 min)

### Path C — System Design Focus
1. [What Is an AI Agent](Notes/01-Agentic-Concepts.md) — vocabulary
2. [The Agent Loop](Notes/02-The-Agent-Loop.md) — understand what you're designing
3. [Agentic System Design](Notes/10-Agentic-System-Design.md) — production architecture
4. [Architectural Patterns](Notes/06-Architectural-Patterns.md) — structure options
5. [Multi-Agent Systems](Notes/08-Multi-Agent-Systems.md) — coordination

### Path D — Framework Focus (building something now)
1. [The Agent Loop](Notes/02-The-Agent-Loop.md) — understand what frameworks wrap
2. [Tool Use & Function Calling](Notes/03-Tool-Use-and-Function-Calling.md) — tool design
3. [Agent Frameworks](Notes/09-Agent-Frameworks.md) — pick and use a framework
4. Browse [Code Labs — Agentic Systems](CodeLabs/03-Agentic-Systems.md)

### Path E — Weak spots only
- Don't know what an agent is → [01-Agentic-Concepts.md](Notes/01-Agentic-Concepts.md)
- Don't understand how the loop works → [02-The-Agent-Loop.md](Notes/02-The-Agent-Loop.md)
- Memory / state confusion → [04-Memory-and-State.md](Notes/04-Memory-and-State.md)
- Planning strategies → [05-Planning-and-Reasoning.md](Notes/05-Planning-and-Reasoning.md)
- Which framework to use → [09-Agent-Frameworks.md](Notes/09-Agent-Frameworks.md)
- Production system design → [10-Agentic-System-Design.md](Notes/10-Agentic-System-Design.md)
- Evaluation and debugging → [11-Evaluation-and-Observability.md](Notes/11-Evaluation-and-Observability.md)

---

## Relationship to Other Sections

| Section | What It Covers | Relationship to This Section |
|---------|---------------|------------------------------|
| [05 — Agents](../05-Agents/INDEX.md) | Framework-specific implementation (LangChain, LangGraph, CrewAI, ADK) | How to build — this section is how to design |
| [06 — Agentic AI] | System design, patterns, evaluation | System-level view — concepts through production |
| [Code Labs — Architecture Patterns](CodeLabs/02-Architectures.md) | Code implementations of the 8 architectural patterns | Executable versions of the patterns in chapter 6 |
| [Code Labs — Agentic Systems](CodeLabs/03-Agentic-Systems.md) | End-to-end system designs in 4 frameworks | Full implementations combining multiple concepts |
| [System Designs](SystemDesigns/insurance-claims-processor.md) | Production-grade system designs with GCP mapping | Applied versions of chapter 10 |

---

## Resources

- [Agentic Architectural Patterns](../Resources/06-Agentic-AI/Agentic_Architectural_Patterns_for_Building_Agent.pdf)
- [Agentic Design Patterns](../Resources/06-Agentic-AI/Agentic_Design_Patterns.pdf)
- [AI Agents vs Agentic AI](../Resources/06-Agentic-AI/AI_Agents_vs_Agentic_AI.pdf)

---

## Navigation

[Previous: 05 — Agents](../05-Agents/INDEX.md) | [Back to Master Index](../index.md)
