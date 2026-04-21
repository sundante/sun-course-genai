"""
Orchestrator-Subagent Architecture — LangGraph
Pattern: Orchestrator node selects specialists via conditional routing

The orchestrator node reads a task queue and dispatches to specialist nodes.
State tracks which tasks are pending and what results have been collected.
"""
import os
from typing import TypedDict, Optional
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END

load_dotenv()
assert os.getenv("GOOGLE_API_KEY"), "Set GOOGLE_API_KEY in .env"

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

CITY_HIGHLIGHTS = {
    "tokyo":     "Shibuya, Senso-ji, Tsukiji, Mt Fuji day trip",
    "paris":     "Eiffel Tower, Louvre, Notre Dame, Seine cruise",
    "bangalore": "Lalbagh, Nandi Hills, Cubbon Park, Vidhana Soudha",
}
CITY_LOGISTICS = {
    "tokyo":     "3h from SFO. Shinkansen. Best: March-May.",
    "paris":     "11h from NYC. Metro/RER. Best: April-June.",
    "bangalore": "9h from Dubai. Ola/Uber. Best: Oct-Feb.",
}


# ── State ─────────────────────────────────────────────────────────────────────

class OrchestratorState(TypedDict):
    city: str
    pending_tasks: list[str]       # tasks the orchestrator queues
    highlights: Optional[str]
    logistics: Optional[str]
    itinerary: Optional[str]
    final_package: Optional[str]
    next_task: str


# ── Orchestrator node ─────────────────────────────────────────────────────────

def orchestrator(state: OrchestratorState) -> OrchestratorState:
    """Read pending_tasks and pop the next one to run."""
    pending = state["pending_tasks"]
    if pending:
        next_task = pending[0]
        remaining = pending[1:]
        print(f"  [Orchestrator] dispatching → {next_task}")
        return {"pending_tasks": remaining, "next_task": next_task}
    return {"next_task": "done"}


def route_orchestrator(state: OrchestratorState) -> str:
    return state["next_task"]


# ── Specialist nodes ──────────────────────────────────────────────────────────

def highlights_agent(state: OrchestratorState) -> OrchestratorState:
    city = state["city"]
    r = llm.invoke([
        SystemMessage(content="List top 3 attractions with one-line descriptions."),
        HumanMessage(content=f"City: {city}\nData: {CITY_HIGHLIGHTS.get(city.lower(), 'N/A')}"),
    ])
    print("  [highlights_agent] done")
    return {"highlights": r.content}


def logistics_agent(state: OrchestratorState) -> OrchestratorState:
    city = state["city"]
    r = llm.invoke([
        SystemMessage(content="Provide practical travel tips: flights, local transport, best season."),
        HumanMessage(content=f"City: {city}\nData: {CITY_LOGISTICS.get(city.lower(), 'N/A')}"),
    ])
    print("  [logistics_agent] done")
    return {"logistics": r.content}


def itinerary_agent(state: OrchestratorState) -> OrchestratorState:
    r = llm.invoke([
        SystemMessage(content="Create a 3-day itinerary using highlights and logistics."),
        HumanMessage(content=f"City: {state['city']}\nHighlights: {state['highlights']}\nLogistics: {state['logistics']}"),
    ])
    print("  [itinerary_agent] done")
    return {"itinerary": r.content}


def package_formatter(state: OrchestratorState) -> OrchestratorState:
    r = llm.invoke([
        SystemMessage(content="Format into a polished trip package with clear '##' sections."),
        HumanMessage(content=f"City: {state['city']}\nHighlights: {state['highlights']}\nLogistics: {state['logistics']}\nItinerary: {state['itinerary']}"),
    ])
    print("  [package_formatter] done")
    return {"final_package": r.content}


# ── Graph ─────────────────────────────────────────────────────────────────────

def build_graph():
    builder = StateGraph(OrchestratorState)
    builder.add_node("orchestrator", orchestrator)
    builder.add_node("highlights", highlights_agent)
    builder.add_node("logistics", logistics_agent)
    builder.add_node("itinerary", itinerary_agent)
    builder.add_node("format", package_formatter)

    builder.add_edge(START, "orchestrator")
    builder.add_conditional_edges("orchestrator", route_orchestrator, {
        "highlights": "highlights",
        "logistics":  "logistics",
        "itinerary":  "itinerary",
        "format":     "format",
        "done":        END,
    })
    for node in ["highlights", "logistics", "itinerary", "format"]:
        builder.add_edge(node, "orchestrator")

    return builder.compile()


if __name__ == "__main__":
    graph = build_graph()
    city = "Tokyo"
    print(f"[Orchestrator] starting trip package for: {city}")

    result = graph.invoke({
        "city": city,
        "pending_tasks": ["highlights", "logistics", "itinerary", "format"],
        "highlights": None, "logistics": None, "itinerary": None,
        "final_package": None, "next_task": "",
    })

    print("\n" + "="*60)
    print(result["final_package"])
