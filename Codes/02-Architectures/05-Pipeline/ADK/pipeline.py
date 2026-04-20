"""
Pipeline Architecture — Google ADK
Pattern: ETL pipeline via tool-based steps

ADK models pipeline stages as tools with explicit step instructions.
The agent calls each tool in sequence, accumulating transformed data.
"""
import asyncio
import os
import json
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

load_dotenv()
assert os.getenv("GOOGLE_API_KEY"), "Set GOOGLE_API_KEY in .env"


def extract_records(raw_data: str) -> dict:
    """Parse pipe-delimited city records into structured data.
    Args:
        raw_data: Newline-separated pipe-delimited records.
    Returns:
        Dict with parsed records list.
    """
    records = []
    for line in raw_data.strip().split("\n"):
        parts = line.split("|")
        if len(parts) == 6:
            city, weather, temp, safety_level, safety_score, time = parts
            records.append({"city": city, "weather": weather, "temp_c": int(temp),
                           "safety_level": safety_level, "safety_score": int(safety_score), "local_time": time})
    return {"status": "ok", "records": records, "count": len(records)}


def enrich_and_rank(json_records: str) -> dict:
    """Add weather_score, combined_score, and rank to records.
    Args:
        json_records: JSON string of city records.
    Returns:
        Dict with enriched and ranked records.
    """
    records = json.loads(json_records)
    score_map = {"Clear": 9, "Partly Cloudy": 7, "Rainy": 6, "Cloudy": 5}
    for r in records:
        r["weather_score"] = score_map.get(r["weather"], 5)
        r["combined_score"] = round((r["weather_score"] + r["safety_score"]) / 2, 1)
    records.sort(key=lambda x: x["combined_score"], reverse=True)
    for i, r in enumerate(records, 1):
        r["rank"] = i
    return {"status": "ok", "enriched_records": records}


agent = Agent(
    name="etl_pipeline",
    model="gemini-2.0-flash",
    description="Runs an ETL pipeline on travel data: extract, transform, then format a report.",
    instruction="""You are an ETL pipeline agent. Follow these steps:

STEP 1 — EXTRACT: Call extract_records() with the raw data string.
STEP 2 — TRANSFORM: Call enrich_and_rank() with the JSON of extracted records.
STEP 3 — LOAD (format): Using the enriched records, write a markdown report:
  ## Travel Data Pipeline Report
  ### Rankings (sorted by combined score)
  | Rank | City | Weather Score | Safety Score | Combined |
  |---|---|---|---|---|
  | 1 | ... |
  ### Top Pick: [city with highest combined score]

Execute all 3 steps sequentially.""",
    tools=[extract_records, enrich_and_rank],
)


async def run_pipeline(raw_data: list[str]) -> str:
    session_service = InMemorySessionService()
    session = await session_service.create_session(app_name="etl_pipeline", user_id="u1")
    runner = InMemoryRunner(agent=agent, session_service=session_service)
    raw_str = "\n".join(raw_data)
    query = f"Run the ETL pipeline on this data:\n{raw_str}"

    final = ""
    async for event in runner.run_async(
        user_id=session.user_id, session_id=session.id,
        new_message=genai_types.Content(role="user", parts=[genai_types.Part(text=query)]),
    ):
        if hasattr(event, "tool_call") and event.tool_call:
            print(f"  [step] {event.tool_call.name}")
        elif event.is_final_response() and event.content:
            for part in event.content.parts:
                if part.text: final += part.text
    return final


if __name__ == "__main__":
    RAW = ["Tokyo|Clear|18|Low|10|22:30 JST", "Paris|Partly Cloudy|16|Low|8|15:30 CET", "Bangalore|Rainy|25|Medium|6|20:00 IST"]
    report = asyncio.run(run_pipeline(RAW))
    print("\n--- Pipeline Report ---")
    print(report)
