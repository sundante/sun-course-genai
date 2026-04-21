# Code Labs — 01: Agent Types

Build single agents from scratch across three complexity levels in all four frameworks. Each level adds a new capability layer on top of the previous.

**Notes companion:** [05 — Agents](../05-Agents/INDEX.md)

---

## Complexity Progression

```
Level 1: Simple           Level 2: Intermediate      Level 3: Complex
─────────────────         ─────────────────────       ────────────────────
ReAct loop                + Memory                    + Planning
Tool binding              + Multi-tool                + Reflection
Basic Gemini call         + Structured output         + Streaming
```

---

## Labs by Framework and Level

### Google ADK

| Level | File | What You Learn |
|-------|------|----------------|
| Simple | `ADK/01-simple/agent.ipynb` | ReAct agent, tool binding, Gemini model config |
| Intermediate | `ADK/02-intermediate/agent.ipynb` | Session memory, multi-tool orchestration, output schema |
| Complex | `ADK/03-complex/agent.ipynb` | Planning steps, self-reflection, streaming response |
| Real-world | `ADK/vertex-ai-real-world/agent.ipynb` | Production ADK on Vertex AI with live APIs |

### LangChain

| Level | File | What You Learn |
|-------|------|----------------|
| Simple | `LangChain/01-simple/agent.ipynb` | LCEL chain, tool calling, message history |
| Intermediate | `LangChain/02-intermediate/agent.ipynb` | ConversationBufferMemory, multi-tool routing |
| Complex | `LangChain/03-complex/agent.ipynb` | Plan-and-execute, output parsers, callbacks |
| Real-world | `LangChain/real-world/agent.ipynb` | Tavily web search, live data integration |

### LangGraph

| Level | File | What You Learn |
|-------|------|----------------|
| Simple | `LangGraph/01-simple/agent.ipynb` | Graph nodes, edges, StateGraph, basic tool call |
| Intermediate | `LangGraph/02-intermediate/agent.ipynb` | Checkpointer memory, conditional edges, tool router |
| Complex | `LangGraph/03-complex/agent.ipynb` | Subgraphs, reflection loop, streaming events |
| Real-world | `LangGraph/real-world/agent.ipynb` | Stateful conversation with web retrieval |

### CrewAI

| Level | File | What You Learn |
|-------|------|----------------|
| Simple | `CrewAI/01-simple/agent.ipynb` | Agent + Task + Crew, role assignment |
| Intermediate | `CrewAI/02-intermediate/agent.ipynb` | Shared crew memory, multi-tool agents |
| Complex | `CrewAI/03-complex/agent.ipynb` | Sequential task chaining, delegation, callbacks |
| Real-world | `CrewAI/real-world/agent.ipynb` | Research crew with live web tools |

---

## Framework Comparison at Each Level

| Capability | ADK | LangChain | LangGraph | CrewAI |
|-----------|-----|-----------|-----------|--------|
| Tool binding | `@tool` decorator | `@tool` + bind_tools | ToolNode | Agent tools list |
| Memory | Session service | ConversationBuffer | Checkpointer | Crew memory |
| State model | Session dict | Message list | TypedDict graph state | Shared crew context |
| Streaming | `stream_query` | `.stream()` | `.stream_events()` | Callback handlers |

---

## Getting Started

```bash
# Start with the simplest ADK notebook
jupyter notebook Codes/01-Agent-Types/ADK/01-simple/agent.ipynb

# Or LangChain if you prefer
jupyter notebook Codes/01-Agent-Types/LangChain/01-simple/agent.ipynb
```

After completing all four simple agents, compare: same task, four different approaches. The differences in state management, tool binding, and model calls become immediately apparent.

---

## What to Read Alongside

- [Agent Fundamentals](../05-Agents/Notes/01-Agent-Fundamentals.md) — the ReAct loop, tool use, memory types
- [Agent Patterns](../05-Agents/Notes/02-Agent-Patterns.md) — planning and reflection patterns used at Level 3
- Framework-specific deep-dives: [GCP ADK](../05-Agents/GCP-ADK/INDEX.md) · [LangChain](../05-Agents/LangChain/INDEX.md) · [LangGraph](../05-Agents/LangGraph/INDEX.md) · [CrewAI](../05-Agents/CrewAI/INDEX.md)

---

## Next: Architecture Patterns

Once you've built single agents, move to [02 — Architecture Patterns](02-Architectures.md) to see how multiple agents coordinate.
