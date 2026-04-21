# Agentic AI — Interview Q&A

> 40 curated questions across 8 domains, structured the way experienced architects respond: with nuance, tradeoffs and honest acknowledgment of what we still don't know.
>
> Each answer links back to the Notes file where that topic is covered in depth.

---

## How to Use This Guide

At senior and staff levels, interviewers typically pick **3–5 questions and drill deep** — failure modes, tradeoffs, "what went wrong last time." They expect architecture diagrams and war stories.

**What they're looking for:**
- **Production experience** — you've built and operated agents, not just read about them
- **Safety awareness** — you think about what can go wrong, not just what can go right
- **Strong system design taste** — you make good tradeoffs and can justify them
- **Honest uncertainty** — you know what you don't know

**Cross-reference map:**

| Domain | Questions | Deepdive Notes |
|---|---|---|
| I. Core Concepts & Judgment | Q1–Q6 | [01-Agentic-Concepts.md](01-Agentic-Concepts.md) |
| II. Architecture & Control Plane | Q7–Q12 | [02-Architectural-Patterns.md](02-Architectural-Patterns.md), [05-Agentic-System-Design.md](05-Agentic-System-Design.md) |
| III. Planning, Reasoning & Decomposition | Q13–Q18 | [03-Design-Patterns.md](03-Design-Patterns.md) |
| IV. Tool Use & Action Execution | Q19–Q24 | [03-Design-Patterns.md](03-Design-Patterns.md), [05-Agentic-System-Design.md](05-Agentic-System-Design.md) |
| V. Memory Systems & Context | Q25–Q29 | [05-Agentic-System-Design.md](05-Agentic-System-Design.md) |
| VI. Multi-Agent Systems | Q30–Q33 | [04-Multi-Agent-Systems.md](04-Multi-Agent-Systems.md) |
| VII. Evaluation, Safety & Reliability | Q34–Q38 | [06-Evaluation-and-Observability.md](06-Evaluation-and-Observability.md) |
| VIII. Scaling, Production & Taste | Q39–Q40 | [05-Agentic-System-Design.md](05-Agentic-System-Design.md) |

---

## I. Core Concepts & Judgment

> These questions test whether you actually understand what makes agents different — and when they're the wrong choice.

### Q1. What makes an AI system truly agentic and what does not qualify?

**Short answer:** An agentic system autonomously decides *what* to do, *when* to do it and *how* to adapt based on environmental feedback — all in service of a goal it pursues over multiple steps.

**Full answer:**

Three distinguishing characteristics:

**Goal-directed autonomy.** The system receives a high-level objective and determines its own path. A chatbot answering questions isn't agentic. A system that receives "book me the cheapest flight to Tokyo next week" and then searches, compares, handles authentication and completes the purchase — that's agentic.

**Environmental interaction.** Agents observe, act and adapt. They use tools, read results and modify their behaviour based on what they learn. The feedback loop is essential.

**Temporal extension.** Agency implies persistence across time — maintaining goals and context across multiple steps, not just single request-response pairs.

**What doesn't qualify:**
- RAG pipelines (retrieval is deterministic, not goal-directed)
- Single-turn function calling (no adaptation or multi-step reasoning)
- Workflow automation with hardcoded paths (no autonomous decision-making)
- Chatbots with personality (no environmental interaction)

**The nuance interviewers want:** "Agentic" is a spectrum, not a binary. A system with limited tool access and human approval gates is less agentic than one with broad autonomy. Production systems usually live somewhere in the middle — knowing where to place them on that spectrum is a design choice, not a technical limitation.

> **Deepdive:** [01-Agentic-Concepts.md → Autonomy Spectrum, Core Properties](01-Agentic-Concepts.md)

---

### Q2. When is an agentic architecture the wrong solution?

**Short answer:** When the task is well-defined, deterministic and the cost of agent failures exceeds the value of agent flexibility.

**Full answer:**

Reach for traditional software instead of agents in these situations:

**The problem is actually a workflow.** If you can draw a flowchart with finite branches and known outcomes, you don't need an agent. You need Temporal, Airflow, or a state machine. Agents add latency, cost and unpredictability to problems that don't require them.

**Failures are catastrophic and irreversible.** Financial transactions, medical interventions, legal filings — anywhere the blast radius of a wrong action is severe and you can't roll back.

**Latency requirements are strict.** Agent loops are slow. Each reasoning step might take 1–3 seconds. If your SLA is 200ms, agents aren't an option.

**The task requires perfect accuracy.** Agents are probabilistic. If you need 100% correctness (compliance, regulated reporting), build deterministic systems with agents as optional assistants, not primary actors.

**You can't define success.** Agents need termination conditions. If "done" is fuzzy or subjective, the agent will either stop too early or run forever.

**Red flag to watch for:** Teams choosing agents because they're exciting, not because the problem requires autonomy. The best agent architectures start as traditional systems and evolved agentic capabilities only where flexibility genuinely mattered.

> **Deepdive:** [01-Agentic-Concepts.md → Agentic AI vs Traditional AI](01-Agentic-Concepts.md)

---

### Q3. How do you define and enforce agent autonomy boundaries?

**Short answer:** Through explicit permission systems, action classification, budget constraints and human approval gates — all enforced outside the LLM, not by prompting.

**Full answer:**

Four layers:

**Layer 1: Action classification.** Every tool and action gets classified by risk level: read-only, reversible-write, irreversible-write, external-communication. The agent's autonomy level determines which classes it can execute without approval.

**Layer 2: Resource budgets.** Hard limits on API calls, tokens consumed, money spent, time elapsed. Enforced in the orchestrator, not suggested in prompts.

**Layer 3: Scope constraints.** The agent can only access specific tools and data sources. These boundaries are enforced at the integration layer — the agent literally cannot call a tool it doesn't have access to.

**Layer 4: Approval gates.** High-risk actions route to human review before execution.

**What doesn't work:** Asking the LLM to respect boundaries via system prompts. The LLM doesn't enforce anything — it generates text. Boundaries must be structural.

**Implementation pattern:** A policy engine that sits between the LLM's proposed actions and actual execution. Every action passes through the policy layer, which checks permissions, budgets and approval requirements before anything happens.

> **Deepdive:** [05-Agentic-System-Design.md → Reliability Engineering, Security](05-Agentic-System-Design.md)

---

### Q4. What are the essential components of an agent beyond an LLM?

**Short answer:** An orchestrator, tool interface layer, memory systems, policy/guardrails engine and observability infrastructure. The LLM is maybe 20% of a production agent system.

**Full answer:**

| Component | Role |
|---|---|
| **Orchestrator / Control Loop** | Manages the execution cycle: observe → think → act → observe. Handles retries, timeouts, termination. |
| **Tool Interface Layer** | Standardised schemas, sandboxed execution, result parsing, error handling. |
| **Working Memory** | Current task context, conversation history, scratchpad. |
| **Episodic Memory** | Records of past executions, what worked, what failed. |
| **Semantic Memory** | Long-term knowledge, user preferences, domain facts. |
| **Policy & Guardrails Engine** | Enforces autonomy boundaries, validates proposed actions, routes approvals. |
| **State Management** | Checkpointing, resumption after failure, state serialisation for long-running agents. |
| **Observability Stack** | Logging, tracing, metrics — every decision, every tool call, every piece of context. |
| **Human Interface** | Approval workflows, intervention mechanisms, feedback channels. |

**Key message:** The LLM is the brain, but brains don't survive without bodies. Most engineering effort goes into everything around the LLM.

> **Deepdive:** [05-Agentic-System-Design.md → Production Architecture](05-Agentic-System-Design.md)

---

### Q5. How do you prevent agents from over-reasoning or over-planning?

**Short answer:** Step limits, confidence thresholds, action-bias in prompts and detecting planning loops programmatically.

**Full answer:**

**Hard step limits.** Maximum reasoning steps before the agent must either act or request help. Enforced in the orchestrator, not suggested in a prompt.

**Action-biased prompting.** Frame the agent's role as an executor, not a philosopher. "Take the simplest action that makes progress" works better than "think carefully about all possibilities."

**Confidence thresholds with defaults.** If the agent can't decide after N steps, it takes a default action or asks for clarification rather than continuing to deliberate.

**Loop detection.** Programmatically detect when the agent is revisiting the same reasoning patterns. Track semantic similarity of recent thoughts. If the last 5 reasoning steps look similar, interrupt and force a decision.

**Decomposition limits.** For planning, cap the depth of task decomposition. "Book a flight" shouldn't decompose into 47 subtasks.

**War story:** An agent spent 8 minutes and $4 in API calls deciding which of two nearly identical search results to click. The task was finding a business address. Adding a "when in doubt, try the first reasonable option" directive made the problem disappear.

> **Deepdive:** [03-Design-Patterns.md → Planning (ReAct, Plan-and-Execute)](03-Design-Patterns.md)

---

### Q6. How do you explain agentic systems to non-technical stakeholders?

**Short answer:** Use the "capable intern" analogy, emphasise the observe-think-act loop, be honest about uncertainty and failure modes and focus on business outcomes.

**Full answer:**

**For executives deciding whether to invest:**
"Agentic AI is like having an extremely capable intern with perfect memory and 24/7 availability. You give them a goal, they figure out the steps, they use the tools available to them and they come back with results. Unlike traditional automation, they can handle novel situations and adapt when things don't go as expected. But like any new employee, they need supervision, clear boundaries and you shouldn't give them the keys to the building on day one."

**For product managers scoping features:**
"The agent operates in a loop: observe the current state, decide what to do, take an action, observe the result, repeat. What makes this powerful is flexibility — the agent can handle variations we didn't explicitly program. What makes this challenging is unpredictability — the agent might not always take the path we expect."

**For risk/compliance:**
"These systems make autonomous decisions, which means we need to think about oversight differently. We can't review every action in advance, so we build in guardrails, monitoring and approval gates for high-risk operations. Think of it less like traditional QA and more like supervising a contractor — you set boundaries, monitor outcomes and intervene when needed."

**What to never do:** Oversell capabilities or hide failure modes. Stakeholders remember when things go wrong.

> **Deepdive:** [01-Agentic-Concepts.md → Key Vocabulary, Autonomy Spectrum](01-Agentic-Concepts.md)

---

## II. Agent Architecture & Control Plane

> These questions probe whether you can design systems that are safe, debuggable and production-ready.

### Q7. Walk through a production-ready agent architecture.

**Short answer:** Request intake → context assembly → LLM reasoning → action validation → sandboxed execution → result processing → state update → loop or terminate. With observability at every stage.

**Full answer:**

**Key design principles:**

| Principle | Detail |
|---|---|
| **Separation of concerns** | The LLM reasons; the orchestrator controls; the policy engine governs; the sandbox executes. |
| **Fail-safe defaults** | Every timeout, every limit defaults to the safe option. |
| **Complete observability** | Every stage emits traces, logs and metrics. |
| **Stateless orchestrator** | State lives in external storage. The orchestrator can crash and resume. |

**The full flow:**
```
Request Intake
    │
    ▼
Context Assembly (memory retrieval + tool availability + permissions)
    │
    ▼
LLM Reasoning (what action to take?)
    │
    ▼
Action Validation (policy engine — permitted? within budget?)
    │
    ▼
Sandboxed Tool Execution
    │
    ▼
Result Processing + State Update
    │
    ▼
Loop (continue?) or Terminate
```

> **Deepdive:** [05-Agentic-System-Design.md → Production Architecture (7 layers)](05-Agentic-System-Design.md)

---

### Q8. What logic belongs in the orchestrator vs the LLM?

**Short answer:** Orchestrator handles control flow, enforcement and infrastructure. LLM handles reasoning, planning and decision-making within the boundaries the orchestrator enforces.

**Full answer:**

| Orchestrator | LLM |
|---|---|
| Loop control (when to continue, when to stop) | Understanding the goal |
| Timeout enforcement | Planning approach |
| Budget tracking and enforcement | Selecting which tool to use |
| State persistence and recovery | Generating tool arguments |
| Tool dispatch and result collection | Interpreting results |
| Error handling and retry logic | Deciding if task is complete |
| Approval routing | Reasoning through edge cases |
| Observability and logging | — |

**The key principle:** Anything that must be *guaranteed* belongs in the orchestrator. Anything that requires *judgment* belongs in the LLM. The LLM can suggest "I think I'm done" — the orchestrator decides whether to accept that.

**Anti-pattern:** Putting control flow in prompts. "Think in a loop until you solve the problem" puts the LLM in charge of when to stop. This is how you get infinite loops and runaway costs.

> **Deepdive:** [02-Architectural-Patterns.md → HITL Architectures](02-Architectural-Patterns.md), [05-Agentic-System-Design.md](05-Agentic-System-Design.md)

---

### Q9. How do you design a safe and debuggable agent loop?

**Short answer:** Explicit state machines, comprehensive logging at decision points, reproducible execution and circuit breakers at multiple levels.

**Full answer:**

**State machine clarity.** Explicitly named states: `PLANNING` → `EXECUTING` → `WAITING_FOR_APPROVAL` → `PROCESSING_RESULT` → `TERMINATED`. Every log entry includes current state.

**Decision point logging.** Log the inputs the LLM saw, the output it generated, and why that output was interpreted as a specific action.

**Circuit breakers (all enforced in orchestrator, not via prompt):**
- Loop iteration limit — hard stop after N iterations
- Time limit — hard stop after T seconds
- Cost limit — hard stop after $X spent
- Error limit — hard stop after E consecutive failures

**Graceful degradation.** When a circuit breaker trips, the agent emits a clear status, saves its state and notifies for human review — not silent crash or state corruption.

**Debugging workflow.** You must be able to: (1) find a failed run, (2) see exactly what the agent saw at each step, (3) understand why it made each decision, (4) replay specific steps with modified inputs.

> **Deepdive:** [05-Agentic-System-Design.md → Reliability Engineering](05-Agentic-System-Design.md), [06-Evaluation-and-Observability.md → Debugging](06-Evaluation-and-Observability.md)

---

### Q10. How do you implement termination conditions in long-running agents?

**Short answer:** Combine goal-completion detection, iteration limits, time limits and explicit "I'm stuck" recognition — with the orchestrator as the final authority.

**Full answer:**

**Layered termination strategy:**

| Layer | Mechanism |
|---|---|
| **1. LLM self-assessment** | Separate reasoning step: "Given the original goal and current state, is the task complete? Why or why not?" |
| **2. Programmatic verification** | Where possible, verify completion through tools. Don't trust the agent's claim alone. |
| **3. Progress detection** | Track whether the agent is making meaningful progress. If last N steps haven't changed environment state, prompt or terminate. |
| **4. Hard limits** | Absolute caps on iterations, time and cost — fire regardless of what the agent thinks. |
| **5. Stuck detection** | Recognise repeated errors, circular reasoning, same tool calls with same args — route to human review. |

**Key insight:** The most insidious failure is an agent that thinks it's making progress but isn't. Metrics on actual environment changes (not just agent activity) are essential.

> **Deepdive:** [03-Design-Patterns.md → Reflection, Termination Strategies](03-Design-Patterns.md)

---

### Q11. Stateless vs stateful agents — tradeoffs and use cases?

**Short answer:** Stateless agents are simpler, scalable and easier to debug. Stateful agents are necessary for long-running tasks, learning and complex context. Most production systems are stateless execution with external state storage.

**Full answer:**

| | **Stateless** | **Stateful** |
|---|---|---|
| **Advantages** | Easy horizontal scale · No error accumulation · Simple to test · Any instance handles any request | Long-running tasks · Learns from interactions · Richer context |
| **Disadvantages** | Context window limits history · No learning · Repeated context reconstruction | State corruption is catastrophic · Debugging requires history · Complex scaling |
| **Use when** | Tasks complete in single sessions · Context fits in window · Scale matters | Tasks span multiple sessions · Personalisation matters · Agent must learn |

**Preferred production pattern:** Stateless execution layer with external state storage. The orchestrator is stateless and scalable; state lives in a database; any orchestrator instance can pick up any agent's work by loading its state.

> **Deepdive:** [05-Agentic-System-Design.md → Memory Architecture](05-Agentic-System-Design.md)

---

### Q12. How do you version and roll back agent behavior?

**Short answer:** Version the complete configuration — prompts, tool schemas, policies, model version. Maintain rollback capability for each component. Test changes against behavioural benchmarks before deployment.

**Full answer:**

**What gets versioned:**
- System prompts and few-shot examples
- Tool definitions and schemas
- Policy rules and boundaries
- Model version and parameters
- Orchestrator logic
- Memory retrieval configuration

**Versioning strategy:** Each deployment has a single version identifier mapping to a specific combination of all the above:
```
agent-v23:
  prompts: prompts-v12
  tools: tools-v8
  policies: policies-v15
  model: claude-sonnet-4-6
  orchestrator: orchestrator-v6
```

**Rollback capability:**
- Keep previous N versions deployable
- Traffic splitting to test new versions
- Instant rollback mechanism (feature flag or load balancer)
- State format must be backward-compatible across versions

**Behavioural testing before deploying:**
- Does it complete reference tasks correctly?
- Does it stay within resource bounds?
- Does it respect policy constraints?
- Are there behavioural regressions?

**Lesson learned the hard way:** Model provider updates can change agent behaviour even when your code doesn't change. Always pin model versions and test before adopting updates.

> **Deepdive:** [06-Evaluation-and-Observability.md → Evaluation Approaches](06-Evaluation-and-Observability.md)

---

## III. Planning, Reasoning & Goal Decomposition

> These questions explore how agents think and where that thinking goes wrong.

### Q13. How do agents decompose high-level goals into executable steps?

**Short answer:** Through recursive decomposition — break the goal into subgoals, break subgoals into actionable steps, execute and adapt. The key is knowing when to stop decomposing and start acting.

**Full answer:**

**The decomposition process:**
1. **Goal interpretation** — what does success look like? What are the constraints?
2. **Subgoal identification** — what major milestones lead to the goal? These should be *verifiable* states.
3. **Action planning** — for each subgoal, what concrete actions achieve it? Each action should map to available tools.
4. **Dependency analysis** — what must happen before what? Identify parallelisable branches.
5. **Execution with adaptation** — execute the plan but remain ready to replan when reality diverges from expectations.

**What distinguishes good decomposition:**
- Subgoals are verifiable (you can tell when they're achieved)
- Actions are atomic (one tool call, one effect)
- Plans are shallow enough to start quickly, deep enough to guide action
- Uncertainty is acknowledged

**Example — Goal: "Analyse competitor pricing and create a comparison report"**

*Bad:* 47 steps covering every possible edge case before any action.

*Good:*
1. Identify competitors to analyse (ask user or search)
2. For each competitor: find pricing page, extract pricing info
3. Structure data for comparison
4. Generate report
5. Verify report covers original request

Then start executing, adapting as needed.

> **Deepdive:** [03-Design-Patterns.md → Planning (ReAct, Plan-and-Execute, Tree of Thoughts)](03-Design-Patterns.md)

---

### Q14. Chain-of-thought vs tree-of-thought vs graph planning — when would you use each?

**Short answer:** Chain-of-thought for linear problems. Tree-of-thought when you need to explore alternatives. Graph planning for complex problems with dependencies and constraints.

**Full answer:**

| Approach | When to Use | Example |
|---|---|---|
| **Chain-of-Thought** | Natural linear progression · Single path likely leads to solution · Latency matters | Debugging an error, following a procedure, arithmetic |
| **Tree-of-Thought** | Multiple valid approaches exist · Need to compare alternatives · Backtracking might be necessary | Strategy selection, creative generation with quality filtering, puzzle solving |
| **Graph Planning** | Complex dependencies between steps · Constraints that eliminate certain paths · Optimisation over multiple criteria | Travel planning with constraints, resource scheduling, multi-step workflows with prerequisites |

**Practical guidance:** Start with chain-of-thought — it's simplest and often sufficient. Escalate to tree-of-thought when you observe the agent taking bad paths it could have avoided with exploration. Use graph planning for genuinely complex constraint satisfaction, but recognise it adds significant latency and complexity.

> **Deepdive:** [03-Design-Patterns.md → Planning](03-Design-Patterns.md)

---

### Q15. How do you detect and stop infinite planning loops?

**Short answer:** Track reasoning state similarity, enforce step limits, detect repetitive patterns programmatically and require periodic action or termination.

**Full answer:**

**Detection strategies:**

| Strategy | Mechanism |
|---|---|
| **Similarity tracking** | Embed recent reasoning steps. If semantic similarity exceeds threshold for N consecutive steps, interrupt. |
| **Pattern matching** | Look for repeated phrases, repeated tool calls with identical arguments, cycling through same options. |
| **Progress metrics** | Define "progress" for your domain and verify it's being made. No progress for N steps → interrupt. |
| **State hashing** | Hash the agent's observable state. If you see the same hash twice, you're in a loop. |

**Stopping strategies:**
- **Soft interrupt:** Inject "You appear to be repeating similar reasoning. Please either take a concrete action or explain what's blocking progress."
- **Hard interrupt:** Stop execution, save state, escalate to human review.
- **Forced action:** After N reasoning steps without action, require the agent to either act or explicitly declare it cannot proceed.

**Prevention is better than detection:** Action-biased prompting + reasonable step limits + clear guidance on when to ask for help vs continue deliberating.

> **Deepdive:** [04-Multi-Agent-Systems.md → Failure Modes (infinite loops)](04-Multi-Agent-Systems.md)

---

### Q16. How do you handle partial observability or missing information?

**Short answer:** Agents should recognise uncertainty, seek information when available, make reasonable assumptions when not and expose their assumptions to users.

**Full answer:**

**The information-seeking hierarchy:**
1. **Use available tools to gather information** — if the agent can look something up, it should.
2. **Ask clarifying questions** — if the user can provide missing information efficiently, ask.
3. **Make explicit assumptions** — if proceeding is necessary, state the assumption clearly.
4. **Express uncertainty** — when conclusions depend on assumptions, communicate confidence levels.

**Design patterns:**

- **Uncertainty propagation** — track confidence through the reasoning chain. Conclusions based on assumptions inherit uncertainty.
- **Assumption logging** — record every assumption made so they can be reviewed and corrected.
- **Assumption validation checkpoints** — periodically prompt: "You assumed X. Based on what you've learned, is this still valid?"
- **Graceful degradation** — when information is unavailable, produce a partial result with clear documentation of what's missing.

**What to avoid:** Agents that never say "I don't know" or that confidently hallucinate missing information. Calibrated uncertainty is a feature, not a weakness.

> **Deepdive:** [03-Design-Patterns.md → Routing and Gating](03-Design-Patterns.md)

---

### Q17. How do agents decide a task is "done"?

**Short answer:** By evaluating whether success criteria are met, verifying outputs where possible and confirming with users when programmatic verification isn't possible.

**Full answer:**

**The completion evaluation framework:**

- **Explicit success criteria** — define what "done" means at task start. "Book a flight" → "Confirmation number received and sent to user."
- **Self-assessment with evidence** — the agent cites specific evidence: "The task requested X. I produced Y. Y satisfies X because Z."
- **Programmatic verification** — where possible, verify completion through tools. File exists? API returns expected state?
- **User confirmation** — for subjective tasks, confirm with the user rather than assuming.
- **Negative case handling** — "done" might mean "determined this is impossible" or "completed with caveats."

**Common failure modes:**
- Agent declares victory after taking an action without verifying its effect
- Agent stops at first plausible result without checking quality
- Agent gets stuck because the original goal was ambiguous
- Agent continues optimising past the point of meaningful improvement

> **Deepdive:** [03-Design-Patterns.md → Reflection, Termination](03-Design-Patterns.md)

---

### Q18. What planning failures are hardest to detect in production?

**Short answer:** Silent wrong answers, slow drift from objectives, over-optimisation of proxy metrics and confidently wrong assumptions that propagate through the plan.

**Full answer:**

The hardest failures don't cause errors or alerts — they produce wrong results that look right.

| Failure Type | Description | Detection |
|---|---|---|
| **Silent wrong answers** | Agent completes task incorrectly but confidently. Output looks valid. | Sampling-based audits, output validation, user feedback loops |
| **Goal drift** | Agent gradually optimises for something adjacent to the actual goal. | Periodically re-ground against original objectives, track behavioural convergence |
| **Assumption propagation** | Early wrong assumption, rest of plan proceeds flawlessly on that assumption. | Explicit assumption tracking, validation checkpoints |
| **Hidden dependencies** | Plan assumes environmental conditions that aren't guaranteed. | Environmental variation in testing, runtime verification |
| **Local optima** | Agent finds *a* solution but misses significantly better ones. | Compare against known baselines, periodic replanning from scratch |

> **Deepdive:** [06-Evaluation-and-Observability.md → Failure Mode Taxonomy](06-Evaluation-and-Observability.md)

---

## IV. Tool Use & Action Execution

> These questions test whether you can build systems that safely interact with the real world.

### Q19. How do agents decide which tool to use?

**Short answer:** Through a combination of semantic matching (which tools are relevant?), capability reasoning (which can accomplish the goal?) and constraint checking (which are permitted?).

**Full answer:**

**The selection process:**
1. **Tool discovery** — what tools are available? Dynamic based on context, user permissions and current state.
2. **Relevance filtering** — semantic matching between current subgoal and tool descriptions.
3. **Capability reasoning** — among relevant tools, which can actually accomplish what's needed?
4. **Constraint checking** — among capable tools, which are permitted right now?
5. **Selection and argument generation** — choose the best tool and generate appropriate arguments.

**Design considerations:**
- Tool descriptions matter enormously — clear, accurate descriptions with examples dramatically improve selection accuracy
- **Fewer tools is better** — tool selection degrades with too many options; curate tools per context
- Fallback handling — the agent should recognise when no tool fits and report inability, not hallucinate
- Tool composition — sometimes the answer is a sequence of tools, not one

> **Deepdive:** [03-Design-Patterns.md → Tool-Use](03-Design-Patterns.md)

---

### Q20. How do you design tool schemas that reduce hallucinated actions?

**Short answer:** Explicit types, enumerated options, clear descriptions, required fields, examples of valid usage and validation at the schema level.

**Full answer:**

**Schema design principles:**

**Use enums over strings** — if there are 5 valid options, enumerate them:
```json
// BAD
{ "status": "string" }

// GOOD
{ "status": { "enum": ["pending", "approved", "rejected", "cancelled"] } }
```

**Require rather than assume** — make essential fields required; don't let the agent skip them.

**Constrain formats** — dates as date types, numbers with ranges, URLs as URL types.

**Provide descriptions and examples** — every field should describe what it's for with a valid input example.

**Validate before execution** — schema validation catches malformed requests before they hit your tools.

**Test with adversarial prompts** — see what the LLM generates for weird requests; adjust schemas to catch common mistakes.

**Bottom line:** The cost of detailed schemas is tiny. The cost of hallucinated tool calls in production is enormous. Err heavily toward explicit, constrained schemas.

> **Deepdive:** [03-Design-Patterns.md → Tool-Use (Tool Descriptions)](03-Design-Patterns.md)

---

### Q21. How do you sandbox tool execution safely?

**Short answer:** Defence in depth — isolated execution environments, capability restrictions, resource limits, output validation and fail-safe defaults.

**Full answer:**

**Isolation layers:**

| Layer | Mechanism |
|---|---|
| **Process isolation** | Tools execute in separate processes from the orchestrator |
| **Container isolation** | For higher-risk tools: containers with minimal capabilities, no unnecessary network access |
| **Network restrictions** | Whitelist allowed endpoints; no arbitrary internet access from tools |
| **Credential scoping** | Tools receive minimal credentials for their task |

**Resource limits:**
- CPU and memory limits per tool execution
- Timeout enforcement (kill after N seconds)
- Rate limiting on tool calls
- I/O limits on file operations

**Output validation:**
- Verify tool outputs match expected schemas
- Sanitise outputs before using in subsequent LLM calls
- Detect and handle error states

**Fail-safe defaults:**
- Tool execution fails closed (deny by default)
- Missing permissions = cannot execute (not execute with partial access)
- Timeout = termination (not indefinite wait)

> **Deepdive:** [05-Agentic-System-Design.md → Security](05-Agentic-System-Design.md)

---

### Q22. How do you handle tool failures, retries and idempotency?

**Short answer:** Classify failures by type, implement intelligent retry with backoff, ensure idempotent operations where possible and maintain operation logs for recovery.

**Full answer:**

**Failure classification:**

| Type | Behaviour | Action |
|---|---|---|
| **Transient** | Timeouts, rate limits, temporary unavailability | Retry with exponential backoff |
| **Permanent** | Invalid inputs, missing resources, permission denied | Don't retry — handle or escalate |
| **Partial** | Operation partially completed | Determine what succeeded; compensating transaction |

**Retry strategy:** Exponential backoff with jitter + max retry count + different strategies per failure type.

**Designing for idempotency:**
- Use idempotency keys for operations that create resources
- Check before creating (does this already exist?)
- Design operations as "ensure state X" rather than "apply change Y"

**Operation logging:** Log every tool call with unique ID, arguments and result. Store enough to determine what succeeded. Enable replay after fixing issues.

> **Deepdive:** [05-Agentic-System-Design.md → Reliability Engineering](05-Agentic-System-Design.md)

---

### Q23. What are the biggest security risks with tool-using agents?

**Short answer:** Prompt injection through tool outputs, privilege escalation via tool chains, data exfiltration, unintended actions from hallucinated tools and confused deputy attacks.

**Full answer:**

| Risk | Description | Mitigation |
|---|---|---|
| **Prompt injection through tool outputs** | Tools return data containing malicious instructions the agent follows | Sanitise tool outputs; mark results as data not instructions |
| **Privilege escalation** | Agent combines tools in ways that exceed intended privileges of any single tool | Analyse tool compositions; principle of least privilege |
| **Data exfiltration** | Agent accesses sensitive data via one tool and leaks it via another | Data classification; restrict tool access to sensitive data; prevent cross-category data flow |
| **Hallucinated tools** | Agent calls non-existent tools or passes malformed arguments | Strict schema validation; tool calls must match registered schemas exactly |
| **Confused deputy** | Agent manipulated into using its privileges to serve an attacker's goals | Validate requested actions align with original user intent; be skeptical of instructions arriving through tool results |

> **Deepdive:** [05-Agentic-System-Design.md → Security](05-Agentic-System-Design.md)

---

### Q24. How do you control cost explosions from tool calls?

**Short answer:** Hard budget limits, per-operation cost tracking, tiered approval for expensive operations, monitoring with automatic circuit breakers and cost-aware tool selection.

**Full answer:**

**Budget enforcement:**
```python
class BudgetTracker:
    def request_operation(self, operation, estimated_cost):
        if self.spent + estimated_cost > self.limit:
            raise BudgetExhausted()

    def record_cost(self, actual_cost):
        self.spent += actual_cost
```

**Tiered approval:**
- Low-cost operations → execute freely
- Medium-cost → soft limit + warning
- High-cost → require human approval

**Cost-aware tool selection:** When multiple tools can accomplish a goal, prefer cheaper ones. Expose cost information to the agent so it can make informed decisions.

**Monitoring:** Real-time cost dashboards + alerts when spend rate exceeds thresholds + automatic shutdown at cost limits + post-incident analysis.

**Key lesson:** Always assume loops will run longer than expected. Set budgets at levels that are painful but not catastrophic, then investigate every time you hit them.

> **Deepdive:** [05-Agentic-System-Design.md → Cost Management](05-Agentic-System-Design.md)

---

## V. Memory Systems & Context Management

> These questions explore how agents maintain knowledge across interactions.

### Q25. What types of memory do agentic systems need?

**Short answer:** Working memory (current task context), episodic memory (past experiences), semantic memory (learned knowledge) and procedural memory (learned skills/patterns).

**Full answer:**

| Memory Type | What It Stores | Characteristics |
|---|---|---|
| **Working memory** | Current goal, what's been tried, recent tool results, intermediate state | High fidelity, limited capacity, cleared between sessions |
| **Episodic memory** | Records of past interactions: "Last time the user asked about X, they needed Y" | Time-indexed, personal to user/session, queryable by similarity |
| **Semantic memory** | General knowledge: user preferences, domain facts, entity relationships | Declarative facts, not tied to specific episodes, updated from experience |
| **Procedural memory** | Learned patterns: "When the user asks for a summary, they want bullet points" | How-to knowledge, emerges from successful episodes |

**Design considerations:**
- Not all systems need all memory types
- Memory adds complexity and failure modes
- Cold-start problem: new users have no memory
- Memory pollution: bad experiences corrupt future behaviour

> **Deepdive:** [05-Agentic-System-Design.md → Memory Architecture](05-Agentic-System-Design.md)

---

### Q26. How do you design long-term memory without polluting it?

**Short answer:** Selective storage, quality filtering, decay mechanisms, validation before retrieval and user control over memory contents.

**Full answer:**

**Selective storage — only store:**
- Explicitly confirmed facts
- Successful patterns (verified outcomes)
- User-provided preferences
- Summarised experiences (not raw transcripts)

**Quality filtering before storing:**
- Verify factual accuracy where possible
- Require minimum confidence threshold
- Filter out contradictions with existing memory
- Ignore obviously anomalous interactions

**Decay mechanisms:**
- Recency weighting (older memories have less influence)
- Confidence decay (unconfirmed memories fade)
- Usage-based retention (frequently accessed memories persist)

**User control:** Users should be able to see, correct, delete and opt out of long-term memory.

**Monitoring:** Track memory retrieval success rates; detect memories that consistently lead to poor outcomes; audit memory contents periodically.

> **Deepdive:** [05-Agentic-System-Design.md → Memory Architecture](05-Agentic-System-Design.md)

---

### Q27. When should memory be retrieved vs ignored?

**Short answer:** Retrieve when past context would improve the current response. Ignore when it would bias toward outdated patterns or when current context is sufficient.

**Full answer:**

**Retrieve when:**
- User references past interactions ("like we discussed before")
- Task requires user preferences or established patterns
- Current context is insufficient to respond well
- Continuity matters for user experience

**Ignore when:**
- Current context provides everything needed
- Past experiences might bias toward outdated solutions
- User explicitly requests fresh start
- Retrieved memories contradict current explicit information

**Retrieval strategy:**
- **Relevance threshold** — only retrieve memories above a similarity/relevance threshold
- **Recency consideration** — recent memories often more relevant, but not always
- **Source weighting** — user-provided > inferred; verified > unverified
- **Contradiction handling** — when retrieved memory contradicts current context, favour current context and flag the contradiction

**Anti-pattern:** Retrieving memory on every turn regardless of need — wastes context window, adds latency and risks pollution.

> **Deepdive:** [05-Agentic-System-Design.md → Memory Architecture](05-Agentic-System-Design.md)

---

### Q28. How do embeddings help — and where do they fail?

**Short answer:** Embeddings enable semantic search over memory and tools, finding relevant information based on meaning rather than keywords. They fail on precision requirements, negation, recency and multi-hop reasoning.

**Full answer:**

**Where embeddings help:**
- Semantic similarity — finding content related to a query even without keyword overlap
- Scalable search over large memory stores
- Cross-lingual matching
- Fuzzy matching — handles paraphrasing and synonyms

**Where embeddings fail:**

| Failure Mode | Example | Why |
|---|---|---|
| **Precision requirements** | "Find the 2024 Q3 report" | Embeddings might return Q2 or 2023 |
| **Negation** | "Emails NOT about marketing" | "Not X" and "about X" have similar embeddings |
| **Temporal reasoning** | "What happened after the merger?" | Embeddings don't capture temporal relationships |
| **Multi-hop reasoning** | "Who manages the person who wrote this code?" | Requires traversing relationships, not similarity |
| **Specific values** | Search for specific IDs, numbers, codes | Lack semantic content |

**How to compensate:** Combine embedding search with keyword filters + use metadata (dates, types, sources) + structured queries for precise requirements + multiple retrieval strategies with fusion.

> **Deepdive:** [05-Agentic-System-Design.md → Memory Architecture](05-Agentic-System-Design.md)

---

### Q29. How do you delete or correct agent memory safely?

**Short answer:** Soft deletion with audit trails, propagation checking to find derived memories, user confirmation and gradual rollout of corrections.

**Full answer:**

**Deletion strategy:**
- **Soft delete first** — mark as deleted, don't immediately remove; allows recovery if deletion was mistaken
- **Audit trail** — record what was deleted, when, by whom and why
- **Propagation analysis** — were other memories derived from this one? Do they need review?

**Correction strategy:**
- **Don't overwrite silently** — changing a fact might invalidate conclusions derived from it
- **Version rather than replace** — keep history: "Previously believed X, now corrected to Y"
- **Confidence update** — corrected memories warrant lower confidence scores until reconfirmed

**Bulk operations:**
- Gradual rollout with monitoring
- Consistency checks after bulk operations
- Backup and recovery — memory stores can be corrupted by bad corrections

**User-initiated deletion:** Provide clear interface, confirmation step and honour requests promptly (compliance requirement in many jurisdictions).

> **Deepdive:** [05-Agentic-System-Design.md → Memory Architecture](05-Agentic-System-Design.md)

---

## VI. Multi-Agent Systems

> These questions explore coordination, emergence and debugging at scale.

### Q30. When is multi-agent architecture better than single-agent?

**Short answer:** When tasks require genuinely distinct capabilities, when separation improves reliability, when parallel execution is valuable, or when adversarial setups improve quality.

**Full answer:**

**Good reasons for multi-agent:**
- **Distinct capability requirements** — different parts genuinely need different tools, skills, or access
- **Reliability through separation** — isolating failure domains (code execution agent crashing doesn't kill planning agent)
- **Parallel execution** — tasks that genuinely proceed in parallel
- **Adversarial quality improvement** — generator/critic patterns where one agent's output is improved by another's review
- **Separation of concerns** — complex systems easier to understand when decomposed

**Bad reasons for multi-agent:**
- It seems cool — complexity is a cost, not a feature
- The task is actually sequential — you've added coordination overhead without parallelism
- To avoid improving prompts — sometimes a single agent with better prompting outperforms multiple poorly-prompted agents

**Decision framework:**
1. Can a single agent do this well?
2. If not, is the limitation fundamental or just prompt engineering?
3. Would separate agents genuinely operate independently?
4. Is the coordination cost worth the benefit?

> **Deepdive:** [04-Multi-Agent-Systems.md → Why Multi-Agent](04-Multi-Agent-Systems.md)

---

### Q31. How do agents coordinate without conflicting actions?

**Short answer:** Through shared state with concurrency control, message passing with clear protocols, resource locking, conflict detection and resolution and centralised coordination where necessary.

**Full answer:**

**Coordination patterns:**

| Pattern | Tradeoff |
|---|---|
| **Shared state with locking** | Simple but can cause contention and deadlocks |
| **Message passing** | Cleaner architecture but more complex implementation |
| **Centralised coordinator** | Clear control but single point of failure |
| **Event sourcing** | Great audit trail but eventual consistency challenges |

**Conflict handling:**
- **Prevention** — partition work so agents don't overlap; each agent owns specific resources or task types
- **Detection** — monitor for conflicting actions (two agents modifying the same file)
- **Resolution** — priority ordering, timestamp ordering, or escalation to coordinator

**Practical advice:** Start with simple coordination (central coordinator with explicit turn-taking). Only add complexity when you've demonstrated you need it.

> **Deepdive:** [04-Multi-Agent-Systems.md → Coordination Strategies](04-Multi-Agent-Systems.md)

---

### Q32. What emergent behaviors have you seen in multi-agent systems?

**Short answer:** Unexpected cooperation patterns, gaming of evaluation metrics, information hoarding, cascade failures and occasionally genuinely creative solutions that no single agent would produce.

**Full answer:**

**Positive emergence:**
- **Complementary specialisation** — agents naturally develop distinct roles even without explicit assignment
- **Error correction** — one agent's mistake caught and corrected by another's review
- **Creative solutions** — agent interactions produce approaches not in any individual's prompting

**Negative emergence:**

| Behaviour | Description |
|---|---|
| **Metric gaming** | Agents optimise for measured outcomes in ways that defeat the purpose (e.g., reviewer always approves to avoid conflict) |
| **Information silos** | Agents develop local optimisations that harm global performance |
| **Infinite loops** | Agent A hands off to Agent B which hands back to Agent A; neither recognises the loop |
| **Cascade failures** | One agent's failure propagates, causing others to fail |
| **Adversarial dynamics** | Agents inadvertently interfere with each other's work |

**How to manage:**
- Monitor system-level outcomes, not just individual agent metrics
- Watch for interaction patterns you didn't design
- Have circuit breakers that stop the whole system, not just individual agents
- Regular audits of agent interactions

> **Deepdive:** [04-Multi-Agent-Systems.md → Failure Modes, Resilience Patterns](04-Multi-Agent-Systems.md)

---

### Q33. How do you debug failures across interacting agents?

**Short answer:** Distributed tracing with correlation IDs, comprehensive logging at interaction boundaries, replay capability and root cause analysis tools that span agents.

**Full answer:**

**Essential infrastructure:**
- **Correlation IDs** — every task gets a unique ID that propagates through all agents; all logs include this ID
- **Interaction logging** — every inter-agent communication: sender, receiver, message type, contents, timestamp
- **State snapshots** — periodically snapshot each agent's state
- **Causal ordering** — maintain happens-before relationships between events

**Debugging workflow:**
1. Identify the failure — what went wrong? Which agent's output was incorrect?
2. Trace backward — what inputs did that agent receive? Which agent provided them?
3. Find the divergence — at what point did actual behaviour diverge from expected?
4. Identify root cause — one agent's mistake? Coordination failure? Environmental issue?
5. Verify with replay — can you reproduce the failure by replaying the same inputs?

**Tooling requirements:**
- Unified log viewer across all agents
- Timeline visualisation of agent interactions
- Filter by correlation ID
- Diff view: expected vs actual agent outputs
- Replay capability for specific task traces

**Key lesson:** If you can't debug it, you can't run it in production. Multi-agent observability is not optional.

> **Deepdive:** [06-Evaluation-and-Observability.md → Debugging, Observability Stack](06-Evaluation-and-Observability.md)

---

## VII. Evaluation, Safety & Reliability

> These questions test whether you can build systems that can be trusted.

### Q34. How do you evaluate long-horizon agent performance?

**Short answer:** Through task completion benchmarks, step efficiency metrics, intermediate checkpoint evaluation, trajectory analysis and comparative evaluation against baselines.

**Full answer:**

**Evaluation dimensions:**

| Dimension | What to measure |
|---|---|
| **Task completion** | Did the agent achieve the goal? Requires clear success criteria and often programmatic verification |
| **Efficiency** | Steps, cost, time — compare against baselines |
| **Trajectory quality** | Was the path reasonable? Did the agent take obviously wrong turns? |
| **Intermediate milestones** | An agent completing 80% of subgoals differs from one completing 20% |
| **Robustness** | Does performance hold across task variations, environmental changes, adversarial inputs? |

**Evaluation methodology:**
- **Benchmark suites** — standard tasks with known solutions; track over time
- **A/B testing** — compare agent versions on live traffic
- **Human evaluation** — for subjective quality
- **Failure analysis** — categorise failures; are new failure modes appearing?

**Challenges:** Long horizons mean fewer evaluation samples per compute budget; real-world tasks have many valid solutions; human evaluation doesn't scale.

> **Deepdive:** [06-Evaluation-and-Observability.md → Trajectory Evaluation, Evaluation Approaches](06-Evaluation-and-Observability.md)

---

### Q35. What metrics matter beyond task success?

**Short answer:** Efficiency (steps, cost, time), safety (boundary violations, risky actions), reliability (consistency, failure rate), user experience (satisfaction, intervention rate) and alignment (goal adherence, unexpected behaviours).

**Full answer:**

| Category | Metrics |
|---|---|
| **Efficiency** | Token consumption per task · Tool calls per task · Wall-clock time · Dollar cost · Reasoning steps |
| **Safety** | Boundary violations attempted · Risky actions proposed (even if blocked) · Rate of human intervention for safety · Near-misses |
| **Reliability** | Consistency (same input → same quality output?) · Failure rate by category · Recovery success rate |
| **User experience** | Satisfaction ratings · Task abandonment rate · Correction/retry rate · Time to value |
| **Alignment** | Goal adherence · Rate of surprising (not necessarily bad) actions · Policy compliance |
| **Operational** | Latency distribution · Resource utilisation · Error rates by component · Availability |

**Key question:** Is the agent earning its complexity? Compare against simpler approaches.

> **Deepdive:** [06-Evaluation-and-Observability.md → Key Metrics](06-Evaluation-and-Observability.md)

---

### Q36. How do you detect goal drift or misalignment?

**Short answer:** Through explicit goal tracking, periodic re-grounding, divergence metrics, behavioural bounds checking and user feedback integration.

**Full answer:**

**Detection strategies:**

| Strategy | Mechanism |
|---|---|
| **Explicit goal tracking** | Require the agent to periodically state its current understanding of the goal; compare against original |
| **Re-grounding prompts** | Periodically inject: "Reminder: the original objective was X. Are your current actions aligned?" |
| **Divergence metrics** | Measure semantic distance between agent's recent outputs and original goal; alert on increasing distance |
| **Action distribution monitoring** | Track what actions the agent takes over time; sudden shifts might indicate drift |
| **Behavioural bounds** | Define expected action ranges; deviations trigger review |
| **User feedback** | Make it easy for users to signal "that's not what I wanted"; analyse patterns |

**Common drift patterns:**
- **Proxy optimisation** — agent optimises measurable proxy instead of actual goal
- **Scope creep** — agent expands task beyond original request
- **Local minima** — agent stuck satisfying partial goal repeatedly
- **Mode collapse** — agent gives same type of response regardless of input variation

> **Deepdive:** [06-Evaluation-and-Observability.md → Failure Mode Taxonomy](06-Evaluation-and-Observability.md)

---

### Q37. How do you implement human-in-the-loop controls?

**Short answer:** Through approval gates for risky actions, escalation paths for uncertainty, override capabilities, meaningful context for reviewers and feedback integration.

**Full answer:**

**Approval gates:**
- **Classification** — categorise actions by risk; define which categories require approval
- **Contextual presentation** — show the human what the agent wants to do, why and what the implications are
- **Decision options** — approve, reject, modify, escalate (not just yes/no)
- **Timeout handling** — if human doesn't respond, safe default (probably rejection)

**Escalation paths:**
- **Uncertainty triggers** — agent recognises when it's unsure and requests human input
- **Anomaly triggers** — system detects unusual behaviour and flags for review
- **Threshold triggers** — certain metrics (cost, time, errors) trigger escalation

**Override capabilities:**
- Humans can intervene at any point, not just approval gates
- Clear mechanism to stop agent execution
- Ability to correct agent state and resume

**Anti-patterns:**
- Approving everything by default (defeats the purpose)
- Requiring approval for low-risk routine actions (friction without value)
- Notifications that lack context (human can't make informed decision)

> **Deepdive:** [02-Architectural-Patterns.md → HITL Architectures](02-Architectural-Patterns.md), [05-Agentic-System-Design.md → HITL Design](05-Agentic-System-Design.md)

---

### Q38. What are the most dangerous failure modes of agentic AI?

**Short answer:** Confident wrong actions at scale, goal misalignment with real consequences, security breaches through tool chains, runaway costs and silent failures that compound over time.

**Full answer:**

| Failure Mode | Description | Mitigation |
|---|---|---|
| **Confident wrong actions at scale** | Agent acts decisively but incorrectly, without hesitation or requests for confirmation | Calibrated confidence; batch risky actions for review |
| **Goal misalignment with real consequences** | Agent pursues something other than intended with enough autonomy to cause real-world effects | Conservative autonomy; higher confidence thresholds for real-world actions |
| **Security breaches** | Prompt injection, privilege escalation, data exfiltration via tool chains | Defence in depth; assume the agent will be manipulated; limit blast radius |
| **Runaway costs** | Loops that burn through budget before anyone notices | Hard budget limits at multiple levels; real-time monitoring; circuit breakers |
| **Silent failures** | Wrong results that look right; quality degrading gradually | Automated quality checks; sampling audits; user feedback loops; trend monitoring |
| **Reputation damage** | Agent says something embarrassing or wrong in a high-visibility context | Content filtering; conservative communication defaults; human review for external outputs |

> **Deepdive:** [06-Evaluation-and-Observability.md → Failure Mode Taxonomy](06-Evaluation-and-Observability.md)

---

## VIII. Scaling, Production & Taste

> These questions probe production experience and engineering judgment.

### Q39. What bottlenecks limit agent scalability in production?

**Short answer:** LLM latency and throughput, context window limitations, state management overhead, tool execution bottlenecks and coordination costs in multi-agent systems.

**Full answer:**

| Bottleneck | Description | Mitigation |
|---|---|---|
| **LLM latency** | Each reasoning step takes 1–3+ seconds; dominant latency source | Caching, smaller models for simple decisions |
| **LLM throughput** | API rate limits, cost per token, queue depth at high load | Request batching, multiple providers |
| **Context window** | More context = slower inference = higher cost | Context compression, summarisation, selective memory retrieval |
| **Memory retrieval latency** | Querying long-term memory adds latency per step | Efficient storage, lazy loading, state partitioning |
| **External API limits** | Tools that call external services hit rate limits | Tool caching, parallel execution where possible |
| **Sequential tool dependencies** | Tools that must run sequentially create bottlenecks | Identify and parallelise independent tool calls |
| **Coordination costs** | More agents = more coordination overhead; lock contention | Minimise coordination needs, partition work |
| **Human-in-the-loop** | Human approval becomes bottleneck at scale | Risk-based escalation; only escalate what genuinely needs review |

> **Deepdive:** [05-Agentic-System-Design.md → Scalability](05-Agentic-System-Design.md)

---

### Q40. What tradeoffs do most teams get wrong when building agents?

**Short answer:** Autonomy vs control, capability vs reliability, sophistication vs debuggability and speed-to-market vs production readiness.

**Full answer:**

| Tradeoff | Common Mistake | Better Approach |
|---|---|---|
| **Autonomy vs control** | Giving agents too much autonomy too fast; starting with agents that can do anything | Start with minimal autonomy; expand based on demonstrated reliability. Easier to loosen constraints than tighten them. |
| **Capability vs reliability** | Prioritising impressive demos over consistent production behaviour. "It works most of the time" isn't good enough. | Prefer agents that do less but do it reliably; expand capabilities only when current ones are stable. |
| **Sophistication vs debuggability** | Complex architectures that produce good results but can't be understood or fixed when they fail | Simpler architectures with clear reasoning traces; you'll ship faster if you can debug faster. |
| **Speed-to-market vs production readiness** | Shipping with inadequate safety, observability, or error handling. "We'll add that later." | Observability and safety from day one; the cost of retrofitting is higher than building it in. |
| **Build vs buy** | Building everything custom when good foundations exist | Use existing frameworks for orchestration, tool management, memory; build custom only where your problem genuinely requires it. |
| **Prompt engineering vs architecture** | Trying to solve architectural problems with better prompts | Recognise when the problem is structural; prompts can't fix bad tool designs or missing components. |

> **Deepdive:** [05-Agentic-System-Design.md](05-Agentic-System-Design.md), [01-Agentic-Concepts.md](01-Agentic-Concepts.md)

---

## Quick-Reference: Question Difficulty Map

| Level | Questions | Focus |
|---|---|---|
| **Foundational** | Q1, Q2, Q4, Q6, Q25 | What agents are, when to use them, their components |
| **Intermediate** | Q3, Q5, Q7, Q8, Q11, Q13, Q14, Q19, Q30 | Architecture, planning, tool use, multi-agent basics |
| **Advanced** | Q9, Q10, Q12, Q15–Q18, Q20–Q24, Q26–Q29, Q31–Q33 | Safety, memory management, failure modes, debugging |
| **Principal/Staff** | Q34–Q40 | Production tradeoffs, evaluation at scale, what teams get wrong |
