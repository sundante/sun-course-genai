# Code Labs

Hands-on companion to the Notes curriculum. Three learning dimensions implemented across four frameworks — LangChain, LangGraph, CrewAI, and Google ADK.

## Three Learning Dimensions

```
DIMENSION 1                     DIMENSION 2                     DIMENSION 3
Agent Evolution                 Architecture Patterns           End-to-End Systems
────────────────                ─────────────────────           ──────────────────
01-Agent-Types/                 02-Architectures/               03-Agentic-Systems/
  × 4 frameworks                  01-Sequential                   01-Research-Assistant
  01-simple                        02-Parallel                     02-Document-Processor
  02-intermediate                  03-Hierarchical                 03-Autonomous-Task-Planner
  03-complex                       04-Orchestrator-Subagent        04-Code-Review-System
                                   05-Pipeline
                                   06-Adversarial-Debate
                                   07-Reflexion

Companion notes:                Companion notes:                Companion notes:
→ 05-Agents                    → 06-Agentic-AI                 → 06-Agentic-AI
                                  (Architectural Patterns)        (System Design)
```

---

## Framework Overview

| Framework | Mental Model | Best For |
|-----------|-------------|---------|
| **Google ADK** | Agent as a configurable object | GCP-native, Vertex AI, production |
| **LangChain** | Chain of callables (LCEL) | Flexibility, broad ecosystem |
| **LangGraph** | State machine / graph | Stateful, complex flows, cycles |
| **CrewAI** | Role-playing crew | Multi-agent collaboration, readable |

Every pattern is implemented in **all four frameworks** using the same mock task — enabling direct side-by-side comparison.

---

## Code Labs Map

| Section | What You Build | Notes Companion | Difficulty |
|---------|---------------|-----------------|-----------|
| [01 — Agent Types](01-Agent-Types.md) | Single agents from simple → complex | [05 — Agents](../05-Agents/INDEX.md) | Beginner → Intermediate |
| [02 — Architecture Patterns](02-Architectures.md) | 7 multi-agent coordination patterns | [06 — Agentic AI: Architectural Patterns](../06-Agentic-AI/Notes/02-Architectural-Patterns.md) | Intermediate → Advanced |
| [03 — Agentic Systems](03-Agentic-Systems.md) | 4 complete end-to-end systems | [06 — Agentic AI: System Design](../06-Agentic-AI/Notes/05-Agentic-System-Design.md) | Advanced |

---

## Recommended Learning Order

1. **Start with notes first** — read the Notes section for the topic before running code
2. **Run Dimension 1** — build a simple agent in your preferred framework
3. **Try all 4 frameworks** — same task, different approach; builds intuition for tradeoffs
4. **Move to Dimension 2** — architectural patterns after you're comfortable with a single agent
5. **Tackle Dimension 3** — end-to-end systems combine multiple patterns from Dimension 2

---

## Quick Start

```bash
cd Codes

# Create virtual environment
python -m venv .venv && source .venv/bin/activate

# Install all dependencies
pip install -r setup/requirements.txt

# Copy and fill in credentials
cp setup/.env.example .env
# Edit .env: add GOOGLE_API_KEY (and optionally OPENAI_API_KEY, TAVILY_API_KEY)

# Open first notebook
jupyter notebook 01-Agent-Types/ADK/01-simple/agent.ipynb
```

For Vertex AI / GCP setup → [Codes/setup/gcp-setup.md](../../Codes/setup/gcp-setup.md)

---

## Notebook Format

Every `.ipynb` follows the same 7-cell structure:

| Cell | Content |
|------|---------|
| 1 | **Title** — framework, level, learning objectives |
| 2 | **Concept** — ASCII diagram or pattern explanation |
| 3 | **Setup** — imports, env vars, model init |
| 4 | **Tools** — mock tool definitions with docstrings |
| 5 | **Agent** — agent/graph/crew construction |
| 6 | **Run** — invoke with sample query, observe output |
| 7 | **Takeaways** — what this demonstrates, what to try next |
