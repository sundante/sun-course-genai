"""
ADK Intermediate Agent
======================
Framework : Google Agent Development Kit (ADK)
Level     : 02 — Intermediate
Model     : gemini-2.0-flash

New concepts vs Simple:
  - 3 tools (added get_travel_advisory)
  - Multi-turn conversation: same session persists across calls
  - Structured output via output_schema (Pydantic model)

Domain: travel assistant that builds a full city briefing over a conversation.
"""

import asyncio
import os
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

load_dotenv()

# ── Structured Output Schema ─────────────────────────────────────────────────

class TravelBriefing(BaseModel):
    city: str = Field(description="Name of the city")
    weather_summary: str = Field(description="Weather conditions and temperature")
    local_time: str = Field(description="Current local time with timezone")
    travel_advisory: str = Field(description="Safety and travel advisory level")
    recommendation: str = Field(description="One-sentence travel recommendation")

# ── Mock Tools ────────────────────────────────────────────────────────────────

def get_weather(city: str) -> dict:
    """Return mock weather data for a city.

    Args:
        city: The city name.
    Returns:
        Weather condition and temperature.
    """
    data = {
        "london":    {"condition": "Cloudy", "temp_c": 12, "humidity": 78},
        "new york":  {"condition": "Sunny",  "temp_c": 22, "humidity": 45},
        "bangalore": {"condition": "Rainy",  "temp_c": 25, "humidity": 85},
        "tokyo":     {"condition": "Clear",  "temp_c": 18, "humidity": 60},
        "paris":     {"condition": "Partly Cloudy", "temp_c": 16, "humidity": 65},
    }
    key = city.lower()
    if key in data:
        d = data[key]
        return {"city": city, "condition": d["condition"],
                "temperature_celsius": d["temp_c"], "humidity_percent": d["humidity"]}
    return {"error": f"No data for '{city}'."}


def get_time(city: str) -> dict:
    """Return the current local time for a city.

    Args:
        city: The city name.
    Returns:
        Local time string with timezone.
    """
    times = {
        "london":    "14:30 GMT", "new york": "09:30 EST",
        "bangalore": "20:00 IST", "tokyo":    "22:30 JST",
        "paris":     "15:30 CET",
    }
    key = city.lower()
    if key in times:
        return {"city": city, "local_time": times[key]}
    return {"error": f"No time data for '{city}'."}


def get_travel_advisory(city: str) -> dict:
    """Return a travel safety advisory for a city.

    Args:
        city: The city name.
    Returns:
        Advisory level and key notes for travelers.
    """
    advisories = {
        "london":    {"level": "Low",    "notes": "Routine precautions. Pickpocketing in tourist areas."},
        "new york":  {"level": "Low",    "notes": "Normal safety precautions. Avoid isolated areas at night."},
        "bangalore": {"level": "Medium", "notes": "Monsoon season affects transport. Air quality can vary."},
        "tokyo":     {"level": "Low",    "notes": "Very safe city. Earthquake preparedness recommended."},
        "paris":     {"level": "Low",    "notes": "Routine precautions. Be alert in crowded tourist spots."},
    }
    key = city.lower()
    if key in advisories:
        a = advisories[key]
        return {"city": city, "advisory_level": a["level"], "notes": a["notes"]}
    return {"error": f"No advisory data for '{city}'."}


# ── Agent ─────────────────────────────────────────────────────────────────────

agent = Agent(
    name="travel_briefing_assistant",
    model="gemini-2.0-flash",
    description="Creates comprehensive travel briefings by checking weather, time, and safety advisories.",
    instruction="""You are a professional travel intelligence assistant.
When asked about a city, always check weather, local time, AND travel advisory before responding.
Build a complete picture using all three tools, then synthesize into a structured briefing.
Remember context from earlier in the conversation — if the user mentioned a preference, use it.""",
    tools=[get_weather, get_time, get_travel_advisory],
    output_schema=TravelBriefing,  # forces final response into this Pydantic schema
)


# ── Runner with persistent session ───────────────────────────────────────────

session_service = InMemorySessionService()

async def create_session():
    return await session_service.create_session(app_name="travel_app", user_id="user_01")


async def run(query: str, session_id: str) -> str:
    runner = InMemoryRunner(agent=agent, session_service=session_service)
    response_text = ""
    async for event in runner.run_async(
        user_id="user_01",
        session_id=session_id,
        new_message=genai_types.Content(
            role="user", parts=[genai_types.Part(text=query)]
        ),
    ):
        if event.is_final_response() and event.content:
            for part in event.content.parts:
                if part.text:
                    response_text += part.text
    return response_text


async def main():
    # Same session = agent remembers the conversation
    session = await create_session()
    sid = session.id

    print("=== Multi-turn conversation with persistent session ===\n")

    turns = [
        "Give me a full travel briefing for Tokyo.",
        "Now do the same for Bangalore. I prefer warm weather — which would you recommend?",
        "Based on what you told me, what's the safer city to visit?",
    ]

    for query in turns:
        print(f"User: {query}")
        response = await run(query, sid)
        print(f"Agent: {response}\n{'-'*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
