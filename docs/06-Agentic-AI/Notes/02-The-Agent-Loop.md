# The Agent Loop

← **Back to Overview:** [Agentic AI](../INDEX.md)

---

## What Makes an Agent an Agent

A chatbot takes one input and produces one output, then stops. It cannot take actions, observe results, or decide what to do next.

An **agent** adds a loop. It generates a response, checks if the task is done, and if not, takes an action, observes what happened, and generates the next response. This loop is what gives an agent agency — the ability to act on the world and adjust based on what it observes.

The loop is not just a useful feature. It is the defining characteristic. Remove the loop, and you have a chatbot. Keep the loop, and everything else in agentic AI follows from it.

---

## The Minimal Agent

The simplest possible agent has three components:

```
LLM  ←→  Tool Executor  ←→  Loop Controller
```

- **LLM**: reasons about what to do and produces either a tool call or a final answer
- **Tool Executor**: receives tool calls, executes them, returns results
- **Loop Controller**: checks whether the agent is done; if not, feeds the tool result back to the LLM and continues

No framework required. Here is a minimal agent in pure Python:

```python
import json
from anthropic import Anthropic

client = Anthropic()

# Define a tool
def get_weather(city: str) -> str:
    # In a real system, this calls a weather API
    return f"The weather in {city} is 22°C and sunny."

TOOLS = [
    {
        "name": "get_weather",
        "description": "Get the current weather for a city.",
        "input_schema": {
            "type": "object",
            "properties": {"city": {"type": "string", "description": "The city name"}},
            "required": ["city"]
        }
    }
]

def run_agent(user_message: str, max_steps: int = 10) -> str:
    messages = [{"role": "user", "content": user_message}]

    for step in range(max_steps):
        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=1024,
            tools=TOOLS,
            messages=messages,
        )

        # Did the agent finish?
        if response.stop_reason == "end_turn":
            return response.content[0].text

        # Did the agent call a tool?
        if response.stop_reason == "tool_use":
            # Add assistant's response to history
            messages.append({"role": "assistant", "content": response.content})

            # Execute each tool call
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = get_weather(**block.input)  # dispatch to the right function
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })

            # Feed results back to the LLM
            messages.append({"role": "user", "content": tool_results})

    return "Reached maximum steps without completing the task."
```

This is the entire loop. Every framework — LangChain, LangGraph, ADK, CrewAI — is a more sophisticated version of this same structure.

---

## What the LLM Actually Sees

To understand agents, you must understand what the LLM receives at each step. The loop works by building up a `messages` array. At every iteration, the LLM sees the full history of what has happened so far.

Here is a concrete example: **"What is the weather in Tokyo and Paris?"**

### Step 1: Initial Request

```
messages = [
    {"role": "user", "content": "What is the weather in Tokyo and Paris?"}
]
```

The LLM sees this and decides: I need to call `get_weather` twice. But it can only call tools now. It outputs a tool call:

```json
{
  "stop_reason": "tool_use",
  "content": [
    {"type": "tool_use", "id": "call_1", "name": "get_weather", "input": {"city": "Tokyo"}}
  ]
}
```

### Step 2: After Tokyo Result

The framework executes the tool and appends the result:

```
messages = [
    {"role": "user",      "content": "What is the weather in Tokyo and Paris?"},
    {"role": "assistant", "content": [{"type": "tool_use", "id": "call_1", "name": "get_weather", "input": {"city": "Tokyo"}}]},
    {"role": "user",      "content": [{"type": "tool_result", "tool_use_id": "call_1", "content": "15°C and overcast"}]}
]
```

Now the LLM sees the Tokyo result. It still needs Paris. It outputs another tool call:

```json
{
  "stop_reason": "tool_use",
  "content": [
    {"type": "tool_use", "id": "call_2", "name": "get_weather", "input": {"city": "Paris"}}
  ]
}
```

### Step 3: After Paris Result

```
messages = [
    {"role": "user",      "content": "What is the weather in Tokyo and Paris?"},
    {"role": "assistant", "content": [{"type": "tool_use", "id": "call_1", ...}]},
    {"role": "user",      "content": [{"type": "tool_result", "tool_use_id": "call_1", "content": "15°C and overcast"}]},
    {"role": "assistant", "content": [{"type": "tool_use", "id": "call_2", ...}]},
    {"role": "user",      "content": [{"type": "tool_result", "tool_use_id": "call_2", "content": "22°C and sunny"}]}
]
```

The LLM now has both results. It knows the task is done. It outputs:

```json
{
  "stop_reason": "end_turn",
  "content": [{"type": "text", "text": "Tokyo is currently 15°C and overcast. Paris is 22°C and sunny."}]
}
```

**Key insight:** The LLM does not "remember" between steps. It is stateless. What appears to be memory is the accumulating `messages` array. The loop controller manages this array — appending each response, appending each tool result — so the LLM always has full context of everything that has happened.

---

## The ReAct Pattern

Most agents don't just call tools silently. They produce explicit reasoning traces before each action. This is the **ReAct pattern** (Reason + Act), and it dramatically improves agent reliability.

Without ReAct:
```
User: "Find the CEO of OpenAI and email them"
Agent: [immediately calls send_email with wrong address]
```

With ReAct (reasoning trace visible in the LLM output or scratchpad):
```
Thought: The user wants me to find the CEO of OpenAI and email them.
         First, I need to search for who the CEO is — I don't know their email.

Action: search_web("OpenAI CEO 2024")
Observation: Sam Altman is the CEO of OpenAI.

Thought: I have the name. Now I need the email address.
Action: find_email("Sam Altman", "OpenAI")
Observation: contact@openai.com (public contact only — no direct email available)

Thought: I only have the public contact email, not a direct email.
         This might not be what the user intended. I should clarify.
Action: [final answer — ask user to clarify]
```

The explicit "Thought" steps serve three functions:
1. **Keeps the agent on track**: writing out reasoning prevents the agent from jumping to action before it understands the situation
2. **Makes debugging possible**: you can see exactly what the agent was thinking at the step where things went wrong
3. **Enables self-correction**: the agent can reason about whether its previous step succeeded before proceeding

ReAct is implemented by including reasoning instructions in the system prompt:
```python
SYSTEM_PROMPT = """
You are a helpful assistant with access to tools.

Before each action, write your reasoning:
Thought: [your reasoning about what to do and why]
Then call the appropriate tool.

When the task is complete, provide a final answer directly.
"""
```

---

## How Context Accumulates

Every step in the agent loop adds tokens to the context window. This is the fundamental resource constraint of agentic systems.

A typical step adds:
- **LLM reasoning output**: 100–500 tokens
- **Tool call**: 20–100 tokens (tool name + arguments)
- **Tool result**: 50–5,000 tokens (varies enormously — a web page can be 50,000 tokens)

After 10 steps, the context might hold 10,000–50,000 tokens. After 30 steps, it could be 150,000 tokens — approaching or exceeding most models' context limits.

```
Context size over time:

Tokens
  |
50k|                              ████
40k|                         ██████
30k|                    ██████
20k|               ██████
10k|          ██████
   |     ██████
   |█████
   └─────────────────────────────────── Steps
      1    5    10   15   20   25   30
```

When context fills up, agents exhibit **context drift** — they start losing track of the original goal, their reasoning becomes inconsistent, and they may repeat work they already did.

**Mitigation strategies:**

1. **Summarize old history**: Instead of keeping every step verbatim, summarize steps 1–10 when you reach step 15. The summary must preserve key facts and decisions.

2. **Trim tool results**: Web pages and documents can be enormous. Truncate or chunk tool results before adding them to context.

3. **Task ledger**: Keep the goal and remaining tasks in a separate compact structure that's always visible, even after history is summarized.

4. **Context budget**: Allocate token budgets to each component: system prompt (2k), task ledger (1k), recent history (50k), and refuse to add more when the budget is exhausted.

```python
def build_context_with_budget(
    system_prompt: str,
    task_ledger: str,
    history: list[dict],
    max_tokens: int = 100_000
) -> list[dict]:
    # Always include
    messages = [{"role": "user", "content": system_prompt + "\n\n" + task_ledger}]
    
    # Add as much recent history as fits
    token_count = count_tokens(messages)
    for message in reversed(history):  # most recent first
        msg_tokens = count_tokens([message])
        if token_count + msg_tokens > max_tokens:
            break
        messages.insert(1, message)  # prepend before current
        token_count += msg_tokens
    
    return messages
```

---

## Termination Conditions

The agent loop must stop. Without explicit termination conditions, agents run indefinitely, accumulate context until they crash, and generate runaway costs.

Every agent needs at least two termination conditions: a **success condition** and an **escape hatch**.

### Success Conditions

The agent signals that the task is complete. In practice, this happens when:

- The LLM produces a response with `stop_reason = "end_turn"` (no more tool calls needed)
- The agent outputs a special completion token defined in the prompt (e.g., `[DONE]`)
- A separate evaluator confirms the output meets quality criteria

```python
# LLM signals completion naturally
if response.stop_reason == "end_turn":
    return extract_final_answer(response)

# Or agent uses explicit done signal
if "[DONE]" in response.content[0].text:
    return extract_final_answer(response)
```

### Escape Hatches (Bounds)

These trigger when the success condition hasn't been reached but the agent must stop anyway:

```python
class AgentBounds:
    max_steps: int = 20          # max iterations of the loop
    max_tokens: int = 200_000    # max tokens across entire context
    max_wall_time: float = 300.0 # seconds
    max_cost_usd: float = 1.00   # dollar cap
    max_tool_calls: int = 50     # individual tool invocations
```

When a bound is hit, the agent should return a **partial result** with a status flag — not silently fail or raise an exception:

```python
if step >= config.max_steps:
    return AgentResult(
        status="limit_reached",
        limit_type="max_steps",
        partial_output=current_best_answer,
        steps_taken=step,
        cost_usd=accumulated_cost
    )
```

### Failure Termination

Some errors warrant immediate termination — not retry, not continuation:

- **Budget exceeded**: Never continue a task that already exceeded its cost limit
- **Safety violation**: Agent attempted a prohibited action
- **Irrecoverable tool failure**: A required tool is down and there's no fallback
- **Infinite loop detected**: The same tool was called with identical arguments 3+ times

---

## The System Prompt as the Agent's Identity

The system prompt is the agent's fixed context — it shapes everything the agent does. Unlike the `messages` array which grows with each step, the system prompt is stable throughout the entire loop.

A well-structured agent system prompt has four sections:

```
SYSTEM PROMPT STRUCTURE:

1. ROLE DEFINITION
   Who you are and what you are for.
   "You are a research assistant that finds and synthesizes information
   from the web. You help analysts prepare research reports."

2. CAPABILITIES AND TOOLS
   What tools you have and when to use them.
   "You have access to:
   - search_web(query): Search the internet for current information
   - read_url(url): Read the full text of a webpage
   - save_note(content): Save a note to the research workspace
   Use search_web first to find relevant sources, then read_url for depth."

3. BEHAVIORAL CONSTRAINTS
   What you must and must not do.
   "Always cite your sources. Never fabricate facts.
   If you cannot find information after 3 searches, say so.
   Do not visit websites that appear to be login pages."

4. OUTPUT FORMAT
   How to structure your responses.
   "When the research is complete, structure your final answer as:
   SUMMARY: [2-3 sentence summary]
   FINDINGS: [bulleted list]
   SOURCES: [numbered list of URLs]"
```

**System prompt pitfalls to avoid:**

- **Contradictions**: "Always be concise" + "Always include full detail" causes unpredictable behavior
- **Vague constraints**: "Be careful" tells the agent nothing. "Do not call write_file unless the user explicitly asked to save a file" is actionable.
- **Missing tool guidance**: Without clear guidance on when to use each tool, agents call the wrong tool or call tools unnecessarily.

---

## Parallel Tool Calls

Many LLMs can call multiple tools in a single step. This dramatically reduces latency for tasks that require multiple independent pieces of information.

Sequential (3 API calls, 3× the latency):
```
Step 1: search("Tokyo weather")     → result
Step 2: search("Paris weather")     → result  
Step 3: search("London weather")    → result
```

Parallel (1 API call, all at once):
```
Step 1: search("Tokyo weather")   ]
        search("Paris weather")   ] → all three results at once
        search("London weather")  ]
```

APIs support this by returning multiple tool calls in one response:

```python
# Claude response with parallel tool calls
response.content = [
    {"type": "tool_use", "id": "call_1", "name": "search_web", "input": {"query": "Tokyo weather"}},
    {"type": "tool_use", "id": "call_2", "name": "search_web", "input": {"query": "Paris weather"}},
    {"type": "tool_use", "id": "call_3", "name": "search_web", "input": {"query": "London weather"}},
]

# Execute all in parallel
import asyncio

async def execute_tools_parallel(tool_calls: list) -> list:
    tasks = [execute_tool(call.name, call.input) for call in tool_calls]
    return await asyncio.gather(*tasks)
```

The LLM will use parallel calls naturally when it recognizes that multiple pieces of information are needed and the queries are independent. You can encourage this by saying "You can call multiple tools at once when they are independent" in the system prompt.

---

## The Agent Loop in Frameworks

Every major framework wraps the same core loop. Understanding the bare loop makes frameworks easier to learn because you can see through the abstraction.

**LangGraph** models the loop as a graph with nodes (agent functions) and edges (transitions). The loop is a graph with a cycle:

```python
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode

graph = StateGraph(AgentState)
graph.add_node("agent", call_model)       # LLM call
graph.add_node("tools", ToolNode(tools))  # tool execution

graph.add_conditional_edges(
    "agent",
    should_continue,                       # termination check
    {"continue": "tools", "end": END}
)
graph.add_edge("tools", "agent")          # loop back
```

**LangChain AgentExecutor** wraps the same loop with retry logic and verbose logging built in.

**Google ADK** uses an event-driven variant where each step emits events that the runner processes.

All three implement: LLM → check done → execute tools → back to LLM.

---

## Common Loop Failures

### Infinite Retry Loop

```
Agent calls search("answer to question")
Tool returns: "No results found"
Agent calls search("answer to question")   ← identical call
Tool returns: "No results found"
...
```

**Prevention**: Track the last N tool calls. If the same call appears twice, either reformulate the query or declare failure.

```python
call_history = []
if tool_call in call_history[-3:]:
    return "Could not find information — search returned no results."
call_history.append(tool_call)
```

### Tool Argument Hallucination

The LLM calls a tool with a parameter value that doesn't exist or wasn't mentioned in the conversation.

```
User: "Look up order ORD-555"
Agent: get_order(order_id="ORD-999")  ← hallucinated ID
```

**Prevention**: Validate tool arguments against the conversation context before execution. For structured arguments, use Pydantic validation:

```python
from pydantic import BaseModel, validator

class GetOrderInput(BaseModel):
    order_id: str
    
    @validator("order_id")
    def validate_format(cls, v):
        if not v.startswith("ORD-"):
            raise ValueError(f"Invalid order ID format: {v}")
        return v
```

### Context Exhaustion

The agent accumulates so much context that the LLM starts forgetting the original goal, repeating work, or producing contradictory reasoning.

**Prevention**: Monitor token count at each step. Trigger summarization before hitting the limit, not after.

```python
current_tokens = count_tokens(messages)
if current_tokens > TOKEN_SUMMARIZE_THRESHOLD:
    summary = summarize_history(messages[1:20])  # keep system prompt + recent
    messages = [messages[0], {"role": "user", "content": summary}] + messages[20:]
```

---

## Study Notes

- The loop is the agent. Everything else — tools, memory, orchestration — is infrastructure that makes the loop more capable and reliable.
- **Never deploy an agent without bounds.** Even a "simple" agent in a loop can exhaust a month's API budget in hours if it gets stuck.
- **Parallel tool calls are free performance.** When the LLM needs multiple independent pieces of information, parallel calls halve the wall-clock time with no extra cost. Encourage them in the system prompt.
- **The messages array is the agent's memory.** It's not infinite. Managing what goes into it — and what gets summarized or dropped — is one of the most important production engineering concerns.
- **Build your loop before picking a framework.** Writing the bare loop once teaches you more than reading framework documentation for an hour. Once you understand what a framework is wrapping, its abstractions become intuitive.

---

## Q&A Review Bank

**Q1: What are the three components of a minimal agent and what does each do?** `[Easy]`
A: An LLM (reasons about what to do and produces either a tool call or a final answer), a Tool Executor (receives tool calls, executes the corresponding function, and returns results), and a Loop Controller (checks whether the agent is done; if not, appends the tool result to the messages array and sends it back to the LLM for the next iteration). Remove any one of the three and you no longer have an agent: without the LLM you have an automated script, without the Tool Executor you have a chatbot, without the Loop Controller you have a single-turn system.

**Q2: Why must the LLM receive the full message history at every step, and what problem does this cause at scale?** `[Medium]`
A: The LLM is stateless — it has no internal memory between calls. The only way it "knows" what happened in previous steps is by reading the full history of messages on every call. This is why the loop controller appends each tool call and each tool result to the messages array. The problem at scale is context window exhaustion: every step adds tokens, and after many steps the accumulated history can approach or exceed the model's context limit. Solutions are context summarization (compressing old history), tool result truncation (trimming long tool outputs before storing them), and task ledgers (keeping a compact goal-tracking structure that's separate from conversational history).

**Q3: What is the ReAct pattern and what three functions do explicit reasoning traces serve?** `[Medium]`
A: ReAct (Reason + Act) is the pattern where the agent writes explicit reasoning traces (labeled "Thought") before each tool call, making its logic visible in the output. The three functions: (1) Keeps the agent on track — writing out reasoning before acting prevents the agent from jumping to action before it understands the situation; (2) Makes debugging possible — you can read exactly what the agent was reasoning at the step where things went wrong; (3) Enables self-correction — the agent can explicitly evaluate whether its previous action succeeded before deciding what to do next. Without ReAct, agents tend to take premature actions and their errors are very hard to trace.

**Q4: Name four termination conditions an agent should have. What should happen when a bound is hit?** `[Medium]`
A: Four conditions: max steps (maximum loop iterations), max tokens (total context size), max wall time (seconds), and max cost (dollar cap). A fifth is infinite-loop detection (same tool call repeated 3+ times). When any bound is hit, the agent should NOT raise a raw exception or return nothing. The correct behavior is to return a partial result with a status flag (`"status": "limit_reached"`, `"limit_type": "max_steps"`), include whatever output was produced before the limit, and log the event for monitoring. This allows the system to return something useful to the user and enables post-hoc analysis of why the agent hit its limit.

**Q5: What is tool argument hallucination and how do you prevent it?** `[Hard]`
A: Tool argument hallucination is when the LLM calls a tool with parameter values that don't appear in the conversation and were not provided by the user — the model invents them. For example, the user mentions order ORD-555 and the agent calls get_order(order_id="ORD-999"). This is a significant real-world failure mode because the tool succeeds syntactically but returns information about the wrong entity. Prevention has two layers: (1) Validate tool arguments before execution — use schema validation (Pydantic) to catch format violations, and cross-reference against context where possible; (2) Improve tool descriptions to be explicit about where arguments should come from: "Use the exact order ID the user provided, verbatim — do not guess or generate order IDs."

**Q6: How do parallel tool calls differ from sequential calls and when should an agent use them?** `[Hard]`
A: Sequential calls execute one tool, wait for the result, then call the next — each call adds full tool latency to the total. Parallel calls send multiple tool invocations simultaneously and wait for all results at once — total latency is the max of any one call rather than the sum. Use parallel calls when (a) multiple pieces of information are needed and (b) the queries are independent — the result of one does not determine the input of another. Example: looking up weather in three cities is perfectly parallel (three independent searches). But looking up a user's order history and then looking up the details of their most recent order is sequential (you need the first result to know what to query next). Most LLMs will choose parallel calls naturally when given permission in the system prompt, but explicitly encouraging them ("You can call multiple tools at once when the queries are independent") improves the frequency.
