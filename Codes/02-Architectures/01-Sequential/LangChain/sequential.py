"""
Sequential Architecture — LangChain
Pattern: Research → Summarize → Format report (A → B → C pipeline)

Each step is a separate LCEL chain. The output of one chain feeds directly
into the next via Python variable passing — no shared state or agent loops.
"""
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()
assert os.getenv("GOOGLE_API_KEY"), "Set GOOGLE_API_KEY in .env"

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
parser = StrOutputParser()

# ── Mock tool (step 1 data source) ──────────────────────────────────────────

def fetch_city_data(city: str) -> str:
    """Simulate fetching raw travel data for a city."""
    data = {
        "tokyo":     "Weather: Clear, 18°C. Safety: Low advisory. Time: 22:30 JST. Highlights: Shibuya, Senso-ji, Ramen.",
        "paris":     "Weather: Partly Cloudy, 16°C. Safety: Low advisory. Time: 15:30 CET. Highlights: Eiffel Tower, Louvre, Croissants.",
        "bangalore": "Weather: Rainy, 25°C. Safety: Medium advisory. Time: 20:00 IST. Highlights: Lalbagh, Nandi Hills, Biryani.",
    }
    return data.get(city.lower(), f"No data for {city}.")


# ── Step 1: Researcher chain ─────────────────────────────────────────────────
# Receives raw data, extracts key facts

researcher_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a travel data researcher. Extract and structure the key facts from raw city data."),
    ("human", "City: {city}\nRaw data: {raw_data}\n\nExtract: weather, safety, local time, top 2 attractions."),
])
researcher_chain = researcher_prompt | llm | parser


# ── Step 2: Summarizer chain ─────────────────────────────────────────────────
# Receives structured facts, writes a summary paragraph

summarizer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a travel writer. Write a concise 2-sentence city summary for travelers."),
    ("human", "Structured facts:\n{structured_facts}\n\nWrite a traveler summary."),
])
summarizer_chain = summarizer_prompt | llm | parser


# ── Step 3: Formatter chain ──────────────────────────────────────────────────
# Receives summary, produces a polished report section

formatter_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a report editor. Format the travel summary into a polished report section with a header."),
    ("human", "City: {city}\nSummary: {summary}\n\nFormat as a report section with '### {city}' header."),
])
formatter_chain = formatter_prompt | llm | parser


# ── Sequential pipeline runner ───────────────────────────────────────────────

def run_sequential_pipeline(city: str) -> str:
    print(f"\n{'='*50}")
    print(f"Processing: {city}")
    print('='*50)

    raw_data = fetch_city_data(city)
    print(f"[Step 0] Raw data fetched: {raw_data[:60]}...")

    structured_facts = researcher_chain.invoke({"city": city, "raw_data": raw_data})
    print(f"[Step 1] Researcher output:\n{structured_facts}\n")

    summary = summarizer_chain.invoke({"structured_facts": structured_facts})
    print(f"[Step 2] Summarizer output:\n{summary}\n")

    report_section = formatter_chain.invoke({"city": city, "summary": summary})
    print(f"[Step 3] Formatter output:\n{report_section}\n")

    return report_section


def run_multi_city_report(cities: list[str]) -> str:
    sections = [run_sequential_pipeline(city) for city in cities]
    report = "# Travel Report\n\n" + "\n\n".join(sections)
    return report


if __name__ == "__main__":
    cities = ["Tokyo", "Paris", "Bangalore"]
    final_report = run_multi_city_report(cities)
    print("\n" + "="*60)
    print("FINAL REPORT")
    print("="*60)
    print(final_report)
