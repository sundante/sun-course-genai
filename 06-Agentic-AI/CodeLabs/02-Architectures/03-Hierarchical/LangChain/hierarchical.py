"""
Hierarchical Architecture — LangChain
Pattern: Manager chain orchestrates Research Lead + Report Lead sub-chains

The manager decides what to delegate. Each lead chain calls its workers.
All are plain LCEL chains — hierarchy is expressed via function calls.
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


# ── Mock data (workers use this) ──────────────────────────────────────────────

WEATHER_DATA = {
    "tokyo":     "Clear, 18°C, weather score 9/10",
    "paris":     "Partly Cloudy, 16°C, weather score 7/10",
    "bangalore": "Rainy, 25°C, weather score 6/10",
}
SAFETY_DATA = {
    "tokyo":     "Low advisory, safety score 10/10. Very safe city.",
    "paris":     "Low advisory, safety score 8/10. Alert in crowded spots.",
    "bangalore": "Medium advisory, safety score 6/10. Monsoon affects transport.",
}


# ── Worker chains ─────────────────────────────────────────────────────────────

weather_worker = (
    ChatPromptTemplate.from_messages([
        ("system", "You are a weather analyst. Report weather conditions clearly."),
        ("human", "City: {city}\nData: {data}\n\nWrite a 1-sentence weather report."),
    ]) | llm | parser
)

safety_worker = (
    ChatPromptTemplate.from_messages([
        ("system", "You are a safety analyst. Report travel safety clearly."),
        ("human", "City: {city}\nData: {data}\n\nWrite a 1-sentence safety report."),
    ]) | llm | parser
)

format_worker = (
    ChatPromptTemplate.from_messages([
        ("system", "You are a report formatter. Create a polished markdown section."),
        ("human", "City: {city}\nResearch: {research}\n\nFormat as a '### {city}' section."),
    ]) | llm | parser
)

summary_worker = (
    ChatPromptTemplate.from_messages([
        ("system", "You are a travel summarizer. Write a single recommendation sentence."),
        ("human", "Research: {research}\n\nWrite a 1-sentence recommendation."),
    ]) | llm | parser
)


# ── Team Lead chains ──────────────────────────────────────────────────────────

def research_lead(city: str) -> str:
    """Research lead: delegates to weather + safety workers."""
    weather = weather_worker.invoke({"city": city, "data": WEATHER_DATA.get(city.lower(), "N/A")})
    safety = safety_worker.invoke({"city": city, "data": SAFETY_DATA.get(city.lower(), "N/A")})
    result = f"Weather: {weather}\nSafety: {safety}"
    print(f"  [Research Lead → workers] {city} done")
    return result


def report_lead(city: str, research: str) -> str:
    """Report lead: delegates to format + summary workers."""
    formatted = format_worker.invoke({"city": city, "research": research})
    summary = summary_worker.invoke({"research": research})
    result = f"{formatted}\n\n*Summary: {summary}*"
    print(f"  [Report Lead → workers] {city} done")
    return result


# ── Manager chain ─────────────────────────────────────────────────────────────

manager_chain = (
    ChatPromptTemplate.from_messages([
        ("system", "You are a travel project manager. Given cities and their reports, write a final executive summary with a top recommendation."),
        ("human", "Cities: {cities}\nReports:\n{reports}\n\nWrite an executive summary with top recommendation."),
    ]) | llm | parser
)


def run_hierarchical(cities: list[str]) -> str:
    print(f"\nManager: decomposing goal for cities: {cities}")
    all_reports = []

    for city in cities:
        print(f"\n  [Manager → Research Lead] delegating research for {city}")
        research = research_lead(city)

        print(f"  [Manager → Report Lead] delegating formatting for {city}")
        report = report_lead(city, research)
        all_reports.append(report)

    combined = "\n\n---\n\n".join(all_reports)
    print("\n  [Manager] synthesizing executive summary...")
    executive_summary = manager_chain.invoke({"cities": ", ".join(cities), "reports": combined})

    return f"# Hierarchical Travel Report\n\n{combined}\n\n---\n\n## Executive Summary\n{executive_summary}"


if __name__ == "__main__":
    cities = ["Tokyo", "Paris"]
    report = run_hierarchical(cities)
    print("\n" + "="*60)
    print(report)
