# 02 — Parallel Architecture

## Pattern: Fan-out → Independent Agents → Aggregate

```
                    Input
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
    ┌──────────┐ ┌──────────┐ ┌──────────┐
    │ Agent A  │ │ Agent B  │ │ Agent C  │
    │ (Tokyo)  │ │ (Paris)  │ │(Bangalore│
    └────┬─────┘ └────┬─────┘ └────┬─────┘
         │            │            │
         └────────────┼────────────┘
                      ▼
               ┌────────────┐
               │ Aggregator │
               └────────────┘
                      │
                   Output
```

## When to Use Parallel

| Scenario | Why Parallel? |
|---|---|
| Multiple independent data sources | No dependency between sources — run simultaneously |
| Same task on N items | Fan-out over a list, merge results |
| Time-sensitive pipelines | Cut latency by parallelizing slow operations |
| Diverse specialist agents | Each agent has different tools/context |

## Trade-offs

| Pro | Con |
|---|---|
| Lower latency (N tasks in 1 LLM round) | Harder to debug — which agent failed? |
| Each agent has focused context | Aggregation step adds complexity |
| Scales to many items | API rate limits may constrain true parallelism |

## Mock Task

**Input:** Three cities — Tokyo, Paris, Bangalore  
**Parallel step:** Each city researched independently (weather + safety + time)  
**Aggregate step:** One aggregator compares all three and ranks them

## Framework Implementations

| Framework | Parallelism Mechanism |
|---|---|
| LangChain | `asyncio.gather()` across LCEL chain calls |
| LangGraph | `Send()` API for dynamic fan-out nodes |
| CrewAI | Multiple Tasks with no `context=` dependency (run concurrently) |
| ADK | Instruction-driven parallel tool calls + aggregator agent |
