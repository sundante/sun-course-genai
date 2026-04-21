"""
Sequential Architecture — CrewAI
Pattern: Research → Summarize → Format report (A → B → C pipeline)

Three agents with distinct roles chained via Task context dependencies.
CrewAI's Process.sequential enforces the order; context= passes data forward.
"""
import os
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool

load_dotenv()
assert os.getenv("GOOGLE_API_KEY"), "Set GOOGLE_API_KEY in .env"

gemini = LLM(model="gemini/gemini-2.0-flash", temperature=0)


# ── Mock tool ────────────────────────────────────────────────────────────────

@tool("City Data Fetcher")
def fetch_city_data(city: str) -> str:
    """Fetch raw travel data for a city. Input: city name."""
    data = {
        "tokyo":     "Weather: Clear, 18°C. Safety: Low. Time: 22:30 JST. Highlights: Shibuya, Senso-ji.",
        "paris":     "Weather: Partly Cloudy, 16°C. Safety: Low. Time: 15:30 CET. Highlights: Eiffel Tower, Louvre.",
        "bangalore": "Weather: Rainy, 25°C. Safety: Medium. Time: 20:00 IST. Highlights: Lalbagh, Nandi Hills.",
    }
    return data.get(city.lower(), f"No data for '{city}'.")


# ── Output schema ─────────────────────────────────────────────────────────────

class TravelReport(BaseModel):
    city: str = Field(description="City name")
    report_section: str = Field(description="Full formatted report section with markdown header")
    summary: str = Field(description="One-sentence traveler summary")


# ── Agents ────────────────────────────────────────────────────────────────────

researcher = Agent(
    role="Travel Data Researcher",
    goal="Fetch and structure raw travel data for the given city.",
    backstory="You gather factual travel data — weather, safety, time, attractions — from data sources.",
    tools=[fetch_city_data],
    llm=gemini,
    verbose=False,
)

summarizer = Agent(
    role="Travel Summarizer",
    goal="Write a concise 2-sentence traveler summary from structured research data.",
    backstory="You distill dense travel data into clear, engaging 2-sentence summaries.",
    tools=[],
    llm=gemini,
    verbose=False,
)

formatter = Agent(
    role="Report Formatter",
    goal="Format the travel summary into a polished markdown report section.",
    backstory="You transform travel summaries into professional report sections with proper headers.",
    tools=[],
    llm=gemini,
    verbose=False,
)


# ── Pipeline builder ─────────────────────────────────────────────────────────

def build_crew(city: str) -> Crew:
    research_task = Task(
        description=f"Fetch and structure travel data for {city}: weather, safety, local time, top attractions.",
        expected_output=f"Structured travel facts for {city}.",
        agent=researcher,
    )

    summarize_task = Task(
        description=f"Write a concise 2-sentence traveler summary for {city} using the research data.",
        expected_output="A 2-sentence traveler summary.",
        agent=summarizer,
        context=[research_task],
    )

    format_task = Task(
        description=f"Format the summary for {city} into a markdown report section with '### {city}' header. Fill all TravelReport fields.",
        expected_output="A complete TravelReport with city, report_section, and summary.",
        agent=formatter,
        context=[summarize_task],
        output_pydantic=TravelReport,
    )

    return Crew(
        agents=[researcher, summarizer, formatter],
        tasks=[research_task, summarize_task, format_task],
        process=Process.sequential,
        verbose=False,
    )


if __name__ == "__main__":
    cities = ["Tokyo", "Paris", "Bangalore"]
    sections = []

    for city in cities:
        print(f"\nProcessing: {city}")
        crew = build_crew(city)
        result = crew.kickoff()
        report: TravelReport = result.pydantic
        if report:
            sections.append(report.report_section)
            print(f"  Summary: {report.summary}")
        else:
            sections.append(result.raw)

    print("\n" + "="*60)
    print("FINAL REPORT")
    print("="*60)
    print("# Travel Report\n")
    print("\n\n".join(sections))
