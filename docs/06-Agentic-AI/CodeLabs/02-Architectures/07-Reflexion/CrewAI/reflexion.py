"""
Reflexion Architecture — CrewAI
Pattern: Generator agent → Critic agent → Rewriter agent (conditional)

The critic scores the draft. If score < threshold, the rewriter improves it.
CrewAI models this as 3 chained tasks with context passing.
"""
import os
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM

load_dotenv()
assert os.getenv("GOOGLE_API_KEY"), "Set GOOGLE_API_KEY in .env"

gemini = LLM(model="gemini/gemini-2.0-flash", temperature=0)


# ── Output schema ─────────────────────────────────────────────────────────────

class ReflexionOutput(BaseModel):
    final_recommendation: str = Field(description="The final polished recommendation")
    quality_score: int = Field(ge=1, le=10, description="Final quality score 1-10")
    improvements_made: str = Field(description="What was improved from draft to final")


# ── Agents ────────────────────────────────────────────────────────────────────

generator = Agent(
    role="Travel Recommendation Writer",
    goal="Write a comprehensive travel recommendation covering attractions, weather, safety, and best time to visit.",
    backstory="You are a travel writer who produces detailed, specific recommendations that travelers love.",
    tools=[],
    llm=gemini,
    verbose=False,
)

critic = Agent(
    role="Travel Content Editor",
    goal="Evaluate travel recommendations and identify specific gaps or weaknesses.",
    backstory="You are a rigorous travel editor with high standards. You always find what's missing and score objectively.",
    tools=[],
    llm=gemini,
    verbose=False,
)

rewriter = Agent(
    role="Travel Recommendation Rewriter",
    goal="Improve a draft recommendation by addressing all critic feedback.",
    backstory="You take rough drafts and polish them into high-quality recommendations by fixing every identified gap.",
    tools=[],
    llm=gemini,
    verbose=False,
)


# ── Crew builder ──────────────────────────────────────────────────────────────

def build_crew(destination: str) -> Crew:
    generate_task = Task(
        description=f"Write a travel recommendation for {destination}. Include: top 3 attractions, best time to visit, weather, safety tips. Be specific.",
        expected_output=f"A comprehensive travel recommendation for {destination}.",
        agent=generator,
    )

    critique_task = Task(
        description=(
            f"Evaluate the travel recommendation for {destination}. "
            "Score it 1-10 based on: specificity of attractions (3pts), weather info (2pts), safety info (2pts), detail/length (3pts). "
            "List all specific gaps."
        ),
        expected_output="A critique with a score and specific list of gaps.",
        agent=critic,
        context=[generate_task],
    )

    rewrite_task = Task(
        description=(
            f"Rewrite the travel recommendation for {destination} addressing ALL gaps identified by the critic. "
            "Produce a ReflexionOutput with the final recommendation, quality score, and a summary of improvements made."
        ),
        expected_output="A complete ReflexionOutput with final recommendation and score.",
        agent=rewriter,
        context=[generate_task, critique_task],
        output_pydantic=ReflexionOutput,
    )

    return Crew(
        agents=[generator, critic, rewriter],
        tasks=[generate_task, critique_task, rewrite_task],
        process=Process.sequential,
        verbose=False,
    )


if __name__ == "__main__":
    destination = "Tokyo"
    print(f"Running reflexion loop for: {destination}\n")

    crew = build_crew(destination)
    result = crew.kickoff()
    output: ReflexionOutput = result.pydantic

    if output:
        print(f"Quality score: {output.quality_score}/10")
        print(f"Improvements: {output.improvements_made}")
        print(f"\nFinal Recommendation:\n{output.final_recommendation}")
    else:
        print(result.raw)
