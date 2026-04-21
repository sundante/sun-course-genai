"""
Research Assistant — LangGraph Implementation
=============================================
System    : 01 — Research Assistant
Framework : LangGraph
Model     : gemini-2.0-flash via langchain-google-genai

What this demonstrates:
  - LangGraph StateGraph for orchestrating a multi-agent system
  - Native parallel execution using Send() for fan-out
  - Conditional edges for the reflexion loop (approve / revise)
  - TypedDict state shared across all nodes
  - Bounded reflexion: iteration counter in state

Architecture:
  orchestrate → [search_technology || search_market || search_regulatory]
              → synthesize → critique → conditional: approved? → END
                                                   → revise → critique (loop)
"""

import os
from typing import TypedDict, Annotated
import operator
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.types import Send

load_dotenv()

# ── State definition ───────────────────────────────────────────────────────────

class ResearchState(TypedDict):
    query: str
    domain_results: Annotated[list[dict], operator.add]  # parallel results accumulate here
    synthesis: str
    critique: str
    iteration: int
    approved: bool
    final_report: str


# ── Mock data ──────────────────────────────────────────────────────────────────

DOMAIN_DATA = {
    "technology": [
        "Toyota plans to commercialize solid-state EV batteries by 2027-2028",
        "2x energy density vs lithium-ion with no liquid electrolyte fire risk",
        "QuantumScape achieved 800+ charge cycles in lab conditions",
        "Key challenge: manufacturing yield rates below 80%",
        "CATL and Samsung SDI both have active solid-state programs",
    ],
    "market": [
        "Global solid-state battery market projected at $8.8B by 2031 (CAGR 36%)",
        "EV sector accounts for 72% of demand; consumer electronics 18%",
        "Japan leads in patents — Toyota holds 1,300+ solid-state battery patents",
        "China government invested $15B in battery R&D since 2020",
        "Key players: Toyota, Samsung SDI, QuantumScape, CATL, Panasonic, Solid Power",
    ],
    "regulatory": [
        "EU Battery Regulation (2023) requires 70% recycled content by 2030",
        "US IRA provides $45/kWh tax credit for domestically manufactured batteries",
        "China GB/T standards updated 2024 to include solid-state safety protocols",
        "UN Transportation of Dangerous Goods regulations updated for solid electrolytes",
        "Japan NITE certification pathway for solid-state cells established 2023",
    ],
}

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.3)

MAX_ITERATIONS = 2


# ── Graph nodes ────────────────────────────────────────────────────────────────

def orchestrate(state: ResearchState) -> dict:
    """Orchestrator: sets up the parallel search fan-out."""
    print(f"\n[Orchestrator] Query: '{state['query']}'")
    print("[Orchestrator] Dispatching parallel searches...")
    return {}


def search_domain(state: dict) -> dict:
    """Generic domain search node — receives {query, domain} from Send()."""
    domain = state["domain"]
    query = state["query"]

    findings = DOMAIN_DATA.get(domain, ["No data available"])
    summary = llm.invoke([
        SystemMessage(content=f"You are a {domain} research specialist. Summarize these findings into 3-5 key insights."),
        HumanMessage(content=f"Query: {query}\n\nFindings:\n" + "\n".join(f"- {f}" for f in findings))
    ]).content

    print(f"[Search Agent: {domain}] Complete")
    return {"domain_results": [{"domain": domain, "summary": summary, "raw": findings}]}


def synthesize(state: ResearchState) -> dict:
    """Synthesis agent: merges domain results into a structured report."""
    print(f"\n[Synthesis Agent] Creating report (iteration {state.get('iteration', 0) + 1})...")

    context = "\n\n".join([
        f"=== {r['domain'].upper()} ===\n{r['summary']}"
        for r in state["domain_results"]
    ])

    revision_note = ""
    if state.get("critique"):
        revision_note = f"\n\nAddress this critique:\n{state['critique']}"

    report = llm.invoke([
        SystemMessage(content="""Create a structured research report with sections:
        1. Executive Summary
        2. Technology Landscape
        3. Market Analysis
        4. Regulatory Environment
        5. Key Insights and Implications
        Be specific and cite evidence from the provided findings."""),
        HumanMessage(content=f"Query: {state['query']}\n\nResearch:\n{context}{revision_note}")
    ]).content

    return {"synthesis": report, "iteration": state.get("iteration", 0) + 1}


def critique(state: ResearchState) -> dict:
    """Critic agent: evaluates the synthesis report."""
    print(f"[Critic Agent] Evaluating report...")

    evaluation = llm.invoke([
        SystemMessage(content="""Evaluate this research report strictly.
        Return format:
        VERDICT: APPROVED or NEEDS_REVISION
        ISSUES (if NEEDS_REVISION): list specific gaps or unsupported claims
        Only approve if genuinely comprehensive."""),
        HumanMessage(content=f"Query: {state['query']}\n\nReport:\n{state['synthesis']}")
    ]).content

    approved = "VERDICT: APPROVED" in evaluation
    print(f"[Critic Agent] Verdict: {'APPROVED' if approved else 'NEEDS_REVISION'}")
    return {"critique": evaluation, "approved": approved}


def finalize(state: ResearchState) -> dict:
    """Final node: wraps up the approved report."""
    print("[Orchestrator] Report approved — task complete")
    return {"final_report": state["synthesis"]}


# ── Conditional routing ────────────────────────────────────────────────────────

def should_revise(state: ResearchState) -> str:
    """Route: revise if not approved and within iteration limit."""
    if state["approved"]:
        return "finalize"
    if state["iteration"] >= MAX_ITERATIONS:
        print(f"[Orchestrator] Max iterations reached — finalizing best report")
        return "finalize"
    return "synthesize"


# ── Fan-out edge ───────────────────────────────────────────────────────────────

def dispatch_searches(state: ResearchState) -> list[Send]:
    """Return Send() objects to trigger parallel domain search nodes."""
    domains = ["technology", "market", "regulatory"]
    return [
        Send("search_domain", {"query": state["query"], "domain": domain})
        for domain in domains
    ]


# ── Build the graph ────────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    graph = StateGraph(ResearchState)

    graph.add_node("orchestrate", orchestrate)
    graph.add_node("search_domain", search_domain)
    graph.add_node("synthesize", synthesize)
    graph.add_node("critique", critique)
    graph.add_node("finalize", finalize)

    graph.set_entry_point("orchestrate")

    # Fan-out: orchestrate → parallel search_domain nodes
    graph.add_conditional_edges("orchestrate", dispatch_searches, ["search_domain"])

    # After all parallel searches complete, synthesize
    graph.add_edge("search_domain", "synthesize")
    graph.add_edge("synthesize", "critique")

    # Conditional: approved → finalize, else → synthesize (revise)
    graph.add_conditional_edges("critique", should_revise, {
        "finalize": "finalize",
        "synthesize": "synthesize",
    })

    graph.add_edge("finalize", END)

    return graph.compile()


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = build_graph()

    initial_state = {
        "query": "solid-state batteries",
        "domain_results": [],
        "synthesis": "",
        "critique": "",
        "iteration": 0,
        "approved": False,
        "final_report": "",
    }

    print("\n" + "="*60)
    print("RESEARCH ASSISTANT — LangGraph")
    print("="*60)

    final_state = app.invoke(initial_state)

    print("\n" + "="*60)
    print("FINAL RESEARCH REPORT")
    print("="*60)
    print(final_state["final_report"])
