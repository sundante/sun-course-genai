# Interview Q&A — Agentic AI

## Conceptual and Definitional Questions

**Q: What is the difference between an agent and an agentic AI system?**
An agent is a single LLM that can use tools in a loop. An agentic AI system is a broader architecture — potentially multiple agents, persistent memory, orchestration logic, human-in-the-loop mechanisms, evaluation layers, and reliability engineering. "Agentic" describes a class of systems that operate autonomously toward goals, make decisions over extended horizons, and coordinate resources. An agent is a component; an agentic system is an architecture.

**Q: What makes a system "agentic"?**
(1) Goal-directed: pursues an objective, not just responding to input. (2) Autonomous action: takes real-world actions without human approval for each step. (3) Extended operation: works over multiple steps, sessions, or time periods. (4) Adaptation: adjusts its approach based on feedback and observations. The degree of each determines how "agentic" a system is — it's a spectrum, not binary.

**Q: How does agentic AI relate to RAG and standard agents?**
RAG: knowledge injection for a single generation. Standard agent: an LLM that can use tools in a loop. Agentic AI takes it further — agents that plan, spawn sub-agents, maintain long-term memory, operate over days/weeks, and coordinate to solve complex open-ended goals. Each level adds autonomy and capability at the cost of reliability and observability.

---

## Architectural Questions

**Q: What are the different Agentic AI architectures?**
| Architecture | Structure | Best For |
|---|---|---|
| **Single Agent** | One LLM with tools in a loop | Simple, focused tasks |
| **Orchestrator-Subagent** | One planner delegates to specialized workers | Complex multi-step tasks with clear decomposition |
| **Hierarchical** | Multi-level orchestration (manager → team leads → workers) | Large-scale systems with nested task trees |
| **Peer-to-Peer (Decentralized)** | Agents communicate directly, no central coordinator | Collaborative tasks where roles are fluid |
| **Pipeline / Sequential** | Output of one agent becomes input of next | ETL-style workflows, document processing |
| **Parallel / Fan-out** | Orchestrator spawns concurrent agents, aggregates results | Research, multi-source analysis, speedup |
| **Debate / Adversarial** | Agents argue opposing positions; judge synthesizes | Fact-checking, red-teaming, critical analysis |
| **Reflexion / Self-Critique** | Agent evaluates its own output and retries | Quality-sensitive tasks requiring iteration |

Key decision axes: centralized vs distributed control, sequential vs parallel execution, static vs dynamic routing.

**Q: Explain the orchestrator-subagent pattern.**
An orchestrator agent receives the high-level goal, decomposes it into subtasks, and delegates to specialized subagents. Each subagent executes its subtask and returns results to the orchestrator, which synthesizes them into a final output or continues planning. Enables parallelism and specialization. The orchestrator doesn't need to know the implementation details of each subagent — it coordinates via a defined interface.

**Q: What is human-in-the-loop (HITL) and when is it required?**
HITL means inserting a human approval/review step at defined points in the agent's execution — before irreversible actions (sending emails, committing code, making payments), when confidence is low, or when an action exceeds a defined risk threshold. Required when: actions have real-world consequences that are hard to reverse, the task involves personal/sensitive data, or regulatory compliance demands human sign-off.

**Q: What is a feedback loop in an agentic system and why is it important?**
A mechanism by which the agent's output or action results are observed, evaluated, and fed back to inform subsequent decisions. Types: (1) Tool observation loops — reading API responses. (2) Critic/evaluator loops — a separate LLM grades the agent's output. (3) Human feedback loops — user approval or correction. Without feedback loops, agents can't detect errors or adapt.

---

## System Design Questions

**Q: How do you design a reliable multi-agent system?**
Key principles: (1) Idempotent actions — retrying a step should be safe. (2) Explicit state — agent state should be serializable and inspectable. (3) Defined interfaces — agents communicate through typed, validated messages. (4) Failure isolation — one subagent failing shouldn't crash the whole system. (5) Observability — log every LLM call, tool call, and state transition. (6) Bounded autonomy — define max steps, max time, and escalation paths.

**Q: What is the difference between sequential and parallel multi-agent execution?**
Sequential: agents execute one at a time, each consuming the previous agent's output. Simple to reason about, easier to debug. Parallel: multiple agents run concurrently, results are merged. Faster for independent subtasks. Use sequential for tasks with dependencies; use parallel for independent subtasks. LangGraph and CrewAI both support both patterns.

**Q: How do you handle state management across long-running agentic tasks?**
Checkpointing: serialize agent state (conversation history, tool results, partial progress) to persistent storage at each step. On failure or resumption, restore from the last checkpoint. For very long tasks, summarize older conversation history rather than keeping everything in context. Maintain a separate task ledger (what's been done, what's remaining) that survives restarts.

**Q: How do you evaluate an agentic AI system?**
Unlike single-turn LLMs, agents need trajectory evaluation — not just whether the final answer is correct, but whether the path was efficient and safe. Metrics: (1) Task completion rate. (2) Steps-to-completion (efficiency). (3) Tool call accuracy. (4) Hallucination rate in intermediate steps. (5) Safety violations. Use simulated environments for evaluation to avoid real-world side effects.
