"""
Sequential Architecture — LangGraph
Pattern: Research → Summarize → Format report (A → B → C pipeline)

Each step is a graph node. State flows through the graph — each node reads
from state and writes back. The graph enforces the A→B→C order explicitly.
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


# ── Mock data source ─────────────────────────────────────────────────────────

def fetch_city_data(city: str) -> str:
    data = {
        "tokyo":     "Weather: Clear, 18°C. Safety: Low. Time: 22:30 JST. Highlights: Shibuya, Senso-ji.",
        "paris":     "Weather: Partly Cloudy, 16°C. Safety: Low. Time: 15:30 CET. Highlights: Eiffel Tower, Louvre.",
        "bangalore": "Weather: Rainy, 25°C. Safety: Medium. Time: 20:00 IST. Highlights: Lalbagh, Nandi Hills.",
    }
    return data.get(city.lower(), f"No data for {city}.")


# ── State ─────────────────────────────────────────────────────────────────────

class PipelineState(TypedDict):
    city: str
    raw_data: str
    structured_facts: Optional[str]
    summary: Optional[str]
    report_section: Optional[str]


# ── Nodes ─────────────────────────────────────────────────────────────────────

def researcher_node(state: PipelineState) -> PipelineState:
    """Step 1: fetch raw data and extract structured facts."""
    raw = fetch_city_data(state["city"])
    response = llm.invoke([
        SystemMessage(content="You are a travel data researcher. Extract and structure the key facts."),
        HumanMessage(content=f"City: {state['city']}\nRaw data: {raw}\n\nExtract: weather, safety, time, top 2 attractions."),
    ])
    print(f"  [researcher] done for {state['city']}")
    return {"raw_data": raw, "structured_facts": response.content}


def summarizer_node(state: PipelineState) -> PipelineState:
    """Step 2: write a 2-sentence traveler summary from structured facts."""
    response = llm.invoke([
        SystemMessage(content="You are a travel writer. Write a concise 2-sentence city summary."),
        HumanMessage(content=f"Facts:\n{state['structured_facts']}\n\nWrite a traveler summary."),
    ])
    print(f"  [summarizer] done for {state['city']}")
    return {"summary": response.content}


def formatter_node(state: PipelineState) -> PipelineState:
    """Step 3: format summary into a polished report section."""
    response = llm.invoke([
        SystemMessage(content="You are a report editor. Format into a polished report section with a markdown header."),
        HumanMessage(content=f"City: {state['city']}\nSummary: {state['summary']}\n\nFormat with '### {state['city']}' header."),
    ])
    print(f"  [formatter] done for {state['city']}")
    return {"report_section": response.content}


# ── Graph ─────────────────────────────────────────────────────────────────────

def build_pipeline() -> StateGraph:
    builder = StateGraph(PipelineState)
    builder.add_node("researcher", researcher_node)
    builder.add_node("summarizer", summarizer_node)
    builder.add_node("formatter", formatter_node)

    builder.add_edge(START, "researcher")
    builder.add_edge("researcher", "summarizer")
    builder.add_edge("summarizer", "formatter")
    builder.add_edge("formatter", END)

    return builder.compile()


def run_pipeline(city: str) -> str:
    graph = build_pipeline()
    initial_state = PipelineState(
        city=city, raw_data="", structured_facts=None, summary=None, report_section=None
    )
    print(f"\nProcessing: {city}")
    final_state = graph.invoke(initial_state)
    return final_state["report_section"]


if __name__ == "__main__":
    cities = ["Tokyo", "Paris", "Bangalore"]
    sections = []
    for city in cities:
        section = run_pipeline(city)
        sections.append(section)

    print("\n" + "="*60)
    print("FINAL REPORT")
    print("="*60)
    print("# Travel Report\n")
    print("\n\n".join(sections))
