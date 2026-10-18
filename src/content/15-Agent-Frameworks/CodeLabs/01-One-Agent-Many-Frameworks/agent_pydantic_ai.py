"""The shop agent with PydanticAI. refund_item is registered with requires_approval=True: the run
ends with a DeferredToolRequests output, and the script resumes it with the approvals.

    pip install -r requirements-pydantic-ai.txt
    python agent_pydantic_ai.py --no-thinking
"""

from pydantic_ai import Agent, DeferredToolRequests, DeferredToolResults, Tool, UsageLimits
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

import common

args = common.parse_args(__doc__)
model = OpenAIChatModel(args.model, provider=OpenAIProvider(base_url=args.base_url, api_key=args.api_key))
settings = {"temperature": 1.0, **({"extra_body": common.extra_body(args)} if args.no_thinking else {})}
limits = UsageLimits(request_limit=20)


def run_one(shop, instruction: str) -> str:
    tools = [Tool(fn, requires_approval=fn.__name__ == "refund_item") for fn in common.make_tools(shop)]
    agent = Agent(model, instructions=common.INSTRUCTIONS, tools=tools,
                  output_type=[str, DeferredToolRequests], model_settings=settings)
    result = agent.run_sync(instruction, usage_limits=limits)
    while isinstance(result.output, DeferredToolRequests):   # paused before a refund: a human decides
        approvals = {}
        for call in result.output.approvals:
            print(f"    approval requested: {call.tool_name}({call.args}) -> approve")
            approvals[call.tool_call_id] = True
        result = agent.run_sync(message_history=result.all_messages(), usage_limits=limits,
                                deferred_tool_results=DeferredToolResults(approvals=approvals))
    return result.output


common.run_tasks("pydantic-ai", args, run_one)
