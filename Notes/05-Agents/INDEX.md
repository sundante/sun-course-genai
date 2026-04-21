# 05 — Agents

## What Are Agents

AI agents are LLM-powered systems that can perceive their environment, reason about goals, and take actions using tools — going beyond single-turn chat to autonomous, multi-step task completion.

## Covered Frameworks

| Framework | Folder | Best For |
|-----------|--------|----------|
| GCP Agent Development Kit | [GCP-ADK/](GCP-ADK/INDEX.md) | Google Cloud-native agents |
| LangChain | [LangChain/](LangChain/INDEX.md) | General-purpose agent chains |
| LangGraph | [LangGraph/](LangGraph/INDEX.md) | Stateful, graph-based agents |
| CrewAI | [CrewAI/](CrewAI/INDEX.md) | Role-based multi-agent crews |

## Recommended Learning Path

1. Read [Agent Fundamentals](Notes/01-Agent-Fundamentals.md) — understand what agents are
2. Study [Agent Patterns](Notes/02-Agent-Patterns.md) — learn common design patterns
3. Pick one framework and work through its Fundamentals → Simple → Complex files
4. Return to [Interview Q&A](../Interview-Questions/05-Agents.md) to consolidate knowledge

## Framework Comparison

| Dimension | GCP ADK | LangChain | LangGraph | CrewAI |
|-----------|---------|-----------|-----------|--------|
| State management | Session-based | Memory modules | Graph state | Shared crew context |
| Multi-agent | Via orchestration | Via chains | Via graph nodes | Native (Crew) |
| Cloud integration | GCP native | Cloud-agnostic | Cloud-agnostic | Cloud-agnostic |
| Best complexity | Medium-High | Low-Medium | Medium-High | Medium-High |

## Code Labs

| Section | What You'll Build | Link |
|---------|------------------|------|
| Agent Types | Simple → Intermediate → Complex agents across all 4 frameworks | [Codes/01-Agent-Types](../Codes/01-Agent-Types.md) |
| Architecture Patterns | 7 multi-agent coordination patterns × 4 frameworks | [Codes/02-Architectures](../Codes/02-Architectures.md) |

## Notes

- [01 — Agent Fundamentals](Notes/01-Agent-Fundamentals.md)
- [02 — Agent Patterns](Notes/02-Agent-Patterns.md)
- [03 — Interview Q&A](../Interview-Questions/05-Agents.md)

## Resources

- [Building Applications with AI Agents](../Resources/05-Agents/Building_Applications_with_AI_Agents.pdf)

## Navigation

[Previous: 04 — MCP](../04-MCP/INDEX.md) | [Next: 06 — Agentic AI](../06-Agentic-AI/INDEX.md)
