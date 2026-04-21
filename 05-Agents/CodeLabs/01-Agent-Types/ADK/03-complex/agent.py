"""
ADK Complex Agent
=================
Framework : Google Agent Development Kit (ADK)
Level     : 03 — Complex
Model     : gemini-2.0-flash

New concepts vs Intermediate:
  - Explicit planning step: agent writes a plan before acting
  - Reflexion loop: agent critiques its own output and rewrites if quality is low
  - Streaming intermediate events (tool calls, thoughts, partial text)
  - Multi-city goal decomposition

Domain: trip planner that produces a ranked city comparison report.
The agent must: plan → gather → critique → refine → deliver.
"""

import asyncio
import json
import os
from pydantic import BaseModel, Field
from typing import Optional
from dotenv import load_dotenv

from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

load_dotenv()

# ── Tools ─────────────────────────────────────────────────────────────────────

def get_weather(city: str) -> dict:
    """Get weather for a city.

    Args:
        city: City name.
    Returns:
        Weather dict with condition, temperature, humidity.
    """
    data = {
        "london":    {"condition": "Cloudy",        "temp_c": 12, "humidity": 78, "score": 5},
        "new york":  {"condition": "Sunny",          "temp_c": 22, "humidity": 45, "score": 8},
        "bangalore": {"condition": "Rainy",          "temp_c": 25, "humidity": 85, "score": 6},
        "tokyo":     {"condition": "Clear",          "temp_c": 18, "humidity": 60, "score": 9},
        "paris":     {"condition": "Partly Cloudy",  "temp_c": 16, "humidity": 65, "score": 7},
    }
    key = city.lower()
    if key in data:
        return {"city": city, **data[key]}
    return {"error": f"No data for '{city}'."}


def get_time(city: str) -> dict:
    """Get local time for a city.

    Args:
        city: City name.
    Returns:
        Dict with city and local_time.
    """
    times = {
        "london": "14:30 GMT", "new york": "09:30 EST",
        "bangalore": "20:00 IST", "tokyo": "22:30 JST", "paris": "15:30 CET",
    }
    key = city.lower()
    return {"city": city, "local_time": times.get(key, "Unknown")}


def get_travel_advisory(city: str) -> dict:
    """Get travel safety advisory for a city.

    Args:
        city: City name.
    Returns:
        Dict with advisory level, notes, and safety score.
    """
    advisories = {
        "london":    {"level": "Low",    "notes": "Routine precautions.",      "safety_score": 8},
        "new york":  {"level": "Low",    "notes": "Normal precautions.",       "safety_score": 7},
        "bangalore": {"level": "Medium", "notes": "Monsoon affects transport.", "safety_score": 6},
        "tokyo":     {"level": "Low",    "notes": "Very safe city.",            "safety_score": 10},
        "paris":     {"level": "Low",    "notes": "Alert in crowded spots.",    "safety_score": 8},
    }
    key = city.lower()
    if key in advisories:
        return {"city": city, **advisories[key]}
    return {"error": f"No advisory data for '{city}'."}


def score_report(report: str) -> dict:
    """Evaluate the quality of a travel comparison report.

    Use this tool to self-assess your report before delivering it.
    A good report scores >= 7. If score < 7, you must improve it.

    Args:
        report: The full text of your draft report.
    Returns:
        Dict with score (1-10) and specific improvement suggestions.
    """
    score = 0
    suggestions = []

    if "rank" in report.lower() or "1." in report or "recommended" in report.lower():
        score += 3
    else:
        suggestions.append("Add a clear ranking or recommendation.")

    if any(c in report.lower() for c in ["weather", "temperature", "°c"]):
        score += 2
    else:
        suggestions.append("Include specific weather data (temperature, conditions).")

    if any(c in report.lower() for c in ["advisory", "safety", "safe"]):
        score += 2
    else:
        suggestions.append("Include safety advisory information.")

    if len(report) > 300:
        score += 2
    else:
        suggestions.append("Report is too brief — add more detail.")

    if any(c in report.lower() for c in ["time", "gmt", "ist", "jst", "est", "cet"]):
        score += 1

    return {
        "score": min(score, 10),
        "threshold": 7,
        "pass": score >= 7,
        "suggestions": suggestions if suggestions else ["Report looks good!"],
    }


# ── Complex Agent ─────────────────────────────────────────────────────────────

agent = Agent(
    name="trip_planner",
    model="gemini-2.0-flash",
    description="A trip planner that produces ranked city comparison reports.",
    instruction="""You are an expert travel analyst. When given a list of cities to compare:

STEP 1 — PLAN: Before calling any tools, write a brief plan:
  "I will research [list cities], checking weather, time, and safety for each."

STEP 2 — GATHER: Call get_weather, get_time, and get_travel_advisory for EVERY city.

STEP 3 — DRAFT: Write a comparison report that ranks the cities for travel.
  Include: weather scores, safety scores, best time to visit.

STEP 4 — CRITIQUE: Call score_report() with your draft.
  If score < 7, revise the report addressing the suggestions.
  If score >= 7, deliver the final report.

Always complete all 4 steps. Never skip the critique.""",
    tools=[get_weather, get_time, get_travel_advisory, score_report],
)


# ── Streaming Runner ──────────────────────────────────────────────────────────

async def run_with_streaming(query: str) -> str:
    session_service = InMemorySessionService()
    session = await session_service.create_session(app_name="trip_planner", user_id="user_01")
    runner = InMemoryRunner(agent=agent, session_service=session_service)

    print(f"User: {query}\n")
    print("--- Agent trace (streaming) ---")

    final_response = ""
    async for event in runner.run_async(
        user_id=session.user_id,
        session_id=session.id,
        new_message=genai_types.Content(
            role="user", parts=[genai_types.Part(text=query)]
        ),
    ):
        # Stream intermediate events
        if hasattr(event, "tool_call") and event.tool_call:
            tc = event.tool_call
            print(f"  [Tool call] {tc.name}({tc.args})")
        elif hasattr(event, "tool_result") and event.tool_result:
            print(f"  [Tool result] {str(event.tool_result)[:80]}...")
        elif event.is_final_response() and event.content:
            for part in event.content.parts:
                if part.text:
                    final_response += part.text

    print("\n--- Final Report ---")
    return final_response


if __name__ == "__main__":
    query = "Compare Tokyo, Paris, and Bangalore for travel. Rank them and give a final recommendation."
    report = asyncio.run(run_with_streaming(query))
    print(report)
