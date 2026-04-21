"""
Parallel Architecture — CrewAI
Pattern: Fan-out (3 city researchers) → Aggregate (ranker)

CrewAI achieves parallelism with Process.sequential where research tasks
have NO context dependencies on each other — they can run independently.
The aggregator task has context=[all_research_tasks].

Note: CrewAI also supports Process.parallel (experimental) for true concurrency.
Here we use the more stable approach: independent tasks that an orchestrator aggregates.
"""
import os
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool

load_dotenv()
assert os.getenv("GOOGLE_API_KEY"), "Set GOOGLE_API_KEY in .env"

gemini = LLM(model="gemini/gemini-2.0-flash", temperature=0)


# ── Mock tools ────────────────────────────────────────────────────────────────

@tool("City Researcher")
def research_city(city: str) -> str:
    """Research weather, safety, and time for a city. Input: city name."""
    data = {
        "tokyo":     "Weather: Clear 18°C (9/10). Safety: Low (10/10). Time: 22:30 JST.",
        "paris":     "Weather: Partly Cloudy 16°C (7/10). Safety: Low (8/10). Time: 15:30 CET.",
        "bangalore": "Weather: Rainy 25°C (6/10). Safety: Medium (6/10). Time: 20:00 IST.",
    }
    return data.get(city.lower(), f"No data for '{city}'.")


# ── Output schema ─────────────────────────────────────────────────────────────

class CityRank(BaseModel):
    city: str
    rank: int = Field(ge=1, le=10)
    reason: str

class RankedReport(BaseModel):
    rankings: List[CityRank] = Field(description="Cities ranked best to worst")
    top_pick: str
    top_pick_reason: str


# ── Agents ────────────────────────────────────────────────────────────────────

# Three identical researcher agents — one per city (true role separation)
researcher_tokyo = Agent(
    role="Tokyo Researcher", goal="Research Tokyo travel data.",
    backstory="You specialize in Japan travel intelligence.",
    tools=[research_city], llm=gemini, verbose=False,
)
researcher_paris = Agent(
    role="Paris Researcher", goal="Research Paris travel data.",
    backstory="You specialize in European travel intelligence.",
    tools=[research_city], llm=gemini, verbose=False,
)
researcher_bangalore = Agent(
    role="Bangalore Researcher", goal="Research Bangalore travel data.",
    backstory="You specialize in South Asian travel intelligence.",
    tools=[research_city], llm=gemini, verbose=False,
)
aggregator = Agent(
    role="Travel Report Aggregator",
    goal="Rank all researched cities by weather and safety scores.",
    backstory="You synthesize multi-city travel research into clear, ranked reports.",
    tools=[], llm=gemini, verbose=False,
)


# ── Crew builder ──────────────────────────────────────────────────────────────

def build_crew() -> Crew:
    # Independent research tasks — no context dependency = parallel-capable
    task_tokyo = Task(
        description="Research Tokyo: call research_city('Tokyo') and report weather, safety, time.",
        expected_output="Structured Tokyo travel data with scores.",
        agent=researcher_tokyo,
    )
    task_paris = Task(
        description="Research Paris: call research_city('Paris') and report weather, safety, time.",
        expected_output="Structured Paris travel data with scores.",
        agent=researcher_paris,
    )
    task_bangalore = Task(
        description="Research Bangalore: call research_city('Bangalore') and report weather, safety, time.",
        expected_output="Structured Bangalore travel data with scores.",
        agent=researcher_bangalore,
    )
    # Aggregator sees all three research results
    aggregate_task = Task(
        description="Using research from all 3 cities, rank Tokyo, Paris, Bangalore by weather + safety. Fill RankedReport.",
        expected_output="A RankedReport with all cities ranked.",
        agent=aggregator,
        context=[task_tokyo, task_paris, task_bangalore],
        output_pydantic=RankedReport,
    )
    return Crew(
        agents=[researcher_tokyo, researcher_paris, researcher_bangalore, aggregator],
        tasks=[task_tokyo, task_paris, task_bangalore, aggregate_task],
        process=Process.sequential,
        verbose=False,
    )


if __name__ == "__main__":
    print("Running parallel city research...")
    crew = build_crew()
    result = crew.kickoff()
    report: RankedReport = result.pydantic

    if report:
        print("\n" + "="*50)
        print("RANKED REPORT")
        print("="*50)
        for r in report.rankings:
            print(f"  {r.rank}. {r.city} — {r.reason}")
        print(f"\nTop Pick: {report.top_pick}")
        print(f"Why: {report.top_pick_reason}")
    else:
        print(result.raw)
