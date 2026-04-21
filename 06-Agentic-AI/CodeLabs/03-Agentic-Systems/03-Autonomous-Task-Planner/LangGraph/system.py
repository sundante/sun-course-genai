"""
Autonomous Task Planner — LangGraph Implementation
==================================================
System    : 03 — Autonomous Task Planner
Framework : LangGraph
Model     : gemini-2.0-flash via langchain-google-genai

What this demonstrates:
  - Plan-and-Execute pattern: full plan generated before execution begins
  - Task ledger in graph state for dependency tracking
  - Monitor node evaluates each result — conditional edge triggers replanning
  - LangGraph's StateGraph loop: plan → execute → monitor → (replan or next_task)
  - Bounded execution: max_iterations prevents infinite replanning loops

Architecture:
  plan → execute_next → monitor → [passed: execute_next | failed: replan] → synthesize → END
"""

import os
import json
from typing import TypedDict, Optional, Annotated
import operator
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END

load_dotenv()

# ── State definition ───────────────────────────────────────────────────────────

class Subtask(TypedDict):
    id: str
    description: str
    depends_on: list[str]
    status: str  # "pending", "in_progress", "done", "failed"
    output: Optional[str]
    replan_count: int


class PlannerState(TypedDict):
    goal: str
    subtasks: list[Subtask]
    current_task_id: Optional[str]
    last_result: Optional[str]
    monitor_verdict: str  # "passed" | "failed"
    completed_outputs: Annotated[list[dict], operator.add]
    total_iterations: int
    final_output: str


MAX_ITERATIONS = 10
MAX_REPLANS_PER_TASK = 2

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.3)


# ── Mock tools available to the executor ──────────────────────────────────────

@tool
def research_topic(topic: str) -> dict:
    """Research a topic and return findings. Use for gathering information."""
    facts = {
        "remote work productivity": {
            "key_findings": [
                "Stanford study: remote workers 13% more productive",
                "47% of remote workers report higher job satisfaction",
                "Challenges: collaboration, onboarding, culture maintenance",
                "Best tools: Slack, Zoom, Notion, Linear for async coordination",
            ],
            "sources": ["Stanford GSB Study 2023", "Buffer State of Remote Work 2024"]
        }
    }
    return facts.get(topic.lower(), {"key_findings": [f"Research findings for: {topic}"], "sources": []})


@tool
def analyze_data(data_description: str) -> dict:
    """Analyze data or findings and return structured insights."""
    return {
        "analysis": f"Analysis of: {data_description}",
        "key_insights": [
            "Productivity gains are real but require deliberate management",
            "Hybrid model balances flexibility with in-person collaboration needs",
            "Tool standardization is critical for distributed team success",
        ],
        "confidence": "high"
    }


@tool
def write_section(title: str, content_brief: str) -> str:
    """Write a section of a document given a title and content brief."""
    return f"## {title}\n\n{content_brief}\n\n[Section complete — detailed content based on research and analysis above]"


# ── Graph nodes ────────────────────────────────────────────────────────────────

def plan(state: PlannerState) -> dict:
    """Planner: decompose the goal into a list of ordered subtasks."""
    print(f"\n[Planner] Goal: {state['goal']}")
    print("[Planner] Generating execution plan...")

    response = llm.invoke([
        SystemMessage(content="""You are a task planning specialist. Break down the goal into 3-5 ordered subtasks.
        Return JSON array only:
        [
          {"id": "1", "description": "...", "depends_on": [], "tool_hint": "research_topic|analyze_data|write_section"},
          {"id": "2", "description": "...", "depends_on": ["1"], "tool_hint": "..."},
          ...
        ]
        Each task should be atomic and executable. Include tool hints."""),
        HumanMessage(content=f"Goal: {state['goal']}")
    ]).content

    try:
        clean = response.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        raw_tasks = json.loads(clean)
    except json.JSONDecodeError:
        # Fallback plan
        raw_tasks = [
            {"id": "1", "description": f"Research: {state['goal']}", "depends_on": [], "tool_hint": "research_topic"},
            {"id": "2", "description": "Analyze findings", "depends_on": ["1"], "tool_hint": "analyze_data"},
            {"id": "3", "description": "Write final report", "depends_on": ["2"], "tool_hint": "write_section"},
        ]

    subtasks = [
        Subtask(
            id=t["id"], description=t["description"], depends_on=t.get("depends_on", []),
            status="pending", output=None, replan_count=0
        )
        for t in raw_tasks
    ]

    print(f"[Planner] Plan created: {len(subtasks)} subtasks")
    for t in subtasks:
        print(f"  [{t['id']}] {t['description']} (deps: {t['depends_on']})")

    return {"subtasks": subtasks, "total_iterations": 0}


def get_next_task(subtasks: list[Subtask]) -> Optional[Subtask]:
    """Find the next executable task (all dependencies done, status pending)."""
    done_ids = {t["id"] for t in subtasks if t["status"] == "done"}
    for task in subtasks:
        if task["status"] == "pending" and all(dep in done_ids for dep in task["depends_on"]):
            return task
    return None


def execute_next(state: PlannerState) -> dict:
    """Executor: find and execute the next ready subtask."""
    next_task = get_next_task(state["subtasks"])
    if not next_task:
        return {"current_task_id": None}

    print(f"\n[Executor] Running task [{next_task['id']}]: {next_task['description']}")

    # Mark in progress
    updated_subtasks = [
        {**t, "status": "in_progress"} if t["id"] == next_task["id"] else t
        for t in state["subtasks"]
    ]

    # Execute the task using LLM with tool context
    result = llm.invoke([
        SystemMessage(content="""Execute the given task. Use the available tools if appropriate.
        Return a clear, specific result that addresses the task description."""),
        HumanMessage(content=f"Task: {next_task['description']}\n\nContext — completed tasks so far:\n" +
                     "\n".join(f"- Task {o['id']}: {o['output'][:100]}..." for o in state["completed_outputs"]))
    ]).content

    print(f"[Executor] Task [{next_task['id']}] complete")

    return {
        "subtasks": updated_subtasks,
        "current_task_id": next_task["id"],
        "last_result": result,
        "total_iterations": state["total_iterations"] + 1,
    }


def monitor(state: PlannerState) -> dict:
    """Monitor: evaluate the quality of the last task result."""
    if not state.get("current_task_id"):
        return {"monitor_verdict": "passed"}

    current_task = next((t for t in state["subtasks"] if t["id"] == state["current_task_id"]), None)
    if not current_task:
        return {"monitor_verdict": "passed"}

    print(f"[Monitor] Evaluating task [{current_task['id']}]...")

    evaluation = llm.invoke([
        SystemMessage(content="""Evaluate this task result. Reply with exactly:
        VERDICT: PASSED
        or
        VERDICT: FAILED
        REASON: [specific issue]
        Only fail if the result is clearly incomplete, wrong, or missing key information."""),
        HumanMessage(content=f"Task: {current_task['description']}\n\nResult:\n{state['last_result']}")
    ]).content

    passed = "VERDICT: PASSED" in evaluation
    print(f"[Monitor] Verdict: {'PASSED' if passed else 'FAILED'}")

    if passed:
        # Mark task done, save output
        updated_subtasks = [
            {**t, "status": "done", "output": state["last_result"]} if t["id"] == state["current_task_id"] else t
            for t in state["subtasks"]
        ]
        return {
            "monitor_verdict": "passed",
            "subtasks": updated_subtasks,
            "completed_outputs": [{"id": state["current_task_id"], "output": state["last_result"]}],
        }
    else:
        # Mark task failed
        updated_subtasks = [
            {**t, "status": "failed", "replan_count": t["replan_count"] + 1}
            if t["id"] == state["current_task_id"] else t
            for t in state["subtasks"]
        ]
        return {
            "monitor_verdict": "failed",
            "subtasks": updated_subtasks,
        }


def replan(state: PlannerState) -> dict:
    """Replanner: update the remaining plan after a task failure."""
    failed_task = next((t for t in state["subtasks"] if t["id"] == state["current_task_id"]), None)
    print(f"\n[Replanner] Replanning after failure in task [{failed_task['id'] if failed_task else '?'}]...")

    if failed_task and failed_task["replan_count"] >= MAX_REPLANS_PER_TASK:
        print(f"[Replanner] Task [{failed_task['id']}] exceeded max replans — skipping")
        updated_subtasks = [
            {**t, "status": "done", "output": f"[Skipped after {t['replan_count']} failed attempts]"}
            if t["id"] == state["current_task_id"] else t
            for t in state["subtasks"]
        ]
        return {"subtasks": updated_subtasks, "monitor_verdict": "passed"}

    # Reset failed task to pending for retry
    updated_subtasks = [
        {**t, "status": "pending"} if t["id"] == state["current_task_id"] else t
        for t in state["subtasks"]
    ]
    return {"subtasks": updated_subtasks}


def synthesize(state: PlannerState) -> dict:
    """Synthesizer: assemble all task outputs into the final result."""
    print("\n[Synthesizer] Assembling final output...")

    completed = [t for t in state["subtasks"] if t["status"] == "done"]
    context = "\n\n".join([
        f"Subtask {t['id']}: {t['description']}\nOutput: {t['output']}"
        for t in completed if t.get("output")
    ])

    final = llm.invoke([
        SystemMessage(content="Synthesize these completed subtask outputs into a coherent final deliverable for the original goal."),
        HumanMessage(content=f"Goal: {state['goal']}\n\nCompleted subtasks:\n{context}")
    ]).content

    return {"final_output": final}


# ── Routing functions ──────────────────────────────────────────────────────────

def after_monitor(state: PlannerState) -> str:
    if state["total_iterations"] >= MAX_ITERATIONS:
        return "synthesize"
    if state["monitor_verdict"] == "failed":
        return "replan"
    next_task = get_next_task(state["subtasks"])
    if next_task:
        return "execute_next"
    return "synthesize"


def after_replan(state: PlannerState) -> str:
    return "execute_next"


# ── Build graph ────────────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    graph = StateGraph(PlannerState)

    graph.add_node("plan", plan)
    graph.add_node("execute_next", execute_next)
    graph.add_node("monitor", monitor)
    graph.add_node("replan", replan)
    graph.add_node("synthesize", synthesize)

    graph.set_entry_point("plan")
    graph.add_edge("plan", "execute_next")
    graph.add_edge("execute_next", "monitor")
    graph.add_conditional_edges("monitor", after_monitor, {
        "execute_next": "execute_next",
        "replan": "replan",
        "synthesize": "synthesize",
    })
    graph.add_conditional_edges("replan", after_replan, {
        "execute_next": "execute_next",
    })
    graph.add_edge("synthesize", END)

    return graph.compile()


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = build_graph()

    goal = "Create a comprehensive report on best practices for remote work productivity, including research findings, analysis, and actionable recommendations"

    print("\n" + "="*60)
    print("AUTONOMOUS TASK PLANNER — LangGraph")
    print(f"Goal: {goal}")
    print("="*60)

    initial_state = PlannerState(
        goal=goal,
        subtasks=[],
        current_task_id=None,
        last_result=None,
        monitor_verdict="",
        completed_outputs=[],
        total_iterations=0,
        final_output="",
    )

    final_state = app.invoke(initial_state)

    print("\n" + "="*60)
    print("FINAL OUTPUT")
    print("="*60)
    print(final_state["final_output"])
