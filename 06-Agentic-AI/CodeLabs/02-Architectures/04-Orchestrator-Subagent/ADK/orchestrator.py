"""
Orchestrator-Subagent Architecture — Google ADK
Pattern: Orchestrator agent with specialist sub-agents

The orchestrator holds the plan; sub-agents are the executors.
Orchestrator transfers control to each specialist in turn, then synthesizes.
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

def get_highlights(city: str) -> dict:
    """Get top tourist highlights for a city.
    Args:
        city: City name.
    Returns:
        Dict with city and top highlights list.
    """
    data = {
        "tokyo":     ["Shibuya crossing", "Senso-ji temple", "Tsukiji market", "Mt Fuji day trip"],
        "paris":     ["Eiffel Tower", "Louvre museum", "Notre Dame", "Seine river cruise"],
        "bangalore": ["Lalbagh Botanical Garden", "Nandi Hills", "Cubbon Park"],
    }
    key = city.lower()
    return {"city": city, "highlights": data.get(key, [])} if key in data else {"error": f"No data for '{city}'."}


def get_logistics(city: str) -> dict:
    """Get travel logistics for a city.
    Args:
        city: City name.
    Returns:
        Dict with flights, local_transport, and best_season.
    """
    data = {
        "tokyo":     {"flights": "~3h from SFO via JAL", "local": "Shinkansen + metro", "season": "March-May"},
        "paris":     {"flights": "~11h from NYC via Air France", "local": "Metro/RER", "season": "April-June"},
        "bangalore": {"flights": "~9h from Dubai via Emirates", "local": "Ola/Uber", "season": "October-February"},
    }
    key = city.lower()
    return {"city": city, **data[key]} if key in data else {"error": f"No data for '{city}'."}


# ── Sub-agents ────────────────────────────────────────────────────────────────

highlights_agent = Agent(
    name="highlights_specialist",
    model="gemini-2.0-flash",
    description="Researches tourist highlights and attractions for cities. Use for 'what to see' queries.",
    instruction="Call get_highlights() for the requested city. Summarize top 3 attractions clearly.",
    tools=[get_highlights],
)

logistics_agent = Agent(
    name="logistics_specialist",
    model="gemini-2.0-flash",
    description="Researches travel logistics: flights, local transport, best season. Use for practical travel info.",
    instruction="Call get_logistics() for the requested city. Summarize flights, transport, and best season.",
    tools=[get_logistics],
)


# ── Orchestrator ──────────────────────────────────────────────────────────────

orchestrator = Agent(
    name="trip_orchestrator",
    model="gemini-2.0-flash",
    description="Orchestrates trip package creation by delegating to specialist agents.",
    instruction="""You are a trip package orchestrator. When asked to create a trip package for a city:

1. Delegate to highlights_specialist to get tourist attractions.
2. Delegate to logistics_specialist to get travel logistics.
3. Using both results, write a complete trip package:
   ## Trip Package: [City]
   ### Top Attractions
   [from highlights_specialist]
   ### Getting There & Around
   [from logistics_specialist]
   ### 3-Day Itinerary
   Day 1: [attractions + logistics]
   Day 2: [...]
   Day 3: [...]
   ### Quick Summary
   [one paragraph overview]""",
    sub_agents=[highlights_agent, logistics_agent],
)


# ── Runner ────────────────────────────────────────────────────────────────────

async def run_orchestrator(city: str) -> str:
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name="trip_orchestrator", user_id="user_01"
    )
    runner = InMemoryRunner(agent=orchestrator, session_service=session_service)
    query = f"Create a complete trip package for {city}."

    print(f"Query: {query}\n")
    final_response = ""
    async for event in runner.run_async(
        user_id=session.user_id, session_id=session.id,
        new_message=genai_types.Content(role="user", parts=[genai_types.Part(text=query)]),
    ):
        if hasattr(event, "tool_call") and event.tool_call:
            print(f"  [tool] {event.tool_call.name}({str(event.tool_call.args)[:40]})")
        elif event.is_final_response() and event.content:
            for part in event.content.parts:
                if part.text: final_response += part.text
    return final_response


if __name__ == "__main__":
    package = asyncio.run(run_orchestrator("Tokyo"))
    print("\n--- Trip Package ---")
    print(package)
