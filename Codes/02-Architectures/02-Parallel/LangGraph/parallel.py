"""
Parallel Architecture — LangGraph
Pattern: Fan-out via Send() → Independent city nodes → Aggregate

LangGraph's Send() API dispatches the same node to run simultaneously
for multiple inputs. Results accumulate in state and the aggregator node
runs once all parallel branches complete.
"""
import os
from typing import TypedDict, Annotated
import operator
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

load_dotenv()
assert os.getenv("GOOGLE_API_KEY"), "Set GOOGLE_API_KEY in .env"

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)


# ── Mock data ─────────────────────────────────────────────────────────────────

CITY_DATA = {
    "tokyo":     {"weather": "Clear, 18°C, score 9/10", "safety": "Low, score 10/10", "time": "22:30 JST"},
    "paris":     {"weather": "Partly Cloudy, 16°C, score 7/10", "safety": "Low, score 8/10", "time": "15:30 CET"},
    "bangalore": {"weather": "Rainy, 25°C, score 6/10", "safety": "Medium, score 6/10", "time": "20:00 IST"},
}


# ── State ─────────────────────────────────────────────────────────────────────

class OverallState(TypedDict):
    cities: list[str]
    city_reports: Annotated[list[str], operator.add]  # accumulates from parallel branches
    final_ranking: str

class CityState(TypedDict):
    city: str


# ── Nodes ─────────────────────────────────────────────────────────────────────

def fan_out(state: OverallState):
    """Dispatch a research task for each city in parallel using Send()."""
    return [Send("research_city", {"city": c}) for c in state["cities"]]


def research_city(state: CityState) -> dict:
    """Research one city — runs in parallel for all cities."""
    city = state["city"]
    d = CITY_DATA.get(city.lower(), {})
    raw = f"{city} — Weather: {d.get('weather','N/A')} | Safety: {d.get('safety','N/A')} | Time: {d.get('time','N/A')}"

    response = llm.invoke([
        SystemMessage(content="Write a structured 3-line city travel report: Weather, Safety, Recommendation."),
        HumanMessage(content=f"City: {city}\nData: {raw}"),
    ])
    print(f"  [parallel] {city} done")
    return {"city_reports": [f"### {city}\n{response.content}"]}


def aggregate(state: OverallState) -> dict:
    """Aggregate all parallel city reports into a final ranking."""
    combined = "\n\n".join(state["city_reports"])
    response = llm.invoke([
        SystemMessage(content="You are a travel editor. Rank the cities best to worst by weather + safety. Justify each rank."),
        HumanMessage(content=f"City reports:\n\n{combined}\n\nRank all cities and name the top pick."),
    ])
    print("  [aggregate] done")
    return {"final_ranking": response.content}


# ── Graph ─────────────────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    builder = StateGraph(OverallState)
    builder.add_node("research_city", research_city)
    builder.add_node("aggregate", aggregate)

    builder.add_conditional_edges(START, fan_out, ["research_city"])
    builder.add_edge("research_city", "aggregate")
    builder.add_edge("aggregate", END)

    return builder.compile()


if __name__ == "__main__":
    graph = build_graph()
    cities = ["Tokyo", "Paris", "Bangalore"]

    print(f"Launching parallel research for: {cities}")
    result = graph.invoke({"cities": cities, "city_reports": [], "final_ranking": ""})

    print("\n" + "="*60)
    print("# Parallel Travel Report\n")
    for report in result["city_reports"]:
        print(report)
        print()
    print("---\n## Final Ranking")
    print(result["final_ranking"])
