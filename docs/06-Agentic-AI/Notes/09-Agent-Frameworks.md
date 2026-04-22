# Agent Frameworks

## Why Frameworks Exist

Building an agent from the bare API (as shown in [02-The-Agent-Loop.md](02-The-Agent-Loop.md)) works for a single, simple agent. As systems grow, you find yourself reimplementing the same infrastructure over and over: state management, checkpointing, multi-agent coordination, streaming, observability hooks, error handling, retry logic.

Frameworks solve this by providing battle-tested implementations of these patterns. The tradeoff is abstraction: you gain productivity, but the framework makes decisions about structure that you must understand and sometimes work around.

**When to use a framework:**
- You need checkpointing, state persistence, or resume-on-failure
- You're building multi-agent systems with complex coordination
- You need streaming support and observability hooks out of the box
- You want to move faster than building primitives

**When to stay close to the bare API:**
- The task is a simple single-agent loop
- You need fine-grained control the framework abstracts away
- The team is still learning how agents work (frameworks can hide important concepts)

---

## LangGraph

### What It Is

LangGraph is a framework for building stateful, multi-actor agentic systems as graphs. Developed by LangChain, it models agent execution as a **directed graph** where:
- **Nodes** are functions (agent steps, tool executions, human checkpoints)
- **Edges** define the flow between nodes
- **State** is a typed object passed between nodes and automatically persisted

The graph metaphor makes complex control flows — loops, branches, parallel execution, human-in-the-loop checkpoints — explicit and visual.

### Core Concepts

```python
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
import operator

# 1. Define state
class AgentState(TypedDict):
    messages: Annotated[list, operator.add]  # append-only
    task_goal: str
    steps_taken: int
    final_answer: str | None

# 2. Define nodes (pure functions: state in, state out)
def call_model(state: AgentState) -> AgentState:
    response = llm.invoke(state["messages"])
    return {
        "messages": [response],
        "steps_taken": state["steps_taken"] + 1
    }

def should_continue(state: AgentState) -> str:
    last_message = state["messages"][-1]
    # If the last message has tool calls → continue to tools
    if last_message.tool_calls:
        return "continue"
    # Otherwise → end
    return "end"

# 3. Build the graph
graph_builder = StateGraph(AgentState)
graph_builder.add_node("agent", call_model)
graph_builder.add_node("tools", ToolNode(tools))

graph_builder.set_entry_point("agent")
graph_builder.add_conditional_edges(
    "agent",
    should_continue,
    {"continue": "tools", "end": END}
)
graph_builder.add_edge("tools", "agent")  # loop back after tool execution

graph = graph_builder.compile()
```

### Built-in Checkpointing

LangGraph's checkpointing saves the full state after every node execution. If the process crashes, you resume from the last checkpoint.

```python
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.memory import MemorySaver

# Development: in-memory checkpointing
memory = MemorySaver()

# Production: SQLite (single-node) or PostgreSQL (multi-node)
memory = SqliteSaver.from_conn_string("agent_checkpoints.db")

graph = graph_builder.compile(checkpointer=memory)

# Each run gets a thread_id — the same thread_id resumes the same conversation
config = {"configurable": {"thread_id": "user-123-task-456"}}

# Run (or resume)
result = graph.invoke(
    {"messages": [HumanMessage(content="Research EV battery market trends")],
     "task_goal": "EV battery market analysis",
     "steps_taken": 0,
     "final_answer": None},
    config
)
```

### Human-in-the-Loop with Interrupt

LangGraph supports pausing execution at any node to wait for human input:

```python
from langgraph.checkpoint.sqlite import SqliteSaver

# Compile with interrupt points
graph = graph_builder.compile(
    checkpointer=memory,
    interrupt_before=["send_email"]  # pause before any email-sending node
)

# Thread runs until the interrupt
for event in graph.stream(initial_state, config):
    print(event)

# System paused — state is checkpointed
# Inspect the proposed action and approve
snapshot = graph.get_state(config)
proposed_email = snapshot.values["draft_email"]

# Resume with human input
graph.update_state(config, {"human_approved": True})
for event in graph.stream(None, config):  # None = continue from checkpoint
    print(event)
```

### When to Use LangGraph

- Stateful, multi-turn agent systems that need to resume across sessions
- Complex control flows: loops, branches, conditional routing, parallel execution
- Systems that require HITL checkpoints at specific steps
- Teams already using LangChain ecosystem (tools, embeddings, integrations)
- When you want visual debugging via LangSmith

**Strengths:** Explicit state, strong checkpointing, HITL support, LangSmith observability integration  
**Watch out for:** Can be verbose for simple agents; the graph abstraction has a learning curve

---

## Google Agent Development Kit (ADK)

### What It Is

Google ADK is an open-source Python framework for building multi-agent systems that run on Google Cloud. It uses an event-driven architecture where agents emit events that the framework's Runner processes. ADK has native integration with Vertex AI (Gemini models, Vector Search) and is designed for production deployment on Cloud Run.

### Core Concepts

```python
from google.adk.agents import Agent
from google.adk.tools import google_search, FunctionTool
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

# 1. Define tools
def get_product_info(product_id: str) -> dict:
    """Retrieve product information from the catalog.
    
    Args:
        product_id: The product ID to look up (format: PROD-XXXXX)
    
    Returns:
        Product details including name, price, and inventory status
    """
    # Mock implementation
    return {"id": product_id, "name": "Widget Pro", "price": 49.99, "in_stock": True}

product_tool = FunctionTool(func=get_product_info)

# 2. Define agent
support_agent = Agent(
    name="customer_support",
    model="gemini-2.0-flash",
    description="A customer support agent that helps users with product inquiries",
    instruction="""
    You are a helpful customer support agent for an e-commerce store.
    Help users find product information, check order status, and resolve issues.
    Always be polite and professional.
    If you cannot help with something, escalate to a human agent.
    """,
    tools=[product_tool, google_search]
)

# 3. Run
session_service = InMemorySessionService()
runner = Runner(agent=support_agent, session_service=session_service, app_name="support")

import asyncio
from google.genai.types import Content, Part

async def run():
    session = await session_service.create_session(app_name="support", user_id="user_001")
    
    user_message = Content(
        parts=[Part(text="What is the price of PROD-12345?")],
        role="user"
    )
    
    async for event in runner.run_async(
        user_id="user_001",
        session_id=session.id,
        new_message=user_message
    ):
        if event.is_final_response():
            print(event.content.parts[0].text)

asyncio.run(run())
```

### Multi-Agent with ADK

ADK supports agent hierarchies through sub-agents:

```python
from google.adk.agents import Agent

# Specialist subagents
research_agent = Agent(
    name="researcher",
    model="gemini-2.0-flash",
    description="Searches for information and retrieves facts",
    tools=[google_search, read_url_tool]
)

writer_agent = Agent(
    name="writer",
    model="gemini-1.5-pro",
    description="Writes well-structured reports from research",
    tools=[]
)

# Orchestrator with subagents
orchestrator = Agent(
    name="research_orchestrator",
    model="gemini-1.5-pro",
    description="Coordinates research and writing tasks",
    instruction="""
    You coordinate research and writing tasks.
    Use the researcher agent to gather information.
    Use the writer agent to produce the final report.
    """,
    sub_agents=[research_agent, writer_agent]
)
```

### When to Use ADK

- Deploying on Google Cloud / Vertex AI (native integration)
- Teams already using Gemini models
- Systems that need Vertex AI Vector Search, Cloud Run, or other GCP services
- Event-driven agent architectures

**Strengths:** GCP-native, Vertex AI integration, open source, clean agent definition  
**Watch out for:** Smaller ecosystem than LangChain; fewer third-party integrations; evolving API

---

## CrewAI

### What It Is

CrewAI is a high-level framework for creating role-based multi-agent systems called "crews." It uses a business metaphor: a Crew has Agents (with Roles), Tasks (with descriptions and expected outputs), and a Process (sequential or hierarchical) for how tasks are assigned.

CrewAI abstracts away most coordination mechanics — you define roles and tasks, and the framework handles delegation, output passing, and execution order.

### Core Concepts

```python
from crewai import Agent, Task, Crew, Process
from crewai_tools import SerperDevTool, FileWriterTool

search_tool = SerperDevTool()
file_writer = FileWriterTool()

# 1. Define agents (roles with backstories)
researcher = Agent(
    role="Market Research Analyst",
    goal="Find comprehensive and current market data on the EV battery industry",
    backstory="""
    You are an experienced market research analyst with 10 years in the clean energy sector.
    You are thorough, cite sources, and distinguish between facts and estimates.
    """,
    tools=[search_tool],
    llm="gemini/gemini-2.0-flash",
    verbose=True
)

analyst = Agent(
    role="Strategic Business Analyst",
    goal="Transform raw research into clear, actionable strategic insights",
    backstory="""
    You are a strategic analyst who specializes in competitive intelligence.
    You identify patterns, extract key metrics, and frame findings for executive audiences.
    """,
    tools=[],  # no tools — pure reasoning
    llm="gemini/gemini-1.5-pro",
    verbose=True
)

writer = Agent(
    role="Technical Report Writer",
    goal="Produce a well-structured, professional report from analytical findings",
    backstory="""
    You write clear, executive-quality reports. You use headings, tables, and bullet points
    effectively. You never include unverified claims.
    """,
    tools=[file_writer],
    llm="gemini/gemini-2.0-flash",
    verbose=True
)

# 2. Define tasks
research_task = Task(
    description="""
    Research the top 5 EV battery manufacturers by global market share.
    For each, find: company overview, 2024 revenue, technology differentiation,
    recent news, and key customers.
    """,
    expected_output="A structured JSON with data for each of the 5 manufacturers",
    agent=researcher
)

analysis_task = Task(
    description="""
    Analyze the research data. Identify:
    - Who is leading and why
    - Key competitive differentiators
    - Emerging threats and opportunities
    - 3 strategic recommendations for a new market entrant
    """,
    expected_output="A structured analysis with sections for each dimension",
    agent=analyst,
    context=[research_task]  # depends on research_task's output
)

report_task = Task(
    description="""
    Write a 2-page executive report based on the analysis.
    Include: executive summary, market overview, competitor analysis table,
    strategic recommendations. Save to report.md.
    """,
    expected_output="A professional markdown report saved to report.md",
    agent=writer,
    context=[research_task, analysis_task],
    output_file="report.md"
)

# 3. Assemble and run the crew
crew = Crew(
    agents=[researcher, analyst, writer],
    tasks=[research_task, analysis_task, report_task],
    process=Process.sequential,  # tasks run in order
    verbose=True
)

result = crew.kickoff()
print(result)
```

### Hierarchical Process

For more complex systems, CrewAI's hierarchical process uses a manager LLM to dynamically delegate tasks:

```python
crew = Crew(
    agents=[researcher, analyst, writer],
    tasks=[complex_task],  # one high-level task
    process=Process.hierarchical,
    manager_llm="gemini/gemini-1.5-pro",  # manager decides who does what
    verbose=True
)
```

### When to Use CrewAI

- Role-based multi-agent tasks with clear specialization
- Business workflows where the "crew" metaphor maps naturally to the domain
- Quick prototyping — lowest boilerplate of the four frameworks
- Teams that want opinionated structure without managing coordination logic

**Strengths:** Very low boilerplate, intuitive role/task model, good documentation  
**Watch out for:** Less flexible than LangGraph for complex control flows; the sequential process is fairly rigid; observability tooling is less mature

---

## AutoGen / AG2

### What It Is

AutoGen (now continued as AG2 by the AutoGen community) is a framework for building conversational multi-agent systems. Its core metaphor is **conversation**: agents talk to each other. A `ConversableAgent` can be an LLM, a tool executor, or a human proxy. Complex behaviors emerge from these conversations.

AutoGen excels at human-in-the-loop patterns because a `HumanProxyAgent` can literally represent a human in the conversation — either routing messages to a real human or using predefined responses in automated mode.

### Core Concepts

```python
import autogen

config_list = [{"model": "gemini-2.0-flash", "api_key": os.environ["GEMINI_API_KEY"]}]
llm_config = {"config_list": config_list}

# 1. Define agents
assistant = autogen.AssistantAgent(
    name="AI_Assistant",
    llm_config=llm_config,
    system_message="""
    You are a helpful AI assistant. You can help with research, analysis, and writing.
    When you finish a task, say 'TERMINATE' to end the conversation.
    """
)

# HumanProxyAgent routes messages to a human (or auto-responds in automated mode)
user_proxy = autogen.UserProxyAgent(
    name="User",
    human_input_mode="NEVER",   # "NEVER", "TERMINATE", or "ALWAYS"
    max_consecutive_auto_reply=10,
    is_termination_msg=lambda msg: "TERMINATE" in msg.get("content", ""),
    code_execution_config={
        "work_dir": "coding",
        "use_docker": True,  # sandbox code execution
    }
)

# 2. Start conversation
user_proxy.initiate_chat(
    assistant,
    message="Research the top 3 cloud providers by revenue and write a comparison."
)
```

### Group Chat (Multi-Agent Conversations)

AutoGen's GroupChat enables multiple agents to participate in a shared conversation, with a GroupChatManager routing messages between them:

```python
researcher = autogen.AssistantAgent(
    name="Researcher",
    llm_config=llm_config,
    system_message="You are a research specialist. Find and verify information."
)

critic = autogen.AssistantAgent(
    name="Critic",
    llm_config=llm_config,
    system_message="You review work critically. Find errors, omissions, and unsupported claims."
)

writer = autogen.AssistantAgent(
    name="Writer",
    llm_config=llm_config,
    system_message="You transform research into polished prose. Write clearly and concisely."
)

user_proxy = autogen.UserProxyAgent(
    name="User",
    human_input_mode="TERMINATE"  # human can intervene when agents say TERMINATE
)

group_chat = autogen.GroupChat(
    agents=[researcher, critic, writer, user_proxy],
    messages=[],
    max_round=20,
    speaker_selection_method="auto"  # manager picks the next speaker
)

manager = autogen.GroupChatManager(
    groupchat=group_chat,
    llm_config=llm_config
)

user_proxy.initiate_chat(
    manager,
    message="Produce a research report on quantum computing commercialization."
)
```

### When to Use AutoGen / AG2

- Conversational agent architectures where the "dialogue" metaphor fits
- Code generation systems — the HumanProxyAgent with code execution is very powerful
- HITL systems — the HumanProxyAgent can pause for human input at any point
- Research and experimentation — large community, many examples
- Systems where agents debate, critique, and iterate collaboratively

**Strengths:** Excellent code execution support, flexible HITL, active community, natural multi-agent conversations  
**Watch out for:** The conversational model can be harder to reason about for sequential workflows; state management is less explicit than LangGraph; non-conversation-based architectures feel forced

---

## Framework Comparison

| Dimension | LangGraph | Google ADK | CrewAI | AutoGen / AG2 |
|-----------|-----------|-----------|--------|----------------|
| **Abstraction level** | Low-Medium | Medium | High | Medium |
| **Multi-agent support** | Full (graph) | Full (sub-agents) | Full (crew) | Full (group chat) |
| **State management** | Explicit TypedDict | Session-based | Task context | Conversation history |
| **Checkpointing** | Built-in (SQLite, Postgres) | Session service | Limited | Limited |
| **HITL support** | Strong (interrupt_before) | Via tool approval | Manual | Strong (HumanProxy) |
| **Code execution** | Via tools | Via tools | Via tools | Built-in (sandbox) |
| **GCP integration** | Via LangChain | Native | No | No |
| **Observability** | LangSmith native | Cloud Trace | Limited | AgentOps, Langfuse |
| **Learning curve** | Steep | Medium | Low | Medium |
| **Maturity** | High | Medium | High | High |
| **Best for** | Complex stateful flows | GCP deployments | Role-based crews | Conversational, code gen |

---

## Framework-Agnostic Patterns

Certain patterns apply regardless of framework:

### The State Object Pattern

Every framework has its own state representation (LangGraph: TypedDict, ADK: Session, CrewAI: Task context, AutoGen: message history). Design your state schema before choosing a framework.

```python
# Framework-agnostic state design
class TaskState:
    task_id: str
    goal: str
    subtasks: list[Subtask]
    intermediate_results: dict[str, Any]
    current_step: str
    errors: list[str]
    final_output: str | None
```

### The Tool Registration Pattern

All frameworks allow registering external functions as tools. The tool implementation is framework-agnostic; only the registration syntax differs.

```python
# The implementation is the same everywhere
def search_web(query: str) -> str:
    """Search the internet. Use for current events, facts, and research."""
    return search_api.search(query)

# LangChain/LangGraph registration
from langchain_core.tools import tool
@tool
def search_web(query: str) -> str: ...

# ADK registration  
from google.adk.tools import FunctionTool
search_tool = FunctionTool(func=search_web)

# CrewAI registration
from crewai_tools import tool as crew_tool
@crew_tool
def search_web(query: str) -> str: ...
```

### The Observability Hook Pattern

All frameworks support middleware or callbacks for logging. Add observability before optimizing anything.

```python
# LangSmith works with LangGraph automatically
os.environ["LANGCHAIN_TRACING_V2"] = "true"

# Langfuse works with any framework via the @observe decorator
from langfuse.decorators import observe

@observe()
def run_agent_task(goal: str) -> str:
    return agent.run(goal)  # all nested LLM calls traced
```

---

## Choosing a Framework

**Use LangGraph if:**
- Your system has complex conditional logic, loops, or branching control flow
- You need reliable checkpointing and resume-on-failure
- You need fine-grained HITL control (interrupt at any specific node)
- You're deploying to any cloud (not just GCP)
- Long-term maintainability and explicit state are priorities

**Use ADK if:**
- You're deploying to Google Cloud / Vertex AI
- You're using Gemini models and want native API integration
- You want GCP-native observability and deployment

**Use CrewAI if:**
- Your task maps naturally to a "team of specialists" metaphor
- You want the fastest path from idea to working prototype
- Sequential workflows with clear role assignments
- The team is less technical and benefits from the high-level abstraction

**Use AutoGen / AG2 if:**
- Code generation is a core part of the system
- You need conversational agents that can debate and critique each other
- HITL is critical and the HumanProxy pattern fits your use case
- You're exploring multi-agent collaboration research

---

## Study Notes

- **Understand the bare loop before picking a framework.** Every framework is a structured version of the same fundamental agent loop. If you understand what the framework is wrapping, you can debug it when it misbehaves. If you don't, abstraction becomes a mystery.
- **LangGraph is the most popular choice for production systems** because of its explicit state, built-in checkpointing, and LangSmith integration. But it requires understanding the graph model.
- **CrewAI is the fastest to prototype with.** If you need something working in a day, CrewAI's role/task model is the quickest path. Migrate to LangGraph when you need finer control.
- **Don't over-commit early.** The tool implementations are framework-agnostic. Start with one framework and know you can migrate the core logic later — the tools and business logic are reusable.
- **Observability from day one.** All four frameworks support Langfuse. Set it up before your first test run, not after you need to debug a production incident.

---

## Q&A Review Bank

**Q1: What problem does LangGraph's graph model solve compared to a simple agent loop?** `[Easy]`
A: A simple agent loop is a while loop — easy to write but hard to extend. LangGraph's graph model makes the control flow explicit: nodes are the computation steps, edges are the transitions, and conditional edges are the routing logic. This makes complex patterns — cycles, branches, parallel paths, HITL interrupts — declarative and visual rather than buried in if/else logic. It also enables checkpointing: because every transition is an edge in the graph, LangGraph knows exactly where to resume after a failure. The graph model is more code upfront but significantly more maintainable for complex systems.

**Q2: What is the core metaphor of each framework?** `[Easy]`
A: LangGraph: a **graph** — nodes are functions, edges are transitions, state flows through the graph. ADK: **event-driven agents** — agents emit and respond to events, the Runner processes them; native integration with Google Cloud services. CrewAI: a **crew of specialists** — Agents have Roles, Tasks define the work, a Process (sequential or hierarchical) coordinates execution. AutoGen/AG2: **conversations** — agents talk to each other through a conversation history; complex multi-agent behavior emerges from dialogue. The right framework is often the one whose metaphor maps most naturally to the problem you're solving.

**Q3: When is CrewAI the right choice and what are its limitations?** `[Medium]`
A: CrewAI is the right choice when: the task naturally fits a "team of specialists" model (researcher, writer, reviewer roles are obvious), you want fast prototyping with minimal boilerplate, and the workflow is mostly sequential with clear task dependencies. Limitations: the sequential process is rigid — complex conditional routing or dynamic loops require workarounds; checkpointing is limited compared to LangGraph (no built-in resume-on-failure for long tasks); observability tooling is less mature; and the hierarchical process, while powerful, is less transparent than explicit orchestration because the manager LLM makes delegation decisions you can't directly inspect.

**Q4: What makes AutoGen's HumanProxyAgent distinctive?** `[Medium]`
A: The HumanProxyAgent represents a human participant in the multi-agent conversation. With `human_input_mode="ALWAYS"`, it pauses execution and waits for real human input at every turn — making it a genuine HITL implementation. With `human_input_mode="TERMINATE"`, it only asks for input when an agent says TERMINATE (or another termination condition). With `human_input_mode="NEVER"`, it uses auto-reply logic. This means the same agent graph can run fully automatically (for testing), semi-automatically (human only reviews final outputs), or fully interactively (human participates in each turn) just by changing the mode. Additionally, the HumanProxyAgent can execute code in a sandbox, making it central to AutoGen's code generation workflows: the AI writes code, the HumanProxy runs it, and the results go back to the AI for revision.

**Q5: What is the key advantage of LangGraph's checkpointing compared to other frameworks?** `[Hard]`
A: LangGraph persists the full graph state after every node execution as a first-class feature — not an afterthought. Because the state is a typed TypedDict and every node receives and returns state, LangGraph knows exactly what the state looks like at every point in the graph. This enables: (1) Resume on failure — if the process crashes at node 7 of 20, the next run picks up from node 7 with the same state; (2) HITL interrupts — `interrupt_before=["send_email"]` pauses execution and serializes state; when the human approves, execution resumes with `graph.stream(None, config)`; (3) State inspection — `graph.get_state(config)` returns the current state at any point; (4) Time-travel debugging — `graph.get_state_history(config)` returns the full history of state snapshots. CrewAI and AutoGen have much more limited checkpointing that essentially requires restarting from scratch after a failure.

**Q6: A team is building a document processing system that reads invoices, classifies them, extracts structured data, validates the extraction, and stores to a database — with a human review step for low-confidence extractions. Which framework would you recommend and why?** `[Hard]`
A: LangGraph is the best fit for this system. The reasons: (1) The workflow is a defined DAG with a conditional branch (high confidence → auto-store, low confidence → HITL), which maps directly to LangGraph's conditional edges; (2) The HITL step requires pausing execution, serializing state, waiting for human input, and resuming — exactly what `interrupt_before` and checkpointing provide; (3) Documents may be processed in batch overnight, so resume-on-failure checkpointing prevents reprocessing documents that succeeded before a crash; (4) Each stage (OCR, classify, extract, validate, store) has a clear input/output contract that maps cleanly to typed LangGraph state. CrewAI could work but offers no built-in resume-on-failure. AutoGen's conversational model is a poor fit for a sequential data pipeline. ADK is viable if deploying to GCP, but LangGraph is more flexible and better documented for this pattern.
