"""
LangGraph Intermediate Agent
=============================
Framework : LangGraph
Level     : 02 — Intermediate
Model     : gemini-2.0-flash

New concepts vs Simple:
  - Richer typed state (messages + structured fields)
  - MemorySaver checkpointer for persistent state across invocations
  - 3 tools (added get_travel_advisory)
  - Structured extraction node that populates state fields from tool results

Domain: travel assistant that builds up a structured briefing in graph state.
"""

import os
from typing import Annotated, Optional
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

# ── Mock Tools ────────────────────────────────────────────────────────────────

@tool
def get_weather(city: str) -> dict:
    """Return mock weather data for a city."""
    data = {
        "london":    {"condition": "Cloudy", "temp_c": 12, "humidity": 78},
        "new york":  {"condition": "Sunny",  "temp_c": 22, "humidity": 45},
        "bangalore": {"condition": "Rainy",  "temp_c": 25, "humidity": 85},
        "tokyo":     {"condition": "Clear",  "temp_c": 18, "humidity": 60},
        "paris":     {"condition": "Partly Cloudy", "temp_c": 16, "humidity": 65},
    }
    key = city.lower()
    if key in data:
        d = data[key]
        return {"city": city, "condition": d["condition"],
                "temperature_celsius": d["temp_c"], "humidity_percent": d["humidity"]}
    return {"error": f"No data for '{city}'."}


@tool
def get_time(city: str) -> dict:
    """Return current local time for a city."""
    times = {
        "london": "14:30 GMT", "new york": "09:30 EST",
        "bangalore": "20:00 IST", "tokyo": "22:30 JST", "paris": "15:30 CET",
    }
    key = city.lower()
    if key in times:
        return {"city": city, "local_time": times[key]}
    return {"error": f"No time data for '{city}'."}


@tool
def get_travel_advisory(city: str) -> dict:
    """Return travel safety advisory for a city."""
    advisories = {
        "london":    {"level": "Low",    "notes": "Routine precautions. Pickpocketing in tourist areas."},
        "new york":  {"level": "Low",    "notes": "Normal safety precautions. Avoid isolated areas at night."},
        "bangalore": {"level": "Medium", "notes": "Monsoon affects transport. Air quality can vary."},
        "tokyo":     {"level": "Low",    "notes": "Very safe city. Earthquake preparedness recommended."},
        "paris":     {"level": "Low",    "notes": "Routine precautions. Alert in crowded tourist spots."},
    }
    key = city.lower()
    if key in advisories:
        a = advisories[key]
        return {"city": city, "advisory_level": a["level"], "notes": a["notes"]}
    return {"error": f"No advisory data for '{city}'."}


tools = [get_weather, get_time, get_travel_advisory]

# ── Richer State ──────────────────────────────────────────────────────────────
# Intermediate: state holds more than just messages — structured extraction fields

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    cities_researched: list          # tracks which cities were covered
    last_city: Optional[str]         # last city mentioned, for context

# ── Model + Nodes ─────────────────────────────────────────────────────────────

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
llm_with_tools = llm.bind_tools(tools)

SYSTEM_MSG = SystemMessage(content=(
    "You are a professional travel intelligence assistant. "
    "When asked about a city, always call get_weather, get_time, AND get_travel_advisory. "
    "Remember context from earlier in this conversation."
))

def llm_node(state: AgentState) -> dict:
    messages = [SYSTEM_MSG] + state["messages"]
    response = llm_with_tools.invoke(messages)

    # Extract city from the latest human message (simple heuristic)
    cities = state.get("cities_researched", [])
    last_msg = state["messages"][-1].content if state["messages"] else ""
    known_cities = ["london", "new york", "bangalore", "tokyo", "paris"]
    last_city = state.get("last_city")
    for c in known_cities:
        if c in last_msg.lower() and c not in [x.lower() for x in cities]:
            cities = cities + [c.title()]
            last_city = c.title()
            break

    return {
        "messages": [response],
        "cities_researched": cities,
        "last_city": last_city,
    }


tools_node = ToolNode(tools)

# ── Graph ─────────────────────────────────────────────────────────────────────

builder = StateGraph(AgentState)
builder.add_node("llm", llm_node)
builder.add_node("tools", tools_node)
builder.set_entry_point("llm")
builder.add_conditional_edges("llm", tools_condition)
builder.add_edge("tools", "llm")

# MemorySaver: persists state across graph.invoke() calls for the same thread_id
checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)


def run(query: str, thread_id: str = "thread_01") -> str:
    # thread_id acts like a session ID — same thread = shared memory
    config = {"configurable": {"thread_id": thread_id}}
    result = graph.invoke(
        {"messages": [HumanMessage(content=query)]},
        config=config,
    )
    return result["messages"][-1].content


if __name__ == "__main__":
    print("=== Multi-turn with MemorySaver (persistent state) ===\n")
    tid = "travel_thread"

    turns = [
        "Give me a full travel briefing for Tokyo.",
        "Now do the same for Bangalore. I prefer warm weather — which would you recommend?",
        "Based on what you told me, what's the safer city to visit?",
    ]

    for query in turns:
        print(f"User: {query}")
        print(f"Agent: {run(query, tid)}\n{'-'*60}\n")

    # Inspect the persisted state
    state_snapshot = graph.get_state({"configurable": {"thread_id": tid}})
    print(f"Cities researched: {state_snapshot.values.get('cities_researched', [])}")
    print(f"Total messages in state: {len(state_snapshot.values.get('messages', []))}")
