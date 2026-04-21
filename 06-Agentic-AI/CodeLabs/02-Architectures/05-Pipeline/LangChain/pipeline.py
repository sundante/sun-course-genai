"""
Pipeline Architecture — LangChain
Pattern: ETL pipeline — Extract → Transform → Load

Mix of pure Python transforms and LLM-powered steps.
LangChain's LCEL pipe operator chains them cleanly.
"""
import os
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnableLambda

load_dotenv()
assert os.getenv("GOOGLE_API_KEY"), "Set GOOGLE_API_KEY in .env"

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)


# ── Raw data (simulates an external data source) ──────────────────────────────

RAW_CITY_DATA = [
    "Tokyo|Clear|18|Low|10|22:30 JST",
    "Paris|Partly Cloudy|16|Low|8|15:30 CET",
    "Bangalore|Rainy|25|Medium|6|20:00 IST",
]


# ── Extract step (pure Python) ────────────────────────────────────────────────

def extract(raw_records: list[str]) -> list[dict]:
    """Parse pipe-delimited strings into structured dicts."""
    result = []
    for line in raw_records:
        city, weather, temp, safety_level, safety_score, time = line.split("|")
        result.append({
            "city": city,
            "weather": weather,
            "temp_c": int(temp),
            "safety_level": safety_level,
            "safety_score": int(safety_score),
            "local_time": time,
        })
    print(f"  [Extract] {len(result)} records parsed")
    return result


# ── Transform step (pure Python + LLM for scoring) ───────────────────────────

def transform(records: list[dict]) -> list[dict]:
    """Enrich records: add weather_score, combined_score, rank."""
    score_map = {"Clear": 9, "Sunny": 9, "Partly Cloudy": 7, "Cloudy": 5, "Rainy": 6, "Overcast": 4}
    for r in records:
        r["weather_score"] = score_map.get(r["weather"], 5)
        r["combined_score"] = round((r["weather_score"] + r["safety_score"]) / 2, 1)

    records.sort(key=lambda x: x["combined_score"], reverse=True)
    for i, r in enumerate(records, 1):
        r["rank"] = i

    print(f"  [Transform] scored + ranked {len(records)} records")
    return records


# ── Load step (LLM formats the output) ───────────────────────────────────────

load_chain = (
    ChatPromptTemplate.from_messages([
        ("system", "You are a report formatter. Convert the structured data into a readable travel ranking report."),
        ("human", "Data: {data}\n\nFormat as a markdown report with rankings and scores."),
    ])
    | llm
    | (lambda r: r.content)
)


def load(records: list[dict]) -> str:
    """Format enriched records into a final report."""
    report = load_chain.invoke({"data": json.dumps(records, indent=2)})
    print("  [Load] report formatted")
    return report


# ── Full pipeline ─────────────────────────────────────────────────────────────

def run_pipeline(raw_data: list[str]) -> str:
    print("Running ETL pipeline...")
    extracted = extract(raw_data)
    transformed = transform(extracted)
    report = load(transformed)
    return report


if __name__ == "__main__":
    report = run_pipeline(RAW_CITY_DATA)
    print("\n" + "="*60)
    print(report)
