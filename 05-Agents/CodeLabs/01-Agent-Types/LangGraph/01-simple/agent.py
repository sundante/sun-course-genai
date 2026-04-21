"""
LangGraph Simple Agent
======================
Framework : LangGraph
Level     : 01 — Simple
Model     : gemini-2.0-flash via langchain-google-genai

What this demonstrates:
  - Defining a typed AgentState with message-accumulating reducer
  - Two graph nodes: llm_node (calls LLM) and tools_node (executes tools)
  - Conditional routing: if LLM returns tool_calls → tools_node, else → END
  - How LangGraph makes the ReAct loop explicit as a state machine

Mock tools used (no credentials needed):
  - get_weather(city)  → fake weather report
  - get_time(city)     → fake local time
"""

import os
from typing import Annotated
from typing_extensions import TypedDict
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

load_dotenv()

# ── Mock Tools ──────────────────────────────────────────────────────────────

@tool
def get_weather(city: str) -> dict:
    """Return a mock weather report for the given city."""
    mock_data = {
        "london":    {"condition": "Cloudy", "temp_c": 12, "humidity": 78},
        "new york":  {"condition": "Sunny",  "temp_c": 22, "humidity": 45},
        "bangalore": {"condition": "Rainy",  "temp_c": 25, "humidity": 85},
        "tokyo":     {"condition": "Clear",  "temp_c": 18, "humidity": 60},
    }
    key = city.lower()
    if key in mock_data:
        d = mock_data[key]
        return {"city": city, "condition": d["condition"],
                "temperature_celsius": d["temp_c"], "humidity_percent": d["humidity"]}
    return {"error": f"No data for '{city}'. Try: London, New York, Bangalore, Tokyo."}


@tool
def get_time(city: str) -> dict:
    """Return the current local time for the given city."""
    mock_times = {
        "london":    "14:30 GMT",
        "new york":  "09:30 EST",
        "bangalore": "20:00 IST",
        "tokyo":     "22:30 JST",
    }
    key = city.lower()
    if key in mock_times:
        return {"city": city, "local_time": mock_times[key]}
    return {"error": f"No time data for '{city}'. Try: London, New York, Bangalore, Tokyo."}


tools = [get_weather, get_time]

# ── State ───────────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    # add_messages reducer: new messages are appended, not overwritten
    messages: Annotated[list, add_messages]

# ── Model ───────────────────────────────────────────────────────────────────

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
llm_with_tools = llm.bind_tools(tools)

SYSTEM_MSG = SystemMessage(content=(
    "You are a helpful travel assistant. "
    "Use tools to answer weather and time questions. Be concise and friendly."
))

# ── Nodes ───────────────────────────────────────────────────────────────────

def llm_node(state: AgentState) -> dict:
    """Call the LLM with current messages. Returns tool calls or final text."""
    messages = [SYSTEM_MSG] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


tools_node = ToolNode(tools)  # auto-executes any tool_calls in the last message

# ── Graph ───────────────────────────────────────────────────────────────────

graph_builder = StateGraph(AgentState)
graph_builder.add_node("llm", llm_node)
graph_builder.add_node("tools", tools_node)

graph_builder.set_entry_point("llm")

# tools_condition: routes to "tools" if last message has tool_calls, else END
graph_builder.add_conditional_edges("llm", tools_condition)
graph_builder.add_edge("tools", "llm")  # after tools, loop back to LLM

graph = graph_builder.compile()

# ── Run ──────────────────────────────────────────────────────────────────────

def run(query: str) -> str:
    result = graph.invoke({"messages": [HumanMessage(content=query)]})
    return result["messages"][-1].content


if __name__ == "__main__":
    queries = [
        "What's the weather like in Bangalore right now?",
        "What time is it in Tokyo, and is it a good day to go outside?",
    ]
    for q in queries:
        print(f"\nUser: {q}")
        print(f"Agent: {run(q)}")
