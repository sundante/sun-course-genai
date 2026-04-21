"""
LangChain Complex Agent
========================
Framework : LangChain (LCEL)
Level     : 03 — Complex
Model     : gemini-2.0-flash

New concepts vs Intermediate:
  - Plan-and-Execute pattern: a Planner chain decomposes the goal into steps,
    then an Executor agent runs each step in sequence
  - Self-critique / Reflexion: a Critic chain scores the output and triggers
    a rewrite if score < threshold
  - Streaming with .stream() on the executor
  - Chaining chains: LCEL pipes across multiple chains

Domain: multi-city trip planner with plan → execute → critique → refine.
"""

import os
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain.agents import AgentExecutor, create_tool_calling_agent

load_dotenv()

# ── Tools ─────────────────────────────────────────────────────────────────────

@tool
def get_weather(city: str) -> dict:
    """Return weather data for a city including a weather score (1-10)."""
    data = {
        "london":    {"condition": "Cloudy",       "temp_c": 12, "score": 5},
        "new york":  {"condition": "Sunny",         "temp_c": 22, "score": 8},
        "bangalore": {"condition": "Rainy",         "temp_c": 25, "score": 6},
        "tokyo":     {"condition": "Clear",         "temp_c": 18, "score": 9},
        "paris":     {"condition": "Partly Cloudy", "temp_c": 16, "score": 7},
    }
    key = city.lower()
    if key in data:
        return {"city": city, **data[key]}
    return {"error": f"No data for '{city}'."}


@tool
def get_time(city: str) -> dict:
    """Return current local time for a city."""
    times = {
        "london": "14:30 GMT", "new york": "09:30 EST",
        "bangalore": "20:00 IST", "tokyo": "22:30 JST", "paris": "15:30 CET",
    }
    return {"city": city, "local_time": times.get(city.lower(), "Unknown")}


@tool
def get_travel_advisory(city: str) -> dict:
    """Return travel safety advisory for a city including a safety score (1-10)."""
    data = {
        "london":    {"level": "Low",    "notes": "Routine precautions.",      "safety_score": 8},
        "new york":  {"level": "Low",    "notes": "Normal precautions.",       "safety_score": 7},
        "bangalore": {"level": "Medium", "notes": "Monsoon affects transport.", "safety_score": 6},
        "tokyo":     {"level": "Low",    "notes": "Very safe city.",            "safety_score": 10},
        "paris":     {"level": "Low",    "notes": "Alert in crowded spots.",    "safety_score": 8},
    }
    key = city.lower()
    if key in data:
        return {"city": city, **data[key]}
    return {"error": f"No advisory for '{city}'."}


tools = [get_weather, get_time, get_travel_advisory]

# ── LLM ───────────────────────────────────────────────────────────────────────

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
llm_creative = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.3)

# ── Chain 1: Planner ──────────────────────────────────────────────────────────
# Decomposes the high-level goal into ordered research steps

planner_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a research planner. Given a travel comparison task, "
     "output a numbered list of research steps. Each step = one city to research. "
     "Be concise. Format: '1. Research [city]: get weather, time, advisory'"),
    ("human", "{goal}"),
])

planner_chain = planner_prompt | llm | StrOutputParser()

# ── Chain 2: Executor Agent ───────────────────────────────────────────────────
# Executes the research plan using tools

executor_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a travel research executor. You receive a research plan and execute it. "
     "For each city in the plan, call get_weather, get_time, and get_travel_advisory. "
     "After gathering all data, write a comprehensive comparison report with city rankings."),
    ("human", "Plan:\n{plan}\n\nExecute this plan and write the comparison report."),
    MessagesPlaceholder("agent_scratchpad"),
])

executor_agent = create_tool_calling_agent(llm, tools, executor_prompt)
executor = AgentExecutor(agent=executor_agent, tools=tools, verbose=False)

# ── Chain 3: Critic ───────────────────────────────────────────────────────────
# Scores the report and returns structured critique

critic_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a travel report editor. Score the report from 1-10 and identify gaps. "
     "Respond with EXACTLY this format:\n"
     "SCORE: [number]\n"
     "ISSUES: [comma-separated list of issues, or 'None']\n"
     "VERDICT: [PASS if score>=7, REVISE if score<7]"),
    ("human", "Report to evaluate:\n\n{report}"),
])

critic_chain = critic_prompt | llm | StrOutputParser()

# ── Chain 4: Reviser ──────────────────────────────────────────────────────────
# Rewrites the report based on critic feedback

reviser_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a travel writer. Improve the report based on the critique. "
               "Keep all existing data, fix the identified issues."),
    ("human", "Original report:\n{report}\n\nCritique:\n{critique}\n\nWrite an improved version:"),
])

reviser_chain = reviser_prompt | llm_creative | StrOutputParser()


# ── Orchestrator ──────────────────────────────────────────────────────────────

def run(goal: str, max_retries: int = 2) -> str:
    print(f"\n[1/4] Planning...")
    plan = planner_chain.invoke({"goal": goal})
    print(f"Plan:\n{plan}\n")

    print(f"[2/4] Executing plan...")
    result = executor.invoke({"plan": plan})
    report = result["output"]
    print(f"Draft report ({len(report)} chars)\n")

    for attempt in range(max_retries):
        print(f"[3/4] Critique (attempt {attempt + 1})...")
        critique = critic_chain.invoke({"report": report})
        print(f"Critique:\n{critique}\n")

        if "VERDICT: PASS" in critique:
            print("[4/4] Report passed quality check.")
            break
        else:
            print(f"[4/4] Revising report...")
            report = reviser_chain.invoke({"report": report, "critique": critique})
            print(f"Revised report ({len(report)} chars)\n")

    return report


if __name__ == "__main__":
    goal = "Compare Tokyo, Paris, and Bangalore for travel. I want the safest and best weather."
    final_report = run(goal)
    print("\n" + "="*60)
    print("FINAL REPORT")
    print("="*60)
    print(final_report)
