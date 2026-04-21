"""
Adversarial Debate Architecture — CrewAI
Pattern: Proposer agent → Critic agent → Judge agent

Three agents with opposing personas debate a topic.
context= passes each argument forward to the next agent.
"""
import os
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM

load_dotenv()
assert os.getenv("GOOGLE_API_KEY"), "Set GOOGLE_API_KEY in .env"

gemini = LLM(model="gemini/gemini-2.0-flash", temperature=0.3)


class DebateVerdict(BaseModel):
    proposer_score: int = Field(ge=1, le=10, description="Score for the FOR argument")
    critic_score: int = Field(ge=1, le=10, description="Score for the AGAINST argument")
    stronger_side: str = Field(description="'FOR' or 'AGAINST'")
    key_insight: str = Field(description="The single most important insight from the debate")
    final_conclusion: str = Field(description="The judge's final conclusion")


proposer = Agent(
    role="Travel Advocate",
    goal="Make the strongest possible case FOR the given travel claim.",
    backstory="You are a passionate travel writer who loves defending bold travel opinions with compelling evidence.",
    tools=[],
    llm=gemini,
    verbose=False,
)

critic = Agent(
    role="Travel Skeptic",
    goal="Rigorously challenge the travel claim and find its weaknesses.",
    backstory="You are a seasoned traveler who has seen it all. You challenge popular travel myths and expose overhyped destinations.",
    tools=[],
    llm=gemini,
    verbose=False,
)

judge = Agent(
    role="Impartial Travel Judge",
    goal="Evaluate both sides of the debate and deliver a fair, scored verdict.",
    backstory="You are a neutral travel analyst with deep expertise. You evaluate arguments on their merits, not their passion.",
    tools=[],
    llm=gemini,
    verbose=False,
)


def run_debate(claim: str) -> DebateVerdict:
    propose_task = Task(
        description=f"Make the STRONGEST case FOR: '{claim}'. Use 3 specific, compelling arguments. 150-200 words.",
        expected_output="A persuasive FOR argument with 3 specific points.",
        agent=proposer,
    )

    critique_task = Task(
        description=f"Argue AGAINST: '{claim}'. Challenge the proposer's arguments specifically. Find real weaknesses. 150-200 words.",
        expected_output="A rigorous AGAINST argument addressing the proposer's specific points.",
        agent=critic,
        context=[propose_task],
    )

    judge_task = Task(
        description=(
            f"Evaluate both sides of the debate about: '{claim}'. "
            "Score each side 1-10, identify the stronger argument, name the key insight, and give a final conclusion. "
            "Fill all DebateVerdict fields."
        ),
        expected_output="A complete DebateVerdict with scores and conclusion.",
        agent=judge,
        context=[propose_task, critique_task],
        output_pydantic=DebateVerdict,
    )

    crew = Crew(
        agents=[proposer, critic, judge],
        tasks=[propose_task, critique_task, judge_task],
        process=Process.sequential,
        verbose=False,
    )

    result = crew.kickoff()
    return result.pydantic


if __name__ == "__main__":
    claim = "Tokyo is the best travel destination for a one-week trip"
    print(f"Debating: '{claim}'\n")
    verdict = run_debate(claim)

    if verdict:
        print(f"FOR score:   {verdict.proposer_score}/10")
        print(f"AGAINST score: {verdict.critic_score}/10")
        print(f"Stronger side: {verdict.stronger_side}")
        print(f"Key insight: {verdict.key_insight}")
        print(f"\nFinal conclusion:\n{verdict.final_conclusion}")
    else:
        print("No structured verdict — check raw output")
