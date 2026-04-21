"""
Reflexion Architecture — Google ADK
Pattern: score_report tool triggers self-critique loop

This is the architectural pattern from ADK 03-complex, presented as a
standalone architecture example. The agent uses score_report() to evaluate
its own draft and rewrite if the score is below threshold.
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


# ── Evaluator tool ────────────────────────────────────────────────────────────

def score_recommendation(draft: str) -> dict:
    """Evaluate the quality of a travel recommendation.
    Call this after writing a draft. If score < 7, rewrite addressing suggestions.

    Args:
        draft: The full text of the draft recommendation.
    Returns:
        Dict with score (1-10), pass (bool), and suggestions list.
    """
    score = 0
    suggestions = []

    if any(kw in draft.lower() for kw in ["attraction", "temple", "museum", "market", "park"]):
        score += 3
    else:
        suggestions.append("Add specific named attractions.")

    if any(kw in draft.lower() for kw in ["°c", "celsius", "weather", "temperature", "season", "rain", "clear"]):
        score += 2
    else:
        suggestions.append("Include specific weather/temperature information.")

    if any(kw in draft.lower() for kw in ["safety", "safe", "advisory", "precaution"]):
        score += 2
    else:
        suggestions.append("Add safety tips or advisory information.")

    if len(draft) > 400:
        score += 3
    elif len(draft) > 200:
        score += 1
        suggestions.append("Expand with more detail (aim for 400+ characters).")
    else:
        suggestions.append("Too brief — add much more detail.")

    return {
        "score": min(score, 10),
        "threshold": 7,
        "pass": score >= 7,
        "suggestions": suggestions if suggestions else ["Recommendation looks great!"],
    }


# ── Reflexion agent ───────────────────────────────────────────────────────────

agent = Agent(
    name="reflexion_writer",
    model="gemini-2.0-flash",
    description="Writes travel recommendations with built-in self-critique and improvement loop.",
    instruction="""You are a travel recommendation writer with a quality gate.

STEP 1 — DRAFT: Write a comprehensive travel recommendation for the requested destination.
  Include: top 3 named attractions, weather/temperature, safety tips, best time to visit.

STEP 2 — EVALUATE: Call score_recommendation() with your draft.
  - If score >= 7: deliver the recommendation as your final answer.
  - If score < 7: read the suggestions, rewrite addressing ALL of them, then evaluate again.

STEP 3 — DELIVER: When score >= 7 (or after 2 revision attempts), present the final recommendation.

You MUST call score_recommendation() at least once before responding.""",
    tools=[score_recommendation],
)


# ── Runner ────────────────────────────────────────────────────────────────────

async def run_reflexion(destination: str) -> str:
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name="reflexion_writer", user_id="u1"
    )
    runner = InMemoryRunner(agent=agent, session_service=session_service)
    query = f"Write a travel recommendation for {destination}."

    print(f"Query: {query}\n")
    print("--- Reflexion trace ---")

    final = ""
    async for event in runner.run_async(
        user_id=session.user_id, session_id=session.id,
        new_message=genai_types.Content(role="user", parts=[genai_types.Part(text=query)]),
    ):
        if hasattr(event, "tool_call") and event.tool_call:
            print(f"  [score_recommendation] called")
        elif hasattr(event, "tool_result") and event.tool_result:
            result_str = str(event.tool_result)
            if "score" in result_str:
                print(f"  [score_result] {result_str[:80]}")
        elif event.is_final_response() and event.content:
            for part in event.content.parts:
                if part.text:
                    final += part.text

    return final


if __name__ == "__main__":
    recommendation = asyncio.run(run_reflexion("Tokyo"))
    print("\n--- Final Recommendation ---")
    print(recommendation)
    print(f"\nQuality check: {score_recommendation(recommendation)}")
