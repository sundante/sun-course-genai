"""
Autonomous Task Planner — LangChain Implementation
==================================================
System    : 03 — Autonomous Task Planner
Framework : LangChain (LCEL)
Model     : gemini-2.0-flash via langchain-google-genai

What this demonstrates:
  - Plan-and-Execute with LangChain: explicit plan → sequential execution loop
  - Monitor function checks each result; triggers replan on failure
  - Task ledger (Python dataclass) tracks state across iterations
  - Bounded loop with MAX_ITERATIONS guard
"""

import os
import json
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.3)

MAX_ITERATIONS = 10
MAX_REPLANS = 2


# ── Task ledger dataclass ──────────────────────────────────────────────────────

@dataclass
class Subtask:
    id: str
    description: str
    depends_on: list[str] = field(default_factory=list)
    status: str = "pending"  # pending | done | failed
    output: Optional[str] = None
    replan_count: int = 0

    def is_ready(self, done_ids: set[str]) -> bool:
        return self.status == "pending" and all(dep in done_ids for dep in self.depends_on)


# ── Agent functions ────────────────────────────────────────────────────────────

def plan_goal(goal: str) -> list[Subtask]:
    """Generate an execution plan for the goal."""
    print(f"\n[Planner] Goal: {goal}")
    print("[Planner] Generating plan...")

    response = llm.invoke([
        SystemMessage(content="""Create a 3-5 step plan. Return JSON array:
        [{"id": "1", "description": "...", "depends_on": []}, ...]
        Each task must be specific and independently executable."""),
        HumanMessage(content=f"Goal: {goal}")
    ]).content

    try:
        clean = response.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        raw = json.loads(clean)
        tasks = [Subtask(id=t["id"], description=t["description"], depends_on=t.get("depends_on", [])) for t in raw]
    except (json.JSONDecodeError, KeyError):
        tasks = [
            Subtask("1", f"Research: {goal}", []),
            Subtask("2", "Analyze and synthesize findings", ["1"]),
            Subtask("3", "Write final recommendations", ["2"]),
        ]

    print(f"[Planner] Plan: {len(tasks)} subtasks")
    for t in tasks:
        print(f"  [{t.id}] {t.description}")
    return tasks


def execute_task(task: Subtask, completed_outputs: list[dict]) -> str:
    """Execute a single subtask."""
    print(f"\n[Executor] Task [{task.id}]: {task.description}")

    context = "\n".join([f"- Task {o['id']}: {o['output'][:100]}" for o in completed_outputs]) if completed_outputs else "No prior context"

    result = llm.invoke([
        SystemMessage(content="Execute the task. Be specific and produce a concrete, complete output."),
        HumanMessage(content=f"Task: {task.description}\n\nPrior work:\n{context}")
    ]).content

    print(f"[Executor] Task [{task.id}] complete ({len(result)} chars)")
    return result


def monitor_result(task: Subtask, result: str) -> tuple[bool, str]:
    """Monitor: evaluate if the task result is acceptable."""
    evaluation = llm.invoke([
        SystemMessage(content="""Evaluate this task result. Reply with:
        VERDICT: PASSED
        or
        VERDICT: FAILED
        REASON: [specific issue]
        Only fail for clearly incomplete or incorrect results."""),
        HumanMessage(content=f"Task: {task.description}\n\nResult:\n{result[:500]}")
    ]).content

    passed = "VERDICT: PASSED" in evaluation
    print(f"[Monitor] Task [{task.id}]: {'PASSED' if passed else 'FAILED'}")
    return passed, evaluation


def synthesize_outputs(goal: str, completed: list[Subtask]) -> str:
    """Synthesize all completed task outputs into final deliverable."""
    print("\n[Synthesizer] Assembling final output...")
    context = "\n\n".join([f"Task {t.id} — {t.description}:\n{t.output}" for t in completed if t.output])
    return llm.invoke([
        SystemMessage(content="Synthesize the completed subtask outputs into a coherent final deliverable."),
        HumanMessage(content=f"Goal: {goal}\n\nCompleted tasks:\n{context}")
    ]).content


# ── Main loop ──────────────────────────────────────────────────────────────────

def run_task_planner(goal: str) -> str:
    subtasks = plan_goal(goal)
    completed_outputs = []
    total_iterations = 0

    while total_iterations < MAX_ITERATIONS:
        total_iterations += 1

        done_ids = {t.id for t in subtasks if t.status == "done"}
        next_task = next((t for t in subtasks if t.is_ready(done_ids)), None)

        if next_task is None:
            break  # All tasks done or no more executable tasks

        # Execute
        result = execute_task(next_task, completed_outputs)

        # Monitor
        passed, critique = monitor_result(next_task, result)

        if passed:
            next_task.status = "done"
            next_task.output = result
            completed_outputs.append({"id": next_task.id, "output": result})
        else:
            next_task.replan_count += 1
            if next_task.replan_count >= MAX_REPLANS:
                print(f"[Replanner] Task [{next_task.id}] skipped after {next_task.replan_count} failures")
                next_task.status = "done"
                next_task.output = f"[Skipped — {next_task.replan_count} failed attempts]"
                completed_outputs.append({"id": next_task.id, "output": next_task.output})
            else:
                print(f"[Replanner] Retrying task [{next_task.id}] (attempt {next_task.replan_count + 1})")
                # Task remains pending — will be picked up in next iteration

    completed = [t for t in subtasks if t.status == "done"]
    return synthesize_outputs(goal, completed)


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    goal = "Create a comprehensive report on best practices for remote work productivity"

    print("\n" + "="*60)
    print("AUTONOMOUS TASK PLANNER — LangChain")
    print(f"Goal: {goal}")
    print("="*60)

    result = run_task_planner(goal)

    print("\n" + "="*60)
    print("FINAL OUTPUT")
    print("="*60)
    print(result)
