# Memory and State

## Why Agents Need Memory

A single-turn LLM call has no memory. Every call starts fresh. This is fine for answering a question, but an agent working on a multi-step task needs to remember what it has done, what it has learned, and what remains.

Without memory, an agent:
- Cannot refer to the result of a tool call it made 10 steps ago
- Cannot resume after a crash or restart
- Cannot build on knowledge accumulated from previous tasks
- Will repeat work it has already done

Memory is what enables agents to operate over extended horizons. But memory is not one thing — there are four distinct types, each serving a different purpose and operating at a different timescale.

---

## The Four Memory Types

```
┌──────────────────────────────────────────────────────────────────┐
│  TIMESCALE: task session                                          │
│                                                                   │
│  1. In-Context Memory (short-term)                                │
│     The LLM's active context window. Everything the model        │
│     can "see" right now. Limited. Lost when session ends.        │
│                                                                   │
│  2. Working Memory (task state)                                   │
│     Structured state outside the context window. Task ledger,   │
│     partial results, assignments. Persisted to a database.       │
│     Survives agent restarts.                                     │
├──────────────────────────────────────────────────────────────────┤
│  TIMESCALE: cross-task, persistent                                │
│                                                                   │
│  3. Episodic Memory (event log)                                   │
│     Sequential log of everything that happened. Append-only.    │
│     Used for debugging, auditing, and training data.             │
│                                                                   │
│  4. Semantic Memory (long-term knowledge)                         │
│     Vector store of accumulated knowledge and preferences.       │
│     Queried semantically when relevant to the current task.      │
└──────────────────────────────────────────────────────────────────┘
```

Each type is accessed at a different moment, stored differently, and fails in different ways when it goes wrong.

---

## 1. In-Context Memory (Short-Term)

**What it is:** The content of the LLM's active context window. Everything the model "sees" in a given API call.

**What goes into it:**
- System prompt (role, capabilities, constraints)
- Conversation history (user messages and assistant responses)
- Tool call results from this session
- Current task goal and relevant context

**Limits:** Every model has a context window limit measured in tokens. As of 2024:

| Model | Context Window |
|-------|---------------|
| Claude 3.5 Sonnet | 200k tokens |
| GPT-4o | 128k tokens |
| Gemini 1.5 Pro | 1M tokens |
| Gemini 2.0 Flash | 1M tokens |

While these numbers seem large, a 10-step agent task can easily accumulate 50–100k tokens if tool results include long documents.

### What Happens When Context Fills Up

When context approaches the limit:
1. The model starts to lose attention to early content — it focuses on recent tokens
2. The original goal, stated at the beginning, gets "pushed out" of effective attention
3. Reasoning quality degrades — the agent starts contradicting its earlier work
4. The API will return an error if you exceed the hard limit

This degradation before hitting the hard limit is called **context drift** — and it's much harder to detect than a hard error.

### Managing In-Context Memory

**Strategy 1: Sliding window**
Keep only the most recent N messages in context. Drop older messages.

```python
def truncate_to_recent(messages: list[dict], max_messages: int = 20) -> list[dict]:
    system = [m for m in messages if m["role"] == "system"]
    non_system = [m for m in messages if m["role"] != "system"]
    
    # Always keep system prompt + most recent messages
    recent = non_system[-max_messages:] if len(non_system) > max_messages else non_system
    return system + recent
```

**Risk:** Drops early context. If the user mentioned an important constraint 30 messages ago, the agent may forget it.

**Strategy 2: Hierarchical summarization**
Summarize groups of older messages while keeping recent messages verbatim.

```python
def compress_history(messages: list[dict], keep_recent: int = 10) -> list[dict]:
    if len(messages) <= keep_recent + 2:  # +2 for system + current
        return messages
    
    system_msgs = [m for m in messages if m["role"] == "system"]
    convo_msgs = [m for m in messages if m["role"] != "system"]
    
    # Summarize old messages
    to_summarize = convo_msgs[:-keep_recent]
    recent = convo_msgs[-keep_recent:]
    
    summary_prompt = f"""
    Summarize the following conversation history into a compact representation.
    Preserve: key decisions made, important facts learned, actions taken.
    Omit: pleasantries, repeated information, irrelevant details.
    
    History: {json.dumps(to_summarize)}
    """
    summary = llm.invoke(summary_prompt).content
    
    summary_msg = {"role": "user", "content": f"[Summary of earlier conversation]: {summary}"}
    return system_msgs + [summary_msg] + recent
```

**Strategy 3: Token budget management**
Allocate explicit token budgets to each context section and enforce them.

```python
class ContextBudget:
    system_prompt: int = 2_000
    task_ledger: int = 1_000
    long_term_memories: int = 5_000
    recent_history: int = 50_000
    tool_results: int = 30_000
    
    @property
    def total(self) -> int:
        return sum([self.system_prompt, self.task_ledger, 
                   self.long_term_memories, self.recent_history, self.tool_results])

def build_context(state: AgentState, budget: ContextBudget) -> list[dict]:
    messages = []
    
    # Always: system prompt
    messages.append({"role": "system", "content": truncate(state.system_prompt, budget.system_prompt)})
    
    # Always: task ledger (compact, critical)
    messages.append({"role": "user", "content": truncate(state.task_ledger.to_markdown(), budget.task_ledger)})
    
    # Semantic memory results (most relevant to current step)
    if state.retrieved_memories:
        messages.append({"role": "user", "content": truncate(format_memories(state.retrieved_memories), budget.long_term_memories)})
    
    # Recent history + tool results
    recent = truncate_by_tokens(state.conversation_history, budget.recent_history + budget.tool_results)
    messages.extend(recent)
    
    return messages
```

---

## 2. Working Memory (Task State)

**What it is:** Structured data maintained by the orchestration layer, outside the LLM's context window. It persists the state of the current task across steps and agent restarts.

**What goes into it:**

```python
from dataclasses import dataclass, field
from typing import Any

@dataclass
class TaskState:
    task_id: str
    goal: str
    status: str                  # "running", "paused", "done", "failed"
    
    # Task structure
    subtasks: list["Subtask"]    # planned subtasks with statuses
    
    # Results
    intermediate_outputs: dict[str, Any]  # keyed by subtask ID
    final_output: str | None
    
    # Execution metadata
    current_step: int
    agent_assignments: dict[str, str]  # subtask_id → agent_id
    
    # Failure tracking
    errors: list[str]
    retry_counts: dict[str, int]  # subtask_id → attempts
    
    # Cost tracking
    total_tokens_used: int
    total_cost_usd: float
    
    # Timestamps
    created_at: str
    updated_at: str
    completed_at: str | None

@dataclass
class Subtask:
    id: str
    description: str
    status: str                  # "pending", "in_progress", "done", "failed", "skipped"
    dependencies: list[str]      # IDs of subtasks that must complete first
    assigned_agent: str | None
    output: Any | None
    error: str | None
```

### The Task Ledger

The task ledger is the most important component of working memory. It is a structured record of what the agent set out to do and how far it has gotten. Unlike conversation history, it is compact and never summarized away.

```python
@dataclass
class TaskLedger:
    goal: str
    subtasks: list[Subtask]
    
    def to_markdown(self) -> str:
        lines = [f"**Goal:** {self.goal}\n", "**Subtasks:**"]
        for task in self.subtasks:
            icon = {"pending": "⬜", "in_progress": "🔄", "done": "✅", "failed": "❌"}.get(task.status, "?")
            lines.append(f"- {icon} [{task.id}] {task.description}")
            if task.output:
                lines.append(f"  → Result: {str(task.output)[:100]}...")
            if task.error:
                lines.append(f"  → Error: {task.error}")
        return "\n".join(lines)
    
    def next_executable(self) -> list[Subtask]:
        """Return subtasks that have all dependencies satisfied."""
        done_ids = {t.id for t in self.subtasks if t.status == "done"}
        return [
            t for t in self.subtasks
            if t.status == "pending"
            and all(dep in done_ids for dep in t.dependencies)
        ]
    
    def is_complete(self) -> bool:
        return all(t.status in ("done", "skipped") for t in self.subtasks)
    
    def has_failed(self) -> bool:
        return any(t.status == "failed" for t in self.subtasks)
```

### Checkpointing: Surviving Failures

Checkpointing serializes the full task state to persistent storage at defined intervals. If the system crashes, restarts, or the agent process dies, it can resume from the last checkpoint.

```python
import json
import redis

class TaskCheckpointer:
    def __init__(self, redis_client: redis.Redis, ttl_seconds: int = 86400):
        self.redis = redis_client
        self.ttl = ttl_seconds
    
    def save(self, state: TaskState):
        key = f"task:{state.task_id}:checkpoint"
        self.redis.setex(key, self.ttl, json.dumps(state.__dict__))
    
    def load(self, task_id: str) -> TaskState | None:
        key = f"task:{task_id}:checkpoint"
        data = self.redis.get(key)
        if not data:
            return None
        return TaskState(**json.loads(data))
    
    def delete(self, task_id: str):
        self.redis.delete(f"task:{task_id}:checkpoint")
```

LangGraph has built-in checkpointing via its `MemorySaver` and `SqliteSaver` backends — every state transition is automatically persisted.

```python
from langgraph.checkpoint.sqlite import SqliteSaver

memory = SqliteSaver.from_conn_string("checkpoints.db")
graph = workflow.compile(checkpointer=memory)

# Resume from a previous checkpoint
config = {"configurable": {"thread_id": "task-001"}}
result = graph.invoke(inputs, config)  # continues from where it left off
```

### State Machines

Some agents benefit from modeling their execution as an explicit state machine — where the current "state" determines what actions are valid and what transitions are possible.

```python
from enum import Enum

class AgentState(Enum):
    PLANNING = "planning"
    RESEARCHING = "researching"
    WRITING = "writing"
    REVIEWING = "reviewing"
    AWAITING_HITL = "awaiting_hitl"
    DONE = "done"
    FAILED = "failed"

VALID_TRANSITIONS = {
    AgentState.PLANNING: [AgentState.RESEARCHING, AgentState.FAILED],
    AgentState.RESEARCHING: [AgentState.WRITING, AgentState.FAILED],
    AgentState.WRITING: [AgentState.REVIEWING, AgentState.AWAITING_HITL],
    AgentState.REVIEWING: [AgentState.DONE, AgentState.WRITING, AgentState.FAILED],
    AgentState.AWAITING_HITL: [AgentState.WRITING, AgentState.FAILED],
}

def transition(current: AgentState, next_state: AgentState) -> AgentState:
    if next_state not in VALID_TRANSITIONS.get(current, []):
        raise ValueError(f"Invalid transition: {current} → {next_state}")
    return next_state
```

State machines make reasoning about the system much easier — you can see at a glance what states are possible, what transitions are valid, and what could cause the system to get stuck.

---

## 3. Episodic Memory (Event Log)

**What it is:** An append-only sequential record of everything the agent did. Every LLM call, tool call, agent assignment, HITL decision, error, and state transition is logged.

**What it is NOT:** Episodic memory is not used for retrieval during the current task. It is written to during execution and read after execution — for debugging, auditing, cost analysis, and generating training data.

```python
from dataclasses import dataclass, field
from datetime import datetime
import json

@dataclass
class AgentEvent:
    event_id: str
    task_id: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    event_type: str = ""  # "llm_call", "tool_call", "state_transition", "hitl", "error"
    
    # LLM call fields
    model: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None
    latency_ms: int | None = None
    
    # Tool call fields
    tool_name: str | None = None
    tool_args: dict | None = None
    tool_result: dict | None = None
    tool_success: bool | None = None
    
    # State transition fields
    from_state: str | None = None
    to_state: str | None = None
    
    # HITL fields
    action_proposed: str | None = None
    human_decision: str | None = None  # "approved", "rejected", "timeout"
    
    # Error fields
    error_type: str | None = None
    error_message: str | None = None
    stack_trace: str | None = None

class EventLog:
    def __init__(self, storage):
        self.storage = storage
    
    def append(self, event: AgentEvent):
        self.storage.append(event.task_id, event)
    
    def get_trace(self, task_id: str) -> list[AgentEvent]:
        return self.storage.get_all(task_id)
    
    def get_cost_summary(self, task_id: str) -> dict:
        events = self.get_trace(task_id)
        llm_events = [e for e in events if e.event_type == "llm_call"]
        return {
            "total_cost_usd": sum(e.cost_usd or 0 for e in llm_events),
            "total_input_tokens": sum(e.input_tokens or 0 for e in llm_events),
            "total_output_tokens": sum(e.output_tokens or 0 for e in llm_events),
            "llm_calls": len(llm_events),
        }
```

### Using Episodic Memory for Debugging

When something goes wrong, episodic memory is the crime scene. The debugging workflow:

1. Load the full trace for the failed task
2. Find the first step where the state diverged from expected
3. Inspect tool call arguments at that step
4. Check whether the tool result was correctly used in the next step
5. Replay from the checkpoint before that step

```python
def find_first_wrong_step(trace: list[AgentEvent]) -> AgentEvent | None:
    """Find the first tool call that returned an error or unexpected result."""
    for event in trace:
        if event.event_type == "tool_call" and not event.tool_success:
            return event
        if event.event_type == "error":
            return event
    return None
```

### Using Episodic Memory as Training Data

High-quality traces where the agent succeeded can be used as few-shot examples or for fine-tuning:

```python
def extract_training_examples(
    traces: list[list[AgentEvent]], 
    min_success_score: float = 0.9
) -> list[dict]:
    examples = []
    for trace in traces:
        # Only use successful traces
        if compute_success_score(trace) < min_success_score:
            continue
        
        # Extract the trajectory as a training example
        examples.append({
            "task": trace[0].task_id,
            "trajectory": [
                {"tool": e.tool_name, "args": e.tool_args, "result": e.tool_result}
                for e in trace if e.event_type == "tool_call"
            ],
            "final_answer": extract_final_answer(trace)
        })
    
    return examples
```

---

## 4. Semantic Memory (Long-Term Knowledge)

**What it is:** A vector store of knowledge and preferences accumulated across many tasks and sessions. When a new task starts, relevant memories are retrieved and included in the context.

**What goes into it:**
- Successful research results from previous tasks
- User preferences and style guides
- Domain knowledge (product specs, company policies, technical facts)
- Templates and successful past outputs
- Learned calibrations ("user prefers bullet points over prose")

**What does NOT go into it:**
- Raw conversation history (too much, too noisy)
- Episodic events (those go in the event log)
- Task state (that's working memory)

### Storing to Semantic Memory

Not every output should be stored. Use selective storage — only store information that is likely to be useful in future tasks.

```python
from langchain.vectorstores import Chroma
from langchain.embeddings import GoogleGenerativeAIEmbeddings

embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
vector_store = Chroma(embedding_function=embeddings, persist_directory="./agent_memory")

@dataclass
class Memory:
    content: str
    memory_type: str           # "fact", "preference", "template", "procedure"
    source_task_id: str
    tags: list[str]
    importance: float          # 0.0 to 1.0 — used for pruning
    created_at: str
    last_accessed: str

def store_memory(content: str, memory_type: str, tags: list[str], importance: float):
    memory = Memory(
        content=content,
        memory_type=memory_type,
        source_task_id=current_task_id(),
        tags=tags,
        importance=importance,
        created_at=datetime.utcnow().isoformat(),
        last_accessed=datetime.utcnow().isoformat()
    )
    vector_store.add_texts(
        texts=[memory.content],
        metadatas=[memory.__dict__]
    )
```

### Retrieving from Semantic Memory

At the start of each task (or each step where new context is needed), retrieve relevant memories using semantic search.

```python
def retrieve_relevant_memories(
    query: str, 
    k: int = 5, 
    memory_types: list[str] | None = None
) -> list[Memory]:
    filter_dict = {}
    if memory_types:
        filter_dict["memory_type"] = {"$in": memory_types}
    
    results = vector_store.similarity_search_with_score(
        query, k=k, filter=filter_dict
    )
    
    # Only return memories above a similarity threshold
    return [
        Memory(**doc.metadata)
        for doc, score in results
        if score > 0.75
    ]

# Usage at task start
relevant_memories = retrieve_relevant_memories(
    query=task_goal,
    k=5,
    memory_types=["fact", "procedure"]
)

if relevant_memories:
    context_addition = "Relevant knowledge from previous tasks:\n" + "\n".join(
        f"- {m.content}" for m in relevant_memories
    )
```

### Memory Pollution

**Memory pollution** occurs when incorrect, outdated, or low-quality information accumulates in long-term memory and starts degrading agent performance. This is a serious production concern for long-running systems.

**Causes:**
- Storing intermediate results without verifying their correctness
- Not updating memories when facts change
- Retrieving a low-relevance memory and treating it as authoritative

**Prevention:**

```python
# 1. Quality gate before storage
def store_if_verified(content: str, evidence: str, importance: float):
    if importance < 0.5:
        return  # don't store low-importance information
    
    # Verify before storing
    verification = llm.invoke(f"""
    Fact to store: {content}
    Evidence: {evidence}
    
    Is this fact accurate and worth storing for future reference?
    Reply YES or NO with brief reasoning.
    """)
    
    if verification.content.startswith("YES"):
        store_memory(content, "fact", [], importance)

# 2. TTL on memories
def prune_expired_memories(max_age_days: int = 90):
    cutoff = datetime.utcnow() - timedelta(days=max_age_days)
    # Remove memories not accessed since cutoff and with low importance
    vector_store.delete(
        where={"$and": [
            {"last_accessed": {"$lt": cutoff.isoformat()}},
            {"importance": {"$lt": 0.7}}
        ]}
    )

# 3. Memory correction
def correct_memory(old_content: str, new_content: str, reason: str):
    # Find and delete the old memory
    results = vector_store.similarity_search(old_content, k=1)
    if results and results[0].page_content.strip() == old_content.strip():
        vector_store.delete([results[0].metadata["id"]])
    
    # Store the corrected version
    store_memory(new_content, "fact", [], importance=0.9)
```

---

## Memory Access Pattern: Putting It Together

A well-designed agent uses all four memory types at the right moments:

```
TASK START:
  → Query semantic memory (long-term) for relevant knowledge
  → Load working memory (task state) if resuming
  → Initialize in-context memory (system prompt + task ledger)
  → Start appending to episodic memory (event log)

EACH STEP:
  → Read from in-context memory (LLM sees full context)
  → Read/write working memory (update task ledger, partial results)
  → Append to episodic memory (log the step)
  → Optionally query semantic memory for specific knowledge needs

TASK END:
  → Extract valuable findings → write to semantic memory
  → Finalize working memory (mark task done)
  → Archive episodic memory trace
  → Clear in-context memory (session ends)
```

```python
class AgentMemoryManager:
    def __init__(self, vector_store, checkpointer, event_log):
        self.vector_store = vector_store
        self.checkpointer = checkpointer
        self.event_log = event_log
    
    def initialize_task(self, task_id: str, goal: str) -> TaskState:
        # Check for existing checkpoint (resume case)
        existing = self.checkpointer.load(task_id)
        if existing:
            return existing
        
        # Retrieve relevant prior knowledge
        memories = retrieve_relevant_memories(goal, k=5)
        
        # Create fresh state with retrieved context
        state = TaskState(
            task_id=task_id,
            goal=goal,
            prior_knowledge=memories,
            status="running"
        )
        self.checkpointer.save(state)
        return state
    
    def after_step(self, state: TaskState, event: AgentEvent):
        self.checkpointer.save(state)   # update working memory
        self.event_log.append(event)    # append to episodic memory
    
    def finalize_task(self, state: TaskState, final_output: str):
        # Extract and store valuable findings for future tasks
        if state.status == "done" and final_output:
            self._extract_and_store_knowledge(state.goal, final_output)
        
        state.status = "done"
        state.final_output = final_output
        self.checkpointer.save(state)
    
    def _extract_and_store_knowledge(self, goal: str, output: str):
        extraction_prompt = f"""
        Task: {goal}
        Output: {output}
        
        Extract 3-5 facts or findings from this output that would be useful in future, similar tasks.
        Format each as a single sentence. Be specific and factual.
        """
        findings = llm.invoke(extraction_prompt).content.split("\n")
        for finding in findings:
            if finding.strip():
                store_memory(finding.strip(), "fact", [], importance=0.7)
```

---

## Study Notes

- **Four memory types, four purposes.** In-context = what the LLM sees right now. Working = task state that survives restarts. Episodic = audit trail for debugging. Semantic = long-term knowledge across sessions. Using the wrong type for the job is a common source of bugs (e.g., trying to use in-context memory for cross-session knowledge).
- **The task ledger is the agent's spine.** It's the one component that should always be in context, never summarized away, and always up to date. An agent without a task ledger is an agent that can forget what it was doing.
- **Checkpointing costs very little; not having it costs everything.** A crashed task that must restart from scratch wastes all the API calls made before the crash. Checkpoint to Redis or SQLite after every significant step.
- **Semantic memory requires discipline.** Storing everything poisons it. Store only verified, important facts with an explicit importance score. TTL and pruning are not optional for long-running production systems.
- **Context window management is an engineering task, not an LLM task.** The LLM does not manage its own context. The framework must actively monitor token counts and apply compression strategies before the limit is hit, not after.

---

## Q&A Review Bank

**Q1: What are the four memory types and what is the primary purpose of each?** `[Easy]`
A: In-Context Memory is the LLM's active context window — everything it can "see" in a given API call; its primary purpose is providing the model with immediate, task-relevant context. Working Memory is structured state maintained outside the context window by the orchestration layer (task ledger, partial results, assignments); its purpose is preserving task progress across steps and agent restarts. Episodic Memory is an append-only event log of everything the agent did (tool calls, LLM calls, errors, HITL decisions); its purpose is debugging, auditing, and training data generation. Semantic Memory is a vector store of accumulated knowledge across sessions (facts, preferences, past research); its purpose is giving agents access to relevant knowledge from previous tasks without repeating work.

**Q2: What is context drift and what is the most reliable prevention?** `[Medium]`
A: Context drift is the gradual degradation of agent reasoning quality as the context window fills — the agent starts losing attention to early content (including the original goal), its reasoning becomes inconsistent, and it may repeat work or contradict earlier decisions. The most reliable prevention is the task ledger: a compact, structured record of the goal and remaining subtasks that is always present at the top of the context, never summarized away, and updated after every step. Even if all historical messages are summarized, the task ledger ensures the agent always knows exactly what it set out to do and what remains.

**Q3: Why is checkpointing critical for production agentic systems?** `[Medium]`
A: A multi-step agent task may involve 10–50 LLM calls and many tool calls. Without checkpointing, any failure — network timeout, process crash, server restart, budget exceeded — causes the entire task to fail and requires restarting from scratch, wasting all computation and API costs already incurred. With checkpointing (serializing task state to persistent storage after every step), a resumed task picks up from the last successful step. This is especially important for long-running tasks where restarting from scratch is expensive, tasks that involve HITL gates (the human may have already approved an action), and systems that need to handle failures gracefully rather than crashing.

**Q4: What is memory pollution and what three mechanisms prevent it?** `[Hard]`
A: Memory pollution is the accumulation of incorrect, outdated, or low-quality information in semantic (long-term) memory, which then degrades agent performance in future tasks when retrieved as "authoritative knowledge." Three prevention mechanisms: (1) Quality gates — verify before storing; use an LLM to confirm a fact is accurate and worth preserving; skip low-importance information (importance < threshold). (2) TTL and pruning — set a maximum age for memories; automatically delete memories that haven't been accessed recently AND have low importance scores; facts that are regularly relevant will be re-accessed and survive pruning. (3) Memory correction — when a stored fact is discovered to be wrong, find and delete it from the vector store and replace it with the corrected version; this requires explicit correction logic, not just a new write (which would create a contradiction).

**Q5: When should you retrieve from semantic memory vs read from working memory?** `[Medium]`
A: Retrieve from semantic memory (vector search) when you need knowledge that was accumulated across previous tasks — facts from past research, user preferences, domain knowledge, successful templates. It requires a similarity search and should happen at task initialization and at specific steps where the agent needs external knowledge. Read from working memory (structured state) when you need the current task's state — the task ledger, partial results, agent assignments, error log. Working memory is always available as structured data (no search required) and is read/written continuously throughout the task. The distinction: semantic memory is "what do I know from past experience?"; working memory is "what is the current state of this specific task?"

**Q6: Describe a complete memory access pattern for a multi-step agent task.** `[Hard]`
A: At task start: query semantic memory (vector search) for knowledge relevant to the goal; load working memory (task state from checkpoint) if resuming; initialize in-context memory (system prompt + task ledger + retrieved semantic memories); start appending to episodic memory. Each step: LLM reads full in-context memory; after the step, update working memory (mark subtask progress, append tool results to intermediate outputs); append the step as an event to episodic memory; optionally query semantic memory for step-specific knowledge needs. At task end: extract high-quality findings from the final output and write them to semantic memory for future use; finalize working memory (mark task done, store final output); archive the episodic trace; discard in-context memory (session ends). This full lifecycle ensures the agent benefits from past experience (semantic), recovers from failures (working + checkpointing), and produces debuggable traces (episodic).
