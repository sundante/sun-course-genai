"""
Parallel Architecture — LangChain
Pattern: Fan-out (3 city researchers) → Aggregate (ranker)

asyncio.gather() runs all city research chains simultaneously.
The aggregator chain receives all results and produces a final ranking.
"""
import asyncio
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()
assert os.getenv("GOOGLE_API_KEY"), "Set GOOGLE_API_KEY in .env"

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
parser = StrOutputParser()


# ── Mock tools ────────────────────────────────────────────────────────────────

CITY_DATA = {
    "tokyo":     {"weather": "Clear, 18°C, score 9/10", "safety": "Low, score 10/10", "time": "22:30 JST"},
    "paris":     {"weather": "Partly Cloudy, 16°C, score 7/10", "safety": "Low, score 8/10", "time": "15:30 CET"},
    "bangalore": {"weather": "Rainy, 25°C, score 6/10", "safety": "Medium, score 6/10", "time": "20:00 IST"},
}

def get_city_raw_data(city: str) -> str:
    d = CITY_DATA.get(city.lower(), {})
    return f"{city} — Weather: {d.get('weather','N/A')} | Safety: {d.get('safety','N/A')} | Time: {d.get('time','N/A')}"


# ── Parallel researcher chain (one per city) ─────────────────────────────────

researcher_chain = (
    ChatPromptTemplate.from_messages([
        ("system", "You are a travel researcher. Write a structured 3-line city report: Weather, Safety, Recommendation."),
        ("human", "City: {city}\nData: {raw_data}\n\nWrite a structured city report."),
    ])
    | llm | parser
)


# ── Aggregator chain ──────────────────────────────────────────────────────────

aggregator_chain = (
    ChatPromptTemplate.from_messages([
        ("system", "You are a travel editor. Rank the cities best to worst based on weather and safety scores. Justify each rank."),
        ("human", "City reports:\n\n{city_reports}\n\nRank all cities and name the top pick."),
    ])
    | llm | parser
)


# ── Parallel runner ───────────────────────────────────────────────────────────

async def research_city(city: str) -> str:
    raw = get_city_raw_data(city)
    result = await researcher_chain.ainvoke({"city": city, "raw_data": raw})
    print(f"  [parallel] {city} done")
    return f"### {city}\n{result}"


async def run_parallel(cities: list[str]) -> str:
    print("Launching parallel research for:", cities)
    reports = await asyncio.gather(*[research_city(c) for c in cities])
    combined = "\n\n".join(reports)
    print("\n[aggregate] ranking all cities...")
    ranking = aggregator_chain.invoke({"city_reports": combined})
    return f"# Parallel Travel Report\n\n{combined}\n\n---\n\n## Final Ranking\n{ranking}"


if __name__ == "__main__":
    cities = ["Tokyo", "Paris", "Bangalore"]
    report = asyncio.run(run_parallel(cities))
    print("\n" + "="*60)
    print(report)
