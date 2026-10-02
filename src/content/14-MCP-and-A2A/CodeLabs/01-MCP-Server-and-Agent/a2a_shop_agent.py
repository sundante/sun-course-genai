"""Code Lab 14-01 - publish the MCP-backed shop agent as an A2A agent, and call it from another agent.

    python a2a_shop_agent.py serve --no-thinking            # A2A server on http://127.0.0.1:9999
    python a2a_shop_agent.py ask "I'm ana.silva@example.com. Cancel my rain jacket order."

The server publishes an Agent Card at /.well-known/agent-card.json, accepts SendMessage over
JSON-RPC, and reports progress as A2A task status updates while the agent works; the final
reply is returned as a task artifact. MCP connects the agent to its tools; A2A connects
agents to each other.
"""

import argparse
import asyncio
import os
import sys

import httpx
import uvicorn
from openai import OpenAI
from starlette.applications import Starlette

from a2a.client import ClientConfig, create_client
from a2a.helpers import new_task_from_user_message, new_text_message, new_text_part
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.types import (AgentCapabilities, AgentCard, AgentInterface, AgentSkill, Role,
                       SendMessageRequest, TaskState)
from mcp import Client

import mcp_agent
import shop_env as env
from shop_server import build_server

URL = "http://127.0.0.1:9999"

CARD = AgentCard(
    name="Outdoor-gear shop support agent",
    description="Resolves order questions, cancellations, address changes and refunds for shop customers.",
    version="0.3.0",
    supported_interfaces=[AgentInterface(url=URL, protocol_binding="JSONRPC", protocol_version="1.0")],
    capabilities=AgentCapabilities(streaming=True),
    default_input_modes=["text/plain"],
    default_output_modes=["text/plain"],
    skills=[AgentSkill(
        id="order-support", name="Order support",
        description="Look up, cancel, re-address or refund a customer's orders under shop policy.",
        tags=["retail", "orders", "refunds"],
        examples=["I'm ana.silva@example.com. Cancel my rain jacket order."])],
)


class ShopAgentExecutor(AgentExecutor):
    def __init__(self, llm: OpenAI, model: str, extra: dict | None):
        self.llm, self.model, self.extra = llm, model, extra
        self.shop = env.Shop()                      # one shop shared by all tasks on this server

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        if context.current_task is None:                      # a new task: publish it first
            await event_queue.enqueue_event(new_task_from_user_message(context.message))
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        await updater.start_work(updater.new_agent_message([new_text_part("Looking into it...")]))
        async with Client(build_server(self.shop), elicitation_callback=mcp_agent.auto_confirm) as mcp:
            tools = mcp_agent.to_openai_tools((await mcp.list_tools()).tools)
            answer, trace = await mcp_agent.run_episode(self.llm, self.model, mcp, tools, None,
                                                        context.get_user_input(), self.extra)
        steps = ", ".join(name for name, _, _ in trace) or "no tool calls"
        await updater.update_status(TaskState.TASK_STATE_WORKING,
                                    updater.new_agent_message([new_text_part(f"Tools used: {steps}")]))
        await updater.add_artifact([new_text_part(answer or "Sorry, I couldn't complete that.")], name="reply")
        await updater.complete()

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        await TaskUpdater(event_queue, context.task_id, context.context_id).cancel()


def serve(args):
    llm = OpenAI(base_url=args.base_url, api_key=os.getenv("OPENAI_API_KEY", "not-needed"))
    extra = {"chat_template_kwargs": {"enable_thinking": False}} if args.no_thinking else None
    handler = DefaultRequestHandler(agent_executor=ShopAgentExecutor(llm, args.model, extra),
                                    task_store=InMemoryTaskStore(), agent_card=CARD)
    app = Starlette(routes=create_agent_card_routes(CARD) + create_jsonrpc_routes(handler, rpc_url="/"))
    uvicorn.run(app, host="127.0.0.1", port=9999, log_level="warning")


async def ask(text: str):
    """A client agent: resolve the Agent Card, send a message, print the streamed task events."""
    config = ClientConfig(httpx_client=httpx.AsyncClient(timeout=180))   # agent tasks take a while
    client = await create_client(URL, client_config=config)
    request = SendMessageRequest(message=new_text_message(text, role=Role.ROLE_USER))
    async for event in client.send_message(request):
        if event.HasField("task"):
            print(f"[task] id={event.task.id[:8]} state={TaskState.Name(event.task.status.state)}")
        elif event.HasField("status_update"):
            s = event.status_update.status
            note = " ".join(p.text for p in s.message.parts) if s.HasField("message") else ""
            print(f"[status] {TaskState.Name(s.state)} {note}")
        elif event.HasField("artifact_update"):
            print("[artifact]", " ".join(p.text for p in event.artifact_update.artifact.parts))
        elif event.HasField("message"):
            print("[message]", " ".join(p.text for p in event.message.parts))
    await client.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("serve")
    s.add_argument("--base-url", default=os.getenv("OPENAI_BASE_URL", "http://localhost:8080/v1"))
    s.add_argument("--model", default=os.getenv("MODEL", "mlx-community/Qwen3-8B-4bit"))
    s.add_argument("--no-thinking", action="store_true")
    a = sub.add_parser("ask")
    a.add_argument("text")
    args = ap.parse_args()
    if args.cmd == "serve":
        serve(args)
    else:
        asyncio.run(ask(args.text))
