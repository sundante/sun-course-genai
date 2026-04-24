# GenAI Learning Curriculum

> Self-paced, beginner-to-advanced coverage of the full modern GenAI stack —  
> from foundational language models through fully autonomous agentic systems.

---

## The Stack

Every layer builds on the one before it:

[01 LLMs](01-LLM-Models/INDEX.md) → [02 Prompts](02-Prompts/INDEX.md) → [03 RAG](03-RAGs/INDEX.md) → [04 MCP](04-MCP/INDEX.md) → [05 Agents](05-Agents/INDEX.md) → [06 Agentic AI](06-Agentic-AI/INDEX.md)

*Engine · Interface · Memory · Protocol · Actors · Systems*

| Layer | What it does |
|-------|-------------|
| **LLMs** | The engine — a model that predicts the next token |
| **Prompts** | The interface — communicating intent precisely |
| **RAG** | The memory — injecting external knowledge at query time |
| **MCP** | The protocol — standardizing how tools connect to any model |
| **Agents** | The actors — LLMs that loop, use tools, and take multi-step action |
| **Agentic AI** | The systems — multiple agents coordinating autonomously |

---

## Curriculum Topics

| # | Topic | What You'll Learn | Notes | Code Labs | Q&A |
|---|-------|------------------|-------|-----------|-----|
| 01 | [LLM Models](01-LLM-Models/INDEX.md) | Transformers, attention, KV cache, training, fine-tuning, GPU, production | 12 | — | 68+ |
| 02 | [Prompt Engineering](02-Prompts/INDEX.md) | Zero-shot → chain-of-thought → meta-prompting, production patterns | 4 | — | ✓ |
| 03 | [RAG](03-RAGs/INDEX.md) | Embeddings, chunking, retrieval, evaluation, Vertex AI, scaling | 12 | — | 80+ |
| 04 | [MCP](04-MCP/INDEX.md) | Protocol definition, components, architecture, getting started | 8 | — | ✓ |
| 05 | [Agents](05-Agents/INDEX.md) | Agent fundamentals + ADK, LangChain, LangGraph, CrewAI deep-dives | 10 | [Agent Types](05-Agents/CodeLabs/01-Agent-Types.md) | ✓ |
| 06 | [Agentic AI](06-Agentic-AI/INDEX.md) | Multi-agent systems, architectural & design patterns, evaluation | 6 | [Architectures](06-Agentic-AI/CodeLabs/02-Architectures.md) · [Systems](06-Agentic-AI/CodeLabs/03-Agentic-Systems.md) | ✓ |

---

## Code Labs

Hands-on practice across three dimensions — every pattern implemented in all four frameworks (**ADK · LangChain · LangGraph · CrewAI**) using the same task for direct side-by-side comparison.

### Dimension 1 — Agent Evolution
> → [05-Agents: Code Labs → Agent Types](05-Agents/CodeLabs/01-Agent-Types.md)

Build progressively more capable agents in all four frameworks:

| Level | What You Build |
|-------|---------------|
| Simple | ReAct loop + tools |
| Intermediate | Memory, context tracking |
| Complex | Planning, reflection, multi-step reasoning |

### Dimension 2 — Architecture Patterns
> → [06-Agentic AI: Code Labs → Architecture Patterns](06-Agentic-AI/CodeLabs/02-Architectures.md)

Seven coordination patterns, each implemented × 4 frameworks:

| Pattern | Key Concept |
|---------|------------|
| Sequential | Agents run in strict order |
| Parallel | Agents run concurrently, results merged |
| Hierarchical | Supervisor delegates to sub-agents |
| Orchestrator-Subagent | Central planner + specialized workers |
| Pipeline | Output of one agent feeds the next |
| Adversarial Debate | Two agents argue; a judge decides |
| Reflexion | Agent critiques and rewrites its own output |

### Dimension 3 — End-to-End Systems
> → [06-Agentic AI: Code Labs → Agentic Systems](06-Agentic-AI/CodeLabs/03-Agentic-Systems.md)

Four production-style systems, each × 4 frameworks:

| System | What It Does |
|--------|-------------|
| Research Assistant | Web search + synthesis + structured report |
| Document Processor | Ingest → extract → summarize → classify |
| Autonomous Task Planner | Break goal → plan steps → execute → adapt |
| Code Review System | Analyze → critique → suggest → validate |

### Framework Comparison

| Framework | Mental Model | Best For |
|-----------|-------------|---------|
| **Google ADK** | Agent as a configurable object | GCP-native, Vertex AI, production |
| **LangChain** | Chain of callables (LCEL) | Flexibility, broad ecosystem |
| **LangGraph** | State machine / graph | Stateful flows, cycles, branching |
| **CrewAI** | Role-playing crew | Multi-agent collaboration, readable code |

---

## Learning Paths

### Path A — Conceptual (new to GenAI)

1. [LLM Fundamentals](01-LLM-Models/Notes/01-LLM-Fundamentals.md)
2. [Transformer Architecture](01-LLM-Models/Notes/02-Architecture.md)
3. [Attention Mechanisms](01-LLM-Models/Notes/03-Attention-Mechanisms.md)
4. [Prompt Basics](02-Prompts/Notes/01-Prompt-Basics.md)
5. [Core Techniques](02-Prompts/Notes/02-Core-Techniques.md)
6. [RAG Fundamentals](03-RAGs/Notes/01-RAG-Fundamentals.md)

### Path B — Interview Preparation

1. [LLM Models](01-LLM-Models/INDEX.md) — all 12 notes
2. [RAG](03-RAGs/INDEX.md) — all 12 notes
3. [Agent Fundamentals](05-Agents/Notes/01-Agent-Fundamentals.md)
4. [Agentic Concepts](06-Agentic-AI/Notes/01-Agentic-Concepts.md)
5. [Architectural Patterns](06-Agentic-AI/Notes/06-Architectural-Patterns.md)
6. [All Q&A — Knowledge Check](All_Questions.md)

### Path C — Hands-On Engineering

1. [Agent Types Code Lab](05-Agents/CodeLabs/01-Agent-Types.md) — simple → intermediate → complex
2. [Architecture Patterns Code Lab](06-Agentic-AI/CodeLabs/02-Architectures.md) — 7 patterns × 4 frameworks
3. [Agentic Systems Code Lab](06-Agentic-AI/CodeLabs/03-Agentic-Systems.md) — 4 end-to-end systems

### Path D — Full Sequence (recommended)

1. [LLM Fundamentals](01-LLM-Models/Notes/01-LLM-Fundamentals.md)
2. [Transformer Architecture](01-LLM-Models/Notes/02-Architecture.md)
3. [Prompt Basics](02-Prompts/Notes/01-Prompt-Basics.md) → [Core Techniques](02-Prompts/Notes/02-Core-Techniques.md)
4. [RAG Fundamentals](03-RAGs/Notes/01-RAG-Fundamentals.md) → [Embeddings & Vector Stores](03-RAGs/Notes/02-Embeddings-and-Vector-Stores.md)
5. [MCP — The Problem](04-MCP/Notes/01-The-Problem.md) → [MCP — Components](04-MCP/Notes/04-Components.md)
6. [Agent Fundamentals](05-Agents/Notes/01-Agent-Fundamentals.md) → [Agent Patterns](05-Agents/Notes/02-Agent-Patterns.md)
7. [LangGraph Fundamentals](05-Agents/LangGraph/01-LangGraph-Fundamentals.md) ← pick one framework
8. [Agent Types Code Lab](05-Agents/CodeLabs/01-Agent-Types.md)
9. [Agentic Concepts](06-Agentic-AI/Notes/01-Agentic-Concepts.md) → [Architectural Patterns](06-Agentic-AI/Notes/06-Architectural-Patterns.md)
10. [Architecture Patterns Code Lab](06-Agentic-AI/CodeLabs/02-Architectures.md)
11. [All Q&A — Knowledge Check](All_Questions.md)

---

## Knowledge Check

All concept review Q&A by topic:

| Topic | Link |
|-------|------|
| All topics (single file) | [All Questions](All_Questions.md) |
| LLM Models | [LLM Models Q&A](Interview-Questions/01-LLM-Models.md) |
| Prompt Engineering | [Prompts Q&A](Interview-Questions/02-Prompt-Engineering.md) |
| RAG | [RAG Q&A](Interview-Questions/03-RAGs.md) |
| MCP | [MCP Q&A](Interview-Questions/04-MCP.md) |
| Agents | [Agents Q&A](Interview-Questions/05-Agents.md) |
| Agentic AI | [Agentic AI Q&A](Interview-Questions/06-Agentic-AI.md) |

---

## Quick Start

### Notes — no setup needed

```bash
pip install mkdocs-material
mkdocs serve
# → http://127.0.0.1:8000
```

### Code Labs

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r setup/requirements.txt
cp setup/.env.example .env
# Edit .env → set GOOGLE_API_KEY
jupyter notebook docs/05-Agents/CodeLabs/01-Agent-Types/ADK/01-simple/agent.ipynb
```

---

Found this useful? Star the repo — it helps others discover it.  
**[★ Star sundante/sun-course-genai on GitHub](https://github.com/sundante/sun-course-genai)**
