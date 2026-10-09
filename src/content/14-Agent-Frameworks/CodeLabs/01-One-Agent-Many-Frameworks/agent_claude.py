"""The shop agent with the Claude Agent SDK (the Claude Code harness as a library). The tools are
served from an in-process MCP server; can_use_tool is the approval gate. Needs the Claude Code
CLI and an Anthropic API key - it cannot run on a local OpenAI-compatible model.

    pip install -r requirements-claude.txt
    export ANTHROPIC_API_KEY=...
    python agent_claude.py
"""

import asyncio
import json
import time

from claude_agent_sdk import (ClaudeAgentOptions, ClaudeSDKClient, PermissionResultAllow, ResultMessage,
                              create_sdk_mcp_server, tool)

import shop_env as env
import common


def mcp_tools(shop):
    out = []
    for fn in common.make_tools(shop):
        params = {name: (int if hint is int else str) for name, hint in fn.__annotations__.items() if name != "return"}

        async def handler(call_args, fn=fn):
            return {"content": [{"type": "text", "text": json.dumps(fn(**call_args), default=str)}]}
        out.append(tool(fn.__name__, fn.__doc__, params)(handler))
    return out


async def approve(tool_name, tool_input, context):
    if tool_name.endswith("refund_item"):
        print(f"    approval requested: {tool_name}({tool_input}) -> approve")
    return PermissionResultAllow()


async def run_one(shop, instruction: str) -> str:
    options = ClaudeAgentOptions(
        model="claude-sonnet-5", system_prompt=common.INSTRUCTIONS, max_turns=20,
        mcp_servers={"shop": create_sdk_mcp_server("shop", tools=mcp_tools(shop))},
        tools=[],                                  # no built-in Read/Bash/...: only the shop tools
        allowed_tools=[f"mcp__shop__{n}" for n in ("find_customer", "list_orders", "get_order")],
        can_use_tool=approve)                      # write tools fall through to the approval callback
    answer = ""
    async with ClaudeSDKClient(options=options) as client:   # can_use_tool needs a streaming session
        await client.query(instruction)
        async for message in client.receive_response():
            if isinstance(message, ResultMessage):
                answer = message.result or ""
    return answer


if __name__ == "__main__":
    passed = 0
    tasks = [t for t in env.TASKS if t.tid in common.TASK_IDS]
    for task in tasks:
        shop, start = env.Shop(), time.time()
        answer = asyncio.run(run_one(shop, task.instruction))
        ok, why = env.grade(task, shop.db, answer)
        passed += ok
        print(f"  {task.tid:16s} {'PASS' if ok else 'FAIL'}  {time.time() - start:5.1f}s  {'' if ok else why[:80]}")
    print(f"[claude-agent-sdk] {passed}/{len(tasks)} passed")
