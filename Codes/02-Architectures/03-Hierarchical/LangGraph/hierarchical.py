"""
Hierarchical Architecture — LangGraph
Pattern: Supervisor node routes to specialist subgraphs

A supervisor node decides which specialist to call next.
Each specialist handles its domain, then returns control to the supervisor.
This models a manager-team structure with explicit routing.
"""
import os
from typing import TypedDict, Literal, Optional
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END

load_dotenv()
assert os.getenv("GOOGLE_API_KEY"), "Set GOOGLE_API_KEY in .env"

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)


# ── Mock data ─────────────────────────────────────────────────────────────────

WEATHER_DATA = {
    "tokyo":     "Clear, 18°C, weather score 9/10",
    "paris":     "Partly Cloudy, 16°C, weather score 7/10",
    "bangalore": "Rainy, 25°C, weather score 6/10",
}
SAFETY_DATA = {
    "tokyo":     "Low advisory, safety score 10/10. Very safe city.",
    "paris":     "Low advisory, safety score 8/10. Alert in crowded spots.",
    "bangalore": "Medium advisory, safety score 6/10. Monsoon affects transport.",
}


# ── State ─────────────────────────────────────────────────────────────────────

class HierarchyState(TypedDict):
    cities: list[str]
    current_city_index: int
    weather_reports: list[str]
    safety_reports: list[str]
    formatted_sections: list[str]
    executive_summary: Optional[str]
    next_step: str  # supervisor routing signal


# ── Supervisor ────────────────────────────────────────────────────────────────

def supervisor(state: HierarchyState) -> HierarchyState:
    """Determine what to do next based on current state."""
    idx = state["current_city_index"]
    n = len(state["cities"])

    if idx < n and len(state["weather_reports"]) <= idx:
        next_step = "research_weather"
    elif idx < n and len(state["safety_reports"]) <= idx:
        next_step = "research_safety"
    elif idx < n and len(state["formatted_sections"]) <= idx:
        next_step = "format_report"
    elif idx < n:
        # Move to next city
        next_step = "research_weather"
    else:
        next_step = "executive_summary"

    print(f"  [supervisor] → {next_step} (city index: {idx})")
    return {"next_step": next_step}


def route_supervisor(state: HierarchyState) -> str:
    return state["next_step"]


# ── Worker nodes ──────────────────────────────────────────────────────────────

def research_weather(state: HierarchyState) -> HierarchyState:
    idx = state["current_city_index"]
    city = state["cities"][idx]
    data = WEATHER_DATA.get(city.lower(), "N/A")
    r = llm.invoke([
        SystemMessage(content="Write a 1-sentence weather report."),
        HumanMessage(content=f"City: {city}\nData: {data}"),
    ])
    print(f"  [weather_worker] {city}")
    reports = state["weather_reports"] + [r.content]
    return {"weather_reports": reports}


def research_safety(state: HierarchyState) -> HierarchyState:
    idx = state["current_city_index"]
    city = state["cities"][idx]
    data = SAFETY_DATA.get(city.lower(), "N/A")
    r = llm.invoke([
        SystemMessage(content="Write a 1-sentence safety report."),
        HumanMessage(content=f"City: {city}\nData: {data}"),
    ])
    print(f"  [safety_worker] {city}")
    reports = state["safety_reports"] + [r.content]
    return {"safety_reports": reports}


def format_report(state: HierarchyState) -> HierarchyState:
    idx = state["current_city_index"]
    city = state["cities"][idx]
    weather = state["weather_reports"][idx]
    safety = state["safety_reports"][idx]
    r = llm.invoke([
        SystemMessage(content="Format into a polished markdown section with header."),
        HumanMessage(content=f"City: {city}\nWeather: {weather}\nSafety: {safety}\n\nUse '### {city}' header."),
    ])
    print(f"  [format_worker] {city}")
    sections = state["formatted_sections"] + [r.content]
    return {"formatted_sections": sections, "current_city_index": idx + 1}


def executive_summary(state: HierarchyState) -> HierarchyState:
    combined = "\n\n".join(state["formatted_sections"])
    r = llm.invoke([
        SystemMessage(content="You are a travel project manager. Write an executive summary with a top recommendation."),
        HumanMessage(content=f"City reports:\n{combined}\n\nWrite an executive summary."),
    ])
    print("  [manager] executive summary done")
    return {"executive_summary": r.content}


# ── Graph ─────────────────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    builder = StateGraph(HierarchyState)
    builder.add_node("supervisor", supervisor)
    builder.add_node("research_weather", research_weather)
    builder.add_node("research_safety", research_safety)
    builder.add_node("format_report", format_report)
    builder.add_node("executive_summary", executive_summary)

    builder.add_edge(START, "supervisor")
    builder.add_conditional_edges("supervisor", route_supervisor, {
        "research_weather": "research_weather",
        "research_safety": "research_safety",
        "format_report": "format_report",
        "executive_summary": "executive_summary",
    })
    builder.add_edge("research_weather", "supervisor")
    builder.add_edge("research_safety", "supervisor")
    builder.add_edge("format_report", "supervisor")
    builder.add_edge("executive_summary", END)

    return builder.compile()


if __name__ == "__main__":
    cities = ["Tokyo", "Paris"]
    graph = build_graph()

    initial = HierarchyState(
        cities=cities, current_city_index=0,
        weather_reports=[], safety_reports=[], formatted_sections=[],
        executive_summary=None, next_step="",
    )

    print(f"Running hierarchical pipeline for: {cities}")
    result = graph.invoke(initial)

    print("\n" + "="*60)
    print("# Hierarchical Travel Report\n")
    for section in result["formatted_sections"]:
        print(section)
        print()
    print("## Executive Summary")
    print(result["executive_summary"])
