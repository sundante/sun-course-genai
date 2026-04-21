"""
Pipeline Architecture — CrewAI
Pattern: ETL pipeline as sequential tasks with data transformation roles

CrewAI models pipeline stages as agents with data transformation goals.
The key difference: agents are transforms, not decision-makers.
"""
import os
import json
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool

load_dotenv()
assert os.getenv("GOOGLE_API_KEY"), "Set GOOGLE_API_KEY in .env"

gemini = LLM(model="gemini/gemini-2.0-flash", temperature=0)

RAW_DATA = [
    "Tokyo|Clear|18|Low|10|22:30 JST",
    "Paris|Partly Cloudy|16|Low|8|15:30 CET",
    "Bangalore|Rainy|25|Medium|6|20:00 IST",
]


@tool("Raw Data Parser")
def parse_raw_data(raw_records: str) -> str:
    """Parse pipe-delimited city records into JSON. Input: newline-separated records."""
    records = []
    for line in raw_records.strip().split("\n"):
        parts = line.split("|")
        if len(parts) == 6:
            city, weather, temp, safety_level, safety_score, time = parts
            records.append({"city": city, "weather": weather, "temp_c": int(temp),
                           "safety_level": safety_level, "safety_score": int(safety_score), "local_time": time})
    return json.dumps(records, indent=2)


@tool("Score Calculator")
def calculate_scores(json_records: str) -> str:
    """Add weather_score, combined_score, and rank to records. Input: JSON string."""
    records = json.loads(json_records)
    score_map = {"Clear": 9, "Partly Cloudy": 7, "Rainy": 6, "Cloudy": 5}
    for r in records:
        r["weather_score"] = score_map.get(r["weather"], 5)
        r["combined_score"] = round((r["weather_score"] + r["safety_score"]) / 2, 1)
    records.sort(key=lambda x: x["combined_score"], reverse=True)
    for i, r in enumerate(records, 1):
        r["rank"] = i
    return json.dumps(records, indent=2)


class TravelRankingReport(BaseModel):
    rankings: List[dict] = Field(description="Ranked city records with all scores")
    summary: str = Field(description="One paragraph narrative summary of the rankings")
    top_city: str


extractor = Agent(role="Data Extractor", goal="Parse raw city records into structured JSON.",
    backstory="You transform raw pipe-delimited data into clean structured records.",
    tools=[parse_raw_data], llm=gemini, verbose=False)

transformer = Agent(role="Data Transformer", goal="Enrich records with weather scores, combined scores, and rankings.",
    backstory="You add computed fields and sort records by combined score.",
    tools=[calculate_scores], llm=gemini, verbose=False)

loader = Agent(role="Report Generator", goal="Format enriched data into a readable ranking report.",
    backstory="You turn structured data into clear, actionable travel reports.",
    tools=[], llm=gemini, verbose=False)


def build_crew(raw_records: list) -> Crew:
    raw_str = "\n".join(raw_records)
    t1 = Task(description=f"Parse these raw records using parse_raw_data:\n{raw_str}",
        expected_output="JSON array of structured city records.", agent=extractor)
    t2 = Task(description="Add weather_score, combined_score, and rank to the extracted records using calculate_scores.",
        expected_output="JSON array with enriched records, sorted by combined_score.", agent=transformer, context=[t1])
    t3 = Task(description="Format the enriched data into a TravelRankingReport with rankings, summary, and top_city.",
        expected_output="A complete TravelRankingReport.", agent=loader, context=[t2],
        output_pydantic=TravelRankingReport)
    return Crew(agents=[extractor, transformer, loader], tasks=[t1, t2, t3], process=Process.sequential, verbose=False)


if __name__ == "__main__":
    result = build_crew(RAW_DATA).kickoff()
    report: TravelRankingReport = result.pydantic
    if report:
        print("\nRankings:")
        for r in report.rankings:
            print(f"  {r.get('rank')}. {r.get('city')} — score {r.get('combined_score')}")
        print(f"\nTop City: {report.top_city}")
        print(f"Summary: {report.summary}")
    else:
        print(result.raw)
