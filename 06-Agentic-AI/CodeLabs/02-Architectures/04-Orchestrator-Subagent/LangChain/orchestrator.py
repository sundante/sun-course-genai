"""
Orchestrator-Subagent Architecture — LangChain
Pattern: Planner chain → dynamically selects + calls specialist sub-chains

The orchestrator chain decides which specialists to invoke and in what order.
Each specialist is a focused LCEL chain. The orchestrator wires them together.
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


# ── Mock data (specialist workers use these) ──────────────────────────────────

CITY_HIGHLIGHTS = {
    "tokyo":     "Shibuya crossing, Senso-ji temple, tsukiji market, Mount Fuji day trip",
    "paris":     "Eiffel Tower, Louvre museum, Notre Dame, Seine river cruise, Montmartre",
    "bangalore": "Lalbagh Botanical Garden, Nandi Hills, Cubbon Park, Vidhana Soudha",
}

CITY_LOGISTICS = {
    "tokyo":     "3h from SFO by Japan Airlines. Shinkansen for local travel. Best months: March-May.",
    "paris":     "11h from NYC by Air France. Metro/RER for local travel. Best months: April-June.",
    "bangalore": "9h from Dubai by Emirates. Ola/Uber for local travel. Best months: October-February.",
}


# ── Specialist sub-chains ─────────────────────────────────────────────────────

highlights_agent = (
    ChatPromptTemplate.from_messages([
        ("system", "You are a travel highlights specialist. List the top 3 attractions with a one-line description each."),
        ("human", "City: {city}\nHighlights data: {data}"),
    ]) | llm | parser
)

logistics_agent = (
    ChatPromptTemplate.from_messages([
        ("system", "You are a travel logistics specialist. Provide practical travel tips: flights, local transport, best season."),
        ("human", "City: {city}\nLogistics data: {data}"),
    ]) | llm | parser
)

itinerary_agent = (
    ChatPromptTemplate.from_messages([
        ("system", "You are a travel itinerary writer. Create a 3-day itinerary using the provided highlights and logistics."),
        ("human", "City: {city}\nHighlights:\n{highlights}\n\nLogistics:\n{logistics}"),
    ]) | llm | parser
)

package_formatter = (
    ChatPromptTemplate.from_messages([
        ("system", "You are a travel package editor. Format all inputs into a polished trip package with clear sections."),
        ("human", "City: {city}\nHighlights:\n{highlights}\n\nLogistics:\n{logistics}\n\nItinerary:\n{itinerary}"),
    ]) | llm | parser
)


# ── Orchestrator ──────────────────────────────────────────────────────────────

def orchestrate_trip_package(city: str) -> str:
    """Orchestrator: plans and delegates to specialists in sequence."""
    print(f"\n[Orchestrator] Planning trip package for: {city}")

    print("  [Orchestrator → highlights_agent]")
    highlights = highlights_agent.invoke({
        "city": city,
        "data": CITY_HIGHLIGHTS.get(city.lower(), "No data."),
    })

    print("  [Orchestrator → logistics_agent]")
    logistics = logistics_agent.invoke({
        "city": city,
        "data": CITY_LOGISTICS.get(city.lower(), "No data."),
    })

    print("  [Orchestrator → itinerary_agent]")
    itinerary = itinerary_agent.invoke({
        "city": city,
        "highlights": highlights,
        "logistics": logistics,
    })

    print("  [Orchestrator → package_formatter]")
    package = package_formatter.invoke({
        "city": city,
        "highlights": highlights,
        "logistics": logistics,
        "itinerary": itinerary,
    })

    return package


if __name__ == "__main__":
    package = orchestrate_trip_package("Tokyo")
    print("\n" + "="*60)
    print(package)
