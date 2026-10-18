"""The shop agent with Google ADK, using LiteLLM to reach an OpenAI-compatible server (on Google
Cloud you would pass a Gemini model name instead). A before_tool_callback is the approval gate:
returning a dict skips the tool and hands that dict to the model as the result.

    pip install -r requirements-adk.txt
    python agent_adk.py --no-thinking
"""

import asyncio

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import InMemoryRunner
from google.genai import types

import common

args = common.parse_args(__doc__)
model = LiteLlm(model=f"openai/{args.model}", api_base=args.base_url, api_key=args.api_key,
                temperature=1.0, extra_body=common.extra_body(args))


def approval_gate(tool, args, tool_context):
    if tool.name == "refund_item":
        print(f"    approval requested: {tool.name}({args}) -> approve")
    return None                                   # None = run the tool; a dict = skip it


async def run_async(shop, instruction: str) -> str:
    agent = LlmAgent(name="shop_support", model=model, instruction=common.INSTRUCTIONS,
                     tools=common.make_tools(shop), before_tool_callback=approval_gate)
    runner = InMemoryRunner(agent=agent, app_name="shop")
    session = await runner.session_service.create_session(app_name="shop", user_id="customer")
    final = ""
    async for event in runner.run_async(user_id="customer", session_id=session.id,
                                        new_message=types.Content(role="user", parts=[types.Part(text=instruction)])):
        if event.is_final_response() and event.content and event.content.parts:
            final = "".join(p.text or "" for p in event.content.parts)
    return final


common.run_tasks("google-adk", args, lambda shop, text: asyncio.run(run_async(shop, text)))
