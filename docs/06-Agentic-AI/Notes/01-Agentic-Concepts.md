# Agentic AI — Core Concepts

## Agentic AI vs Traditional AI

### Concept

Traditional AI systems are **reactive**: given an input, produce an output. A chatbot responds to a message. A classifier labels an image. A RAG system retrieves context and generates a grounded answer. The system does exactly what it's told, nothing more.

Agentic AI systems are **proactive and autonomous**: given a *goal*, they figure out *how* to achieve it. They decide what to do next, take actions, observe results, and continue until the goal is met — or until something goes wrong. The key shift is **agency**: the system owns the path, not just the output.

| Dimension | Traditional AI | Agentic AI |
|-----------|---------------|------------|
| Input | Single prompt or query | High-level goal or objective |
| Output | Single response or classification | Sequence of actions + final result |
| Horizon | Single step | Multi-step, extended time |
| Decision-making | None (follows instructions exactly) | Chooses what to do next |
| Failure handling | Returns error or bad output | Can detect failure and retry |
| Human involvement | Every step | Defined checkpoints only |
| Predictability | High | Lower — emergent behavior |

The difference is not just technical — it's a shift in *who holds the initiative*. In traditional AI, the human drives every step. In agentic AI, the system drives the steps within a defined goal boundary.

---

## The Autonomy Spectrum

Agentic AI is not binary — it's a spectrum. Systems become more agentic as they gain more autonomy, capability, and persistence.

```
Chatbot → RAG System → Single Agent → Multi-Agent → Agentic System
  ↑           ↑              ↑               ↑              ↑
Reactive   Knowledge     Tool use       Coordination    Goal-driven,
response   injection     + reasoning    + parallelism   persistent,
                                                         self-managing
```

**Level 1 — Chatbot**
Stateless, reactive. Responds to each message independently. No memory, no tools, no planning.

**Level 2 — RAG System**
Retrieves relevant context before generating. Still fundamentally reactive — one retrieval + one generation per query. No action-taking beyond answering.

**Level 3 — Single Agent**
An LLM that can use tools in a loop: reason → call a tool → observe result → reason again → repeat until done. Can handle tasks that require multiple steps and tool calls. The first genuinely agentic level.

**Level 4 — Multi-Agent System**
Multiple specialized agents coordinated toward a common goal. Each agent handles a subtask. Introduces planning (who does what), communication (how agents share information), and orchestration (how the work is assembled).

**Level 5 — Agentic System**
A full system designed for autonomy: persistent state across sessions, long-horizon planning, dynamic replanning when blocked, human-in-the-loop gates for high-risk actions, memory that survives restarts, and monitoring/observability as a first-class concern. Operates over hours, days, or longer.

**The cost of moving up the spectrum:** Each level adds capability but reduces predictability and reliability. A chatbot always behaves deterministically. An agentic system can get stuck in loops, hallucinate in tool arguments, or take unintended actions. Engineering for reliability is what separates production agentic systems from demos.

---

## Core Properties of Agentic Systems

Four properties define how "agentic" a system is. A system that maximizes all four is fully agentic; most real systems sit somewhere between.

### 1. Goal-Directed
The system pursues an objective, not just responds to input. It knows *what* it is trying to accomplish and uses that goal to evaluate whether its actions are working.

Example: "Research the competitive landscape for electric vehicles and write a 2-page summary" — the goal guides every step, not a single prompt.

### 2. Autonomous Action
The system takes real-world actions without human approval for each step. It calls APIs, reads/writes files, executes code, sends emails — and decides *which* action to take based on its current understanding.

Example: A system that, without asking, searches three websites, extracts data, deduplicates results, and writes a report.

### 3. Extended Horizon
The system operates over multiple steps, sessions, or time periods. It maintains context and state between steps and can resume after interruption.

Example: A system that runs over 20 minutes, issues 12 tool calls, and produces a final output — not a single round-trip.

### 4. Adaptive
The system adjusts its approach based on feedback and observations. If a tool call fails, it tries a different approach. If a search returns irrelevant results, it reformulates the query.

Example: The system notices that the first three web searches returned paywalled content and switches to a different search strategy.

**How to use these properties:** When evaluating whether to build or use an agentic architecture, ask: does the task actually require all four? A task that needs tool use but not extended horizon or adaptation is a standard agent, not an agentic system. Over-engineering to "full agentic" when it's not needed adds complexity and cost with no benefit.

---

## Key Vocabulary

| Term | Definition |
|------|-----------|
| **Agent** | A single LLM that can use tools in a reasoning loop |
| **Agentic system** | An architecture of multiple agents, memory, orchestration, and reliability mechanisms working toward a goal |
| **Orchestrator** | The agent responsible for planning, task decomposition, and delegating to subagents |
| **Subagent** | A specialized agent that executes a specific subtask assigned by an orchestrator |
| **Tool** | A callable function (API, search, code executor) that gives an agent capabilities beyond text generation |
| **Planning** | Decomposing a goal into a sequence of subtasks that can be executed |
| **Grounding** | Constraining agent outputs to verifiable facts — via RAG (document grounding) or tool results (action grounding) |
| **HITL** | Human-in-the-loop — inserting a human approval or review step at defined points in the agent's execution |
| **Checkpointing** | Serializing agent state (conversation history, partial results, task ledger) to persistent storage so execution can resume after failure |
| **Idempotency** | A property of actions where executing the same action multiple times produces the same result — critical for safe retries |
| **Bounded autonomy** | Limits placed on an agent's autonomy: max steps, max time, max cost, max risk level — prevents runaway execution |
| **Context drift** | The gradual degradation of an agent's reasoning quality as the context window fills with accumulated history |
| **Task ledger** | A structured record of subtasks, their status (pending / in-progress / done / failed), and their outputs — used for replanning |

---

## Where Agentic AI Fits in the Stack

Agentic AI is not a replacement for RAG or standard agents — it's a composition of them, operating at a higher level of abstraction.

```
Agentic System (goal-directed, persistent, self-managing)
    ↓ uses
Multi-Agent Coordination (orchestrator + specialized subagents)
    ↓ each agent uses
Standard Agent Loop (LLM + tools + ReAct reasoning)
    ↓ tools may use
RAG (knowledge retrieval), APIs, code execution, databases
    ↓ RAG uses
Embeddings + Vector Stores (semantic search over your documents)
```

**RAG provides knowledge** — the ability to answer questions grounded in your documents.
**Agents provide tools** — the ability to take actions beyond text generation.
**Agentic AI provides agency** — the ability to decide what to do, coordinate multiple agents, maintain persistent state, and operate toward a goal over time.

Each layer solves a different problem. The skill in system design is knowing which layer(s) a given task actually needs.

---

## Study Notes

- Agentic AI is about **systems**, not models. The model's capability matters, but the system design — orchestration, memory, reliability, HITL — is what makes or breaks a production agentic system.
- The spectrum metaphor is more useful than a binary definition. When someone asks "is this agentic?", ask which of the four properties it has and to what degree.
- Agentic systems are **harder to evaluate** than traditional AI. A wrong final answer is obvious; a subtly wrong intermediate step that compounds into a wrong final answer is not.
- The biggest practical risk in agentic systems is **unintended action** — the system takes a real-world action (sends an email, deletes a file, makes an API call) that was not intended. HITL and bounded autonomy are the primary mitigations.

---

## Q&A Review Bank

**Q1: What is the fundamental difference between traditional AI and agentic AI?** `[Easy]`
A: Traditional AI is reactive — given a single input, it produces a single output and stops. Agentic AI is proactive — given a goal, it decides what steps to take, executes them, observes results, and continues until the goal is met. The key shift is who holds the initiative: in traditional AI the human drives every step; in agentic AI the system drives the steps within a defined goal boundary. This difference is not just technical but architectural — agentic systems require planning, memory, tool use, and failure handling that single-turn systems don't need.

**Q2: What are the four core properties of an agentic system?** `[Easy]`
A: Goal-directed (the system pursues an objective, not just responds to input), Autonomous Action (takes real-world actions without human approval at each step), Extended Horizon (operates across multiple steps and sessions with persistent state), and Adaptive (adjusts its approach based on feedback and failure). Most real systems sit somewhere between fully agentic and fully traditional — the four properties describe a spectrum. When evaluating whether to use an agentic architecture, ask whether the task actually requires all four; over-engineering to "full agentic" when it's not needed adds cost and complexity.

**Q3: Why isn't a RAG system considered agentic, even though it uses retrieval tools?** `[Medium]`
A: A RAG system is Level 2 on the autonomy spectrum — it retrieves relevant context before generating, but it's still fundamentally reactive: one retrieval plus one generation per query. It doesn't decide what to do next based on results, can't take actions beyond answering, and has no extended horizon or goal-directed behavior. Agentic systems start at Level 3 (single agent) where an LLM can use tools in a loop, reason about results, and continue until a multi-step task is complete. RAG provides knowledge; agentic systems provide agency — the ability to decide and act.

**Q4: What is "context drift" and why does it only appear in agentic systems?** `[Medium]`
A: Context drift is the gradual degradation of an agent's reasoning quality as the context window fills with accumulated history — the agent starts losing track of the original goal and later reasoning contradicts earlier reasoning. It only appears in extended-horizon systems because a single-turn LLM never accumulates more than one round of context. In agentic systems, a task ledger (a separate structured record of the goal and remaining steps) is the primary mitigation — the goal is always retrievable even when the conversation history is long or summarized.

**Q5: What does "bounded autonomy" mean and why is it essential in production?** `[Hard]`
A: Bounded autonomy means placing explicit limits on an agent's ability to act: maximum steps, maximum wall-clock time, maximum cost, maximum number of retries, and a restricted set of permitted actions. Without these limits, agents can enter infinite retry loops, exhaust API quotas, accumulate runaway costs, or take unintended real-world actions. In production, every agent config should declare these limits explicitly, and when a limit is hit the agent should record partial results, set a status flag, and exit gracefully — not silently fail or continue indefinitely. Bounded autonomy is what separates a reliable production system from a demo that works in the happy path.

**Q6: Why does moving up the autonomy spectrum reduce predictability, and how do you manage that tradeoff?** `[Hard]`
A: Each level up the spectrum adds emergent behavior: the system makes more of its own decisions, meaning more paths through the state space are possible. A chatbot has one output per input. An agentic system can take dozens of different tool-call sequences to reach the same goal — and some of those sequences may be subtly wrong in ways that don't surface until production. You manage this tradeoff by investing in trajectory evaluation (evaluating the execution path, not just the final answer), HITL gates for high-risk decisions, and observability tooling (LangSmith, Langfuse) that captures every step for debugging. The goal isn't to eliminate unpredictability but to instrument it so failures are detectable and correctable.
