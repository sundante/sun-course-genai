"""The shop agent with Microsoft Agent Framework. refund_item is wrapped with
approval_mode="always_require": the response carries a function_approval_request, and the script
answers it in the same session.

    pip install -r requirements-maf.txt
    python agent_maf.py --no-thinking
"""

import asyncio

from agent_framework import Agent, Message, tool
from agent_framework.openai import OpenAIChatCompletionClient

import common

args = common.parse_args(__doc__)
client = OpenAIChatCompletionClient(args.model, base_url=args.base_url, api_key=args.api_key)
options = {"temperature": 1.0, **({"extra_body": common.extra_body(args)} if args.no_thinking else {})}


async def run_async(shop, instruction: str) -> str:
    tools = [tool(fn, approval_mode="always_require" if fn.__name__ == "refund_item" else "never_require")
             for fn in common.make_tools(shop)]
    agent = Agent(client, common.INSTRUCTIONS, name="shop_support", tools=tools, default_options=options)
    session = agent.create_session()
    response = await agent.run(instruction, session=session)
    while response.user_input_requests:          # paused before a refund: a human decides
        answers = []
        for request in response.user_input_requests:
            print(f"    approval requested: {request.function_call.name}({request.function_call.arguments}) -> approve")
            answers.append(request.to_function_approval_response(True))
        response = await agent.run(Message("user", answers), session=session)
    return response.text


common.run_tasks("ms-agent-framework", args, lambda shop, text: asyncio.run(run_async(shop, text)))
