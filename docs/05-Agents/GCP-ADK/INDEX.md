# GCP Agent Development Kit (ADK)

← **Back to Overview:** [Agents](../INDEX.md)

## What Is Google ADK

Google's Agent Development Kit is a framework for building, deploying, and managing AI agents on Google Cloud. It provides abstractions for agent state, tool integration, session management, and multi-agent orchestration.

## When to Use ADK

- You are deploying on Google Cloud / Vertex AI
- You need tight integration with GCP services (BigQuery, Cloud Storage, etc.)
- You want managed agent infrastructure with built-in observability

## ADK vs Other Frameworks

| | ADK | LangGraph | CrewAI |
|--|-----|-----------|--------|
| Cloud-native | GCP | Agnostic | Agnostic |
| State model | Session | Graph | Crew context |
| Multi-agent | Orchestrator pattern | Graph nodes | Role-based |

## Chapter Map

| File | Topic |
|------|-------|
| [01 — ADK Fundamentals](01-ADK-Fundamentals.md) | Core concepts, setup |
| [02 — Simple Agent](02-Simple-Agent.md) | Single-tool agent walkthrough |
| [03 — Complex Agent](03-Complex-Agent.md) | Multi-tool, stateful agent |

## Navigation

[Back to Agents Index](../INDEX.md)
