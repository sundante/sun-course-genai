"""
Adversarial Debate Architecture — Google ADK
Pattern: Proposer sub-agent → Critic sub-agent → Judge synthesizes

The moderator agent orchestrates the debate:
- delegates to proposer_agent and critic_agent in turn
- synthesizes both arguments into a final verdict
"""
import asyncio
import os
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

load_dotenv()
assert os.getenv("GOOGLE_API_KEY"), "Set GOOGLE_API_KEY in .env"


proposer_agent = Agent(
    name="travel_proposer",
    model="gemini-2.0-flash",
    description="Makes the strongest case FOR a travel claim. Use when you need arguments supporting a claim.",
    instruction="""You are a passionate travel advocate. When given a claim:
1. Make the STRONGEST possible case FOR it using 3 specific arguments.
2. Be persuasive and specific. 150-200 words.
3. Return your argument clearly labeled 'FOR: [your argument]'""",
    tools=[],
)

critic_agent = Agent(
    name="travel_critic",
    model="gemini-2.0-flash",
    description="Argues AGAINST a travel claim and finds weaknesses. Use when you need counterarguments.",
    instruction="""You are a rigorous travel skeptic. When given a claim and a FOR argument:
1. Argue AGAINST the claim, challenging the specific points made.
2. Find real weaknesses and alternatives. 150-200 words.
3. Return your argument labeled 'AGAINST: [your argument]'""",
    tools=[],
)

moderator_agent = Agent(
    name="debate_moderator",
    model="gemini-2.0-flash",
    description="Moderates a travel debate: collects both sides and delivers a scored verdict.",
    instruction="""You are a debate moderator. When given a claim to debate:

1. Ask travel_proposer to argue FOR the claim.
2. Ask travel_critic to argue AGAINST the claim (share the proposer's argument).
3. Synthesize both into a final verdict:

   ## Debate: [Claim]

   ### FOR
   [proposer's argument]

   ### AGAINST
   [critic's argument]

   ### Verdict
   - FOR score: X/10
   - AGAINST score: X/10
   - Stronger side: FOR/AGAINST
   - Key insight: [one sentence]
   - Conclusion: [2-3 sentences]""",
    sub_agents=[proposer_agent, critic_agent],
)


async def run_debate(claim: str) -> str:
    session_service = InMemorySessionService()
    session = await session_service.create_session(app_name="debate_moderator", user_id="u1")
    runner = InMemoryRunner(agent=moderator_agent, session_service=session_service)
    query = f"Debate this claim: '{claim}'"

    print(f"Claim: {claim}\n")
    final = ""
    async for event in runner.run_async(
        user_id=session.user_id, session_id=session.id,
        new_message=genai_types.Content(role="user", parts=[genai_types.Part(text=query)]),
    ):
        if event.is_final_response() and event.content:
            for part in event.content.parts:
                if part.text: final += part.text
    return final


if __name__ == "__main__":
    result = asyncio.run(run_debate("Tokyo is the best travel destination for a one-week trip"))
    print(result)
