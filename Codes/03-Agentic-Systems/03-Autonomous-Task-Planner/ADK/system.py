"""
Autonomous Task Planner — Google ADK Implementation
===================================================
System    : 03 — Autonomous Task Planner
Framework : Google Agent Development Kit (ADK)
Model     : gemini-2.0-flash

What this demonstrates:
  - ADK SequentialAgent composing planner, executor, monitor, and synthesizer
  - FunctionTool for task management utilities (get_next_task, mark_done)
  - Each agent in the sequence builds on prior outputs
  - Bounded execution through agent instructions
"""

import os
import json
from dotenv import load_dotenv
from google.adk.agents import Agent, SequentialAgent
from google.adk.tools import FunctionTool
from google.adk.runners import InProcessRunner
from google.adk.sessions import InMemorySessionService

load_dotenv()

GOAL = "Create a comprehensive report on remote work productivity best practices"


# ── Tools ──────────────────────────────────────────────────────────────────────

def decompose_goal(goal: str) -> dict:
    """Decompose a goal into structured subtasks with dependencies.

    Args:
        goal: The high-level goal to decompose

    Returns:
        dict with subtasks list, each having id, description, and depends_on
    """
    # In production this would call an LLM or task planning service
    return {
        "goal": goal,
        "subtasks": [
            {"id": "1", "description": f"Research: {goal}", "depends_on": []},
            {"id": "2", "description": "Analyze findings and extract insights", "depends_on": ["1"]},
            {"id": "3", "description": "Write recommendations and structure final report", "depends_on": ["2"]},
        ]
    }


def validate_task_output(task_description: str, output_summary: str) -> dict:
    """Validate whether a task output meets quality standards.

    Args:
        task_description: What the task was supposed to accomplish
        output_summary: Brief summary of what was produced

    Returns:
        dict with passed (bool), issues (list), and recommendation
    """
    # Simple heuristic validation — in production use LLM-as-Judge
    is_empty = len(output_summary.strip()) < 50
    return {
        "passed": not is_empty,
        "issues": ["Output too short or empty"] if is_empty else [],
        "recommendation": "retry" if is_empty else "proceed"
    }


# ── ADK Agents ─────────────────────────────────────────────────────────────────

planner_agent = Agent(
    name="task_planner",
    model="gemini-2.0-flash",
    description="Decomposes goals into structured execution plans",
    instruction="""You are a task planning specialist. Given a goal:
    1. Use the decompose_goal tool to get a structured breakdown
    2. Review the subtasks and add any missing steps
    3. Present the final plan clearly with numbered steps and dependencies

    Output the plan in this format:
    PLAN FOR: [goal]
    SUBTASKS:
    [1] Description (no dependencies)
    [2] Description (depends on: 1)
    ...""",
    tools=[FunctionTool(decompose_goal)],
)

executor_agent = Agent(
    name="task_executor",
    model="gemini-2.0-flash",
    description="Executes planned subtasks in dependency order",
    instruction="""You are a task execution specialist. Given the plan from the planner:
    Execute each subtask in the correct order (respecting dependencies).

    For each subtask:
    1. State which task you are executing
    2. Produce a concrete, specific output for that task
    3. Mark it complete before moving to the next

    Be thorough — each task output should be substantive and specific.""",
)

monitor_agent = Agent(
    name="execution_monitor",
    model="gemini-2.0-flash",
    description="Monitors execution quality and flags issues",
    instruction="""You are a quality monitor. Review the execution outputs:
    1. Use validate_task_output to check each task's output quality
    2. Identify any tasks that produced insufficient output
    3. Flag specific issues for any failed tasks

    Report:
    MONITORING REPORT:
    - Task 1: [PASSED/FAILED] - [brief note]
    - Task 2: [PASSED/FAILED] - [brief note]
    OVERALL: [PASSED/NEEDS_REVISION] - [summary]""",
    tools=[FunctionTool(validate_task_output)],
)

synthesizer_agent = Agent(
    name="output_synthesizer",
    model="gemini-2.0-flash",
    description="Synthesizes all task outputs into the final deliverable",
    instruction="""You are a synthesis specialist. Using all outputs from the executor:
    Create the final comprehensive deliverable for the original goal.

    Structure the final output with:
    1. Executive Summary
    2. Main content sections (based on what was researched and analyzed)
    3. Actionable Recommendations
    4. Conclusion

    The output should be polished, complete, and ready for the end user.""",
)

# ── Compose full planner system ────────────────────────────────────────────────

task_planner_system = SequentialAgent(
    name="autonomous_task_planner",
    description="Complete autonomous task planner: plan → execute → monitor → synthesize",
    sub_agents=[planner_agent, executor_agent, monitor_agent, synthesizer_agent],
)


# ── Runner ──────────────────────────────────────────────────────────────────────

def run_planner(goal: str) -> str:
    session_service = InMemorySessionService()
    runner = InProcessRunner(
        agent=task_planner_system,
        session_service=session_service,
        app_name="task_planner",
    )
    session = session_service.create_session(app_name="task_planner", user_id="u001")

    from google.adk.types import Content, Part
    response = runner.run(
        user_id="u001",
        session_id=session.id,
        new_message=Content(parts=[Part(text=f"Goal: {goal}")]),
    )
    return response.text if hasattr(response, 'text') else str(response)


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "="*60)
    print("AUTONOMOUS TASK PLANNER — ADK")
    print(f"Goal: {GOAL}")
    print("="*60)

    result = run_planner(GOAL)

    print("\n" + "="*60)
    print("FINAL OUTPUT")
    print("="*60)
    print(result)
