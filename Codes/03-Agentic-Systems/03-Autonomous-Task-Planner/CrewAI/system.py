"""
Autonomous Task Planner — CrewAI Implementation
===============================================
System    : 03 — Autonomous Task Planner
Framework : CrewAI
Model     : gemini-2.0-flash via langchain-google-genai

What this demonstrates:
  - CrewAI hierarchical process: manager agent delegates to worker agents
  - Manager plans and oversees; workers execute specific tasks
  - Quality reviewer agent validates outputs
  - CrewAI task context passing for dependency management
"""

import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.3)

GOAL = "Create a comprehensive report on best practices for remote work productivity, covering research, analysis, and actionable recommendations"


# ── Agents ─────────────────────────────────────────────────────────────────────

project_manager = Agent(
    role="Project Manager and Strategic Planner",
    goal="Plan the work, coordinate agents, and ensure the final deliverable meets quality standards",
    backstory="""You are an experienced project manager who excels at breaking down complex goals
    into actionable tasks, delegating effectively, and synthesizing results into coherent deliverables.
    You always start by creating a clear plan before execution begins.""",
    llm=llm,
    verbose=True,
    allow_delegation=True,
)

research_specialist = Agent(
    role="Research Specialist",
    goal="Find, gather, and synthesize relevant information and data on assigned topics",
    backstory="""You are a thorough researcher who finds specific, credible information.
    You never make up data — you present findings with appropriate context and note
    when information is uncertain. Your research is always cited and structured.""",
    llm=llm,
    verbose=True,
)

analyst = Agent(
    role="Strategic Analyst",
    goal="Analyze research findings and extract actionable insights and recommendations",
    backstory="""You are an expert analyst who transforms raw research into structured insights.
    You identify patterns, extract implications, and develop concrete recommendations
    based on evidence. Your analysis is always logical and well-reasoned.""",
    llm=llm,
    verbose=True,
)

writer = Agent(
    role="Professional Writer and Report Specialist",
    goal="Transform research and analysis into well-structured, clear, and compelling reports",
    backstory="""You are a professional writer specializing in business and research reports.
    You excel at organizing information logically, writing clearly for executive audiences,
    and creating deliverables that are both comprehensive and easy to read.""",
    llm=llm,
    verbose=True,
)

quality_reviewer = Agent(
    role="Quality Assurance Reviewer",
    goal="Review final deliverables for completeness, accuracy, and professional quality",
    backstory="""You are a demanding quality reviewer who ensures deliverables meet high standards.
    You check for logical consistency, completeness, citation quality, and actionability.
    You provide specific, constructive feedback when quality standards are not met.""",
    llm=llm,
    verbose=True,
)


# ── Tasks ──────────────────────────────────────────────────────────────────────

planning_task = Task(
    description=f"""Create a detailed execution plan for: {GOAL}

    The plan should specify:
    1. What information needs to be researched
    2. What analysis needs to be performed
    3. What sections the final report should contain
    4. Any specific data points or examples to find

    Return a structured plan with clear sections and priorities.""",
    expected_output="A structured execution plan with 4-6 specific research and writing tasks",
    agent=project_manager,
)

research_task = Task(
    description=f"""Research remote work productivity best practices comprehensively.

    Based on the plan from the project manager, gather:
    - Statistical data on remote work productivity (specific studies and numbers)
    - Common challenges and their frequencies
    - Best practices that have proven results
    - Tools and technologies that support remote teams
    - Examples from companies that have implemented successful remote work

    Be specific — cite numbers, studies, and company examples.""",
    expected_output="A comprehensive research document with specific data points, statistics, and examples",
    agent=research_specialist,
    context=[planning_task],
)

analysis_task = Task(
    description="""Analyze the research findings on remote work productivity.

    Develop:
    1. Key patterns and themes from the data
    2. The most impactful best practices (ranked by evidence quality)
    3. Common failure modes and how to avoid them
    4. A framework for assessing remote work readiness
    5. Specific, actionable recommendations for managers and employees""",
    expected_output="Structured analysis with prioritized insights and concrete recommendations",
    agent=analyst,
    context=[research_task],
)

writing_task = Task(
    description="""Write a comprehensive report on remote work productivity best practices.

    Use the research and analysis from previous tasks. Structure:
    1. Executive Summary (3-4 sentences)
    2. Current State of Remote Work (with statistics)
    3. Key Productivity Best Practices (with evidence)
    4. Common Pitfalls and How to Avoid Them
    5. Tools and Technologies
    6. Actionable Recommendations (separated for managers vs employees)
    7. Conclusion

    Target audience: business leaders and managers. Professional tone. ~600 words.""",
    expected_output="A complete, well-structured 600-word report with all seven sections",
    agent=writer,
    context=[research_task, analysis_task],
)

review_task = Task(
    description="""Review the final remote work productivity report for quality.

    Check:
    1. Are all 7 required sections present and substantive?
    2. Are statistics and examples specific (not vague generalizations)?
    3. Are recommendations concrete and actionable?
    4. Is the executive summary accurate and compelling?
    5. Professional tone maintained throughout?

    Provide:
    - Overall quality assessment
    - Specific strengths
    - Any gaps or improvements needed
    - Final verdict: APPROVED or NEEDS_REVISION""",
    expected_output="Quality review with specific feedback and APPROVED or NEEDS_REVISION verdict",
    agent=quality_reviewer,
    context=[writing_task],
)


# ── Crew and main ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "="*60)
    print("AUTONOMOUS TASK PLANNER — CrewAI")
    print(f"Goal: {GOAL}")
    print("="*60)

    crew = Crew(
        agents=[project_manager, research_specialist, analyst, writer, quality_reviewer],
        tasks=[planning_task, research_task, analysis_task, writing_task, review_task],
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff()

    print("\n" + "="*60)
    print("FINAL OUTPUT")
    print("="*60)
    print(result)
