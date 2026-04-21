# Code Review System

A multi-agent system that accepts a code diff, fans out to specialized reviewers running in parallel, aggregates their findings, and produces a prioritized, actionable code review report with a final quality pass.

## Architecture

```
Code Diff Input
      ↓
[Orchestrator]
      ├──→ [Static Analysis Agent]  ──┐
      ├──→ [Security Review Agent]  ──→ [Aggregator Agent] → Review Draft
      ├──→ [Style Check Agent]      ──┘        ↓
      └──→ [Complexity Agent]       ──┘   [Reflexion: Critic]
                                                ↓
                                         Final Report
```

## Patterns Used

| Pattern | Where It Appears |
|---------|-----------------|
| Parallel / Fan-out | Four specialized reviewers run concurrently |
| Aggregation | Aggregator merges parallel findings into unified report |
| Reflexion | Critic evaluates the aggregated report for completeness |

## Agent Roles

| Agent | Review Focus | Output |
|-------|-------------|--------|
| Static Analysis Agent | Potential bugs, null checks, error handling, logic errors | List of issues with severity |
| Security Review Agent | SQL injection, XSS, hardcoded secrets, insecure dependencies | Security findings with CVSS-like severity |
| Style Check Agent | Naming conventions, code formatting, documentation quality | Style issues and suggestions |
| Complexity Agent | Cyclomatic complexity, function length, code smells | Refactoring recommendations |
| Aggregator | Merges all reviews, deduplicates, prioritizes | Structured review report |
| Critic | Evaluates report quality — are all issues covered? | Approval or revision request |

## Sample Code Diff

The example reviews a Python function with intentional issues: missing error handling, a potential SQL injection, and poor naming.

## What This Demonstrates

1. Parallel fan-out: four independent reviewers running concurrently
2. Aggregation with deduplication across multiple parallel outputs
3. Priority ranking: Critical → High → Medium → Low
4. Reflexion on the aggregated output (not individual agent outputs)
5. How to structure parallel results in shared state

## Implementations

- [LangChain](LangChain/system.py) — ThreadPoolExecutor for parallel + LCEL aggregation chain
- [LangGraph](LangGraph/system.py) — Send() fan-out, state accumulation, conditional reflexion
- [CrewAI](CrewAI/system.py) — Parallel process crew with specialized reviewer agents
- [ADK](ADK/system.py) — ParallelAgent for reviews + SequentialAgent for aggregation
