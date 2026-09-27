"""The shop agent with the OpenAI Agents SDK. refund_item is declared needs_approval=True, so the
run pauses with an interruption; the script approves it and resumes from the saved RunState.

    pip install -r requirements-openai.txt
    python agent_openai.py --no-thinking
"""

from agents import (Agent, ModelSettings, OpenAIChatCompletionsModel, Runner, function_tool,
                    set_tracing_disabled)
from openai import AsyncOpenAI

import common

args = common.parse_args(__doc__)
set_tracing_disabled(True)                       # traces go to the OpenAI dashboard by default
model = OpenAIChatCompletionsModel(model=args.model,
                                   openai_client=AsyncOpenAI(base_url=args.base_url, api_key=args.api_key))


def run_one(shop, instruction: str) -> str:
    tools = [function_tool(fn, needs_approval=fn.__name__ == "refund_item") for fn in common.make_tools(shop)]
    agent = Agent(name="shop_support", instructions=common.INSTRUCTIONS, tools=tools, model=model,
                  model_settings=ModelSettings(temperature=1.0, extra_body=common.extra_body(args)))
    result = Runner.run_sync(agent, instruction, max_turns=20)
    while result.interruptions:                   # paused before a refund: a human decides
        state = result.to_state()
        for item in result.interruptions:
            print(f"    approval requested: {item.name}({item.arguments}) -> approve")
            state.approve(item)
        result = Runner.run_sync(agent, state, max_turns=20)
    return result.final_output


common.run_tasks("openai-agents", args, run_one)
