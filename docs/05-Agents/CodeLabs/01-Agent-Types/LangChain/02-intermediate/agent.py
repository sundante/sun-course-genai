"""
LangChain Intermediate Agent
=============================
Framework : LangChain (LCEL)
Level     : 02 — Intermediate
Model     : gemini-2.0-flash

New concepts vs Simple:
  - 3 tools (added get_travel_advisory)
  - Multi-turn memory via RunnableWithMessageHistory + ChatMessageHistory
  - Structured output via PydanticOutputParser

Domain: travel assistant that maintains conversation history across turns.
"""

import os
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.runnables.history import RunnableWithMessageHistory

load_dotenv()

# ── Structured Output Schema ──────────────────────────────────────────────────

class TravelBriefing(BaseModel):
    city: str = Field(description="Name of the city")
    weather_summary: str = Field(description="Weather conditions and temperature")
    local_time: str = Field(description="Current local time with timezone")
    travel_advisory: str = Field(description="Safety advisory level and key notes")
    recommendation: str = Field(description="One-sentence travel recommendation")

# ── Mock Tools ────────────────────────────────────────────────────────────────

@tool
def get_weather(city: str) -> dict:
    """Return weather conditions for a city. Use when asked about weather or temperature."""
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


@tool
def get_time(city: str) -> dict:
    """Return current local time for a city. Use when asked about time or timezone."""
    times = {
        "london": "14:30 GMT", "new york": "09:30 EST",
        "bangalore": "20:00 IST", "tokyo": "22:30 JST", "paris": "15:30 CET",
    }
    key = city.lower()
    if key in times:
        return {"city": city, "local_time": times[key]}
    return {"error": f"No time data for '{city}'."}


@tool
def get_travel_advisory(city: str) -> dict:
    """Return travel safety advisory for a city. Use when asked about safety or travel advisories."""
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


tools = [get_weather, get_time, get_travel_advisory]

# ── Model + Prompt ────────────────────────────────────────────────────────────

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a professional travel intelligence assistant. "
     "When asked about a city, always check weather, local time, AND travel advisory. "
     "Remember context from earlier in the conversation."),
    MessagesPlaceholder("chat_history"),   # ← injected by RunnableWithMessageHistory
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad"),
])

# ── Agent + Memory ────────────────────────────────────────────────────────────

agent = create_tool_calling_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=False)

# In-memory store: session_id → ChatMessageHistory
_store: dict[str, BaseChatMessageHistory] = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in _store:
        _store[session_id] = ChatMessageHistory()
    return _store[session_id]

# Wrap the executor: automatically reads/writes chat_history for each session_id
agent_with_memory = RunnableWithMessageHistory(
    executor,
    get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history",
)


def run(query: str, session_id: str = "session_01") -> str:
    result = agent_with_memory.invoke(
        {"input": query},
        config={"configurable": {"session_id": session_id}},
    )
    return result["output"]


if __name__ == "__main__":
    print("=== Multi-turn conversation with memory ===\n")
    sid = "travel_session"

    turns = [
        "Give me a full travel briefing for Tokyo.",
        "Now do the same for Bangalore. I prefer warm weather — which would you recommend?",
        "Based on what you told me, what's the safer city to visit?",
    ]

    for query in turns:
        print(f"User: {query}")
        print(f"Agent: {run(query, sid)}\n{'-'*60}\n")

    # Show what's in memory
    history = get_session_history(sid)
    print(f"\nMessages in memory for session '{sid}': {len(history.messages)}")
