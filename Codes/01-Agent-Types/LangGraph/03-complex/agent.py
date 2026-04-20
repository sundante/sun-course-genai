"""
LangGraph Complex Agent
========================
Framework : LangGraph
Level     : 03 — Complex
Model     : gemini-2.0-flash

New concepts vs Intermediate:
  - Explicit planning node (separate from execution)
  - Reflexion loop: critic node scores output, conditional edge retries if score < 7
  - Richer state: tracks plan, draft, critique, attempt count
  - Streaming with graph.stream() — see every node transition
  - Conditional edges based on custom state fields (not just tool_calls)

Domain: multi-city trip planner with plan → research → draft → critique → conditional retry.
"""

import os
from typing import Annotated, Optional
from typing_extensions import TypedDict
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, END
from langgraph.graph import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

load_dotenv()

# ── Tools ─────────────────────────────────────────────────────────────────────

@tool
def get_weather(city: str) -> dict:
    """Return weather data including a weather score (1-10) for a city."""
    data = {
        "london":    {"condition": "Cloudy",       "temp_c": 12, "score": 5},
        "new york":  {"condition": "Sunny",         "temp_c": 22, "score": 8},
        "bangalore": {"condition": "Rainy",         "temp_c": 25, "score": 6},
        "tokyo":     {"condition": "Clear",         "temp_c": 18, "score": 9},
        "paris":     {"condition": "Partly Cloudy", "temp_c": 16, "score": 7},
    }
    key = city.lower()
    return {"city": city, **data[key]} if key in data else {"error": f"No data for '{city}'."}


@tool
def get_time(city: str) -> dict:
    """Return current local time for a city."""
    times = {
        "london": "14:30 GMT", "new york": "09:30 EST",
        "bangalore": "20:00 IST", "tokyo": "22:30 JST", "paris": "15:30 CET",
    }
    return {"city": city, "local_time": times.get(city.lower(), "Unknown")}


@tool
def get_travel_advisory(city: str) -> dict:
    """Return travel safety advisory and safety score for a city."""
    data = {
        "london":    {"level": "Low",    "notes": "Routine precautions.",      "safety_score": 8},
        "new york":  {"level": "Low",    "notes": "Normal precautions.",       "safety_score": 7},
        "bangalore": {"level": "Medium", "notes": "Monsoon affects transport.", "safety_score": 6},
        "tokyo":     {"level": "Low",    "notes": "Very safe city.",            "safety_score": 10},
        "paris":     {"level": "Low",    "notes": "Alert in crowded spots.",    "safety_score": 8},
    }
    key = city.lower()
    return {"city": city, **data[key]} if key in data else {"error": f"No advisory for '{city}'."}


tools = [get_weather, get_time, get_travel_advisory]

# ── State ─────────────────────────────────────────────────────────────────────

class PlannerState(TypedDict):
    messages: Annotated[list, add_messages]
    plan: Optional[str]          # step-by-step research plan
    draft_report: Optional[str]  # current best draft
    critique: Optional[str]      # latest critique
    quality_score: int           # latest quality score (0-10)
    attempt: int                 # reflexion attempt count
    goal: str                    # original user goal

# ── LLMs ──────────────────────────────────────────────────────────────────────

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
llm_with_tools = llm.bind_tools(tools)

# ── Nodes ─────────────────────────────────────────────────────────────────────

RESEARCH_SYSTEM = SystemMessage(content=(
    "You are a travel researcher. Call get_weather, get_time, and get_travel_advisory "
    "for EVERY city mentioned in the plan. Gather all data before stopping."
))

def planner_node(state: PlannerState) -> dict:
    """Decompose the goal into a numbered research plan."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Create a numbered research plan. Each line: 'N. Research [city]: weather, time, advisory'"),
        ("human", "{goal}"),
    ])
    chain = prompt | llm | StrOutputParser()
    plan = chain.invoke({"goal": state["goal"]})
    return {
        "plan": plan,
        "messages": [AIMessage(content=f"Plan:\n{plan}")],
    }


def researcher_node(state: PlannerState) -> dict:
    """Call the LLM with tools to execute the plan."""
    instruction = f"Execute this research plan:\n{state['plan']}\n\nCall all required tools."
    messages = [RESEARCH_SYSTEM, HumanMessage(content=instruction)] + state["messages"][-4:]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


tools_node = ToolNode(tools)


def drafter_node(state: PlannerState) -> dict:
    """Synthesize tool results into a comparison report."""
    tool_results = [m for m in state["messages"] if hasattr(m, "type") and m.type == "tool"]
    data_summary = "\n".join(str(m.content)[:200] for m in tool_results[-10:])

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "Write a travel comparison report. Include: ranked list of cities, "
         "weather scores, safety scores, and a final recommendation. "
         "Minimum 300 words. Be specific with numbers."),
        ("human", f"Research data:\n{data_summary}\n\nWrite the report:"),
    ])
    draft = (prompt | llm | StrOutputParser()).invoke({})
    return {
        "draft_report": draft,
        "messages": [AIMessage(content=f"Draft report written ({len(draft)} chars)")],
    }


def critic_node(state: PlannerState) -> dict:
    """Score the draft report and return structured feedback."""
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "Score this travel report 1-10. Check: has rankings? specific numbers? "
         "safety info? at least 200 chars?\n"
         "Respond ONLY: SCORE:[number] VERDICT:[PASS/REVISE] ISSUES:[text or None]"),
        ("human", f"Report:\n{state['draft_report']}"),
    ])
    critique = (prompt | llm | StrOutputParser()).invoke({})

    # Parse score
    score = 5
    for part in critique.split():
        if part.startswith("SCORE:"):
            try:
                score = int(part.split(":")[1])
            except ValueError:
                pass

    return {
        "critique": critique,
        "quality_score": score,
        "attempt": state.get("attempt", 0) + 1,
        "messages": [AIMessage(content=f"Critique: {critique}")],
    }


def reviser_node(state: PlannerState) -> dict:
    """Rewrite the draft addressing the critique."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Improve this travel report. Fix the issues. Keep all existing data."),
        ("human",
         f"Original report:\n{state['draft_report']}\n\n"
         f"Critique:\n{state['critique']}\n\nImproved version:"),
    ])
    revised = (prompt | llm | StrOutputParser()).invoke({})
    return {
        "draft_report": revised,
        "messages": [AIMessage(content=f"Report revised (attempt {state['attempt']})")],
    }


# ── Routing Logic ──────────────────────────────────────────────────────────────

def route_after_research(state: PlannerState) -> str:
    """After research node: route to tools if tool_calls exist, else to drafter."""
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return "drafter"


def route_after_critic(state: PlannerState) -> str:
    """After critic: pass if score >= 7 or max retries reached, else revise."""
    if state["quality_score"] >= 7 or state.get("attempt", 0) >= 2:
        return END
    return "reviser"


# ── Graph ─────────────────────────────────────────────────────────────────────

builder = StateGraph(PlannerState)
builder.add_node("planner",    planner_node)
builder.add_node("researcher", researcher_node)
builder.add_node("tools",      tools_node)
builder.add_node("drafter",    drafter_node)
builder.add_node("critic",     critic_node)
builder.add_node("reviser",    reviser_node)

builder.set_entry_point("planner")
builder.add_edge("planner", "researcher")
builder.add_conditional_edges("researcher", route_after_research,
                               {"tools": "tools", "drafter": "drafter"})
builder.add_edge("tools", "researcher")
builder.add_edge("drafter", "critic")
builder.add_conditional_edges("critic", route_after_critic,
                               {"reviser": "reviser", END: END})
builder.add_edge("reviser", "critic")

graph = builder.compile()


def run(goal: str) -> str:
    print(f"Goal: {goal}\n")
    final_state = None

    for step in graph.stream(
        {"messages": [], "goal": goal, "attempt": 0, "quality_score": 0,
         "plan": None, "draft_report": None, "critique": None},
        stream_mode="values",
    ):
        node_msgs = step.get("messages", [])
        if node_msgs:
            last = node_msgs[-1]
            if hasattr(last, "content") and isinstance(last.content, str):
                preview = last.content[:100].replace("\n", " ")
                print(f"  → {preview}")
        final_state = step

    return final_state["draft_report"] if final_state else "No output"


if __name__ == "__main__":
    goal = "Compare Tokyo, Paris, and Bangalore for travel. Rank by best weather and safety."
    report = run(goal)
    print("\n" + "="*60)
    print("FINAL REPORT")
    print("="*60)
    print(report)
