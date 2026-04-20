# 01 — Agent Types

## What This Section Teaches

A single AI agent, built four different ways, growing in complexity across three levels. The goal is to understand how each framework approaches the same core problem — and how the agent itself evolves as you add memory, planning, and reflection.

---

## The Three Levels

```
SIMPLE                    INTERMEDIATE               COMPLEX
──────                    ────────────               ───────
One goal                  Multi-tool                 Goal decomposition
1–2 mock tools            Short-term memory          Planning step
No memory                 Structured output          Self-critique + retry
One-shot response         Tool chaining              Streaming output

Concepts: ReAct loop      Concepts: memory,          Concepts: planning,
tool binding, prompt      output parsers             reflection, autonomy
```

---

## Framework Comparison

| Feature | LangChain | LangGraph | CrewAI | ADK |
|---|---|---|---|---|
| **Mental model** | Chain of callables | State machine | Role-playing crew | Configurable agent object |
| **State** | Message history | Typed graph state | Shared crew context | Session-based |
| **Tool binding** | `.bind_tools()` | Node functions | `@tool` decorator | `FunctionTool` |
| **Memory** | `ConversationBufferMemory` | State dict | Crew context | `session.state` |
| **Streaming** | `.stream()` | `.stream()` | Built-in | `runner.run_async()` |
| **GCP / Vertex AI** | Via LangChain-Google | Manual | Manual | Native |

---

## Folder Structure

```
01-Agent-Types/
├── LangChain/
│   ├── 01-simple/         agent.ipynb + agent.py
│   ├── 02-intermediate/   agent.ipynb + agent.py
│   ├── 03-complex/        agent.ipynb + agent.py
│   └── real-world/        Tavily web search example
├── LangGraph/             same structure
├── CrewAI/                same structure
└── ADK/
    ├── 01-simple/
    ├── 02-intermediate/
    ├── 03-complex/
    └── vertex-ai-real-world/    ADK + Vertex AI on GCP
```

---

## Recommended Path

1. Pick one framework (recommended: **ADK** for GCP focus)
2. Work through `01-simple` → `02-intermediate` → `03-complex` in that framework
3. Then read the same level in another framework to compare
4. Finish with the real-world example of your primary framework
