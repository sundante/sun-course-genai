"""
ADK Simple Agent
================
Framework : Google Agent Development Kit (ADK)
Level     : 01 — Simple
Model     : gemini-2.0-flash (via Gemini API key)

What this demonstrates:
  - Defining tools as Python functions decorated with type hints
  - Creating an ADK Agent with a system instruction and tools
  - Using InMemoryRunner to run the agent locally
  - The ReAct loop: model decides when and which tool to call

Mock tools used (no credentials needed):
  - get_weather(city)   → returns a fake weather report
  - get_time(city)      → returns a fake current time
"""

import asyncio
import os
from dotenv import load_dotenv

from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

load_dotenv()

# ── Mock Tools ──────────────────────────────────────────────────────────────

def get_weather(city: str) -> dict:
    """Return a mock weather report for the given city.

    Args:
        city: The name of the city to get weather for.

    Returns:
        A dictionary with weather details.
    """
    mock_data = {
        "london":    {"condition": "Cloudy", "temp_c": 12, "humidity": 78},
        "new york":  {"condition": "Sunny",  "temp_c": 22, "humidity": 45},
        "bangalore": {"condition": "Rainy",  "temp_c": 25, "humidity": 85},
        "tokyo":     {"condition": "Clear",  "temp_c": 18, "humidity": 60},
    }
    city_key = city.lower()
    if city_key in mock_data:
        data = mock_data[city_key]
        return {
            "city": city,
            "condition": data["condition"],
            "temperature_celsius": data["temp_c"],
            "humidity_percent": data["humidity"],
        }
    return {"error": f"No weather data for '{city}'. Try: London, New York, Bangalore, Tokyo."}


def get_time(city: str) -> dict:
    """Return a mock current local time for the given city.

    Args:
        city: The name of the city to get the time for.

    Returns:
        A dictionary with the local time string.
    """
    mock_times = {
        "london":    "14:30 GMT",
        "new york":  "09:30 EST",
        "bangalore": "20:00 IST",
        "tokyo":     "22:30 JST",
    }
    city_key = city.lower()
    if city_key in mock_times:
        return {"city": city, "local_time": mock_times[city_key]}
    return {"error": f"No time data for '{city}'. Try: London, New York, Bangalore, Tokyo."}


# ── Agent Definition ─────────────────────────────────────────────────────────

agent = Agent(
    name="weather_assistant",
    model="gemini-2.0-flash",
    description="A helpful assistant that answers weather and time questions.",
    instruction="""You are a helpful travel assistant.
When asked about weather or local time in a city, use the available tools.
Always be concise and friendly in your responses.""",
    tools=[get_weather, get_time],
)


# ── Runner ────────────────────────────────────────────────────────────────────

async def run(query: str) -> str:
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name="weather_app",
        user_id="user_01",
    )
    runner = InMemoryRunner(agent=agent, session_service=session_service)

    response_text = ""
    async for event in runner.run_async(
        user_id=session.user_id,
        session_id=session.id,
        new_message=genai_types.Content(
            role="user",
            parts=[genai_types.Part(text=query)],
        ),
    ):
        if event.is_final_response() and event.content:
            for part in event.content.parts:
                if part.text:
                    response_text += part.text
    return response_text


if __name__ == "__main__":
    queries = [
        "What's the weather like in Bangalore right now?",
        "What time is it in Tokyo, and is it a good day to go outside?",
    ]
    for q in queries:
        print(f"\nUser: {q}")
        answer = asyncio.run(run(q))
        print(f"Agent: {answer}")
