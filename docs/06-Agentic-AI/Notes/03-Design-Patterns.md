# Agentic Design Patterns

## Overview

Design patterns are **reusable solutions to recurring problems** within agentic systems. Where architectural patterns define the structure (how many agents and how they relate), design patterns define the **behavior and logic** of individual agents and agent interactions.

Five design patterns appear across almost all agentic systems:

| Pattern | Problem It Solves | Core Mechanism |
|---------|------------------|----------------|
| Tool-Use | Agent needs capabilities beyond text generation | LLM calls external functions and acts on results |
| Reflection | Single-pass outputs aren't good enough | Agent critiques its own output and revises |
| Planning | Complex goals need decomposition before execution | Explicit plan produced before any action is taken |
| Multi-Agent Coordination | Tasks too complex for one agent | Specialized agents collaborate via defined interfaces |
| Routing and Gating | Not all inputs need the same processing path | Conditional logic determines the execution branch |

---

## Tool-Use Pattern

### Concept

Tools extend an agent's capabilities beyond what an LLM can do with text alone: searching the web, reading files, executing code, calling APIs, querying databases. Without tools, an agent is a sophisticated text transformer. With tools, it can act on the world.

**How tool use works:**
1. The LLM is given a list of available tools (name, description, parameter schema)
2. When the LLM decides a tool is needed, it outputs a structured tool call (JSON)
3. The framework intercepts the tool call, executes the function, and returns the result
4. The LLM receives the tool result and continues reasoning

This loop (reason → tool call → observe result → reason again) is the **ReAct pattern** at its core.

### Designing Good Tools

**Write for the LLM, not just the implementation.** The tool description is part of the prompt. The LLM reads it to decide whether to use this tool and how.

| Good Tool Description | Bad Tool Description |
|----------------------|---------------------|
| "Search the company product database. Use this when the user asks about product availability, pricing, or specifications. Input: product name or SKU. Output: product details dict." | "Search products" |
| "Get current weather for a city. Returns temperature in Celsius, conditions (sunny/cloudy/rain), and humidity. Do NOT use for historical weather." | "Weather tool" |

**Rules for tool design:**
- Each tool should do one thing well (single responsibility)
- Parameter names and types should be self-evident
- Return types should be consistent and predictable
- Include error states in the return type (not just success)
- Document when NOT to use the tool (prevents misuse)

### Tool Chaining

Tools can be chained — the output of one tool becomes the input to another. The LLM manages this chaining naturally within its reasoning loop.

```
User: "Summarize the latest earnings report for AAPL"

Agent reasoning:
1. search_web("AAPL earnings report 2024") → returns URLs
2. read_url("https://apple.com/earnings/...") → returns raw text
3. extract_financials(raw_text) → returns structured data
4. [LLM synthesizes structured data into summary]
```

### Error Handling in Tool Loops

Tools fail. APIs return errors. The agent must handle these gracefully.

**Patterns:**
- Return structured errors: `{"error": "rate_limit", "retry_after": 30}` — gives the LLM actionable information
- Distinguish retryable from fatal errors in the tool response
- Set a max tool call limit per task to prevent infinite retry loops
- Log every tool call and result for debugging

### Code

```python
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

@tool
def search_products(query: str) -> dict:
    """Search the product catalog by name or description.
    
    Use this when the user asks about product availability, pricing, or details.
    Input: a product name, category, or description.
    Output: list of matching products with id, name, price, and stock.
    """
    # Mock product database
    catalog = {
        "laptop": {"id": "LP001", "name": "ProBook Laptop", "price": 1299, "stock": 15},
        "mouse": {"id": "MS001", "name": "Ergonomic Mouse", "price": 49, "stock": 200},
        "keyboard": {"id": "KB001", "name": "Mechanical Keyboard", "price": 129, "stock": 45},
    }
    results = [v for k, v in catalog.items() if query.lower() in k.lower()]
    return {"products": results, "count": len(results)} if results else {"error": "no_results", "query": query}

@tool
def check_order_status(order_id: str) -> dict:
    """Check the status of a customer order by order ID.
    
    Use this when the user asks about their order status, shipping, or delivery.
    Input: order ID (format: ORD-XXXXXX).
    Output: order status, estimated delivery, and tracking info.
    Do NOT use for product searches — use search_products instead.
    """
    orders = {
        "ORD-123456": {"status": "shipped", "delivery": "2024-12-20", "tracking": "UPS-789"},
        "ORD-654321": {"status": "processing", "delivery": "2024-12-22", "tracking": None},
    }
    return orders.get(order_id, {"error": "order_not_found", "order_id": order_id})

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
tools = [search_products, check_order_status]

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful customer support agent. Use the available tools to assist customers."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

agent = create_tool_calling_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
```

---

## Reflection Pattern

### Concept

Reflection is the pattern where an agent evaluates its own output, identifies weaknesses, and uses that critique to produce a better output. It's the agentic equivalent of "draft, review, revise."

The core insight: **a second LLM call evaluating an output is often cheaper and more reliable than trying to get a perfect first pass.** The LLM is better at judging text than producing perfect text on the first try.

### Variants

**Self-reflection (same model)**
The agent generates output, then is prompted to critique it in a separate call, then revises.

```
Pass 1: "Write a market analysis for EV batteries"
         → Draft analysis

Pass 2: "Review this analysis. What claims are unsupported? What is missing? Be specific."
         → Critique: "Missing competitive landscape section. Claim about market size cites no source."

Pass 3: "Revise the analysis based on this critique: [critique]"
         → Improved analysis
```

**External evaluator (separate model or role)**
A separate agent or a stronger model acts as the evaluator. This avoids the self-consistency bias — the same model will often fail to catch its own errors.

```
Generator Agent → Draft → Evaluator Agent → Critique → Generator Agent → Revision
```

**Test-driven reflection**
For code generation: write tests first, run the generated code against tests, feed failures back as the critique.

```
User: "Write a function that sorts a list of dicts by a given key"
Agent → generates code → runs unit tests → 2 tests fail
Agent → receives: "test_empty_list failed: KeyError on empty list; test_missing_key failed: should return original list"
Agent → revises code to handle edge cases → all tests pass
```

### When to Use Reflection

- When the first pass is consistently good but not production-quality
- When there's a verifiable quality criterion (test suite, rubric, factual check)
- When the output will be seen by users or acted upon directly

### When NOT to Use Reflection

- When the task is simple and one pass is sufficient (adds cost for no benefit)
- When you don't have a good stopping criterion (infinite loops are expensive)
- When latency is critical (each reflection adds a full LLM round-trip)

### Termination

Always define a termination condition:
- Score above threshold (e.g., evaluator scores above 8/10)
- No critical issues found (evaluator finds no "must fix" items)
- Max iterations reached (e.g., 3 revision rounds maximum)

### Code

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.3)

def reflect_and_revise(task: str, max_iterations: int = 3) -> str:
    # Generate initial draft
    draft = llm.invoke([
        SystemMessage(content="You are a professional technical writer."),
        HumanMessage(content=task)
    ]).content

    for iteration in range(max_iterations):
        # Evaluate the draft
        critique = llm.invoke([
            SystemMessage(content="""You are a strict technical editor.
            Evaluate the draft and list SPECIFIC issues in these categories:
            1. Factual errors or unsupported claims
            2. Missing important sections
            3. Unclear explanations
            Reply with "APPROVED" if no significant issues remain."""),
            HumanMessage(content=f"Draft to review:\n\n{draft}")
        ]).content

        if "APPROVED" in critique:
            print(f"Approved after {iteration + 1} iteration(s)")
            break

        # Revise based on critique
        draft = llm.invoke([
            SystemMessage(content="You are a professional technical writer revising based on editor feedback."),
            HumanMessage(content=f"Original task: {task}\n\nCurrent draft:\n{draft}\n\nEditor critique:\n{critique}\n\nRevise the draft to address all critique points.")
        ]).content
        print(f"Iteration {iteration + 1}: revised based on critique")

    return draft
```

---

## Planning Patterns

### Concept

Planning patterns separate the **thinking** (what to do) from the **doing** (doing it). Instead of reasoning and acting interleaved step-by-step, the agent first builds an explicit plan, then executes it.

Planning is valuable when:
- The task has complex dependencies between steps
- The agent needs to communicate its approach before executing
- You want to enable human review of the plan before committing to execution
- The task requires backtracking or replanning when steps fail

### ReAct (Reason + Act)

ReAct is the most common planning pattern — it doesn't produce an explicit upfront plan but interleaves reasoning traces with actions.

```
Thought: I need to find the population of Tokyo. I'll use the search tool.
Action: search("Tokyo population 2024")
Observation: Tokyo population is approximately 13.9 million (city) or 37.4 million (metro area).
Thought: I have the city and metro figures. The question asks for the city population.
Action: [DONE — answer: 13.9 million]
```

**Why it works:** Explicit reasoning traces make the agent's logic visible, which helps the LLM stay on track and makes debugging much easier.

**When to use:** Most general-purpose agentic tasks. ReAct is the default — use it unless you have a specific reason to choose another pattern.

### Plan-and-Execute

The agent first produces a complete plan (a list of steps), then executes each step in order. The plan can be updated mid-execution if a step fails.

```
Phase 1 — Planning:
  Goal: "Prepare a competitive analysis of EV battery manufacturers"
  Plan:
    Step 1: Search for top 5 EV battery manufacturers by market share
    Step 2: For each manufacturer, find recent news and financials
    Step 3: Extract key metrics (revenue, growth rate, technology)
    Step 4: Compare across manufacturers in a structured table
    Step 5: Write executive summary

Phase 2 — Execution:
  Execute Step 1 → result → Execute Step 2 → ...
```

**When to use:**
- Tasks where the full plan can be determined upfront
- When human review of the plan before execution is desired
- When steps have clear dependencies and the plan is relatively stable

**Replanning:** If a step fails, the executor returns the failure to the planner, which updates the remaining plan. This "plan → execute → replan if needed" loop is the most resilient form.

### Tree of Thoughts (ToT)

The agent explores multiple reasoning paths simultaneously (like a search tree), evaluating each path's quality before committing to one.

```
Goal: "Design a fault-tolerant data pipeline"

Branch A: Event-driven (Kafka)
  → Evaluate: High throughput, complex ops — score: 7/10

Branch B: Batch processing (Spark)
  → Evaluate: Simple ops, high latency — score: 5/10

Branch C: Lambda architecture (both)
  → Evaluate: Best of both, complex to build — score: 8/10

Select Branch C → Continue planning from there
```

**When to use:** Complex decisions where the "right" first step isn't obvious and exploring alternatives before committing improves quality. Expensive — use only for high-stakes decisions.

---

## Multi-Agent Coordination Pattern

### Concept

When a task is too complex for one agent, you split it across multiple agents. Coordination defines how they work together without stepping on each other.

### Role Assignment

Each agent has a clearly defined role: what it does, what it doesn't do, and what its inputs/outputs look like.

**Good role definition:**
- **Research Agent**: Searches the web and returns structured summaries. Does NOT write or evaluate — only retrieves.
- **Writer Agent**: Transforms structured research into prose. Does NOT research — only writes.
- **Critic Agent**: Evaluates prose quality and factual consistency. Does NOT write — only critiques.

**Why strict roles matter:** When roles overlap, agents start doing each other's work and producing conflicting outputs. Clear role boundaries prevent this.

### Communication Protocols

**Structured messages:** Agents communicate via typed, validated message formats rather than free-form text. This makes the interface explicit and prevents misinterpretation.

```python
# Good: structured interface
class ResearchResult:
    sources: list[str]
    findings: list[str]
    confidence: float
    limitations: list[str]

# Bad: free-form handoff
"Here are the research results: [paragraph of unstructured text]"
```

**Shared state:** All agents read from and write to a shared state object. Each agent reads what it needs, does its work, and writes its output back. The orchestrator coordinates access.

**Message passing:** Agents communicate via explicit message objects passed through the orchestrator. No agent talks to another agent directly — all communication goes through a defined channel.

### Avoiding Coordination Failures

| Failure Mode | Prevention |
|-------------|------------|
| Agents overwrite each other's output | Assign each agent a dedicated output key in shared state |
| Agent A waits for Agent B's output (deadlock) | Define a clear execution order or use dependency resolution |
| Agent produces output in wrong format | Define and validate output schemas; return error if validation fails |
| Agent calls another agent without permission | Restrict inter-agent calls through the orchestrator only |

---

## Routing and Gating

### Concept

Not all inputs need the same processing path. Routing sends each input to the appropriate handler based on its characteristics. Gating blocks execution until a condition is met.

### Input Routing

The router classifies the input and sends it to the appropriate agent or pipeline.

```
Incoming request
    ↓
[Router Agent: classify intent]
    ├── "billing question" → [Billing Agent]
    ├── "technical support" → [Tech Support Agent]
    ├── "general inquiry" → [General Agent]
    └── "escalation" → [Human Support Queue]
```

**Router design:** The router is often a lightweight LLM call with a classification prompt. It doesn't need to solve the task — just route it correctly.

### Confidence Gating

The agent estimates its own confidence and routes to different handlers based on confidence level.

```python
result = agent.run(task)
confidence = evaluate_confidence(result)  # 0.0 to 1.0

if confidence > 0.85:
    return result  # High confidence: proceed automatically
elif confidence > 0.60:
    enqueue_for_review(result)  # Medium: human review queue
else:
    escalate_to_human(task)  # Low: route to human immediately
```

### HITL Gates

A HITL gate is a checkpoint that requires human approval before the agent proceeds with an irreversible or high-risk action.

```
Agent plans to: "Send invoice to client@company.com for $15,000"
    ↓
HITL Gate triggered (irreversible action + dollar amount > $10,000 threshold)
    ↓
Present to human: [action preview + justification + approve/reject]
    ↓
Human: Approve → Agent sends invoice
Human: Reject  → Agent aborts and reports reason
Human: Timeout → Agent escalates to supervisor
```

---

## Study Notes

- Tool-use is the foundation — every agentic system uses it. Master tool design (descriptions, schemas, error handling) before anything else.
- Reflection adds quality but adds cost and latency. Measure both. The improvement must justify the expense.
- Plan-and-Execute is particularly useful when HITL is required — you can show the human the plan and get approval before any action is taken.
- Routing is often underestimated. A good router dramatically improves system performance by sending each input to the specialist that handles it best.
- Multi-agent coordination is the hardest pattern to get right. Start with the simplest coordination mechanism (shared state via orchestrator) before introducing direct agent-to-agent communication.

---

## Interview Questions

**Q1: What is the ReAct pattern and why is it the default for most agentic tasks?** `[Easy]`
A: ReAct (Reason + Act) interleaves explicit reasoning traces with tool calls: Thought → Action → Observation → Thought → ... The agent writes out its reasoning before each action, making its logic visible and keeping it on track. It's the default because it handles most general-purpose agentic tasks without requiring an explicit upfront plan, it's simple to implement, and the visible reasoning traces make debugging straightforward. Use something more complex (Plan-and-Execute, Tree of Thoughts) only when you have a specific reason — most tasks don't need it.

**Q2: Why does tool description quality matter as much as tool implementation quality?** `[Medium]`
A: The tool description is part of the prompt — the LLM reads it to decide whether to use the tool and how to call it. A vague description ("Search products") gives the model no guidance on when to use the tool, what input format is expected, or what it will return. A good description specifies: what the tool does, when to use it, when NOT to use it, the input format, and the output format. A well-implemented tool with a poor description will be called at wrong times or with wrong arguments; a well-described tool is used correctly even in edge cases. Tool descriptions are LLM-facing documentation, not human-facing documentation.

**Q3: When should you use an external evaluator rather than self-reflection?** `[Medium]`
A: Use an external evaluator (a separate agent or a stronger model) when the task requires catching the model's own blind spots — the same model that generated an output will often fail to identify its own errors due to self-consistency bias (it will evaluate using the same flawed reasoning that produced the error). A stronger model as evaluator works because it has better reasoning; a different model works because it has different priors. Self-reflection is acceptable for tasks like stylistic revision where the model can improve on its own draft without needing to catch factual errors. For factual accuracy, security review, or adversarial analysis, always use a separate evaluator.

**Q4: What is the difference between Plan-and-Execute and ReAct?** `[Medium]`
A: ReAct interleaves reasoning and action — the agent decides what to do at each step based on the most recent observation, with no upfront plan. Plan-and-Execute separates planning from execution: the agent first produces a complete list of steps, then executes them in sequence, only returning to planning if a step fails (replanning). Plan-and-Execute is better when the full plan can be determined upfront, when HITL review of the plan before execution is required, or when the task has stable dependencies. ReAct is better when the right next step depends on the result of the previous step and can't be planned ahead. Most production systems use ReAct for dynamic tasks and Plan-and-Execute for structured workflows.

**Q5: What must every Reflection loop have, and what happens without it?** `[Hard]`
A: Every Reflection loop requires a termination condition: a quality score threshold the evaluator must award (e.g., 8/10), a specific criterion the evaluator must declare met (e.g., "APPROVED"), or a hard maximum iteration count. Without a termination condition, the loop runs indefinitely — the agent keeps revising, the evaluator keeps finding new issues, and cost grows without bound. In practice, always set a `max_iterations` even when you have a quality threshold as a safety net: an evaluator with an inconsistent rubric can reject every revision forever. Three conditions in combination (score threshold OR "no critical issues" OR max iterations = 3) is the standard pattern.

**Q6: How does a confidence-gated HITL differ from a fixed HITL gate?** `[Hard]`
A: A fixed HITL gate always pauses at a defined point — for example, "always get approval before sending any email." A confidence-gated HITL is conditional: the agent computes or estimates its confidence in the output, and routes to human review only when confidence falls below a threshold (e.g., <0.85 routes to queue, <0.60 routes directly to human). Confidence gating reduces human interruptions for routine high-confidence actions while still catching genuinely uncertain cases. The challenge is that LLM self-confidence estimates are unreliable — models are often confidently wrong. Calibrate confidence thresholds empirically against known error rates before deploying confidence gating in production.
