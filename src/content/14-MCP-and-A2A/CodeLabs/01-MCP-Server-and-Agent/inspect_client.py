"""Code Lab 14-01 - explore an MCP server from the client side.

    python inspect_client.py                          # in-process server (no subprocess, no network)
    python inspect_client.py --stdio                  # launch shop_server.py as a subprocess
    python inspect_client.py --url http://127.0.0.1:8765/mcp   # a running HTTP server
    python inspect_client.py --pin-file pins.json     # pin tool definitions; warn if they change

Lists tools (with annotations and output schemas), resources, templates and prompts; calls
tools, including a refund that triggers an elicitation round trip; and pins tool
definitions by hash so a changed description (a "rug pull") is detected.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sys

from mcp import Client
from mcp.client import ClientRequestContext
from mcp.client.stdio import StdioServerParameters
from mcp.types import ElicitRequestParams, ElicitResult


def tool_fingerprint(tool) -> str:
    """Hash everything the model will read about a tool."""
    blob = json.dumps({"name": tool.name, "description": tool.description,
                       "input_schema": tool.input_schema}, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def check_pins(tools, path: str) -> list[str]:
    """Trust on first use: record fingerprints, then report any tool whose definition changed."""
    current = {t.name: tool_fingerprint(t) for t in tools}
    if not os.path.exists(path):
        json.dump(current, open(path, "w"), indent=2)
        print(f"  pinned {len(current)} tool definitions to {path}")
        return []
    pinned = json.load(open(path))
    changed = [n for n, fp in current.items() if n in pinned and pinned[n] != fp]
    added = [n for n in current if n not in pinned]
    for n in changed:
        print(f"  !! tool '{n}' definition CHANGED since it was pinned - refuse until a human reviews it")
    for n in added:
        print(f"  !! new tool '{n}' appeared - review before exposing it to the model")
    return changed + added


async def ask_user(context: ClientRequestContext, params: ElicitRequestParams) -> ElicitResult:
    """The host's job: show which server is asking and what; collect accept/decline/cancel."""
    print(f"\n  [elicitation from server] {params.message}")
    if not sys.stdin.isatty() or os.getenv("AUTO_CONFIRM"):
        print("  (auto-confirming: non-interactive run)")
        return ElicitResult(action="accept", content={"confirm": True})
    answer = input("  confirm? [y/N] ").strip().lower()
    return ElicitResult(action="accept", content={"confirm": answer == "y"}) if answer in ("y", "n") \
        else ElicitResult(action="cancel")


async def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--stdio", action="store_true")
    g.add_argument("--url")
    ap.add_argument("--pin-file")
    args = ap.parse_args()

    if args.url:
        target = args.url
    elif args.stdio:
        target = StdioServerParameters(command=sys.executable, args=["shop_server.py"])
    else:
        from shop_server import build_server
        target = build_server()

    async with Client(target, elicitation_callback=ask_user) as client:
        print(f"protocol {client.protocol_version}; server {client.server_info.name} {client.server_info.version}")

        tools = await client.list_tools()
        print(f"\ntools (ttl_ms={tools.ttl_ms}, cache_scope={tools.cache_scope}):")
        for t in tools.tools:
            a = t.annotations
            hints = ", ".join(f"{k}={v}" for k, v in (a.model_dump(exclude_none=True).items() if a else []))
            print(f"  {t.name:15s} [{hints}] output_schema={'yes' if t.output_schema else 'no'}")
        if args.pin_file and check_pins(tools.tools, args.pin_file):
            print("  stopping: unreviewed tool changes")
            return

        res = await client.list_resources()
        tmpl = await client.list_resource_templates()
        prompts = await client.list_prompts()
        print("\nresources:", [r.uri for r in res.resources],
              "templates:", [t.uri_template for t in tmpl.resource_templates],
              "prompts:", [p.name for p in prompts.prompts])
        policy = await client.read_resource("shop://policy")
        print("\nshop://policy ->", policy.contents[0].text.splitlines()[2][:90], "...")

        print("\nget_order O1001 -> structured_content:")
        r = await client.call_tool("get_order", {"order_id": "O1001"})
        print(" ", json.dumps(r.structured_content)[:160], "...")

        print("\ncancel_order O1003 (shipped) -> tool execution error, returned as a result:")
        r = await client.call_tool("cancel_order", {"order_id": "O1003", "reason": "test"})
        print(f"  is_error={r.is_error}: {r.content[0].text}")

        print("\nrefund_item O1001 item 1 (120.00, above the confirmation threshold):")
        r = await client.call_tool("refund_item", {"order_id": "O1001", "item_id": 1})
        print(f"  is_error={r.is_error}: {r.structured_content or r.content[0].text}")

        p = await client.get_prompt("customer_request", {"email": "ana.silva@example.com",
                                                          "request": "Where is my rain jacket?"})
        print("\nprompt customer_request ->", p.messages[0].content.text)


if __name__ == "__main__":
    asyncio.run(main())
