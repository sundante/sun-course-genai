# GenAI Code Labs

A structured, hands-on code repository for learning the four major AI agent frameworks — LangChain, LangGraph, CrewAI, and Google ADK — with special focus on ADK + Vertex AI.

**Companion notes:** [GenAI-all/](../GenAI-all/INDEX.md)

---

## Two Learning Dimensions

```
DIMENSION 1 — AGENT EVOLUTION          DIMENSION 2 — ARCHITECTURE PATTERNS
─────────────────────────────────       ────────────────────────────────────
01-Agent-Types/                         02-Architectures/
  LangChain / LangGraph /                 01-Sequential
  CrewAI / ADK                            02-Parallel
    ↓                                     03-Hierarchical
  01-simple       ← ReAct + tools         04-Orchestrator-Subagent
  02-intermediate ← memory + output       05-Pipeline
  03-complex      ← plan + reflect        06-Adversarial-Debate
  real-world      ← live APIs             07-Reflexion
```

Start with **Dimension 1** to understand how a single agent works in each framework.  
Move to **Dimension 2** to see how multiple agents coordinate.

---

## Quick Start

```bash
# 1. Clone / open this folder
cd Course-GenAI/Codes

# 2. Create virtual environment
python -m venv .venv && source .venv/bin/activate

# 3. Install dependencies
pip install -r setup/requirements.txt

# 4. Set up credentials
cp setup/.env.example .env
# Edit .env and add your GOOGLE_API_KEY

# 5. Open the first notebook
jupyter notebook 01-Agent-Types/ADK/01-simple/agent.ipynb
```

For Vertex AI / GCP setup → [setup/gcp-setup.md](setup/gcp-setup.md)

---

## Learning Roadmap

### Dimension 1 — Agent Types (start here)

| Step | Framework | Level | What You Learn |
|---|---|---|---|
| 1 | ADK | Simple | ReAct loop, tool binding, Gemini model |
| 2 | LangChain | Simple | LCEL chains, tool calling |
| 3 | LangGraph | Simple | Graph nodes, edges, state |
| 4 | CrewAI | Simple | Agents, tasks, crew |
| 5 | All | Intermediate | Memory, multi-tool, structured output |
| 6 | All | Complex | Planning, reflection, streaming |
| 7 | ADK | Vertex AI real-world | Production ADK on GCP |

### Dimension 2 — Architecture Patterns

| Pattern | Key Concept | Recommended Order |
|---|---|---|
| Sequential | A→B→C pipeline | Start here |
| Parallel | Fan-out + aggregate | 2nd |
| Orchestrator-Subagent | Planner + workers | 3rd |
| Hierarchical | Nested orchestration | 4th |
| Pipeline | Data-flow, no shared state | 5th |
| Adversarial/Debate | Proposer vs Critic vs Judge | 6th |
| Reflexion | Self-critique + retry | 7th |

Each pattern is implemented in **all four frameworks** using the same mock task — enabling direct comparison.

---

## Repo Structure

```
Codes/
├── README.md                   ← You are here
├── _toc.yml                    ← Jupyter Book navigation
├── _config.yml                 ← Jupyter Book config
│
├── setup/
│   ├── requirements.txt
│   ├── .env.example
│   └── gcp-setup.md
│
├── 01-Agent-Types/
│   ├── README.md
│   ├── LangChain/
│   │   ├── 01-simple/          ← agent.ipynb + agent.py
│   │   ├── 02-intermediate/
│   │   ├── 03-complex/
│   │   └── real-world/         ← Tavily web search
│   ├── LangGraph/              ← same structure
│   ├── CrewAI/                 ← same structure
│   └── ADK/
│       ├── 01-simple/
│       ├── 02-intermediate/
│       ├── 03-complex/
│       └── vertex-ai-real-world/
│
└── 02-Architectures/
    ├── README.md
    ├── 01-Sequential/          ← LangChain/ LangGraph/ CrewAI/ ADK/
    ├── 02-Parallel/
    ├── 03-Hierarchical/
    ├── 04-Orchestrator-Subagent/
    ├── 05-Pipeline/
    ├── 06-Adversarial-Debate/
    └── 07-Reflexion/
```

---

## Notebook Format

Every `.ipynb` follows the same 7-cell structure:

1. **Title** — framework, level, learning objectives
2. **Concept** — ASCII diagram or pattern explanation
3. **Setup** — imports, env vars, model init
4. **Tools** — mock tool definitions with docstrings
5. **Agent** — agent/graph/crew construction
6. **Run** — invoke with sample query, observe output
7. **Takeaways** — what this demonstrates, what to explore next

---

## Framework Overview

| Framework | Mental Model | Best For |
|---|---|---|
| **Google ADK** | Agent as a configurable object | GCP-native, Vertex AI, production |
| **LangChain** | Chain of callables (LCEL) | Flexibility, broad ecosystem |
| **LangGraph** | State machine / graph | Stateful, complex flows, cycles |
| **CrewAI** | Role-playing crew | Multi-agent collaboration, readable |
