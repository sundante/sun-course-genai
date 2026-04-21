"""
Code Review System — CrewAI Implementation
==========================================
System    : 04 — Code Review System
Framework : CrewAI
Model     : gemini-2.0-flash via langchain-google-genai

What this demonstrates:
  - CrewAI with multiple specialist reviewer agents
  - Sequential process where each reviewer contributes in turn
  - Aggregator and critic as final crew members
  - Context threading: each agent builds on prior reviews
"""

import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.2)

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

# ── Agents ─────────────────────────────────────────────────────────────────────

static_reviewer = Agent(
    role="Static Analysis Specialist",
    goal="Find all bugs, error handling issues, and logic errors in the code",
    backstory="""You are a static analysis expert who finds subtle bugs that compilers miss.
    You specialize in null pointer issues, error handling gaps, logic errors, and unreachable code.
    You always provide specific fixes for every issue you find.""",
    llm=llm, verbose=True,
)

security_reviewer = Agent(
    role="Security Review Specialist",
    goal="Find all security vulnerabilities and risks in the code",
    backstory="""You are a security engineer specialized in finding vulnerabilities.
    You think like an attacker — SQL injection, hardcoded secrets, XSS, authentication bypass.
    You classify each issue by OWASP category and provide specific remediation steps.""",
    llm=llm, verbose=True,
)

style_reviewer = Agent(
    role="Code Style and Quality Reviewer",
    goal="Identify style issues, naming problems, and documentation gaps",
    backstory="""You enforce clean code principles: meaningful names, clear documentation,
    no magic numbers, proper formatting, and no dead code. You cite specific style guide rules
    when relevant and provide concrete improvement examples.""",
    llm=llm, verbose=True,
)

complexity_reviewer = Agent(
    role="Complexity and Architecture Reviewer",
    goal="Identify complexity issues and recommend refactoring",
    backstory="""You analyze algorithmic complexity, code smells, and architectural problems.
    You identify O(n²) algorithms, deeply nested code, and poor abstractions.
    You provide specific refactoring recommendations with code examples where helpful.""",
    llm=llm, verbose=True,
)

aggregator = Agent(
    role="Senior Code Review Aggregator",
    goal="Merge all specialist reviews into a clear, prioritized, actionable report",
    backstory="""You are a senior engineer who writes the final code review.
    You merge reviews from multiple specialists, deduplicate findings, and prioritize clearly.
    Your reports are known for being direct, specific, and actionable.""",
    llm=llm, verbose=True,
)

quality_critic = Agent(
    role="Review Quality Critic",
    goal="Ensure the code review is complete, accurate, and actionable",
    backstory="""You ensure code reviews meet the highest standards.
    You check for missed issues, wrong priorities, and unclear guidance.
    You only approve reviews that would genuinely help the developer improve the code.""",
    llm=llm, verbose=True,
)


# ── Build crew ─────────────────────────────────────────────────────────────────

def build_review_crew(code_diff: str) -> Crew:
    static_task = Task(
        description=f"""Perform static analysis on this code diff:
        {code_diff}
        Find: null checks, missing error handling, exception safety, logic errors.
        For each issue: SEVERITY (Critical/High/Medium/Low), LOCATION, DESCRIPTION, FIX.""",
        expected_output="List of static analysis findings with severity, location, description, and fix for each",
        agent=static_reviewer,
    )

    security_task = Task(
        description=f"""Perform security review on this code diff:
        {code_diff}
        Find: SQL injection, hardcoded secrets, XSS, insecure auth, sensitive data exposure.
        For each issue: SEVERITY, OWASP category, DESCRIPTION, REMEDIATION.""",
        expected_output="List of security findings with OWASP categories and specific remediation steps",
        agent=security_reviewer,
    )

    style_task = Task(
        description=f"""Perform style and quality review on this code diff:
        {code_diff}
        Find: naming issues, missing docs, magic numbers, dead code, formatting.
        For each issue: SEVERITY (Low/Medium), LOCATION, DESCRIPTION, IMPROVEMENT.""",
        expected_output="List of style and quality issues with specific improvement suggestions",
        agent=style_reviewer,
    )

    complexity_task = Task(
        description=f"""Perform complexity review on this code diff:
        {code_diff}
        Find: algorithmic complexity (O(n²) etc.), deeply nested code, code smells, poor abstractions.
        For each issue: SEVERITY, DESCRIPTION, REFACTORING_RECOMMENDATION.""",
        expected_output="List of complexity issues with specific refactoring recommendations",
        agent=complexity_reviewer,
    )

    aggregate_task = Task(
        description="""Merge all four code review findings into one structured report.

        Structure:
        # Code Review Report
        ## Summary
        ## Critical Issues (block merge)
        ## High Priority Issues
        ## Medium Priority Issues
        ## Low Priority / Style
        ## Positive Observations

        Deduplicate overlapping findings. Rank by priority correctly.""",
        expected_output="Complete structured code review report with all sections populated and findings properly prioritized",
        agent=aggregator,
        context=[static_task, security_task, style_task, complexity_task],
    )

    critic_task = Task(
        description="""Review the aggregated code review report for quality and completeness.

        Check: all significant issues found, priorities correct, fixes specific and actionable.
        Missing any category of issues?

        Provide your assessment and end with:
        VERDICT: APPROVED — if report is comprehensive and actionable
        VERDICT: NEEDS_REVISION: [specific gaps] — if important issues were missed""",
        expected_output="Quality assessment with specific findings and APPROVED or NEEDS_REVISION verdict",
        agent=quality_critic,
        context=[aggregate_task],
    )

    return Crew(
        agents=[static_reviewer, security_reviewer, style_reviewer, complexity_reviewer, aggregator, quality_critic],
        tasks=[static_task, security_task, style_task, complexity_task, aggregate_task, critic_task],
        process=Process.sequential,
        verbose=True,
    )


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "="*60)
    print("CODE REVIEW SYSTEM — CrewAI")
    print("="*60)

    crew = build_review_crew(SAMPLE_DIFF)
    result = crew.kickoff()

    print("\n" + "="*60)
    print("FINAL CODE REVIEW REPORT")
    print("="*60)
    print(result)
