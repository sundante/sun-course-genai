"""
Adversarial Debate Architecture — LangChain
Pattern: Proposer → Critic → Judge

Three LCEL chains with opposing personas debate a topic.
The judge receives both arguments and delivers a final verdict.
"""
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()
assert os.getenv("GOOGLE_API_KEY"), "Set GOOGLE_API_KEY in .env"

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.3)
parser = StrOutputParser()


# ── Proposer chain ────────────────────────────────────────────────────────────

proposer_chain = (
    ChatPromptTemplate.from_messages([
        ("system", "You are a passionate travel advocate. Make the STRONGEST possible case FOR the claim. Use 3 compelling arguments. Be persuasive and specific."),
        ("human", "Claim: {claim}\n\nMake your case FOR this claim in 150-200 words."),
    ]) | llm | parser
)


# ── Critic chain ──────────────────────────────────────────────────────────────

critic_chain = (
    ChatPromptTemplate.from_messages([
        ("system", "You are a rigorous skeptic. You must argue AGAINST the claim. Find real weaknesses in the proposer's arguments. Be specific and fact-based."),
        ("human", "Claim: {claim}\n\nProposer's argument:\n{proposal}\n\nNow argue AGAINST this claim in 150-200 words."),
    ]) | llm | parser
)


# ── Judge chain ───────────────────────────────────────────────────────────────

judge_chain = (
    ChatPromptTemplate.from_messages([
        ("system", "You are an impartial judge. Evaluate both sides fairly. Give a final verdict with a score (1-10) for each side and an overall conclusion."),
        ("human", "Claim: {claim}\n\nFOR:\n{proposal}\n\nAGAINST:\n{critique}\n\nDeliver your verdict: score each side, identify the stronger argument, give your final conclusion."),
    ]) | llm | parser
)


# ── Debate runner ─────────────────────────────────────────────────────────────

def run_debate(claim: str) -> dict:
    print(f"\nClaim: '{claim}'\n")

    print("[Proposer] arguing FOR...")
    proposal = proposer_chain.invoke({"claim": claim})
    print(f"Proposal:\n{proposal}\n")

    print("[Critic] arguing AGAINST...")
    critique = critic_chain.invoke({"claim": claim, "proposal": proposal})
    print(f"Critique:\n{critique}\n")

    print("[Judge] deliberating...")
    verdict = judge_chain.invoke({"claim": claim, "proposal": proposal, "critique": critique})
    print(f"Verdict:\n{verdict}")

    return {"claim": claim, "proposal": proposal, "critique": critique, "verdict": verdict}


if __name__ == "__main__":
    result = run_debate("Tokyo is the best travel destination for a one-week trip")
    print("\n" + "="*60)
    print("DEBATE COMPLETE")
    print("="*60)
