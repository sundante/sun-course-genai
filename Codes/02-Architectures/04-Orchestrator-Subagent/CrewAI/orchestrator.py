"""
Orchestrator-Subagent Architecture — CrewAI
Pattern: Manager agent orchestrates specialist subagents via task delegation

The orchestrator agent holds no tools itself — it delegates every task to
specialist agents. Each specialist has focused tools and a narrow role.
"""
import os
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool

load_dotenv()
assert os.getenv("GOOGLE_API_KEY"), "Set GOOGLE_API_KEY in .env"

gemini = LLM(model="gemini/gemini-2.0-flash", temperature=0)


# ── Mock tools ────────────────────────────────────────────────────────────────

@tool("City Highlights Lookup")
def get_highlights(city: str) -> str:
    """Get top tourist highlights for a city. Input: city name."""
    data = {
        "tokyo":     "Shibuya crossing, Senso-ji temple, Tsukiji market, Mount Fuji day trip",
        "paris":     "Eiffel Tower, Louvre museum, Notre Dame, Seine river cruise",
        "bangalore": "Lalbagh Botanical Garden, Nandi Hills, Cubbon Park",
    }
    return data.get(city.lower(), f"No highlights for '{city}'.")


@tool("City Logistics Lookup")
def get_logistics(city: str) -> str:
    """Get travel logistics for a city: flights, local transport, best time. Input: city name."""
    data = {
        "tokyo":     "3h from SFO via Japan Airlines. Shinkansen + metro locally. Best: March-May.",
        "paris":     "11h from NYC via Air France. Metro/RER locally. Best: April-June.",
        "bangalore": "9h from Dubai via Emirates. Ola/Uber locally. Best: October-February.",
    }
    return data.get(city.lower(), f"No logistics for '{city}'.")


# ── Output schema ─────────────────────────────────────────────────────────────

class TripPackage(BaseModel):
    city: str
    highlights_summary: str = Field(description="Top 3 attractions with descriptions")
    logistics_summary: str = Field(description="Flight, local transport, best season")
    itinerary: str = Field(description="3-day itinerary")
    package_overview: str = Field(description="One-paragraph trip package overview")


# ── Specialist agents ─────────────────────────────────────────────────────────

highlights_specialist = Agent(
    role="City Highlights Researcher",
    goal="Find and describe the top tourist attractions for a city.",
    backstory="You are a travel guide expert with deep knowledge of city attractions.",
    tools=[get_highlights],
    llm=gemini, verbose=False,
)

logistics_specialist = Agent(
    role="Travel Logistics Planner",
    goal="Provide practical travel logistics: flights, local transport, best season.",
    backstory="You are a travel operations expert who makes journeys smooth and efficient.",
    tools=[get_logistics],
    llm=gemini, verbose=False,
)

itinerary_writer = Agent(
    role="Travel Itinerary Writer",
    goal="Create a compelling 3-day travel itinerary using research data.",
    backstory="You craft detailed, enjoyable day-by-day travel itineraries.",
    tools=[],
    llm=gemini, verbose=False,
)

package_formatter_agent = Agent(
    role="Trip Package Editor",
    goal="Assemble all research and planning into a polished trip package.",
    backstory="You produce beautifully formatted trip packages that travelers love.",
    tools=[],
    llm=gemini, verbose=False,
)


# ── Crew builder ──────────────────────────────────────────────────────────────

def build_crew(city: str) -> Crew:
    highlights_task = Task(
        description=f"Research top highlights for {city} using get_highlights tool.",
        expected_output=f"Top 3 attractions for {city} with descriptions.",
        agent=highlights_specialist,
    )
    logistics_task = Task(
        description=f"Research travel logistics for {city} using get_logistics tool.",
        expected_output=f"Practical travel info for {city}: flights, transport, season.",
        agent=logistics_specialist,
    )
    itinerary_task = Task(
        description=f"Create a 3-day itinerary for {city} using the highlights and logistics research.",
        expected_output=f"A 3-day itinerary for {city}.",
        agent=itinerary_writer,
        context=[highlights_task, logistics_task],
    )
    package_task = Task(
        description=f"Assemble a complete TripPackage for {city} using all research and itinerary.",
        expected_output=f"A complete TripPackage for {city}.",
        agent=package_formatter_agent,
        context=[highlights_task, logistics_task, itinerary_task],
        output_pydantic=TripPackage,
    )
    return Crew(
        agents=[highlights_specialist, logistics_specialist, itinerary_writer, package_formatter_agent],
        tasks=[highlights_task, logistics_task, itinerary_task, package_task],
        process=Process.sequential,
        verbose=False,
    )


if __name__ == "__main__":
    city = "Tokyo"
    print(f"Orchestrating trip package for: {city}")
    result = build_crew(city).kickoff()
    pkg: TripPackage = result.pydantic

    if pkg:
        print(f"\n## Trip Package: {pkg.city}")
        print(f"\n### Highlights\n{pkg.highlights_summary}")
        print(f"\n### Logistics\n{pkg.logistics_summary}")
        print(f"\n### 3-Day Itinerary\n{pkg.itinerary}")
        print(f"\n### Overview\n{pkg.package_overview}")
    else:
        print(result.raw)
