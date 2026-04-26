# Learn AI: Generative AI to Agentic AI

A structured, beginner-to-advanced curriculum covering the full AI stack — from foundational LLMs and Generative AI through fully autonomous Agentic systems — with prose notes, code labs, and interview Q&A.

**Live site:** [sundante.github.io/sun-course-genai](https://sundante.github.io/sun-course-genai)

---

## Curriculum Topics

| # | Topic | Notes | Code Labs | Q&A | Status |
|---|-------|-------|-----------|-----|--------|
| 01 | LLM Models | 12 files — fundamentals through production deployment | Code snippets in notes | 68+ Q&A | Complete |
| 02 | Prompt Engineering | 4 files — basics through production | — | ✅ | Complete |
| 03 | RAG | 12 files — fundamentals through GCP production | ✅ | 80+ Q&A | Complete |
| 04 | MCP | 8 files — problem through getting started | — | ✅ | Complete |
| 05 | Agents | Conceptual notes + 4 framework deep-dives | ✅ Codes/01-Agent-Types | ✅ | Complete |
| 06 | Agentic AI | 6 files — concepts through evaluation | ✅ Codes/02-Architectures + 03-Systems | ✅ | Complete |

---

## Code Labs

Three dimensions of hands-on practice across **LangChain, LangGraph, CrewAI, and Google ADK**:

```
DIMENSION 1 — AGENT EVOLUTION          DIMENSION 2 — ARCHITECTURE PATTERNS      DIMENSION 3 — END-TO-END SYSTEMS
──────────────────────────────          ────────────────────────────────────      ─────────────────────────────────
Codes/01-Agent-Types/                   Codes/02-Architectures/                   Codes/03-Agentic-Systems/
  × 4 frameworks                          01-Sequential                             01-Research-Assistant
    01-simple   ← ReAct + tools           02-Parallel                               02-Document-Processor
    02-intermediate ← memory             03-Hierarchical                            03-Autonomous-Task-Planner
    03-complex  ← plan + reflect          04-Orchestrator-Subagent                  04-Code-Review-System
                                          05-Pipeline
                                          06-Adversarial-Debate
                                          07-Reflexion
```

Each pattern is implemented in all 4 frameworks using the same mock task for direct comparison.

| Framework | Mental Model | Best For |
|-----------|-------------|---------|
| Google ADK | Agent as a configurable object | GCP-native, Vertex AI, production |
| LangChain | Chain of callables (LCEL) | Flexibility, broad ecosystem |
| LangGraph | State machine / graph | Stateful, complex flows, cycles |
| CrewAI | Role-playing crew | Multi-agent collaboration, readable |

---

## Repo Structure

```
sun-course-genai/
│
├── Notes/                          ← Prose curriculum (served by MkDocs)
│   ├── index.md                    ← Home page
│   ├── 01-LLM-Models/              ← 12 files: fundamentals → production
│   ├── 02-Prompts/                 ← 4 files: basics → production
│   ├── 03-RAGs/                    ← 12 files: fundamentals → GCP
│   ├── 04-MCP/                     ← 8 files: problem → getting started
│   ├── 05-Agents/                  ← Conceptual + 4 framework deep-dives
│   ├── 06-Agentic-AI/              ← 6 files: concepts → evaluation
│   ├── Codes/                      ← Code Labs documentation (MkDocs pages)
│   ├── Interview-Questions/        ← Per-topic Q&A files
│   └── All_Questions.md            ← Consolidated Q&A
│
├── Codes/                          ← Runnable notebooks and scripts
│   ├── setup/                      ← requirements.txt, .env.example, gcp-setup.md
│   ├── 01-Agent-Types/             ← Single agent × 3 levels × 4 frameworks
│   ├── 02-Architectures/           ← 7 patterns × 4 frameworks
│   └── 03-Agentic-Systems/         ← 4 end-to-end systems × 4 frameworks
│
├── Resources/                      ← Reference PDFs (papers, handbooks)
├── status.md                       ← Curriculum completion tracker
└── mkdocs.yml                      ← MkDocs site config
```

---

## Quick Start

### Read the notes (no setup needed)

Visit the live site: [sundante.github.io/sun-course-genai](https://sundante.github.io/sun-course-genai)

Or run locally:

```bash
pip install mkdocs-material
mkdocs serve
# → http://127.0.0.1:8000
```

### Run the code labs

```bash
cd Codes

# Create virtual environment
python -m venv .venv && source .venv/bin/activate

# Install dependencies
pip install -r setup/requirements.txt

# Set up credentials
cp setup/.env.example .env
# Edit .env and add your GOOGLE_API_KEY

# Open the first notebook
jupyter notebook 01-Agent-Types/ADK/01-simple/agent.ipynb
```

For Vertex AI / GCP setup → [Codes/setup/gcp-setup.md](Codes/setup/gcp-setup.md)

---

## Learning Paths

### Path A — Conceptual (beginner)
LLM Fundamentals → Transformer Architecture → Attention Mechanisms → Prompt Engineering → RAG Fundamentals

### Path B — Interview Preparation
LLM Models (all 12 files) → RAG (12 files) → Agents → Agentic AI → All Q&A Banks

### Path C — Hands-On Engineering
Codes/01-Agent-Types (simple → complex) → Codes/02-Architectures → Codes/03-Agentic-Systems

### Path D — Production Focus
LLM Production Deployment → RAG System Design → Agentic System Design → Evaluation & Observability

---

## Tech Stack

**Notes:** MkDocs Material, Google Analytics GA4, GitHub Pages via GitHub Actions

**Code Labs:** Python 3.11+, LangChain, LangGraph, CrewAI, Google ADK, Vertex AI, Jupyter Notebooks
