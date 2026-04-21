"""
LangChain Simple Agent
======================
Framework : LangChain (LCEL)
Level     : 01 — Simple
Model     : gemini-2.0-flash via langchain-google-genai

What this demonstrates:
  - Defining tools with @tool decorator + docstrings
  - Building a tool-calling agent with create_tool_calling_agent + AgentExecutor
  - How LCEL chains compose: prompt | llm_with_tools | output_parser
  - AgentExecutor managing the ReAct loop automatically

Mock tools used (no credentials needed):
  - get_weather(city)  → fake weather report
  - get_time(city)     → fake local time
"""

import os
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor, create_tool_calling_agent

load_dotenv()

# ── Mock Tools ──────────────────────────────────────────────────────────────

@tool
def get_weather(city: str) -> dict:
    """Return a mock weather report for the given city.

    Use this tool when the user asks about weather conditions, temperature,
    or climate in a specific city.
    """
    mock_data = {
        "london":    {"condition": "Cloudy", "temp_c": 12, "humidity": 78},
        "new york":  {"condition": "Sunny",  "temp_c": 22, "humidity": 45},
        "bangalore": {"condition": "Rainy",  "temp_c": 25, "humidity": 85},
        "tokyo":     {"condition": "Clear",  "temp_c": 18, "humidity": 60},
    }
    key = city.lower()
    if key in mock_data:
        d = mock_data[key]
        return {"city": city, "condition": d["condition"],
                "temperature_celsius": d["temp_c"], "humidity_percent": d["humidity"]}
    return {"error": f"No data for '{city}'. Try: London, New York, Bangalore, Tokyo."}


@tool
def get_time(city: str) -> dict:
    """Return the current local time for the given city.

    Use this tool when the user asks what time it is in a specific location.
    """
    mock_times = {
        "london":    "14:30 GMT",
        "new york":  "09:30 EST",
        "bangalore": "20:00 IST",
        "tokyo":     "22:30 JST",
    }
    key = city.lower()
    if key in mock_times:
        return {"city": city, "local_time": mock_times[key]}
    return {"error": f"No time data for '{city}'. Try: London, New York, Bangalore, Tokyo."}


tools = [get_weather, get_time]

# ── Model + Prompt ──────────────────────────────────────────────────────────

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful travel assistant. Use tools to answer weather and time questions. Be concise and friendly."),
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad"),  # required: stores intermediate tool call steps
])

# ── Agent + Executor ────────────────────────────────────────────────────────

agent = create_tool_calling_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)


# ── Run ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    queries = [
        "What's the weather like in Bangalore right now?",
        "What time is it in Tokyo, and is it a good day to go outside?",
    ]
    for q in queries:
        print(f"\nUser: {q}")
        result = executor.invoke({"input": q})
        print(f"Agent: {result['output']}")
