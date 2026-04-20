# 04 — Orchestrator-Subagent Architecture

## Pattern: Planner Orchestrates Specialist Workers

```
User Goal
    │
    ▼
┌──────────────────┐
│   Orchestrator   │  ← plans, delegates, never executes directly
│   (Planner LLM)  │
└────────┬─────────┘
         │  dynamic task assignment
    ┌────┼────┬────┐
    ▼    ▼    ▼    ▼
 Search  Code  Write  Summarize
 Agent  Agent  Agent   Agent
```

## How It Differs from Hierarchical

| Hierarchical | Orchestrator-Subagent |
|---|---|
| Fixed team structure (leads + workers) | Dynamic: orchestrator picks which agents to use |
| Manager delegates to leads | Orchestrator delegates directly to specialists |
| Multi-level chain of command | Two levels only: planner + workers |
| Workers don't communicate with each other | Workers are fully isolated, orchestrator wires them |

## Mock Task

**Goal:** Research a travel destination and produce a complete trip package  
**Orchestrator:** Plans: "I need search + write + format"  
**Search Agent:** Looks up city highlights  
**Writer Agent:** Drafts itinerary  
**Format Agent:** Produces final structured output

## When to Use

- Dynamic task decomposition (goal unknown upfront)
- Specialists that should stay isolated from each other
- Orchestrator needs to decide the workflow at runtime
