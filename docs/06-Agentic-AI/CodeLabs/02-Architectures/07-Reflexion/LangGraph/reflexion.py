"""
Reflexion Architecture — LangGraph
Pattern: generator → critic → conditional: rewriter or END

The loop is an explicit graph edge (critic → generator for retry).
Max retries enforced by the routing function using state counter.
"""
import os
import re
from typing import TypedDict, Optional
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END

load_dotenv()
assert os.getenv("GOOGLE_API_KEY"), "Set GOOGLE_API_KEY in .env"

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
THRESHOLD = 7
MAX_RETRIES = 2


class ReflexionState(TypedDict):
    destination: str
    draft: Optional[str]
    score: int
    issues: str
    attempts: int
    final_output: Optional[str]


def generator_node(state: ReflexionState) -> ReflexionState:
    prompt = f"Write a travel recommendation for {state['destination']}. Include: top attractions, best time to visit, safety tips, weather."
    if state["issues"]:
        prompt += f"\n\nImprove by fixing these issues: {state['issues']}"
    r = llm.invoke([
        SystemMessage(content="You are a travel writer."),
        HumanMessage(content=prompt),
    ])
    print(f"  [generator] attempt {state['attempts'] + 1}")
    return {"draft": r.content, "attempts": state["attempts"] + 1}


def critic_node(state: ReflexionState) -> ReflexionState:
    r = llm.invoke([
        SystemMessage(content="""Score 1-10 on: specificity (3pts), weather (2pts), safety (2pts), detail (3pts).
Format: SCORE:[n] ISSUES:[list] VERDICT:[PASS/REVISE]"""),
        HumanMessage(content=f"Recommendation:\n{state['draft']}\n\nScore:"),
    ])
    text = r.content
    score_m = re.search(r"SCORE:(\d+)", text)
    issues_m = re.search(r"ISSUES:(.+?)(?:\n|$)", text)
    score = int(score_m.group(1)) if score_m else 5
    issues = issues_m.group(1).strip() if issues_m else ""
    print(f"  [critic] score {score}/10 | attempts so far: {state['attempts']}")
    return {"score": score, "issues": issues}


def route_after_critic(state: ReflexionState) -> str:
    if state["score"] >= THRESHOLD:
        return "done"
    if state["attempts"] >= MAX_RETRIES + 1:
        return "done"
    return "retry"


def finalize(state: ReflexionState) -> ReflexionState:
    print(f"  [done] final score {state['score']}/10 after {state['attempts']} attempt(s)")
    return {"final_output": state["draft"]}


def build_graph():
    builder = StateGraph(ReflexionState)
    builder.add_node("generator", generator_node)
    builder.add_node("critic", critic_node)
    builder.add_node("finalize", finalize)

    builder.add_edge(START, "generator")
    builder.add_edge("generator", "critic")
    builder.add_conditional_edges("critic", route_after_critic, {
        "retry": "generator",
        "done":  "finalize",
    })
    builder.add_edge("finalize", END)
    return builder.compile()


if __name__ == "__main__":
    graph = build_graph()
    result = graph.invoke({
        "destination": "Tokyo", "draft": None, "score": 0,
        "issues": "", "attempts": 0, "final_output": None,
    })
    print("\n" + "="*60)
    print(f"Final score: {result['score']}/10 | Attempts: {result['attempts']}")
    print(result["final_output"])
