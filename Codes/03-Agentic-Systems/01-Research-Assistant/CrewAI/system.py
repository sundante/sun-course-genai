"""
Research Assistant — CrewAI Implementation
==========================================
System    : 01 — Research Assistant
Framework : CrewAI
Model     : gemini-2.0-flash via langchain-google-genai

What this demonstrates:
  - Role-based agent design for a research crew
  - CrewAI Process.hierarchical for orchestrator-subagent pattern
  - Crew with manager agent coordinating specialist agents
  - Reflexion via a dedicated critic agent task
  - Task dependencies: research tasks feed into synthesis which feeds into critique

Architecture:
  Manager (orchestrates) → [Tech Researcher || Market Researcher || Regulatory Researcher]
                        → Synthesis Specialist → Research Critic
"""

import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

load_dotenv()

# ── LLM ───────────────────────────────────────────────────────────────────────

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.3)

# ── Mock tools ─────────────────────────────────────────────────────────────────

class TechnologySearchTool(BaseTool):
    name: str = "technology_search"
    description: str = "Search for technology, R&D, and engineering information about a topic. Input: research topic as a string."

    def _run(self, query: str) -> str:
        data = {
            "solid-state batteries": [
                "Toyota plans to commercialize solid-state EV batteries by 2027-2028",
                "2x energy density vs lithium-ion with no liquid electrolyte fire risk",
                "QuantumScape achieved 800+ charge cycles in lab conditions",
                "Key challenge: manufacturing yield rates below 80%",
                "CATL and Samsung SDI both have active solid-state programs",
            ]
        }
        findings = data.get(query.lower(), ["No technology data found"])
        return "\n".join(f"- {f}" for f in findings)


class MarketSearchTool(BaseTool):
    name: str = "market_search"
    description: str = "Search for market size, competitive landscape, and business intelligence. Input: research topic as a string."

    def _run(self, query: str) -> str:
        data = {
            "solid-state batteries": [
                "Global solid-state battery market projected at $8.8B by 2031 (CAGR 36%)",
                "EV sector accounts for 72% of demand; consumer electronics 18%",
                "Japan leads in patents — Toyota holds 1,300+ solid-state battery patents",
                "China government invested $15B in battery R&D since 2020",
                "Key players: Toyota, Samsung SDI, QuantumScape, CATL, Panasonic, Solid Power",
            ]
        }
        findings = data.get(query.lower(), ["No market data found"])
        return "\n".join(f"- {f}" for f in findings)


class RegulatorySearchTool(BaseTool):
    name: str = "regulatory_search"
    description: str = "Search for regulations, policies, and compliance requirements. Input: research topic as a string."

    def _run(self, query: str) -> str:
        data = {
            "solid-state batteries": [
                "EU Battery Regulation (2023) requires 70% recycled content by 2030",
                "US IRA provides $45/kWh tax credit for domestically manufactured batteries",
                "China GB/T standards updated 2024 to include solid-state safety protocols",
                "UN Transportation of Dangerous Goods regulations updated for solid electrolytes",
                "Japan NITE certification pathway for solid-state cells established 2023",
            ]
        }
        findings = data.get(query.lower(), ["No regulatory data found"])
        return "\n".join(f"- {f}" for f in findings)


# ── Agent definitions ──────────────────────────────────────────────────────────

tech_researcher = Agent(
    role="Technology Research Specialist",
    goal="Research the technical and engineering aspects of the given topic and provide comprehensive findings",
    backstory="""You are a technology analyst with deep expertise in emerging technologies.
    You excel at finding and synthesizing technical research, patents, and engineering developments.
    You always cite specific data points and avoid vague generalizations.""",
    tools=[TechnologySearchTool()],
    llm=llm,
    verbose=True,
    max_iter=3,
)

market_researcher = Agent(
    role="Market Research Analyst",
    goal="Research the market landscape, competitive dynamics, and business intelligence for the given topic",
    backstory="""You are a market intelligence analyst specializing in emerging technology sectors.
    You excel at market sizing, competitive analysis, and identifying key players.
    You always provide specific numbers and sources when available.""",
    tools=[MarketSearchTool()],
    llm=llm,
    verbose=True,
    max_iter=3,
)

regulatory_researcher = Agent(
    role="Regulatory Intelligence Specialist",
    goal="Research the regulatory environment, policies, and compliance requirements relevant to the topic",
    backstory="""You are a regulatory affairs specialist with expertise in technology policy.
    You track government regulations, standards bodies, and compliance requirements globally.
    You understand how policy shapes market dynamics.""",
    tools=[RegulatorySearchTool()],
    llm=llm,
    verbose=True,
    max_iter=3,
)

synthesis_specialist = Agent(
    role="Research Synthesis Specialist",
    goal="Synthesize multi-domain research findings into a comprehensive, structured research report",
    backstory="""You are an expert at synthesizing complex research from multiple domains into
    coherent, actionable reports. You excel at identifying cross-domain patterns and implications.
    Your reports are known for being specific, well-structured, and evidence-based.""",
    llm=llm,
    verbose=True,
    max_iter=3,
)

research_critic = Agent(
    role="Research Quality Reviewer",
    goal="Critically evaluate research reports for completeness, accuracy, and analytical rigor",
    backstory="""You are a demanding research director who reviews reports before publication.
    You identify gaps, unsupported claims, missing context, and analytical weaknesses.
    You provide specific, actionable feedback. You never approve a report that has significant gaps.""",
    llm=llm,
    verbose=True,
    max_iter=3,
)


# ── Task definitions ───────────────────────────────────────────────────────────

def build_crew(query: str) -> Crew:
    tech_task = Task(
        description=f"""Research the technology and engineering aspects of: {query}
        Use the technology_search tool with the exact query: {query}
        Provide a structured summary with:
        - Current state of the technology
        - Key technical challenges
        - Leading organizations and their progress
        - Timeline expectations""",
        expected_output="A structured technology research report with 5+ specific data points",
        agent=tech_researcher,
    )

    market_task = Task(
        description=f"""Research the market landscape for: {query}
        Use the market_search tool with the exact query: {query}
        Provide a structured summary with:
        - Market size and growth projections
        - Key players and their positions
        - Investment landscape
        - Geographic dynamics""",
        expected_output="A structured market research report with specific figures and named companies",
        agent=market_researcher,
    )

    regulatory_task = Task(
        description=f"""Research the regulatory environment for: {query}
        Use the regulatory_search tool with the exact query: {query}
        Provide a structured summary with:
        - Key regulations and their requirements
        - Government policies and incentives
        - Compliance considerations
        - Geographic regulatory differences""",
        expected_output="A structured regulatory research report with specific regulations and their implications",
        agent=regulatory_researcher,
    )

    synthesis_task = Task(
        description=f"""Synthesize the technology, market, and regulatory research about '{query}'
        into a comprehensive research report.

        Use the research from the previous tasks (tech_task, market_task, regulatory_task context).

        Structure:
        1. Executive Summary (2-3 sentences capturing the big picture)
        2. Technology Landscape (key developments and challenges)
        3. Market Analysis (size, growth, players)
        4. Regulatory Environment (key rules and their impact)
        5. Key Insights and Strategic Implications

        Be specific. Reference the data from all three research streams.""",
        expected_output="A complete 500-800 word research report with all five sections fully populated",
        agent=synthesis_specialist,
        context=[tech_task, market_task, regulatory_task],
    )

    critique_task = Task(
        description=f"""Review the research report on '{query}' from the synthesis specialist.

        Evaluate strictly:
        1. Are all claims supported by specific evidence?
        2. Are all five required sections present and substantive?
        3. Are there any significant gaps or missing perspectives?
        4. Is the executive summary accurate and impactful?

        Provide specific improvement recommendations if needed.
        End with either "VERDICT: APPROVED" or "VERDICT: NEEDS_REVISION: [reasons]"
        """,
        expected_output="A detailed critique with specific findings and a clear APPROVED or NEEDS_REVISION verdict",
        agent=research_critic,
        context=[synthesis_task],
    )

    crew = Crew(
        agents=[tech_researcher, market_researcher, regulatory_researcher, synthesis_specialist, research_critic],
        tasks=[tech_task, market_task, regulatory_task, synthesis_task, critique_task],
        process=Process.sequential,
        verbose=True,
    )

    return crew


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    query = "solid-state batteries"

    print("\n" + "="*60)
    print("RESEARCH ASSISTANT — CrewAI")
    print(f"Query: {query}")
    print("="*60)

    crew = build_crew(query)
    result = crew.kickoff()

    print("\n" + "="*60)
    print("FINAL RESEARCH REPORT")
    print("="*60)
    print(result)
