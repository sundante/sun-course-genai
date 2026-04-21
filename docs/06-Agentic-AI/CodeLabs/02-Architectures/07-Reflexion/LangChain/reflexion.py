"""
Reflexion Architecture — LangChain
Pattern: Generator → Critic → Conditional Rewriter (Python loop)

The generator produces a draft. The critic scores it.
If score < threshold, the rewriter improves it. Max 2 retries.
"""
import os
import re
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()
assert os.getenv("GOOGLE_API_KEY"), "Set GOOGLE_API_KEY in .env"

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
parser = StrOutputParser()

THRESHOLD = 7
MAX_RETRIES = 2


# ── Generator chain ───────────────────────────────────────────────────────────

generator_chain = (
    ChatPromptTemplate.from_messages([
        ("system", "You are a travel writer. Write a travel recommendation."),
        ("human", "Write a travel recommendation for {destination}. Include: top attractions, best time to visit, safety tips, weather."),
    ]) | llm | parser
)


# ── Critic chain ──────────────────────────────────────────────────────────────

critic_chain = (
    ChatPromptTemplate.from_messages([
        ("system", """You are a travel editor. Score this recommendation 1-10 based on:
- Specificity of attractions (3 pts)
- Weather information (2 pts)
- Safety information (2 pts)
- Length and detail (3 pts)

Output format (MUST follow exactly):
SCORE:[number]
ISSUES:[comma-separated list of what's missing or weak]
VERDICT:[PASS if score>=7, REVISE if score<7]"""),
        ("human", "Recommendation:\n{draft}\n\nScore it:"),
    ]) | llm | parser
)


# ── Rewriter chain ────────────────────────────────────────────────────────────

rewriter_chain = (
    ChatPromptTemplate.from_messages([
        ("system", "You are a travel editor. Rewrite the recommendation addressing the specific issues listed."),
        ("human", "Original recommendation:\n{draft}\n\nIssues to fix:\n{issues}\n\nRewrite it addressing all issues:"),
    ]) | llm | parser
)


# ── Parse critic output ───────────────────────────────────────────────────────

def parse_critique(critique: str) -> tuple[int, str, str]:
    score_match = re.search(r"SCORE:(\d+)", critique)
    issues_match = re.search(r"ISSUES:(.+?)(?:\n|$)", critique)
    verdict_match = re.search(r"VERDICT:(PASS|REVISE)", critique)
    score = int(score_match.group(1)) if score_match else 5
    issues = issues_match.group(1).strip() if issues_match else "Unknown issues"
    verdict = verdict_match.group(1) if verdict_match else "REVISE"
    return score, issues, verdict


# ── Reflexion loop ────────────────────────────────────────────────────────────

def run_reflexion(destination: str) -> str:
    print(f"\n[Generator] drafting recommendation for {destination}...")
    draft = generator_chain.invoke({"destination": destination})
    print(f"Draft ({len(draft)} chars)")

    for attempt in range(MAX_RETRIES + 1):
        print(f"\n[Critic] evaluating (attempt {attempt + 1})...")
        critique = critic_chain.invoke({"draft": draft})
        score, issues, verdict = parse_critique(critique)
        print(f"Score: {score}/10 | Verdict: {verdict} | Issues: {issues}")

        if verdict == "PASS" or score >= THRESHOLD:
            print(f"✓ Quality threshold met at attempt {attempt + 1}")
            break

        if attempt < MAX_RETRIES:
            print(f"[Rewriter] improving draft (attempt {attempt + 1})...")
            draft = rewriter_chain.invoke({"draft": draft, "issues": issues})
        else:
            print(f"Max retries reached. Returning best draft (score {score}/10)")

    return draft


if __name__ == "__main__":
    final = run_reflexion("Tokyo")
    print("\n" + "="*60)
    print("FINAL RECOMMENDATION")
    print("="*60)
    print(final)
