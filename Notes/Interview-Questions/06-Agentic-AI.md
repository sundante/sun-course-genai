# Concept Review — Agentic AI

## Conceptual and Definitional Questions

**Q: What is the difference between an agent and an agentic AI system?**
An agent is a single LLM that can use tools in a loop. An agentic AI system is a broader architecture — potentially multiple agents, persistent memory, orchestration logic, human-in-the-loop mechanisms, evaluation layers, and reliability engineering. "Agentic" describes a class of systems that operate autonomously toward goals, make decisions over extended horizons, and coordinate resources. An agent is a component; an agentic system is an architecture.

**Q: What makes a system "agentic"?**
(1) Goal-directed: pursues an objective, not just responding to input. (2) Autonomous action: takes real-world actions without human approval for each step. (3) Extended operation: works over multiple steps, sessions, or time periods. (4) Adaptation: adjusts its approach based on feedback and observations. The degree of each determines how "agentic" a system is — it's a spectrum, not binary.

**Q: How does agentic AI relate to RAG and standard agents?**
RAG: knowledge injection for a single generation. Standard agent: an LLM that can use tools in a loop. Agentic AI takes it further — agents that plan, spawn sub-agents, maintain long-term memory, operate over days/weeks, and coordinate to solve complex open-ended goals. Each level adds autonomy and capability at the cost of reliability and observability.

**Q: Describe the autonomy spectrum from chatbot to agentic system.**
Chatbot (reactive, stateless) → RAG system (knowledge-grounded, still reactive) → single agent (tools + ReAct loop, multi-step) → multi-agent system (specialized coordination, parallelism) → full agentic system (persistent state, replanning, HITL, monitoring, long-horizon goals). Each step up the spectrum adds capability and reduces predictability. The key transitions: agent → multi-agent adds coordination overhead; multi-agent → agentic system adds persistence, reliability engineering, and production concerns.

**Q: What is the ReAct pattern and why is it the foundation of agentic systems?**
ReAct (Reason + Act) interleaves reasoning traces with actions: the agent thinks about what to do, calls a tool, observes the result, thinks again, and repeats. The explicit reasoning trace makes the agent's logic visible to the LLM on the next step, which dramatically improves performance on multi-step tasks. It's the foundation because every agentic system — no matter how complex — uses this inner loop as the basic execution unit of each agent.

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

**Q: When would you choose Pipeline over Orchestrator-Subagent?**
Pipeline when: the task decomposition is fixed and known upfront, stages have a clear sequential dependency (output of A is always input to B), and modularity is important (you want to swap stages independently). Orchestrator-Subagent when: the plan needs to be dynamic (the orchestrator decides what to do next based on intermediate results), some stages can run in parallel, or you need to handle failures by replanning rather than halting.

**Q: What are the tradeoffs of hierarchical vs flat orchestration?**
Hierarchical: better isolation (a team-level failure doesn't propagate to the manager), natural for very large tasks, mirrors human organizational structure. But: more latency (each layer adds a round-trip), harder to debug (failures surface only after propagating up), and more complex to build. Flat (single orchestrator): simpler, faster, easier to debug. But: doesn't scale to many agents; the orchestrator becomes a bottleneck. Choose hierarchical only when task scale or isolation requirements justify the complexity.

**Q: What are hybrid patterns and give an example?**
Real systems combine multiple patterns. Common example: Orchestrator-Subagent + Parallel — the orchestrator fans out to parallel subagents for independent subtasks, waits for all results, then synthesizes. Another: Pipeline + Reflexion — a pipeline where the writing stage includes an internal critique loop before passing to the next stage. Hybrid patterns are the rule, not the exception, in production systems.

---

## Design Pattern Questions

**Q: What makes a good tool description for an LLM agent?**
Good tool descriptions answer: (1) What does this tool do? (2) When should you use it? (3) What inputs does it expect? (4) What does it return? (5) When should you NOT use it? The description is part of the agent's context — it must be precise enough that the LLM consistently calls the right tool with the right arguments. A vague description ("search tool") leads to misuse; a precise description ("search the product catalog by name or SKU — returns price, stock, and product ID") guides correct usage.

**Q: Explain the Reflection design pattern. When does it improve quality and when is it not worth it?**
Reflection: the agent generates a draft, a critic (same or different LLM) evaluates it against a rubric, and the agent revises. Repeats until quality threshold is met or max iterations is hit. Improves quality when: the task is iterative by nature (writing, code), there's a verifiable quality criterion, and the first pass is consistently close-but-not-good-enough. Not worth it when: one pass is sufficient, there's no good stopping criterion (risk of infinite loops), or latency is critical (each iteration adds full LLM round-trips).

**Q: What is Plan-and-Execute and when is it preferable to ReAct?**
Plan-and-Execute: generate a complete plan first, then execute each step. Preferable to ReAct when: (1) HITL is required — you can show the plan to a human before any action is taken; (2) the task has complex dependencies that benefit from upfront reasoning; (3) you want to detect infeasible goals before investing in execution. ReAct is better when: the right next step can only be determined from the results of the previous step (emergent tasks), or the task is straightforward enough that upfront planning adds overhead.

**Q: How do you design a routing agent?**
A routing agent classifies incoming inputs and sends them to the appropriate handler. Design: (1) Define exhaustive categories with clear boundaries and examples; (2) Use a lightweight model for routing (cost optimization — routing is classification, not complex reasoning); (3) Add a catch-all "unknown" route for inputs that don't fit categories; (4) Log all routing decisions for monitoring; (5) Make the routing explicit — don't embed routing logic deep in a general-purpose agent's prompt. A dedicated routing step that returns a category label is more reliable than asking an agent to "figure out the right thing to do."

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

**Q: What is bounded autonomy and why is it essential in production?**
Bounded autonomy means placing explicit limits on every dimension of agent execution: max LLM calls, max tool calls, max wall-clock time, max cost, max retries. Without bounds, agents can loop indefinitely, exhaust quotas, or take an unbounded number of actions before failing. In production, a misbehaving agent without bounds can incur large costs and take many unintended actions before anyone notices. Bounded autonomy limits blast radius — the worst-case outcome is now predictable.

**Q: How do you handle prompt injection in a multi-agent system?**
Prompt injection: malicious content in external data (web pages, user documents) attempts to override agent instructions. In multi-agent systems this is especially dangerous — injection in one agent's context can propagate through the system. Mitigations: (1) Input sanitization — strip or escape instruction-like patterns from external content. (2) Role separation — have a content agent that processes external data separately from the reasoning agent that takes actions. (3) Action validation — before executing any action, verify it's consistent with the original user intent and the agent's role. (4) Least privilege — each agent only has the tools it needs; a research agent should not have email-sending capability.

**Q: Describe the four types of memory in an agentic system and their roles.**
(1) Short-term memory (context window): the LLM's active context for the current session — lost when the session ends. (2) Working memory (agent state): structured state maintained by the orchestration layer — task ledger, partial results, error log — persisted to a database, survives restarts. (3) Long-term memory (vector store): semantic knowledge accumulated across tasks — past research, user preferences — queried via semantic search. (4) Episodic memory (event log): a sequential audit trail of every LLM call, tool call, HITL decision — used for debugging and compliance.

**Q: How do you manage costs in a production agentic system?**
(1) Set explicit token budgets per task type — enforce them by tracking cost in state and terminating gracefully when the budget is near exhaustion. (2) LLM routing — use smaller, cheaper models for simple tasks (classification, formatting) and reserve large models for complex reasoning. (3) Instrument every LLM call from day one — you need cost data before you can optimize. (4) Identify expensive patterns early: Reflexion loops, large context windows, over-broad parallel fan-outs. (5) Cache deterministic tool results — the same web search doesn't need to hit the API twice in the same task.

**Q: How do you scale an agentic system to handle many concurrent tasks?**
(1) Queue-backed architecture: tasks are submitted to a queue; stateless worker processes pick them up. Scale workers horizontally by adding more instances. (2) Async processing: accept tasks and return a job ID; notify on completion via webhook or polling. (3) Shared state in a database: workers are stateless because all state is in the database, not in memory. (4) Rate limiting and back-pressure: queue depth limits prevent overwhelming downstream services. (5) Agent pool: pre-initialized agents avoid cold-start overhead per task.

---

## Evaluation and Observability Questions

**Q: What is trajectory evaluation and why is it necessary?**
Trajectory evaluation assesses the quality of the agent's execution path — each step — not just the final answer. Necessary because: an agent can produce the right final answer via an inefficient or dangerous path (hallucinated tool arguments that happened to not cause visible errors, unnecessary loops, redundant calls). Final answer quality is easy to measure and easy to game; trajectory quality reflects true system health. Key trajectory metrics: tool selection accuracy, argument correctness, steps-to-completion, retry rate.

**Q: How would you set up observability for a new agentic system from day one?**
(1) Choose a tracing tool: LangSmith for LangChain/LangGraph projects; Langfuse for framework-agnostic or self-hosted setups. (2) Instrument every LLM call: model, input/output tokens, cost, latency. (3) Instrument every tool call: name, arguments, result, latency, error. (4) Log all state transitions: what changed in the shared state at each step. (5) Log HITL events: who approved what, when, and what happened next. (6) Set up dashboards for completion rate, cost/task, and error rate. (7) Set alerts for safety violations, budget overruns, and error rate spikes.

**Q: You have a multi-agent task that's producing a wrong final answer. How do you debug it?**
(1) Get the full trajectory: pull the complete trace from your observability tool. (2) Find the first wrong step — don't start from the error, start from the beginning. (3) Check tool call arguments at that step: were they grounded in context or hallucinated? (4) Check whether the tool result was correctly interpreted. (5) If the issue is in an LLM reasoning step, inspect the full context that was provided at that step. (6) Replay from checkpoint: use the framework's checkpointing to reproduce the failure deterministically. (7) Fix the root cause — improved tool description, better prompt, input validation — and verify the fix by replaying.

**Q: What is the difference between LLM-as-Judge for single-turn eval vs trajectory eval?**
Single-turn: LLM judge rates the final output — correctness, completeness, style. Simple to set up. Trajectory: LLM judge evaluates each step — right tool? right arguments? appropriate reasoning? — and the overall path (was it efficient? did it avoid unnecessary steps?). Harder because the judge must understand the task, the available tools, and the reasoning at each step. Trajectory eval requires a stronger judge model and a more detailed rubric. The two are complementary — use both.

**Q: What are the most common failure modes in production agentic systems?**
(1) Cascading failure: agent A produces bad output → agent B uses it → errors compound silently. Fix: validate outputs between agents. (2) Infinite loops: reflection/retry cycle with no termination. Fix: always set max_iterations. (3) Context drift: agent loses track of the original goal as context accumulates. Fix: pin goal in system message; use task ledger. (4) Prompt injection via external content: external data overrides agent instructions. Fix: input sanitization, role separation. (5) Hallucinated tool arguments: agent invents parameter values not in context. Fix: validate arguments, log every tool call. (6) HITL timeout: no human responds, task is stuck. Fix: define timeout policy and escalation path.
