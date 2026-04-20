"""
Research Assistant — LangChain Implementation
==============================================
System    : 01 — Research Assistant
Framework : LangChain (LCEL)
Model     : gemini-2.0-flash via langchain-google-genai

What this demonstrates:
  - Orchestrator-Subagent pattern with LangChain
  - Parallel fan-out to three domain-specific search agents
  - Reflexion loop: critic evaluates synthesis, synthesis revises
  - Structured state passed between agents via Python dicts
  - Bounded autonomy: max_iterations on the critique loop

Architecture:
  Orchestrator → [Search A || Search B || Search C] → Synthesis → Critic → (revise if needed)
"""

import os
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

# ── Mock data representing domain-specific search results ──────────────────────

DOMAIN_DATA = {
    "technology": {
        "solid-state batteries": [
            "Toyota plans to commercialize solid-state EV batteries by 2027-2028",
            "Solid-state batteries offer 2x energy density vs lithium-ion with no liquid electrolyte fire risk",
            "QuantumScape (backed by VW) achieved 800+ charge cycles in lab conditions",
            "Key challenge: manufacturing at scale — current yield rates below 80%",
            "CATL and Samsung SDI both have active solid-state programs",
        ],
        "default": ["No technology data found for this query"]
    },
    "market": {
        "solid-state batteries": [
            "Global solid-state battery market projected at $8.8B by 2031 (CAGR 36%)",
            "EV sector accounts for 72% of demand; consumer electronics 18%",
            "Japan leads in patents (Toyota holds 1,300+ solid-state battery patents)",
            "China government invested $15B in battery R&D since 2020",
            "Key players: Toyota, Samsung SDI, QuantumScape, CATL, Panasonic, Solid Power",
        ],
        "default": ["No market data found for this query"]
    },
    "regulatory": {
        "solid-state batteries": [
            "EU Battery Regulation (2023) requires 70% recycled content by 2030",
            "US IRA provides $45/kWh tax credit for domestically manufactured batteries",
            "China GB/T standards updated 2024 to include solid-state safety protocols",
            "UN Transportation of Dangerous Goods regulations updated for solid electrolytes",
            "Japan NITE certification pathway for solid-state cells established 2023",
        ],
        "default": ["No regulatory data found for this query"]
    }
}


@tool
def search_technology(query: str) -> dict:
    """Search for technology and R&D information about the given topic.

    Use this for: technical specifications, research progress, engineering challenges,
    patents, and scientific developments. Returns structured technology findings.
    """
    key = query.lower().strip()
    results = DOMAIN_DATA["technology"].get(key, DOMAIN_DATA["technology"]["default"])
    return {"domain": "technology", "query": query, "findings": results, "count": len(results)}


@tool
def search_market(query: str) -> dict:
    """Search for market data, business intelligence, and competitive landscape.

    Use this for: market size, growth projections, company positions, investment data,
    and commercial developments. Returns structured market findings.
    """
    key = query.lower().strip()
    results = DOMAIN_DATA["market"].get(key, DOMAIN_DATA["market"]["default"])
    return {"domain": "market", "query": query, "findings": results, "count": len(results)}


@tool
def search_regulatory(query: str) -> dict:
    """Search for regulatory, policy, and compliance information.

    Use this for: regulations, standards, government policies, compliance requirements,
    and legal frameworks. Returns structured regulatory findings.
    """
    key = query.lower().strip()
    results = DOMAIN_DATA["regulatory"].get(key, DOMAIN_DATA["regulatory"]["default"])
    return {"domain": "regulatory", "query": query, "findings": results, "count": len(results)}


# ── LLM setup ──────────────────────────────────────────────────────────────────

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.3)


# ── Agent functions ────────────────────────────────────────────────────────────

def run_search_agent(domain: str, query: str) -> dict:
    """Run a single domain search agent."""
    tool_map = {
        "technology": search_technology,
        "market": search_market,
        "regulatory": search_regulatory,
    }
    tool_fn = tool_map[domain]
    result = tool_fn.invoke({"query": query})

    # LLM summarizes and structures the raw results
    summary = llm.invoke([
        SystemMessage(content=f"You are a {domain} research specialist. Summarize these findings into 3-5 key insights relevant to the research query."),
        HumanMessage(content=f"Query: {query}\n\nRaw findings:\n" + "\n".join(f"- {f}" for f in result["findings"]))
    ]).content

    return {"domain": domain, "findings": result["findings"], "summary": summary}


def run_parallel_search(query: str) -> dict:
    """Fan-out: run three domain search agents in parallel."""
    print(f"\n[Orchestrator] Starting parallel search for: '{query}'")

    domains = ["technology", "market", "regulatory"]

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {domain: executor.submit(run_search_agent, domain, query) for domain in domains}
        results = {domain: future.result() for domain, future in futures.items()}

    print(f"[Orchestrator] All {len(domains)} domain searches complete")
    return results


def run_synthesis_agent(query: str, search_results: dict, critique: str = "") -> str:
    """Synthesis agent: merge search results into a structured report."""
    revision_context = ""
    if critique:
        revision_context = f"\n\nPrevious critique to address:\n{critique}\n\nRevise the report to address all critique points."

    context = "\n\n".join([
        f"=== {domain.upper()} FINDINGS ===\n{data['summary']}"
        for domain, data in search_results.items()
    ])

    report = llm.invoke([
        SystemMessage(content="""You are a research synthesis specialist.
        Create a structured research report with these sections:
        1. Executive Summary (2-3 sentences)
        2. Technology Landscape
        3. Market Analysis
        4. Regulatory Environment
        5. Key Insights and Implications

        Be specific, cite the evidence from the provided findings."""),
        HumanMessage(content=f"Research Query: {query}\n\nDomain Research:\n{context}{revision_context}")
    ]).content

    return report


def run_critic_agent(query: str, report: str) -> dict:
    """Critic agent: evaluate the synthesis report and return critique."""
    evaluation = llm.invoke([
        SystemMessage(content="""You are a critical research reviewer.
        Evaluate the research report strictly. Return your response in this exact format:

        VERDICT: APPROVED or NEEDS_REVISION

        ISSUES (if NEEDS_REVISION):
        - [specific issue 1]
        - [specific issue 2]

        STRENGTHS:
        - [strength 1]

        Be specific. Only approve if the report is genuinely comprehensive and well-supported."""),
        HumanMessage(content=f"Original query: {query}\n\nReport to evaluate:\n{report}")
    ]).content

    approved = "VERDICT: APPROVED" in evaluation
    return {"approved": approved, "critique": evaluation}


def run_research_assistant(query: str, max_iterations: int = 2) -> str:
    """
    Main orchestrator: runs the full research assistant pipeline.

    Flow: parallel search → synthesis → critique → (revise if needed) → final report
    """
    print(f"\n{'='*60}")
    print(f"RESEARCH ASSISTANT — LangChain")
    print(f"Query: {query}")
    print(f"{'='*60}")

    # Step 1: Parallel search (fan-out)
    search_results = run_parallel_search(query)

    # Step 2: Initial synthesis
    print("\n[Synthesis Agent] Creating initial report...")
    report = run_synthesis_agent(query, search_results)

    # Step 3: Reflexion loop (critique + revise)
    for iteration in range(max_iterations):
        print(f"\n[Critic Agent] Evaluating report (iteration {iteration + 1}/{max_iterations})...")
        eval_result = run_critic_agent(query, report)

        if eval_result["approved"]:
            print(f"[Critic Agent] Report APPROVED after {iteration + 1} evaluation(s)")
            break

        print(f"[Critic Agent] Revisions requested")
        print(f"[Synthesis Agent] Revising report...")
        report = run_synthesis_agent(query, search_results, critique=eval_result["critique"])
    else:
        print(f"[Orchestrator] Max iterations reached — returning best available report")

    return report


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    query = "solid-state batteries"

    final_report = run_research_assistant(query)

    print(f"\n{'='*60}")
    print("FINAL RESEARCH REPORT")
    print(f"{'='*60}")
    print(final_report)
