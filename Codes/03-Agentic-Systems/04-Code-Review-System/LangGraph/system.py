"""
Code Review System — LangGraph Implementation
=============================================
System    : 04 — Code Review System
Framework : LangGraph
Model     : gemini-2.0-flash via langchain-google-genai

What this demonstrates:
  - Parallel fan-out using Send() to specialized review agents
  - Annotated list state for accumulating parallel results
  - Aggregation node merges and deduplicates findings
  - Reflexion loop: critic evaluates aggregated report
  - Conditional edge: approve or request revision

Architecture:
  orchestrate → [static_review || security_review || style_review || complexity_review]
              → aggregate → critique → [approved: finalize | revise: aggregate]
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

# ── Sample code with intentional issues for review ────────────────────────────

SAMPLE_DIFF = '''
+def get_user_data(user_id, db_connection):
+    query = "SELECT * FROM users WHERE id = " + user_id  # SQL injection risk
+    result = db_connection.execute(query)
+    data = result.fetchall()
+    return data  # Returns raw DB rows — no error handling
+
+def process_usr(d, t):  # Poor naming: 'usr', 'd', 't'
+    API_KEY = "sk-1234abcd5678"  # Hardcoded secret
+    if t == "premium":
+        for i in range(len(d)):      # Could use enumerate()
+            for j in range(len(d)):  # O(n²) — nested loop on same data
+                if d[i]["score"] > d[j]["score"]:
+                    pass  # TODO: implement swap logic
+    return d
'''


# ── State ──────────────────────────────────────────────────────────────────────

class ReviewState(TypedDict):
    code_diff: str
    review_findings: Annotated[list[dict], operator.add]  # accumulates parallel reviews
    aggregated_report: str
    critique: str
    iteration: int
    approved: bool
    final_report: str


llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.2)
MAX_ITERATIONS = 2


# ── Review node (shared by all reviewers, dispatched with different focus) ─────

def run_specialized_review(state: dict) -> dict:
    """Single review node — receives {code_diff, review_type} from Send()."""
    review_type = state["review_type"]
    code_diff = state["code_diff"]

    instructions = {
        "static_analysis": """Review for: null/undefined checks, error handling, exception safety,
        off-by-one errors, logic errors, unreachable code. For each issue: describe the problem,
        location, severity (Critical/High/Medium/Low), and suggested fix.""",

        "security": """Review for: SQL injection, XSS, command injection, hardcoded secrets/keys,
        insecure direct object references, missing authentication checks, sensitive data exposure.
        For each issue: describe the vulnerability, CVE/OWASP category if applicable, severity, and fix.""",

        "style": """Review for: naming conventions (functions, variables, classes), code formatting,
        missing or inadequate documentation, magic numbers, overly long functions, dead code.
        For each issue: describe the style problem, location, and improvement.""",

        "complexity": """Review for: cyclomatic complexity (nested conditions/loops), function length,
        code duplication, poor abstractions, premature optimization, unnecessary complexity.
        For each issue: describe the complexity problem, refactoring recommendation.""",
    }

    instruction = instructions.get(review_type, "Perform a general code review.")

    print(f"[{review_type.replace('_', ' ').title()} Agent] Reviewing...")

    findings = llm.invoke([
        SystemMessage(content=f"""You are a specialized code reviewer focused on {review_type.replace('_', ' ')}.
        {instruction}
        Return a structured list of findings. If no issues found in your category, say "No issues found."
        Format each finding as:
        ISSUE: [title]
        SEVERITY: Critical|High|Medium|Low
        LOCATION: [function/line]
        DESCRIPTION: [what's wrong]
        FIX: [how to fix it]
        ---"""),
        HumanMessage(content=f"Code diff to review:\n{code_diff}")
    ]).content

    print(f"[{review_type.replace('_', ' ').title()} Agent] Complete")
    return {"review_findings": [{"reviewer": review_type, "findings": findings}]}


# ── Other nodes ────────────────────────────────────────────────────────────────

def orchestrate(state: ReviewState) -> dict:
    """Orchestrator: dispatches parallel reviews."""
    print(f"\n[Orchestrator] Dispatching 4 parallel code reviews...")
    return {}


def aggregate(state: ReviewState) -> dict:
    """Aggregator: merges findings from all reviewers into a structured report."""
    print(f"\n[Aggregator] Merging {len(state['review_findings'])} review streams...")

    all_findings = "\n\n".join([
        f"=== {r['reviewer'].upper()} REVIEW ===\n{r['findings']}"
        for r in state["review_findings"]
    ])

    revision_note = ""
    if state.get("critique"):
        revision_note = f"\n\nPrevious critique to address:\n{state['critique']}"

    report = llm.invoke([
        SystemMessage(content="""You are a senior code reviewer. Merge all findings into a structured report:

        # Code Review Report

        ## Summary
        [2-3 sentence overview of code quality]

        ## Critical Issues (must fix before merge)
        [list with explanation and fix]

        ## High Priority Issues
        [list with explanation and fix]

        ## Medium Priority Issues
        [list]

        ## Low Priority / Style Suggestions
        [list]

        ## Positive Observations
        [what the code does well]

        Deduplicate issues found by multiple reviewers. Prioritize accurately."""),
        HumanMessage(content=f"Individual reviews:\n{all_findings}{revision_note}")
    ]).content

    return {"aggregated_report": report, "iteration": state.get("iteration", 0) + 1}


def critique_report(state: ReviewState) -> dict:
    """Critic: evaluates the aggregated review report."""
    print(f"[Critic] Evaluating review report...")

    evaluation = llm.invoke([
        SystemMessage(content="""Evaluate this code review report. Reply with:
        VERDICT: APPROVED
        or
        VERDICT: NEEDS_REVISION
        ISSUES: [specific gaps — missing issue types, wrong priorities, unclear fixes]
        Only approve if the report is comprehensive and actionable."""),
        HumanMessage(content=f"Code reviewed:\n{state['code_diff']}\n\nReview report:\n{state['aggregated_report']}")
    ]).content

    approved = "VERDICT: APPROVED" in evaluation
    print(f"[Critic] Verdict: {'APPROVED' if approved else 'NEEDS_REVISION'}")
    return {"critique": evaluation, "approved": approved}


def finalize(state: ReviewState) -> dict:
    """Final node: publish the approved report."""
    print("[Orchestrator] Report approved")
    return {"final_report": state["aggregated_report"]}


# ── Routing ────────────────────────────────────────────────────────────────────

def dispatch_reviews(state: ReviewState) -> list[Send]:
    review_types = ["static_analysis", "security", "style", "complexity"]
    return [
        Send("run_specialized_review", {"code_diff": state["code_diff"], "review_type": rt})
        for rt in review_types
    ]


def after_critique(state: ReviewState) -> str:
    if state["approved"] or state["iteration"] >= MAX_ITERATIONS:
        return "finalize"
    return "aggregate"


# ── Build graph ────────────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    graph = StateGraph(ReviewState)

    graph.add_node("orchestrate", orchestrate)
    graph.add_node("run_specialized_review", run_specialized_review)
    graph.add_node("aggregate", aggregate)
    graph.add_node("critique_report", critique_report)
    graph.add_node("finalize", finalize)

    graph.set_entry_point("orchestrate")
    graph.add_conditional_edges("orchestrate", dispatch_reviews, ["run_specialized_review"])
    graph.add_edge("run_specialized_review", "aggregate")
    graph.add_edge("aggregate", "critique_report")
    graph.add_conditional_edges("critique_report", after_critique, {
        "finalize": "finalize",
        "aggregate": "aggregate",
    })
    graph.add_edge("finalize", END)

    return graph.compile()


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = build_graph()

    print("\n" + "="*60)
    print("CODE REVIEW SYSTEM — LangGraph")
    print("="*60)

    initial_state = ReviewState(
        code_diff=SAMPLE_DIFF,
        review_findings=[],
        aggregated_report="",
        critique="",
        iteration=0,
        approved=False,
        final_report="",
    )

    final_state = app.invoke(initial_state)

    print("\n" + "="*60)
    print("FINAL CODE REVIEW REPORT")
    print("="*60)
    print(final_state["final_report"])
