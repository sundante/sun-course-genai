"""
Sequential Architecture — Google ADK
Pattern: Research → Summarize → Format report (A → B → C pipeline)

ADK implements sequential pipelines via agent instruction with explicit numbered steps.
The single agent follows a deterministic sequence without branching.
"""
import asyncio
import os
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

load_dotenv()
assert os.getenv("GOOGLE_API_KEY"), "Set GOOGLE_API_KEY in .env"


# ── Mock tools ────────────────────────────────────────────────────────────────

def fetch_city_data(city: str) -> dict:
    """Fetch raw travel data for a city.
    Args:
        city: City name.
    Returns:
        Dict with weather, safety, time, and highlights.
    """
    data = {
        "tokyo":     {"weather": "Clear, 18°C", "safety": "Low", "time": "22:30 JST", "highlights": "Shibuya, Senso-ji"},
        "paris":     {"weather": "Partly Cloudy, 16°C", "safety": "Low", "time": "15:30 CET", "highlights": "Eiffel Tower, Louvre"},
        "bangalore": {"weather": "Rainy, 25°C", "safety": "Medium", "time": "20:00 IST", "highlights": "Lalbagh, Nandi Hills"},
    }
    key = city.lower()
    return {"city": city, **data[key]} if key in data else {"error": f"No data for '{city}'."}


def write_summary(city: str, facts: str) -> dict:
    """Store intermediate summary for a city (acts as a passthrough/logger).
    Args:
        city: City name.
        facts: Structured facts string.
    Returns:
        Acknowledgment dict.
    """
    return {"status": "ok", "city": city, "note": "Summary will be written by the LLM in the next step."}


# ── Sequential agent ──────────────────────────────────────────────────────────

agent = Agent(
    name="sequential_travel_reporter",
    model="gemini-2.0-flash",
    description="Produces a formatted travel report via a strict Research → Summarize → Format pipeline.",
    instruction="""You are a travel report generator. For any city comparison request, follow these steps EXACTLY:

STEP 1 — RESEARCH: Call fetch_city_data() for EACH city. Never skip a city.

STEP 2 — SUMMARIZE: For each city, write a concise 2-sentence summary using the fetched data.
  Format: "City summary: [2 sentences covering weather, safety, key attraction]"

STEP 3 — FORMAT: Compile all summaries into a polished travel report:
  - Use '## Travel Report' as the top header
  - Use '### [City Name]' as each city's section header
  - Include weather, safety level, local time, and top attraction for each city
  - End with a '## Recommendation' section naming the best city for a safe, pleasant trip

Complete all 3 steps before responding. Never skip ahead to formatting before research is done.""",
    tools=[fetch_city_data, write_summary],
)


# ── Runner ────────────────────────────────────────────────────────────────────

async def run_sequential(cities: list[str]) -> str:
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name="sequential_travel_reporter", user_id="user_01"
    )
    runner = InMemoryRunner(agent=agent, session_service=session_service)
    query = f"Create a travel report comparing: {', '.join(cities)}."

    print(f"Query: {query}\n")
    print("--- Pipeline trace ---")

    final_response = ""
    async for event in runner.run_async(
        user_id=session.user_id,
        session_id=session.id,
        new_message=genai_types.Content(
            role="user", parts=[genai_types.Part(text=query)]
        ),
    ):
        if hasattr(event, "tool_call") and event.tool_call:
            print(f"  [step] {event.tool_call.name}({str(event.tool_call.args)[:50]})")
        elif event.is_final_response() and event.content:
            for part in event.content.parts:
                if part.text:
                    final_response += part.text

    return final_response


if __name__ == "__main__":
    cities = ["Tokyo", "Paris", "Bangalore"]
    report = asyncio.run(run_sequential(cities))
    print("\n--- Final Report ---")
    print(report)
