"""
Pipeline Architecture — LangGraph
Pattern: ETL as a state graph — Extract → Transform → Load nodes

Each step is a graph node with a clear state contract.
Pure Python nodes and LLM nodes are mixed transparently.
"""
import os
import json
from typing import TypedDict, Optional
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END

load_dotenv()
assert os.getenv("GOOGLE_API_KEY"), "Set GOOGLE_API_KEY in .env"

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

RAW_DATA = [
    "Tokyo|Clear|18|Low|10|22:30 JST",
    "Paris|Partly Cloudy|16|Low|8|15:30 CET",
    "Bangalore|Rainy|25|Medium|6|20:00 IST",
]


class PipelineState(TypedDict):
    raw_records: list[str]
    extracted: Optional[list[dict]]
    transformed: Optional[list[dict]]
    final_report: Optional[str]


def extract_node(state: PipelineState) -> PipelineState:
    records = []
    for line in state["raw_records"]:
        city, weather, temp, safety_level, safety_score, time = line.split("|")
        records.append({"city": city, "weather": weather, "temp_c": int(temp),
                        "safety_level": safety_level, "safety_score": int(safety_score), "local_time": time})
    print(f"  [extract] {len(records)} records")
    return {"extracted": records}


def transform_node(state: PipelineState) -> PipelineState:
    score_map = {"Clear": 9, "Partly Cloudy": 7, "Rainy": 6, "Cloudy": 5}
    records = state["extracted"].copy()
    for r in records:
        r["weather_score"] = score_map.get(r["weather"], 5)
        r["combined_score"] = round((r["weather_score"] + r["safety_score"]) / 2, 1)
    records.sort(key=lambda x: x["combined_score"], reverse=True)
    for i, r in enumerate(records, 1):
        r["rank"] = i
    print(f"  [transform] scored + ranked")
    return {"transformed": records}


def load_node(state: PipelineState) -> PipelineState:
    r = llm.invoke([
        SystemMessage(content="Format structured data into a markdown travel ranking report."),
        HumanMessage(content=f"Data: {json.dumps(state['transformed'], indent=2)}"),
    ])
    print("  [load] report formatted")
    return {"final_report": r.content}


def build_pipeline():
    builder = StateGraph(PipelineState)
    builder.add_node("extract", extract_node)
    builder.add_node("transform", transform_node)
    builder.add_node("load", load_node)
    builder.add_edge(START, "extract")
    builder.add_edge("extract", "transform")
    builder.add_edge("transform", "load")
    builder.add_edge("load", END)
    return builder.compile()


if __name__ == "__main__":
    graph = build_pipeline()
    result = graph.invoke({"raw_records": RAW_DATA, "extracted": None, "transformed": None, "final_report": None})
    print("\n" + "="*60)
    print(result["final_report"])
