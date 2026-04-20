"""
Research Assistant — Google ADK Implementation
==============================================
System    : 01 — Research Assistant
Framework : Google Agent Development Kit (ADK)
Model     : gemini-2.0-flash

What this demonstrates:
  - ADK ParallelAgent for fan-out to domain search agents
  - ADK SequentialAgent for the synthesis → critique pipeline
  - Composing ParallelAgent + SequentialAgent for a complete system
  - ADK tool definitions using FunctionTool
  - Structured agent output passing through ADK's state system

Architecture:
  SequentialAgent(
    ParallelAgent(tech_agent, market_agent, regulatory_agent),
    synthesis_agent,
    critic_agent
  )
"""

import os
from dotenv import load_dotenv
from google.adk.agents import Agent, ParallelAgent, SequentialAgent
from google.adk.tools import FunctionTool
from google.adk.runners import InProcessRunner
from google.adk.sessions import InMemorySessionService

load_dotenv()

# ── Mock search functions ──────────────────────────────────────────────────────

def search_technology(query: str) -> dict:
    """Search for technology and R&D information about the given topic.

    Args:
        query: The technology topic to research (e.g., 'solid-state batteries')

    Returns:
        dict with domain, query, and list of technology findings
    """
    data = {
        "solid-state batteries": [
            "Toyota plans to commercialize solid-state EV batteries by 2027-2028",
            "2x energy density vs lithium-ion with no liquid electrolyte fire risk",
            "QuantumScape achieved 800+ charge cycles in lab conditions",
            "Key challenge: manufacturing yield rates below 80%",
            "CATL and Samsung SDI both have active solid-state programs",
        ]
    }
    findings = data.get(query.lower(), ["No technology data found for this query"])
    return {"domain": "technology", "query": query, "findings": findings}


def search_market(query: str) -> dict:
    """Search for market size, competitive landscape, and business intelligence.

    Args:
        query: The market topic to research (e.g., 'solid-state batteries')

    Returns:
        dict with domain, query, and list of market findings
    """
    data = {
        "solid-state batteries": [
            "Global solid-state battery market projected at $8.8B by 2031 (CAGR 36%)",
            "EV sector accounts for 72% of demand; consumer electronics 18%",
            "Japan leads in patents — Toyota holds 1,300+ solid-state battery patents",
            "China government invested $15B in battery R&D since 2020",
            "Key players: Toyota, Samsung SDI, QuantumScape, CATL, Panasonic, Solid Power",
        ]
    }
    findings = data.get(query.lower(), ["No market data found for this query"])
    return {"domain": "market", "query": query, "findings": findings}


def search_regulatory(query: str) -> dict:
    """Search for regulatory, policy, and compliance information.

    Args:
        query: The regulatory topic to research (e.g., 'solid-state batteries')

    Returns:
        dict with domain, query, and list of regulatory findings
    """
    data = {
        "solid-state batteries": [
            "EU Battery Regulation (2023) requires 70% recycled content by 2030",
            "US IRA provides $45/kWh tax credit for domestically manufactured batteries",
            "China GB/T standards updated 2024 to include solid-state safety protocols",
            "UN Transportation of Dangerous Goods regulations updated for solid electrolytes",
            "Japan NITE certification pathway for solid-state cells established 2023",
        ]
    }
    findings = data.get(query.lower(), ["No regulatory data found for this query"])
    return {"domain": "regulatory", "query": query, "findings": findings}


# ── ADK Agents ─────────────────────────────────────────────────────────────────

tech_agent = Agent(
    name="technology_researcher",
    model="gemini-2.0-flash",
    description="Technology and R&D research specialist",
    instruction="""You are a technology research specialist. When given a research topic:
    1. Use the search_technology tool to find technical information
    2. Summarize the findings into 3-5 key technology insights
    3. Focus on: current state, key challenges, leading organizations, timeline""",
    tools=[FunctionTool(search_technology)],
)

market_agent = Agent(
    name="market_researcher",
    model="gemini-2.0-flash",
    description="Market intelligence and competitive analysis specialist",
    instruction="""You are a market research analyst. When given a research topic:
    1. Use the search_market tool to find market intelligence
    2. Summarize into 3-5 key market insights
    3. Focus on: market size, growth rate, key players, geographic dynamics""",
    tools=[FunctionTool(search_market)],
)

regulatory_agent = Agent(
    name="regulatory_researcher",
    model="gemini-2.0-flash",
    description="Regulatory intelligence and policy research specialist",
    instruction="""You are a regulatory research specialist. When given a research topic:
    1. Use the search_regulatory tool to find regulatory information
    2. Summarize into 3-5 key regulatory insights
    3. Focus on: specific regulations, incentives, compliance requirements, geographic differences""",
    tools=[FunctionTool(search_regulatory)],
)

parallel_research = ParallelAgent(
    name="parallel_research_team",
    description="Three domain researchers running in parallel",
    sub_agents=[tech_agent, market_agent, regulatory_agent],
)

synthesis_agent = Agent(
    name="synthesis_specialist",
    model="gemini-2.0-flash",
    description="Research synthesis and report writing specialist",
    instruction="""You are a research synthesis specialist. Using the research from the previous agents:
    Create a comprehensive research report with these sections:
    1. Executive Summary (2-3 sentences)
    2. Technology Landscape
    3. Market Analysis
    4. Regulatory Environment
    5. Key Insights and Strategic Implications

    Be specific and reference evidence from all three research domains.""",
)

critic_agent = Agent(
    name="research_critic",
    model="gemini-2.0-flash",
    description="Research quality reviewer and critic",
    instruction="""You are a demanding research quality reviewer. Evaluate the synthesis report:
    1. Are all five sections present and substantive?
    2. Are claims supported by specific data?
    3. Are there significant gaps or missing perspectives?

    Provide specific feedback and end with:
    VERDICT: APPROVED — if the report is comprehensive and well-supported
    VERDICT: NEEDS_REVISION: [specific reasons] — if significant gaps exist""",
)

# ── Compose the full system ────────────────────────────────────────────────────

research_assistant = SequentialAgent(
    name="research_assistant_system",
    description="Complete multi-agent research assistant: parallel search → synthesis → critique",
    sub_agents=[parallel_research, synthesis_agent, critic_agent],
)


# ── Runner setup ───────────────────────────────────────────────────────────────

def run_research_assistant(query: str) -> str:
    """Run the research assistant system and return the final report."""
    session_service = InMemorySessionService()
    runner = InProcessRunner(
        agent=research_assistant,
        session_service=session_service,
        app_name="research_assistant",
    )

    session = session_service.create_session(
        app_name="research_assistant",
        user_id="user_001",
    )

    print(f"\n{'='*60}")
    print("RESEARCH ASSISTANT — ADK")
    print(f"Query: {query}")
    print(f"{'='*60}")

    from google.adk.types import Content, Part

    response = runner.run(
        user_id="user_001",
        session_id=session.id,
        new_message=Content(parts=[Part(text=query)]),
    )

    return response.text if hasattr(response, 'text') else str(response)


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    query = "solid-state batteries"
    result = run_research_assistant(query)

    print("\n" + "="*60)
    print("FINAL RESEARCH REPORT")
    print("="*60)
    print(result)
