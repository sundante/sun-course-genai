"""The shop agent with LangChain v1's create_agent (built on LangGraph), plus human-in-the-loop
middleware that pauses before every refund.

    pip install -r requirements-langchain.txt
    python agent_langchain.py --no-thinking
"""

import uuid

from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware, ToolCallLimitMiddleware
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

import common

args = common.parse_args(__doc__)
model = ChatOpenAI(model=args.model, base_url=args.base_url, api_key=args.api_key,
                   temperature=1.0, extra_body=common.extra_body(args))


def run_one(shop, instruction: str) -> str:
    agent = create_agent(
        model,
        tools=common.make_tools(shop),
        system_prompt=common.INSTRUCTIONS,
        middleware=[
            HumanInTheLoopMiddleware(interrupt_on={"refund_item": {"allowed_decisions": ["approve", "reject"]}}),
            ToolCallLimitMiddleware(run_limit=20),
        ],
        checkpointer=InMemorySaver(),            # interrupts need a checkpointer to pause and resume
    )
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    result = agent.invoke({"messages": [{"role": "user", "content": instruction}]}, config)
    while "__interrupt__" in result:              # paused before a refund: a human decides
        for request in result["__interrupt__"][0].value["action_requests"]:
            print(f"    approval requested: {request['name']}({request['args']}) -> approve")
        decisions = [{"type": "approve"} for _ in result["__interrupt__"][0].value["action_requests"]]
        result = agent.invoke(Command(resume={"decisions": decisions}), config)
    return result["messages"][-1].content


common.run_tasks("langchain", args, run_one)
