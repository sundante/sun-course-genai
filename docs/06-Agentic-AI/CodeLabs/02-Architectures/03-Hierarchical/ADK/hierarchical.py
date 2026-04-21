"""
Hierarchical Architecture — Google ADK
Pattern: Root agent delegates to sub-agents

ADK supports multi-agent hierarchy via sub_agents= parameter.
The root (manager) agent can transfer control to specialized sub-agents.
Sub-agents report back to the manager who synthesizes the final output.
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
    """Get weather and score for a city.
    Args:
        city: City name.
    Returns:
        Dict with weather details and score.
    """
    data = {
        "tokyo":     {"condition": "Clear", "temp_c": 18, "score": 9},
        "paris":     {"condition": "Partly Cloudy", "temp_c": 16, "score": 7},
        "bangalore": {"condition": "Rainy", "temp_c": 25, "score": 6},
    }
    key = city.lower()
    return {"city": city, **data[key]} if key in data else {"error": f"No data for '{city}'."}


def get_safety(city: str) -> dict:
    """Get safety advisory and score for a city.
    Args:
        city: City name.
    Returns:
        Dict with advisory level, notes, and score.
    """
    data = {
        "tokyo":     {"level": "Low", "notes": "Very safe.", "score": 10},
        "paris":     {"level": "Low", "notes": "Alert in crowded spots.", "score": 8},
        "bangalore": {"level": "Medium", "notes": "Monsoon affects transport.", "score": 6},
    }
    key = city.lower()
    return {"city": city, **data[key]} if key in data else {"error": f"No data for '{city}'."}


# ── Sub-agents (specialists) ──────────────────────────────────────────────────

weather_agent = Agent(
    name="weather_specialist",
    model="gemini-2.0-flash",
    description="Researches weather conditions for cities. Use this for any weather-related queries.",
    instruction="""You are a weather specialist. When asked about weather:
1. Call get_weather() for each requested city.
2. Summarize: city name, condition, temperature, and weather score.
3. Return structured weather data to the manager.""",
    tools=[get_weather],
)

safety_agent = Agent(
    name="safety_specialist",
    model="gemini-2.0-flash",
    description="Researches travel safety advisories for cities. Use this for safety-related queries.",
    instruction="""You are a safety specialist. When asked about safety:
1. Call get_safety() for each requested city.
2. Summarize: city name, advisory level, key notes, and safety score.
3. Return structured safety data to the manager.""",
    tools=[get_safety],
)


# ── Root (manager) agent ──────────────────────────────────────────────────────

manager_agent = Agent(
    name="travel_manager",
    model="gemini-2.0-flash",
    description="Travel report manager that coordinates research and produces final reports.",
    instruction="""You are a travel project manager. When asked to compare cities:

STEP 1: Delegate weather research to weather_specialist for all cities.
STEP 2: Delegate safety research to safety_specialist for all cities.
STEP 3: Synthesize all results into a hierarchical travel report:
  - '## Travel Report' header
  - '### [City]' section per city with weather + safety
  - '## Executive Summary' with top city recommendation

You orchestrate — specialists do the data collection.""",
    sub_agents=[weather_agent, safety_agent],
)


# ── Runner ────────────────────────────────────────────────────────────────────

async def run_hierarchical(cities: list[str]) -> str:
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name="travel_manager", user_id="user_01"
    )
    runner = InMemoryRunner(agent=manager_agent, session_service=session_service)
    query = f"Compare these cities for travel: {', '.join(cities)}. Produce a full hierarchical report."

    print(f"Query: {query}\n")
    print("--- Hierarchical trace ---")

    final_response = ""
    async for event in runner.run_async(
        user_id=session.user_id,
        session_id=session.id,
        new_message=genai_types.Content(role="user", parts=[genai_types.Part(text=query)]),
    ):
        if hasattr(event, "tool_call") and event.tool_call:
            print(f"  [tool] {event.tool_call.name}({str(event.tool_call.args)[:50]})")
        elif event.is_final_response() and event.content:
            for part in event.content.parts:
                if part.text:
                    final_response += part.text

    return final_response


if __name__ == "__main__":
    cities = ["Tokyo", "Paris"]
    report = asyncio.run(run_hierarchical(cities))
    print("\n--- Final Report ---")
    print(report)
