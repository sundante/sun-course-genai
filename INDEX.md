# GenAI Learning Curriculum

> Self-paced coverage of the full modern GenAI stack — from foundational models through autonomous agentic systems.

---

## Table of Contents

| # | Topic | Description |
|---|-------|-------------|
| [01](#01--llm-models) | LLM Models | Transformers, architecture, training, fine-tuning |
| [02](#02--prompt-engineering) | Prompt Engineering | Techniques, production patterns, advanced methods |
| [03](#03--rag) | RAG | Retrieval, embeddings, chunking, evaluation, scaling |
| [04](#04--mcp) | MCP | Protocol, architecture, components, getting started |
| [05](#05--agents) | Agents | Fundamentals + 4 frameworks (ADK, LangChain, LangGraph, CrewAI) |
| [06](#06--agentic-ai) | Agentic AI | Multi-agent systems, design & architectural patterns |
| [C](#codes) | Codes | Runnable implementations by agent type and architecture |
| [IQ](#interview-preparation) | Interview Prep | Consolidated Q&A per topic |
| [R](#resources) | Resources | PDFs and reference materials |

---

## Learning Path

```
01           02            03        04         05          06
LLMs    →  Prompts  →   RAGs   →  MCP    →  Agents  →  Agentic AI

Foundation  Interface  Knowledge  Protocol  Frameworks   Systems
```

---

## 01 — LLM Models

[Topic Index](Notes/01-LLM-Models/INDEX.md)

| # | File | Description |
|---|------|-------------|
| 1 | [LLM Fundamentals](Notes/01-LLM-Models/Notes/01-LLM-Fundamentals.md) | What LLMs are, types, tokens, context |
| 2 | [Architecture](Notes/01-LLM-Models/Notes/02-Architecture.md) | Transformers, attention, model families |
| 3 | [Training and Fine-Tuning](Notes/01-LLM-Models/Notes/03-Training-and-Finetuning.md) | Pre-training, RLHF, LoRA |
| 4 | [Prompting Strategies](Notes/01-LLM-Models/Notes/04-Prompting-Strategies.md) | Zero-shot, CoT, system prompts |

---

## 02 — Prompt Engineering

[Topic Index](Notes/02-Prompts/INDEX.md)

| # | File | Description |
|---|------|-------------|
| 1 | [Prompt Basics](Notes/02-Prompts/Notes/01-Prompt-Basics.md) | Anatomy, system vs user, mental model |
| 2 | [Core Techniques](Notes/02-Prompts/Notes/02-Core-Techniques.md) | Zero-shot, few-shot, CoT, ReAct |
| 3 | [Advanced Techniques](Notes/02-Prompts/Notes/03-Advanced-Techniques.md) | ToT, self-consistency, meta-prompting |
| 4 | [Prompts in Production](Notes/02-Prompts/Notes/04-Prompt-Engineering-for-Production.md) | Templates, versioning, injection, evals |

---

## 03 — RAG

[Topic Index](Notes/03-RAGs/INDEX.md)

| # | File | Description |
|---|------|-------------|
| 1 | [RAG Fundamentals](Notes/03-RAGs/Notes/01-RAG-Fundamentals.md) | Pipeline, RAG vs fine-tuning |
| 2 | [Embeddings and Vector Stores](Notes/03-RAGs/Notes/02-Embeddings-and-Vector-Stores.md) | Semantic search foundations |
| 3 | [Chunking and Indexing](Notes/03-RAGs/Notes/03-Chunking-and-Indexing.md) | Splitting and indexing strategies |
| 4 | [Retrieval Strategies](Notes/03-RAGs/Notes/04-Retrieval-Strategies.md) | Dense, sparse, hybrid, re-ranking |
| 5 | [Advanced RAG Patterns](Notes/03-RAGs/Notes/05-Advanced-RAG-Patterns.md) | Multi-query, self-RAG, GraphRAG |
| 6 | [Evaluation and Failure Modes](Notes/03-RAGs/Notes/06-RAG-Evaluation-and-Failure-Modes.md) | RAGAS, failures, observability |
| 7 | [RAG Types Taxonomy](Notes/03-RAGs/Notes/07-RAG-Types-Taxonomy.md) | Classification of RAG variants |
| 8 | [RAG System Design](Notes/03-RAGs/Notes/08-RAG-System-Design.md) | End-to-end design decisions |
| 9 | [Vertex AI RAG](Notes/03-RAGs/Notes/09-Vertex-AI-RAG.md) | GCP-native RAG implementation |
| 10 | [Production Deployment](Notes/03-RAGs/Notes/10-Production-Deployment.md) | Deployment patterns and ops |
| 11 | [Scaling and LLM Issues](Notes/03-RAGs/Notes/11-Scaling-and-LLM-Issues.md) | Scaling concerns and failure modes |
| 12 | [Interview Q&A Bank](Notes/03-RAGs/Notes/12-Interview-QA-Bank.md) | RAG-specific interview questions |

---

## 04 — MCP

[Topic Index](Notes/04-MCP/INDEX.md)

| # | File | Description |
|---|------|-------------|
| 1 | [The Problem](Notes/04-MCP/Notes/01-The-Problem.md) | Why MCP exists — the N×M integration problem |
| 2 | [Definition](Notes/04-MCP/Notes/02-Definition.md) | What MCP is |
| 3 | [The Solution](Notes/04-MCP/Notes/03-The-Solution.md) | How it works |
| 4 | [Components](Notes/04-MCP/Notes/04-Components.md) | Architecture |
| 5 | [Capabilities](Notes/04-MCP/Notes/05-Capabilities.md) | Use cases |
| 6 | [Why It Matters](Notes/04-MCP/Notes/06-Why-MCP-Matters.md) | Strategic value |
| 7 | [Architecture Deep-Dive](Notes/04-MCP/Notes/07-Architecture-Deep-Dive.md) | Technical internals |
| 8 | [Getting Started](Notes/04-MCP/Notes/08-Getting-Started.md) | Hands-on guide |

---

## 05 — Agents

[Topic Index](Notes/05-Agents/INDEX.md)

**Core Concepts**

| # | File | Description |
|---|------|-------------|
| 1 | [Agent Fundamentals](Notes/05-Agents/Notes/01-Agent-Fundamentals.md) | What agents are, the agent loop |
| 2 | [Agent Patterns](Notes/05-Agents/Notes/02-Agent-Patterns.md) | ReAct, plan-execute, reflection |

**Frameworks**

| Framework | Index | Fundamentals | Simple Agent | Complex Agent |
|-----------|-------|-------------|--------------|---------------|
| GCP ADK | [INDEX](Notes/05-Agents/GCP-ADK/INDEX.md) | [Fundamentals](Notes/05-Agents/GCP-ADK/01-ADK-Fundamentals.md) | [Simple](Notes/05-Agents/GCP-ADK/02-Simple-Agent.md) | [Complex](Notes/05-Agents/GCP-ADK/03-Complex-Agent.md) |
| LangChain | [INDEX](Notes/05-Agents/LangChain/INDEX.md) | [Fundamentals](Notes/05-Agents/LangChain/01-LangChain-Fundamentals.md) | [Simple](Notes/05-Agents/LangChain/02-Simple-Agent.md) | [Complex](Notes/05-Agents/LangChain/03-Complex-Agent.md) |
| LangGraph | [INDEX](Notes/05-Agents/LangGraph/INDEX.md) | [Fundamentals](Notes/05-Agents/LangGraph/01-LangGraph-Fundamentals.md) | [Simple](Notes/05-Agents/LangGraph/02-Simple-Agent.md) | [Complex](Notes/05-Agents/LangGraph/03-Complex-Agent.md) |
| CrewAI | [INDEX](Notes/05-Agents/CrewAI/INDEX.md) | [Fundamentals](Notes/05-Agents/CrewAI/01-CrewAI-Fundamentals.md) | [Simple](Notes/05-Agents/CrewAI/02-Simple-Agent.md) | [Complex](Notes/05-Agents/CrewAI/03-Complex-Agent.md) |

---

## 06 — Agentic AI

[Topic Index](Notes/06-Agentic-AI/INDEX.md)

| # | File | Description |
|---|------|-------------|
| 1 | [Agentic Concepts](Notes/06-Agentic-AI/Notes/01-Agentic-Concepts.md) | Core vocabulary, distinctions |
| 2 | [Architectural Patterns](Notes/06-Agentic-AI/Notes/02-Architectural-Patterns.md) | Orchestrator-subagent, HITL |
| 3 | [Design Patterns](Notes/06-Agentic-AI/Notes/03-Design-Patterns.md) | Tool-use, reflection, planning |
| 4 | [Multi-Agent Systems](Notes/06-Agentic-AI/Notes/04-Multi-Agent-Systems.md) | Coordination, communication |

---

## Codes

[Codes README](Codes/README.md) · [Setup](Codes/setup/) · [Environment](Codes/setup/.env.example) · [Requirements](Codes/setup/requirements.txt)

**01 — Agent Types** — [README](Codes/01-Agent-Types/README.md)

Each framework implemented at three complexity levels (simple / intermediate / complex).

| Framework | Simple | Intermediate | Complex |
|-----------|--------|--------------|---------|
| ADK | [agent.py](Codes/01-Agent-Types/ADK/01-simple/agent.py) · [.ipynb](Codes/01-Agent-Types/ADK/01-simple/agent.ipynb) | [agent.py](Codes/01-Agent-Types/ADK/02-intermediate/agent.py) · [.ipynb](Codes/01-Agent-Types/ADK/02-intermediate/agent.ipynb) | [agent.py](Codes/01-Agent-Types/ADK/03-complex/agent.py) · [.ipynb](Codes/01-Agent-Types/ADK/03-complex/agent.ipynb) |
| LangChain | [agent.py](Codes/01-Agent-Types/LangChain/01-simple/agent.py) · [.ipynb](Codes/01-Agent-Types/LangChain/01-simple/agent.ipynb) | [agent.py](Codes/01-Agent-Types/LangChain/02-intermediate/agent.py) · [.ipynb](Codes/01-Agent-Types/LangChain/02-intermediate/agent.ipynb) | [agent.py](Codes/01-Agent-Types/LangChain/03-complex/agent.py) · [.ipynb](Codes/01-Agent-Types/LangChain/03-complex/agent.ipynb) |
| LangGraph | [agent.py](Codes/01-Agent-Types/LangGraph/01-simple/agent.py) · [.ipynb](Codes/01-Agent-Types/LangGraph/01-simple/agent.ipynb) | [agent.py](Codes/01-Agent-Types/LangGraph/02-intermediate/agent.py) · [.ipynb](Codes/01-Agent-Types/LangGraph/02-intermediate/agent.ipynb) | [agent.py](Codes/01-Agent-Types/LangGraph/03-complex/agent.py) · [.ipynb](Codes/01-Agent-Types/LangGraph/03-complex/agent.ipynb) |
| CrewAI | [agent.py](Codes/01-Agent-Types/CrewAI/01-simple/agent.py) · [.ipynb](Codes/01-Agent-Types/CrewAI/01-simple/agent.ipynb) | [agent.py](Codes/01-Agent-Types/CrewAI/02-intermediate/agent.py) · [.ipynb](Codes/01-Agent-Types/CrewAI/02-intermediate/agent.ipynb) | [agent.py](Codes/01-Agent-Types/CrewAI/03-complex/agent.py) · [.ipynb](Codes/01-Agent-Types/CrewAI/03-complex/agent.ipynb) |

**02 — Architectures** — [README](Codes/02-Architectures/README.md)

Each architecture implemented across all four frameworks.

| Architecture | README | ADK | LangChain | LangGraph | CrewAI |
|--------------|--------|-----|-----------|-----------|--------|
| Sequential | [README](Codes/02-Architectures/01-Sequential/README.md) | [.py](Codes/02-Architectures/01-Sequential/ADK/sequential.py) · [.ipynb](Codes/02-Architectures/01-Sequential/ADK/sequential.ipynb) | [.py](Codes/02-Architectures/01-Sequential/LangChain/sequential.py) · [.ipynb](Codes/02-Architectures/01-Sequential/LangChain/sequential.ipynb) | [.py](Codes/02-Architectures/01-Sequential/LangGraph/sequential.py) · [.ipynb](Codes/02-Architectures/01-Sequential/LangGraph/sequential.ipynb) | [.py](Codes/02-Architectures/01-Sequential/CrewAI/sequential.py) · [.ipynb](Codes/02-Architectures/01-Sequential/CrewAI/sequential.ipynb) |
| Parallel | [README](Codes/02-Architectures/02-Parallel/README.md) | [.py](Codes/02-Architectures/02-Parallel/ADK/parallel.py) · [.ipynb](Codes/02-Architectures/02-Parallel/ADK/parallel.ipynb) | [.py](Codes/02-Architectures/02-Parallel/LangChain/parallel.py) · [.ipynb](Codes/02-Architectures/02-Parallel/LangChain/parallel.ipynb) | [.py](Codes/02-Architectures/02-Parallel/LangGraph/parallel.py) · [.ipynb](Codes/02-Architectures/02-Parallel/LangGraph/parallel.ipynb) | [.py](Codes/02-Architectures/02-Parallel/CrewAI/parallel.py) · [.ipynb](Codes/02-Architectures/02-Parallel/CrewAI/parallel.ipynb) |
| Hierarchical | [README](Codes/02-Architectures/03-Hierarchical/README.md) | [.py](Codes/02-Architectures/03-Hierarchical/ADK/hierarchical.py) · [.ipynb](Codes/02-Architectures/03-Hierarchical/ADK/hierarchical.ipynb) | [.py](Codes/02-Architectures/03-Hierarchical/LangChain/hierarchical.py) · [.ipynb](Codes/02-Architectures/03-Hierarchical/LangChain/hierarchical.ipynb) | [.py](Codes/02-Architectures/03-Hierarchical/LangGraph/hierarchical.py) · [.ipynb](Codes/02-Architectures/03-Hierarchical/LangGraph/hierarchical.ipynb) | [.py](Codes/02-Architectures/03-Hierarchical/CrewAI/hierarchical.py) · [.ipynb](Codes/02-Architectures/03-Hierarchical/CrewAI/hierarchical.ipynb) |
| Orchestrator-Subagent | [README](Codes/02-Architectures/04-Orchestrator-Subagent/README.md) | [.py](Codes/02-Architectures/04-Orchestrator-Subagent/ADK/orchestrator.py) · [.ipynb](Codes/02-Architectures/04-Orchestrator-Subagent/ADK/orchestrator.ipynb) | [.py](Codes/02-Architectures/04-Orchestrator-Subagent/LangChain/orchestrator.py) · [.ipynb](Codes/02-Architectures/04-Orchestrator-Subagent/LangChain/orchestrator.ipynb) | [.py](Codes/02-Architectures/04-Orchestrator-Subagent/LangGraph/orchestrator.py) · [.ipynb](Codes/02-Architectures/04-Orchestrator-Subagent/LangGraph/orchestrator.ipynb) | [.py](Codes/02-Architectures/04-Orchestrator-Subagent/CrewAI/orchestrator.py) · [.ipynb](Codes/02-Architectures/04-Orchestrator-Subagent/CrewAI/orchestrator.ipynb) |
| Pipeline | [README](Codes/02-Architectures/05-Pipeline/README.md) | [.py](Codes/02-Architectures/05-Pipeline/ADK/pipeline.py) · [.ipynb](Codes/02-Architectures/05-Pipeline/ADK/pipeline.ipynb) | [.py](Codes/02-Architectures/05-Pipeline/LangChain/pipeline.py) · [.ipynb](Codes/02-Architectures/05-Pipeline/LangChain/pipeline.ipynb) | [.py](Codes/02-Architectures/05-Pipeline/LangGraph/pipeline.py) · [.ipynb](Codes/02-Architectures/05-Pipeline/LangGraph/pipeline.ipynb) | [.py](Codes/02-Architectures/05-Pipeline/CrewAI/pipeline.py) · [.ipynb](Codes/02-Architectures/05-Pipeline/CrewAI/pipeline.ipynb) |
| Adversarial Debate | [README](Codes/02-Architectures/06-Adversarial-Debate/README.md) | [.py](Codes/02-Architectures/06-Adversarial-Debate/ADK/debate.py) · [.ipynb](Codes/02-Architectures/06-Adversarial-Debate/ADK/debate.ipynb) | [.py](Codes/02-Architectures/06-Adversarial-Debate/LangChain/debate.py) · [.ipynb](Codes/02-Architectures/06-Adversarial-Debate/LangChain/debate.ipynb) | [.py](Codes/02-Architectures/06-Adversarial-Debate/LangGraph/debate.py) · [.ipynb](Codes/02-Architectures/06-Adversarial-Debate/LangGraph/debate.ipynb) | [.py](Codes/02-Architectures/06-Adversarial-Debate/CrewAI/debate.py) · [.ipynb](Codes/02-Architectures/06-Adversarial-Debate/CrewAI/debate.ipynb) |
| Reflexion | [README](Codes/02-Architectures/07-Reflexion/README.md) | [.py](Codes/02-Architectures/07-Reflexion/ADK/reflexion.py) · [.ipynb](Codes/02-Architectures/07-Reflexion/ADK/reflexion.ipynb) | [.py](Codes/02-Architectures/07-Reflexion/LangChain/reflexion.py) · [.ipynb](Codes/02-Architectures/07-Reflexion/LangChain/reflexion.ipynb) | [.py](Codes/02-Architectures/07-Reflexion/LangGraph/reflexion.py) · [.ipynb](Codes/02-Architectures/07-Reflexion/LangGraph/reflexion.ipynb) | [.py](Codes/02-Architectures/07-Reflexion/CrewAI/reflexion.py) · [.ipynb](Codes/02-Architectures/07-Reflexion/CrewAI/reflexion.ipynb) |

---

## Interview Preparation

[All Questions (consolidated)](Notes/All_Questions.md) · [Interview Questions Index](Notes/Interview-Questions/INDEX.md)

| Topic | File |
|-------|------|
| LLM Models | [01-LLM-Models.md](Notes/Interview-Questions/01-LLM-Models.md) |
| Prompt Engineering | [02-Prompt-Engineering.md](Notes/Interview-Questions/02-Prompt-Engineering.md) |
| RAGs | [03-RAGs.md](Notes/Interview-Questions/03-RAGs.md) |
| MCP | [04-MCP.md](Notes/Interview-Questions/04-MCP.md) |
| Agents | [05-Agents.md](Notes/Interview-Questions/05-Agents.md) |
| Agentic AI | [06-Agentic-AI.md](Notes/Interview-Questions/06-Agentic-AI.md) |

---

## Resources

[Resources Index](Notes/Resources/INDEX.md)

| File | Topic |
|------|-------|
| [Gemma Handbook](Notes/Resources/01-LLM-Models/Gemma-Handbook.pdf) | LLM Models |
| [Building Applications with AI Agents](Notes/Resources/05-Agents/Building_Applications_with_AI_Agents.pdf) | Agents |
| [ReAct Paper](Notes/Resources/05-Agents/REACT-SYNERGIZING-REASONING-AND-ACTING-IN-LANGUAGE-MODELS.pdf) | Agents |
| [Agentic Architectural Patterns](Notes/Resources/06-Agentic-AI/Agentic_Architectural_Patterns_for_Building_Agent.pdf) | Agentic AI |
| [Agentic Design Patterns](Notes/Resources/06-Agentic-AI/Agentic_Design_Patterns.pdf) | Agentic AI |
| [AI Agents vs Agentic AI](Notes/Resources/06-Agentic-AI/AI_Agents_vs_Agentic_AI.pdf) | Agentic AI |
| [MCP Diagrams](Notes/Resources/04-MCP/mcp-img-assets/) | MCP |
