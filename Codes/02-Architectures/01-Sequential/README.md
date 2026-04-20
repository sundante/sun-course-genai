# Sequential Architecture

## Pattern

```
[Agent A] ──→ [Agent B] ──→ [Agent C]
 Research       Summarize     Format
    ↓               ↓            ↓
 raw notes     summary text   final report
```

Each agent receives the previous agent's output as its input. No agent starts until the previous one finishes.

## When to Use

- Tasks with strict ordering — each step depends on the last
- Document processing pipelines (extract → analyze → format)
- Multi-stage transformations where context must flow forward

## Trade-offs

| Pro | Con |
|---|---|
| Simple to reason about | Slow — no parallelism |
| Easy to debug (clear handoffs) | One bottleneck stalls everything |
| Output is fully traceable | Later agents can't correct earlier ones |

## The Mock Task

**Topic research report pipeline:**
1. `ResearchAgent` — collects bullet facts about a topic (mock tool)
2. `SummaryAgent` — condenses the bullets into 2–3 sentences
3. `FormatterAgent` — wraps summary into a structured markdown report

## Implementations

| Framework | File |
|---|---|
| LangChain | [LangChain/sequential.ipynb](LangChain/sequential.ipynb) |
| LangGraph | [LangGraph/sequential.ipynb](LangGraph/sequential.ipynb) |
| CrewAI | [CrewAI/sequential.ipynb](CrewAI/sequential.ipynb) |
| ADK | [ADK/sequential.ipynb](ADK/sequential.ipynb) |
