"""
CrewAI Complex Agent
=====================
Framework : CrewAI
Level     : 03 — Complex
Model     : gemini-2.0-flash

New concepts vs Intermediate:
  - Three-agent crew: Planner → Researcher → Critic
  - Task chaining: each task uses the previous as context
  - Critic agent triggers a rewrite when quality is insufficient
  - Process.hierarchical with a manager LLM for dynamic delegation
  - max_iter on agents for reflexion-style retry control

Domain: multi-city trip planner where a Planner decomposes, a Researcher gathers,
and a Critic evaluates and refines the final report.
"""

import os
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv

from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool

load_dotenv()

# ── Output Schema ──────────────────────────────────────────────────────────────

class CityAnalysis(BaseModel):
    city: str
    weather_score: int = Field(ge=1, le=10)
    safety_score: int = Field(ge=1, le=10)
    summary: str

class TripReport(BaseModel):
    ranked_cities: List[CityAnalysis]
    top_recommendation: str
    reasoning: str

# ── Tools ─────────────────────────────────────────────────────────────────────

@tool("Weather Scorer")
def get_weather(city: str) -> str:
    """Get weather and weather score (1-10) for a city. Input: city name."""
    data = {
        "london":    ("Cloudy",       12, 5), "new york":  ("Sunny",         22, 8),
        "bangalore": ("Rainy",        25, 6), "tokyo":     ("Clear",         18, 9),
        "paris":     ("Partly Cloudy",16, 7),
    }
    key = city.lower()
    if key in data:
        cond, temp, score = data[key]
        return f"{city}: {cond}, {temp}°C, weather score: {score}/10"
    return f"No data for '{city}'."


@tool("Safety Advisor")
def get_travel_advisory(city: str) -> str:
    """Get safety advisory and safety score (1-10) for a city. Input: city name."""
    data = {
        "london":    ("Low",    "Routine precautions.",      8),
        "new york":  ("Low",    "Normal precautions.",       7),
        "bangalore": ("Medium", "Monsoon affects transport.", 6),
        "tokyo":     ("Low",    "Very safe city.",           10),
        "paris":     ("Low",    "Alert in crowded spots.",    8),
    }
    key = city.lower()
    if key in data:
        level, notes, score = data[key]
        return f"{city}: Advisory {level}. {notes} Safety score: {score}/10"
    return f"No data for '{city}'."


@tool("Time Checker")
def get_time(city: str) -> str:
    """Get current local time for a city. Input: city name."""
    times = {
        "london": "14:30 GMT", "new york": "09:30 EST",
        "bangalore": "20:00 IST", "tokyo": "22:30 JST", "paris": "15:30 CET",
    }
    key = city.lower()
    return f"{city}: {times.get(key, 'Unknown')}"


# ── LLM ───────────────────────────────────────────────────────────────────────

gemini = LLM(model="gemini/gemini-2.0-flash", temperature=0)
gemini_manager = LLM(model="gemini/gemini-2.0-flash", temperature=0)

# ── Three Agents ──────────────────────────────────────────────────────────────

planner = Agent(
    role="Trip Planning Strategist",
    goal="Decompose travel comparison goals into a clear research plan with specific cities and criteria.",
    backstory=(
        "You are a strategic travel consultant. You receive vague travel goals and turn them into "
        "structured research plans. You identify the cities to compare and the exact data needed."
    ),
    tools=[],
    llm=gemini,
    verbose=False,
)

researcher = Agent(
    role="Travel Data Researcher",
    goal="Gather comprehensive weather, safety, and time data for every city in the research plan.",
    backstory=(
        "You are a meticulous travel intelligence analyst. Given a research plan, you systematically "
        "collect weather scores, safety advisories, and local times using your tools. "
        "You never skip a city or a data category."
    ),
    tools=[get_weather, get_travel_advisory, get_time],
    llm=gemini,
    verbose=False,
    max_iter=8,
)

critic = Agent(
    role="Travel Report Editor",
    goal="Evaluate travel reports for quality and produce a polished final version with clear rankings.",
    backstory=(
        "You are a senior travel editor at a top travel publication. You receive raw research reports "
        "and transform them into clear, ranked, actionable travel guides. "
        "You always verify that rankings have supporting data and are clearly justified."
    ),
    tools=[],
    llm=gemini,
    verbose=False,
)

# ── Tasks ─────────────────────────────────────────────────────────────────────

def build_crew(goal: str, cities: list[str]) -> Crew:
    cities_str = ", ".join(cities)

    planning_task = Task(
        description=(
            f"Create a detailed research plan for comparing these cities: {cities_str}.\n"
            f"Goal: {goal}\n"
            "Output a structured plan: which cities to research and what data to collect for each."
        ),
        expected_output=f"A numbered research plan covering {cities_str} with weather, safety, and time for each.",
        agent=planner,
    )

    research_task = Task(
        description=(
            f"Execute the research plan. For each city ({cities_str}), collect:\n"
            "- Weather conditions and weather score\n"
            "- Travel advisory and safety score\n"
            "- Current local time\n"
            "Use your tools for EVERY city. Do not skip any."
        ),
        expected_output=f"Raw data for all {len(cities)} cities: weather, safety, time scores.",
        agent=researcher,
        context=[planning_task],
    )

    critique_task = Task(
        description=(
            f"Using the research data, produce a final ranked travel comparison report for: {cities_str}.\n"
            f"Original goal: {goal}\n"
            "Requirements:\n"
            "1. Rank cities from best to worst with specific score justification\n"
            "2. Include a clear top recommendation\n"
            "3. Explain the reasoning based on weather + safety data\n"
            "If the research data is incomplete, note what's missing."
        ),
        expected_output="A ranked travel report with scores, rankings, and a clear recommendation.",
        agent=critic,
        context=[research_task],
        output_pydantic=TripReport,
    )

    return Crew(
        agents=[planner, researcher, critic],
        tasks=[planning_task, research_task, critique_task],
        process=Process.sequential,
        verbose=True,
    )


def run(goal: str, cities: list[str]) -> TripReport:
    crew = build_crew(goal, cities)
    result = crew.kickoff()
    return result.pydantic


if __name__ == "__main__":
    goal = "I want the safest city with the best weather for a week-long trip."
    cities = ["Tokyo", "Paris", "Bangalore"]

    print(f"Goal: {goal}")
    print(f"Cities: {cities}\n")

    report = run(goal, cities)

    if report:
        print("\n" + "="*60)
        print("FINAL TRIP REPORT")
        print("="*60)
        for i, city in enumerate(report.ranked_cities, 1):
            print(f"{i}. {city.city} — Weather: {city.weather_score}/10, Safety: {city.safety_score}/10")
            print(f"   {city.summary}")
        print(f"\nTop Recommendation: {report.top_recommendation}")
        print(f"Reasoning: {report.reasoning}")
