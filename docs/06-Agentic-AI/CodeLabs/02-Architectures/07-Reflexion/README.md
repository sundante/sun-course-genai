# 07 — Reflexion Architecture

## Pattern: Generate → Evaluate → Conditionally Rewrite

```
Input
  │
  ▼
┌──────────┐
│ Generate │  ← produce initial output
└────┬─────┘
     │
     ▼
┌──────────┐
│ Evaluate │  ← score / critique the output
└────┬─────┘
     │
  score < threshold?
  ┌───┴───┐
  │ YES   │ NO
  ▼       ▼
Rewrite  Output
  │
  └──► Evaluate (loop, max N times)
```

## Key Insight

**Reflexion = self-improvement via structured feedback loop**

Unlike Adversarial Debate (two agents argue), Reflexion uses one agent (or a critic chain) to evaluate its own output and decide whether to revise. The loop terminates when quality is acceptable or max iterations is reached.

## Mock Task

**Input:** Write a travel recommendation for Tokyo  
**Generate:** Draft recommendation  
**Evaluate:** Score 1-10 on specificity, safety info, weather info  
**Rewrite (if score < 7):** Improve based on critique  
**Max retries:** 2

## When to Use Reflexion

- Output quality is measurable (can score it)
- First-pass LLM output is often incomplete or vague
- You want guaranteed minimum quality without manual review
- Quality bar is more important than latency

## How Each Framework Implements Reflexion

| Framework | Loop Control | Evaluator |
|---|---|---|
| LangChain | Python `for` loop | Critic chain |
| LangGraph | Conditional edge (explicit graph loop) | Critic node |
| CrewAI | Dedicated Critic agent + context | Task context |
| ADK | `score_report` tool in instruction | Tool call |

*Note: ADK Reflexion is already demonstrated in `01-Agent-Types/ADK/03-complex/`. This pattern shows the same concept in LangChain, LangGraph, and CrewAI architecturally.*
