"""
Parallel Architecture — Google ADK
Pattern: Fan-out (parallel tool calls) → Aggregate

ADK achieves parallelism via the LLM's native ability to call multiple tools
simultaneously in a single inference pass. The instruction tells the agent
to research ALL cities before aggregating.
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

def get_weather(city: str) -> dict:
    """Get weather data and score for a city.
    Args:
        city: City name.
    Returns:
        Dict with condition, temperature, and weather_score.
    """
    data = {
        "tokyo":     {"condition": "Clear", "temp_c": 18, "weather_score": 9},
        "paris":     {"condition": "Partly Cloudy", "temp_c": 16, "weather_score": 7},
        "bangalore": {"condition": "Rainy", "temp_c": 25, "weather_score": 6},
    }
    key = city.lower()
    return {"city": city, **data[key]} if key in data else {"error": f"No data for '{city}'."}


def get_safety(city: str) -> dict:
    """Get travel safety advisory and score for a city.
    Args:
        city: City name.
    Returns:
        Dict with level, notes, and safety_score.
    """
    data = {
        "tokyo":     {"level": "Low", "notes": "Very safe.", "safety_score": 10},
        "paris":     {"level": "Low", "notes": "Alert in crowded spots.", "safety_score": 8},
        "bangalore": {"level": "Medium", "notes": "Monsoon affects transport.", "safety_score": 6},
    }
    key = city.lower()
    return {"city": city, **data[key]} if key in data else {"error": f"No data for '{city}'."}


# ── Agent ─────────────────────────────────────────────────────────────────────

agent = Agent(
    name="parallel_travel_ranker",
    model="gemini-2.0-flash",
    description="Researches multiple cities in parallel and produces a ranked travel report.",
    instruction="""You are a travel analyst. When given a list of cities to compare:

PHASE 1 — PARALLEL RESEARCH: Call get_weather() AND get_safety() for ALL cities simultaneously.
  Do not wait for one city before starting another. Call all tools at once.

PHASE 2 — AGGREGATE & RANK: Using all collected data:
  - Rank cities best to worst by combined weather + safety score
  - Show scores for each city
  - Name the top pick with a clear reason

Format output as:
  ## Parallel Travel Report
  ### Rankings
  1. [City] — Weather: X/10, Safety: X/10, Total: X/20
  2. ...
  ## Top Pick: [City]
  [Reason]""",
    tools=[get_weather, get_safety],
)


# ── Runner ────────────────────────────────────────────────────────────────────

async def run_parallel(cities: list[str]) -> str:
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name="parallel_travel_ranker", user_id="user_01"
    )
    runner = InMemoryRunner(agent=agent, session_service=session_service)
    query = f"Research and rank these cities: {', '.join(cities)}."

    print(f"Query: {query}\n")
    print("--- Phase 1: Parallel tool calls ---")

    final_response = ""
    async for event in runner.run_async(
        user_id=session.user_id,
        session_id=session.id,
        new_message=genai_types.Content(role="user", parts=[genai_types.Part(text=query)]),
    ):
        if hasattr(event, "tool_call") and event.tool_call:
            print(f"  [tool] {event.tool_call.name}({str(event.tool_call.args)[:40]})")
        elif event.is_final_response() and event.content:
            for part in event.content.parts:
                if part.text:
                    final_response += part.text

    return final_response


if __name__ == "__main__":
    cities = ["Tokyo", "Paris", "Bangalore"]
    report = asyncio.run(run_parallel(cities))
    print("\n--- Phase 2: Aggregated Report ---")
    print(report)
