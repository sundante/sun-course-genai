"""
Hierarchical Architecture — CrewAI
Pattern: Process.hierarchical with manager_llm

CrewAI's Process.hierarchical gives a manager LLM full autonomy to:
- Plan how to use the agents and tasks
- Delegate tasks to appropriate agents
- Synthesize the final output

No explicit task chaining needed — the manager handles orchestration.
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

@tool("Weather Researcher")
def get_weather(city: str) -> str:
    """Get weather data for a city. Input: city name."""
    data = {
        "tokyo":     "Clear, 18°C, weather score 9/10",
        "paris":     "Partly Cloudy, 16°C, weather score 7/10",
        "bangalore": "Rainy, 25°C, weather score 6/10",
    }
    return data.get(city.lower(), f"No weather data for '{city}'.")


@tool("Safety Researcher")
def get_safety(city: str) -> str:
    """Get travel safety advisory for a city. Input: city name."""
    data = {
        "tokyo":     "Low advisory, safety score 10/10. Very safe.",
        "paris":     "Low advisory, safety score 8/10. Alert in crowded spots.",
        "bangalore": "Medium advisory, safety score 6/10. Monsoon affects transport.",
    }
    return data.get(city.lower(), f"No safety data for '{city}'.")


# ── Output schema ─────────────────────────────────────────────────────────────

class CitySection(BaseModel):
    city: str
    weather_summary: str
    safety_summary: str
    recommendation: str

class HierarchicalReport(BaseModel):
    city_sections: List[CitySection]
    executive_summary: str = Field(description="Overall recommendation across all cities")
    top_city: str


# ── Agents (workers — manager LLM delegates to these) ────────────────────────

weather_researcher = Agent(
    role="Weather Intelligence Specialist",
    goal="Collect accurate weather data and scores for any city.",
    backstory="You are a meteorology expert who translates weather data into traveler-friendly reports.",
    tools=[get_weather],
    llm=gemini,
    verbose=False,
)

safety_researcher = Agent(
    role="Travel Safety Analyst",
    goal="Collect accurate safety advisories and risk scores for any city.",
    backstory="You are a security analyst specializing in travel safety assessment.",
    tools=[get_safety],
    llm=gemini,
    verbose=False,
)

report_writer = Agent(
    role="Travel Report Editor",
    goal="Synthesize research into a polished, structured travel report.",
    backstory="You are a senior travel editor who turns raw research into actionable reports.",
    tools=[],
    llm=gemini,
    verbose=False,
)


# ── Tasks ─────────────────────────────────────────────────────────────────────

def build_crew(cities: list) -> Crew:
    cities_str = ", ".join(cities)

    weather_task = Task(
        description=f"Research weather conditions for each of these cities: {cities_str}. Use get_weather for each city.",
        expected_output=f"Weather data with scores for all {len(cities)} cities.",
        agent=weather_researcher,
    )

    safety_task = Task(
        description=f"Research safety advisories for each of these cities: {cities_str}. Use get_safety for each city.",
        expected_output=f"Safety advisory data with scores for all {len(cities)} cities.",
        agent=safety_researcher,
    )

    report_task = Task(
        description=(
            f"Using weather and safety research for {cities_str}, create a HierarchicalReport. "
            "Include a section per city and an executive summary with a top city recommendation."
        ),
        expected_output="A complete HierarchicalReport with city sections and executive summary.",
        agent=report_writer,
        context=[weather_task, safety_task],
        output_pydantic=HierarchicalReport,
    )

    return Crew(
        agents=[weather_researcher, safety_researcher, report_writer],
        tasks=[weather_task, safety_task, report_task],
        process=Process.hierarchical,
        manager_llm=gemini,
        verbose=False,
    )


if __name__ == "__main__":
    cities = ["Tokyo", "Paris"]
    print(f"Running hierarchical crew for: {cities}")
    crew = build_crew(cities)
    result = crew.kickoff()

    report: HierarchicalReport = result.pydantic
    if report:
        print("\n" + "="*50)
        print("HIERARCHICAL TRAVEL REPORT")
        print("="*50)
        for section in report.city_sections:
            print(f"\n### {section.city}")
            print(f"  Weather: {section.weather_summary}")
            print(f"  Safety:  {section.safety_summary}")
            print(f"  Rec:     {section.recommendation}")
        print(f"\n## Executive Summary")
        print(report.executive_summary)
        print(f"\nTop City: {report.top_city}")
    else:
        print(result.raw)
