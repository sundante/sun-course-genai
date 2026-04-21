"""
CrewAI Simple Agent
===================
Framework : CrewAI
Level     : 01 — Simple
Model     : gemini-2.0-flash via CrewAI's LLM integration

What this demonstrates:
  - Defining tools with @tool decorator (from crewai.tools)
  - Creating an Agent with role, goal, and backstory (role-playing model)
  - Wrapping a task in a Task object with description + expected_output
  - Running a single-agent Crew with Process.sequential

Mock tools used (no credentials needed):
  - get_weather(city)  → fake weather report
  - get_time(city)     → fake local time
"""

import os
from dotenv import load_dotenv

from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool

load_dotenv()

# ── Mock Tools ──────────────────────────────────────────────────────────────

@tool("Weather Tool")
def get_weather(city: str) -> str:
    """Get the current weather conditions for a given city.
    Returns temperature, weather condition, and humidity.
    Input: city name (string).
    """
    mock_data = {
        "london":    ("Cloudy", 12, 78),
        "new york":  ("Sunny",  22, 45),
        "bangalore": ("Rainy",  25, 85),
        "tokyo":     ("Clear",  18, 60),
    }
    key = city.lower()
    if key in mock_data:
        condition, temp, humidity = mock_data[key]
        return (f"{city}: {condition}, {temp}°C, humidity {humidity}%. "
                f"{'Bring an umbrella!' if condition == 'Rainy' else 'Enjoy the weather!'}")
    return f"No weather data for '{city}'. Available: London, New York, Bangalore, Tokyo."


@tool("Time Tool")
def get_time(city: str) -> str:
    """Get the current local time for a given city.
    Input: city name (string).
    """
    mock_times = {
        "london":    "14:30 GMT",
        "new york":  "09:30 EST",
        "bangalore": "20:00 IST",
        "tokyo":     "22:30 JST",
    }
    key = city.lower()
    if key in mock_times:
        return f"Current time in {city}: {mock_times[key]}"
    return f"No time data for '{city}'. Available: London, New York, Bangalore, Tokyo."


# ── LLM Configuration ───────────────────────────────────────────────────────

gemini = LLM(model="gemini/gemini-2.0-flash", temperature=0)

# ── Agent Definition ─────────────────────────────────────────────────────────
# CrewAI uses role-playing: the agent has a persona (role + goal + backstory)
# The LLM is guided by this persona when deciding how to respond and use tools.

weather_agent = Agent(
    role="Travel Weather Assistant",
    goal="Provide accurate, friendly weather and time information for any city the traveler asks about.",
    backstory=(
        "You are an experienced travel concierge who helps travelers plan their trips "
        "by providing up-to-date local weather conditions and time zone information. "
        "You always use your tools to get the latest data before answering."
    ),
    tools=[get_weather, get_time],
    llm=gemini,
    verbose=True,
)

# ── Task Definition ──────────────────────────────────────────────────────────
# A Task defines WHAT the agent should accomplish and WHAT good output looks like.

def create_task(query: str) -> Task:
    return Task(
        description=f"Answer the following user question about weather or time: {query}",
        expected_output=(
            "A concise, friendly response that directly answers the user's question. "
            "Include specific numbers (temperature, humidity) where available. "
            "Keep it to 2–3 sentences."
        ),
        agent=weather_agent,
    )


# ── Crew + Run ───────────────────────────────────────────────────────────────

def run(query: str) -> str:
    task = create_task(query)
    crew = Crew(
        agents=[weather_agent],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
    )
    result = crew.kickoff()
    return str(result)


if __name__ == "__main__":
    queries = [
        "What's the weather like in Bangalore right now?",
        "What time is it in Tokyo, and is it a good day to go outside?",
    ]
    for q in queries:
        print(f"\nUser: {q}")
        print(f"Agent: {run(q)}")
