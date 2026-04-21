"""
CrewAI Intermediate Agent
==========================
Framework : CrewAI
Level     : 02 — Intermediate
Model     : gemini-2.0-flash

New concepts vs Simple:
  - Two agents working in sequence (Researcher + Formatter)
  - Task dependencies: Formatter's context = Researcher's output
  - Structured output via output_pydantic on the final task

Domain: travel assistant where one agent gathers data, another formats the briefing.
"""

import os
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool

load_dotenv()

# ── Structured Output Schema ──────────────────────────────────────────────────

class TravelBriefing(BaseModel):
    city: str = Field(description="Name of the city")
    weather_summary: str = Field(description="Weather conditions and temperature")
    local_time: str = Field(description="Current local time with timezone")
    travel_advisory: str = Field(description="Safety advisory level and key notes")
    recommendation: str = Field(description="One-sentence travel recommendation")

# ── Mock Tools ────────────────────────────────────────────────────────────────

@tool("Weather Tool")
def get_weather(city: str) -> str:
    """Get current weather for a city. Input: city name."""
    data = {
        "london":    ("Cloudy", 12, 78), "new york":  ("Sunny", 22, 45),
        "bangalore": ("Rainy",  25, 85), "tokyo":     ("Clear", 18, 60),
        "paris":     ("Partly Cloudy", 16, 65),
    }
    key = city.lower()
    if key in data:
        cond, temp, hum = data[key]
        return f"{city}: {cond}, {temp}°C, humidity {hum}%."
    return f"No data for '{city}'."


@tool("Time Tool")
def get_time(city: str) -> str:
    """Get current local time for a city. Input: city name."""
    times = {
        "london": "14:30 GMT", "new york": "09:30 EST",
        "bangalore": "20:00 IST", "tokyo": "22:30 JST", "paris": "15:30 CET",
    }
    key = city.lower()
    if key in times:
        return f"Current time in {city}: {times[key]}"
    return f"No time data for '{city}'."


@tool("Travel Advisory Tool")
def get_travel_advisory(city: str) -> str:
    """Get travel safety advisory for a city. Input: city name."""
    advisories = {
        "london":    ("Low",    "Routine precautions. Pickpocketing in tourist areas."),
        "new york":  ("Low",    "Normal precautions. Avoid isolated areas at night."),
        "bangalore": ("Medium", "Monsoon affects transport. Air quality can vary."),
        "tokyo":     ("Low",    "Very safe. Earthquake preparedness recommended."),
        "paris":     ("Low",    "Routine precautions. Alert in crowded spots."),
    }
    key = city.lower()
    if key in advisories:
        level, notes = advisories[key]
        return f"{city} Advisory: Level {level}. {notes}"
    return f"No advisory data for '{city}'."


# ── LLM ───────────────────────────────────────────────────────────────────────

gemini = LLM(model="gemini/gemini-2.0-flash", temperature=0)

# ── Two Agents ────────────────────────────────────────────────────────────────

researcher = Agent(
    role="Travel Intelligence Researcher",
    goal="Gather comprehensive, accurate travel data for a given city using all available tools.",
    backstory=(
        "You are a meticulous travel data analyst who always checks weather, local time, "
        "and safety advisories before compiling a city report. You never skip a data source."
    ),
    tools=[get_weather, get_time, get_travel_advisory],
    llm=gemini,
    verbose=False,
)

formatter = Agent(
    role="Travel Briefing Specialist",
    goal="Transform raw travel research data into a polished, actionable travel briefing.",
    backstory=(
        "You are a professional travel writer who takes raw data from research analysts "
        "and crafts clear, concise briefings that help travelers make informed decisions."
    ),
    tools=[],        # formatter doesn't need tools — it works with the researcher's output
    llm=gemini,
    verbose=False,
)

# ── Tasks with Dependency ─────────────────────────────────────────────────────

def build_crew(city: str) -> Crew:
    research_task = Task(
        description=f"Research the city '{city}'. Gather: current weather, local time, and travel advisory.",
        expected_output=(
            f"Raw data for {city}: weather conditions + temperature, "
            "local time with timezone, safety advisory level and key notes."
        ),
        agent=researcher,
    )

    format_task = Task(
        description=(
            f"Using the research data provided, create a structured travel briefing for {city}. "
            "Fill all fields of the TravelBriefing schema accurately."
        ),
        expected_output="A complete TravelBriefing with all fields populated.",
        agent=formatter,
        context=[research_task],          # formatter receives researcher's output as context
        output_pydantic=TravelBriefing,   # final output is parsed into TravelBriefing
    )

    return Crew(
        agents=[researcher, formatter],
        tasks=[research_task, format_task],
        process=Process.sequential,
        verbose=False,
    )


def run(city: str) -> TravelBriefing:
    crew = build_crew(city)
    result = crew.kickoff()
    return result.pydantic  # returns TravelBriefing instance


if __name__ == "__main__":
    for city in ["Tokyo", "Bangalore"]:
        print(f"\n{'='*50}")
        print(f"Briefing for {city}")
        print('='*50)
        briefing = run(city)
        if briefing:
            print(f"  Weather:    {briefing.weather_summary}")
            print(f"  Time:       {briefing.local_time}")
            print(f"  Advisory:   {briefing.travel_advisory}")
            print(f"  Rec:        {briefing.recommendation}")
        else:
            print("  (Structured output not available — check verbose output above)")
