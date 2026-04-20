"""
Code Review System — Google ADK Implementation
==============================================
System    : 04 — Code Review System
Framework : Google Agent Development Kit (ADK)
Model     : gemini-2.0-flash

What this demonstrates:
  - ADK ParallelAgent for concurrent code reviews
  - ADK SequentialAgent composing parallel reviews + aggregation + critique
  - FunctionTool for severity classification utility
  - Natural ADK composition: ParallelAgent nested inside SequentialAgent

Architecture:
  SequentialAgent(
    ParallelAgent(static_agent, security_agent, style_agent, complexity_agent),
    aggregator_agent,
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
+            for j in range(len(d)):  # O(n²)
+                pass  # TODO: not implemented
+    return d
'''


# ── Tools ──────────────────────────────────────────────────────────────────────

def classify_issue_severity(issue_description: str, issue_type: str) -> dict:
    """Classify the severity of a code issue based on its type and description.

    Args:
        issue_description: Description of the code issue
        issue_type: Category of issue (security, bug, style, complexity)

    Returns:
        dict with severity level and reasoning
    """
    # Heuristic severity classification
    critical_keywords = ["injection", "secret", "password", "token", "credential", "auth bypass"]
    high_keywords = ["error handling", "null", "crash", "data loss", "exception"]
    medium_keywords = ["complexity", "performance", "naming", "duplicate"]

    desc_lower = issue_description.lower()
    if issue_type == "security" or any(k in desc_lower for k in critical_keywords):
        severity = "Critical"
        reason = "Security vulnerabilities require immediate attention"
    elif any(k in desc_lower for k in high_keywords):
        severity = "High"
        reason = "Could cause runtime failures or data issues"
    elif any(k in desc_lower for k in medium_keywords):
        severity = "Medium"
        reason = "Affects code quality and maintainability"
    else:
        severity = "Low"
        reason = "Style or minor quality issue"

    return {"severity": severity, "reasoning": reason}


# ── Specialist review agents ────────────────────────────────────────────────────

static_agent = Agent(
    name="static_analysis_reviewer",
    model="gemini-2.0-flash",
    description="Finds bugs, missing error handling, and logic errors",
    instruction="""You are a static analysis specialist. Review the code for:
    - Missing error handling (no try/except, no return value checks)
    - Potential null/None access
    - Logic errors and unreachable code
    - Incomplete implementations (TODO markers, pass without implementation)

    Use classify_issue_severity to rate each finding.

    Format each finding:
    [STATIC] ISSUE: [name] | SEVERITY: [x] | LOCATION: [fn] | FIX: [solution]""",
    tools=[FunctionTool(classify_issue_severity)],
)

security_agent = Agent(
    name="security_reviewer",
    model="gemini-2.0-flash",
    description="Finds security vulnerabilities and risks",
    instruction="""You are a security review specialist. Review the code for:
    - SQL injection vulnerabilities (string concatenation in queries)
    - Hardcoded secrets, API keys, passwords
    - Insecure data handling
    - Missing input validation

    Use classify_issue_severity with issue_type="security" for all findings.

    Format each finding:
    [SECURITY] ISSUE: [name] | SEVERITY: [x] | OWASP: [category] | FIX: [remediation]""",
    tools=[FunctionTool(classify_issue_severity)],
)

style_agent = Agent(
    name="style_reviewer",
    model="gemini-2.0-flash",
    description="Finds naming, documentation, and style issues",
    instruction="""You are a code style specialist. Review the code for:
    - Poor naming (single letters, abbreviations, unclear names)
    - Missing docstrings and comments
    - Magic numbers and literals
    - Code formatting issues

    Use classify_issue_severity for each finding.

    Format each finding:
    [STYLE] ISSUE: [name] | SEVERITY: [x] | LOCATION: [fn] | IMPROVEMENT: [suggestion]""",
    tools=[FunctionTool(classify_issue_severity)],
)

complexity_agent = Agent(
    name="complexity_reviewer",
    model="gemini-2.0-flash",
    description="Finds complexity issues and recommends refactoring",
    instruction="""You are a complexity analysis specialist. Review the code for:
    - Nested loops (O(n²) or worse)
    - High cyclomatic complexity (deeply nested conditions)
    - Code smells (unnecessary complexity, poor abstractions)
    - Performance issues

    Use classify_issue_severity for each finding.

    Format each finding:
    [COMPLEXITY] ISSUE: [name] | SEVERITY: [x] | BIG-O: [complexity] | REFACTOR: [approach]""",
    tools=[FunctionTool(classify_issue_severity)],
)

# ── Aggregator and critic ──────────────────────────────────────────────────────

aggregator_agent = Agent(
    name="review_aggregator",
    model="gemini-2.0-flash",
    description="Merges specialist reviews into a structured report",
    instruction="""You are a senior code reviewer merging findings from all specialists.
    Create a structured report:

    # Code Review Report
    ## Summary
    ## Critical Issues (must fix before merge)
    ## High Priority Issues
    ## Medium Priority Issues
    ## Low Priority / Style Suggestions
    ## Positive Observations

    Deduplicate overlapping findings. Rank issues correctly by actual severity.""",
)

critic_agent = Agent(
    name="review_critic",
    model="gemini-2.0-flash",
    description="Evaluates and validates the completeness of the review report",
    instruction="""You are a critical reviewer of code review quality.
    Check if the aggregated report:
    1. Caught all the significant issues in the code
    2. Prioritized them correctly (security issues should be Critical/High)
    3. Provided specific, actionable fixes

    End with:
    VERDICT: APPROVED — if comprehensive and actionable
    VERDICT: NEEDS_REVISION: [what was missed] — if important issues were overlooked""",
)

# ── Compose the system ─────────────────────────────────────────────────────────

parallel_reviews = ParallelAgent(
    name="parallel_code_reviewers",
    description="Four specialist reviewers running in parallel",
    sub_agents=[static_agent, security_agent, style_agent, complexity_agent],
)

code_review_system = SequentialAgent(
    name="code_review_system",
    description="Complete code review: parallel specialists → aggregation → critique",
    sub_agents=[parallel_reviews, aggregator_agent, critic_agent],
)


# ── Runner ──────────────────────────────────────────────────────────────────────

def run_code_review(code_diff: str) -> str:
    session_service = InMemorySessionService()
    runner = InProcessRunner(
        agent=code_review_system,
        session_service=session_service,
        app_name="code_review",
    )
    session = session_service.create_session(app_name="code_review", user_id="u001")

    from google.adk.types import Content, Part
    response = runner.run(
        user_id="u001",
        session_id=session.id,
        new_message=Content(parts=[Part(text=f"Review this code:\n{code_diff}")]),
    )
    return response.text if hasattr(response, 'text') else str(response)


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "="*60)
    print("CODE REVIEW SYSTEM — ADK")
    print("="*60)

    result = run_code_review(SAMPLE_DIFF)

    print("\n" + "="*60)
    print("FINAL CODE REVIEW REPORT")
    print("="*60)
    print(result)
