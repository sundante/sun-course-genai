"""
Code Review System — LangChain Implementation
=============================================
System    : 04 — Code Review System
Framework : LangChain (LCEL)
Model     : gemini-2.0-flash via langchain-google-genai

What this demonstrates:
  - ThreadPoolExecutor for parallel fan-out to 4 reviewer chains
  - LCEL aggregation chain merges parallel results
  - Reflexion loop on the aggregated report
  - Priority-ranked final output
"""

import os
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.2)
MAX_ITERATIONS = 2

SAMPLE_DIFF = '''
+def get_user_data(user_id, db_connection):
+    query = "SELECT * FROM users WHERE id = " + user_id  # SQL injection risk
+    result = db_connection.execute(query)
+    return result.fetchall()  # No error handling
+
+def process_usr(d, t):  # Poor naming
+    API_KEY = "sk-1234abcd5678"  # Hardcoded secret
+    if t == "premium":
+        for i in range(len(d)):
+            for j in range(len(d)):  # O(n²) loop
+                pass  # TODO: not implemented
+    return d
'''

REVIEW_CONFIGS = {
    "static_analysis": "Review for null checks, error handling, logic errors, unreachable code, exception safety",
    "security": "Review for SQL injection, hardcoded secrets, XSS, insecure auth, sensitive data exposure",
    "style": "Review for naming conventions, documentation, magic numbers, code formatting, dead code",
    "complexity": "Review for nested loops, cyclomatic complexity, long functions, code duplication, smells",
}


def run_single_review(review_type: str, code_diff: str) -> dict:
    """Run one specialized code review."""
    instruction = REVIEW_CONFIGS[review_type]
    print(f"[{review_type.replace('_',' ').title()}] Reviewing...")

    findings = llm.invoke([
        SystemMessage(content=f"""You are a specialized code reviewer: {instruction}.
        List each issue with SEVERITY (Critical/High/Medium/Low), LOCATION, DESCRIPTION, and FIX.
        If no issues in your category: say "No issues found."
        Use this format:
        ISSUE: [title]
        SEVERITY: Critical|High|Medium|Low
        LOCATION: [where]
        DESCRIPTION: [problem]
        FIX: [solution]
        ---"""),
        HumanMessage(content=f"Code to review:\n{code_diff}")
    ]).content

    print(f"[{review_type.replace('_',' ').title()}] Done")
    return {"review_type": review_type, "findings": findings}


def run_parallel_reviews(code_diff: str) -> list[dict]:
    """Fan-out: run all 4 reviews in parallel."""
    print("\n[Orchestrator] Starting parallel reviews...")
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {rt: executor.submit(run_single_review, rt, code_diff) for rt in REVIEW_CONFIGS}
        results = [future.result() for future in futures.values()]
    print("[Orchestrator] All reviews complete")
    return results


def aggregate_reviews(code_diff: str, reviews: list[dict], critique: str = "") -> str:
    """Aggregate all reviews into a structured report."""
    print("\n[Aggregator] Merging reviews...")

    all_findings = "\n\n".join([f"=== {r['review_type'].upper()} ===\n{r['findings']}" for r in reviews])
    revision_note = f"\n\nCritique to address:\n{critique}" if critique else ""

    return llm.invoke([
        SystemMessage(content="""Merge all code review findings into a structured report:
        # Code Review Report
        ## Summary
        ## Critical Issues (must fix before merge)
        ## High Priority Issues
        ## Medium Priority Issues
        ## Low Priority / Style Suggestions
        ## Positive Observations
        Deduplicate overlapping findings. Prioritize accurately."""),
        HumanMessage(content=f"Reviews:\n{all_findings}{revision_note}")
    ]).content


def critique_report(code_diff: str, report: str) -> dict:
    """Critique the aggregated report."""
    print("[Critic] Evaluating report...")
    result = llm.invoke([
        SystemMessage(content="""Evaluate this code review report.
        VERDICT: APPROVED
        or
        VERDICT: NEEDS_REVISION
        ISSUES: [what's missing or wrong]
        Only approve if comprehensive and actionable."""),
        HumanMessage(content=f"Code:\n{code_diff}\n\nReport:\n{report}")
    ]).content
    approved = "VERDICT: APPROVED" in result
    print(f"[Critic] {'APPROVED' if approved else 'NEEDS_REVISION'}")
    return {"approved": approved, "critique": result}


def run_code_review(code_diff: str) -> str:
    """Main orchestrator: run the full code review pipeline."""
    print("\n" + "="*60)
    print("CODE REVIEW SYSTEM — LangChain")
    print("="*60)

    # Parallel fan-out
    reviews = run_parallel_reviews(code_diff)

    # Reflexion loop on aggregated report
    report = aggregate_reviews(code_diff, reviews)
    for iteration in range(MAX_ITERATIONS):
        result = critique_report(code_diff, report)
        if result["approved"]:
            print(f"[Critic] Approved after {iteration + 1} evaluation(s)")
            break
        print("[Aggregator] Revising...")
        report = aggregate_reviews(code_diff, reviews, critique=result["critique"])
    else:
        print("[Orchestrator] Max iterations reached")

    return report


if __name__ == "__main__":
    final_report = run_code_review(SAMPLE_DIFF)
    print("\n" + "="*60)
    print("FINAL CODE REVIEW REPORT")
    print("="*60)
    print(final_report)
