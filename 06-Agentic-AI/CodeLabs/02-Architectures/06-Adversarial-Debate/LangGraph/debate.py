"""
Adversarial Debate Architecture — LangGraph
Pattern: proposer_node → critic_node → judge_node

State accumulates the full debate transcript.
Optional: multiple debate rounds via a loop edge.
"""
import os
from typing import TypedDict, Optional
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END

load_dotenv()
assert os.getenv("GOOGLE_API_KEY"), "Set GOOGLE_API_KEY in .env"

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.3)


class DebateState(TypedDict):
    claim: str
    proposal: Optional[str]
    critique: Optional[str]
    verdict: Optional[str]
    round: int


def proposer_node(state: DebateState) -> DebateState:
    r = llm.invoke([
        SystemMessage(content="You are a passionate travel advocate. Make the STRONGEST case FOR the claim. 3 arguments, 150 words."),
        HumanMessage(content=f"Claim: {state['claim']}\n\nArgue FOR in 150 words."),
    ])
    print(f"  [proposer] round {state['round']}")
    return {"proposal": r.content}


def critic_node(state: DebateState) -> DebateState:
    r = llm.invoke([
        SystemMessage(content="You are a rigorous skeptic. Argue AGAINST the claim. Find real weaknesses. 150 words."),
        HumanMessage(content=f"Claim: {state['claim']}\n\nFOR:\n{state['proposal']}\n\nArgue AGAINST:"),
    ])
    print(f"  [critic] round {state['round']}")
    return {"critique": r.content}


def judge_node(state: DebateState) -> DebateState:
    r = llm.invoke([
        SystemMessage(content="You are an impartial judge. Score each side 1-10, identify the stronger argument, give a final conclusion."),
        HumanMessage(content=f"Claim: {state['claim']}\n\nFOR:\n{state['proposal']}\n\nAGAINST:\n{state['critique']}\n\nDeliver verdict:"),
    ])
    print(f"  [judge] verdict reached after round {state['round']}")
    return {"verdict": r.content}


def build_debate_graph(max_rounds: int = 1):
    builder = StateGraph(DebateState)
    builder.add_node("proposer", proposer_node)
    builder.add_node("critic", critic_node)
    builder.add_node("judge", judge_node)

    builder.add_edge(START, "proposer")
    builder.add_edge("proposer", "critic")

    if max_rounds > 1:
        def route_after_critic(state: DebateState):
            return "proposer" if state["round"] < max_rounds else "judge"
        builder.add_conditional_edges("critic", route_after_critic, {"proposer": "proposer", "judge": "judge"})
    else:
        builder.add_edge("critic", "judge")

    builder.add_edge("judge", END)
    return builder.compile()


if __name__ == "__main__":
    claim = "Tokyo is the best travel destination for a one-week trip"
    graph = build_debate_graph(max_rounds=1)

    result = graph.invoke({"claim": claim, "proposal": None, "critique": None, "verdict": None, "round": 1})

    print(f"\nClaim: {claim}")
    print(f"\n--- FOR ---\n{result['proposal']}")
    print(f"\n--- AGAINST ---\n{result['critique']}")
    print(f"\n--- VERDICT ---\n{result['verdict']}")
