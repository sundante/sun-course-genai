"""Code Lab 12-01 - an agent loop from scratch, evaluated with pass^k.

The loop talks to any OpenAI-compatible Chat Completions endpoint (a local
mlx_lm / vLLM / Ollama server, or a hosted API), runs the tools in shop_env.py,
and is graded on the final database state.

    python agent_lab.py --no-thinking --limit 3 --trials 1   # smoke test
    python agent_lab.py --no-thinking                        # all tasks, 4 trials, 3 variants
    python agent_lab.py --variants full --trials 8 --show-failures
"""

from __future__ import annotations

import argparse
import json
import math
import os
import time
from collections import Counter
from dataclasses import dataclass, field

from openai import OpenAI

import shop_env as env

# ---------------------------------------------------------------------------
# Argument validation - a tiny JSON-schema subset (types, required, no extras)
# ---------------------------------------------------------------------------

_PY_TYPES = {"string": str, "integer": int, "number": (int, float), "boolean": bool}


def validate_args(args: dict, schema: dict) -> str | None:
    """Return an error message, or None if args match the schema."""
    if not isinstance(args, dict):
        return "arguments must be a JSON object"
    props = schema.get("properties", {})
    for name in schema.get("required", []):
        if name not in args:
            return f"missing required argument {name!r}"
    for name, value in args.items():
        if name not in props:
            return f"unknown argument {name!r}; allowed: {sorted(props)}"
        want = _PY_TYPES.get(props[name].get("type"))
        if want and (not isinstance(value, want) or (want is int and isinstance(value, bool))):
            return f"argument {name!r} must be {props[name]['type']}, got {type(value).__name__}"
    return None


# ---------------------------------------------------------------------------
# The loop
# ---------------------------------------------------------------------------

@dataclass
class Bounds:
    max_steps: int = 12          # model calls per episode
    max_tool_calls: int = 20
    max_repeats: int = 2         # identical (tool, args) calls allowed before we refuse to run it again


@dataclass
class Result:
    status: str                  # "done" | "max_steps" | "max_tool_calls" | "truncated" | "error"
    answer: str = ""
    steps: int = 0
    tool_calls: int = 0
    tool_errors: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    trace: list = field(default_factory=list)


def run_agent(client: OpenAI, model: str, system: str, user: str, tools: list[dict],
              functions: dict, bounds: Bounds, temperature: float = 1.0, top_p: float = 1.0,
              max_tokens: int = 1024, extra_body: dict | None = None) -> Result:
    schemas = {t["function"]["name"]: t["function"]["parameters"] for t in tools}
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    res = Result(status="error")
    seen: Counter = Counter()

    for step in range(1, bounds.max_steps + 1):
        res.steps = step
        resp = client.chat.completions.create(
            model=model, messages=messages, tools=tools, tool_choice="auto",
            temperature=temperature, top_p=top_p, max_tokens=max_tokens,
            extra_body=extra_body)
        choice = resp.choices[0]
        msg = choice.message
        if resp.usage:
            res.prompt_tokens += resp.usage.prompt_tokens
            res.completion_tokens += resp.usage.completion_tokens

        # 1. Truncated output: a tool call cut off by max_tokens must not be executed.
        if choice.finish_reason == "length":
            res.status, res.answer = "truncated", msg.content or ""
            return res

        # 2. No tool calls: the model has answered - the normal way a loop ends.
        if not msg.tool_calls:
            res.status, res.answer = "done", (msg.content or "").strip()
            res.trace.append(("answer", res.answer))
            return res

        # 3. Keep the assistant turn *with* its tool_calls, then answer every call.
        #    Each tool_call id must get exactly one tool message, or the next request is invalid.
        messages.append({"role": "assistant", "content": msg.content or "",
                         "tool_calls": [tc.model_dump() for tc in msg.tool_calls]})
        for tc in msg.tool_calls:
            res.tool_calls += 1
            name, raw = tc.function.name, tc.function.arguments or "{}"
            try:
                args = json.loads(raw)
                if name not in functions:
                    raise env.ToolError(f"Unknown tool {name!r}; available: {sorted(functions)}")
                err = validate_args(args, schemas[name])
                if err:
                    raise env.ToolError(err)
                key = (name, json.dumps(args, sort_keys=True))
                seen[key] += 1
                if seen[key] > bounds.max_repeats:
                    raise env.ToolError("You already made this exact call; use the earlier result "
                                        "or try something different.")
                output = {"ok": True, "result": functions[name](**args)}
            except json.JSONDecodeError:
                output = {"ok": False, "error": f"arguments were not valid JSON: {raw[:200]}"}
            except env.ToolError as e:
                output = {"ok": False, "error": str(e)}
            if not output["ok"]:
                res.tool_errors += 1
            res.trace.append(("call", name, raw, output))
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(output)})

        if res.tool_calls >= bounds.max_tool_calls:
            res.status = "max_tool_calls"
            return res

    res.status = "max_steps"
    return res


# ---------------------------------------------------------------------------
# Evaluation: pass@1, pass^k and pass@k over repeated trials
# ---------------------------------------------------------------------------

VARIANTS = {
    # name: (system prompt, tool schemas)
    "full": (env.POLICY, env.TOOLS_FULL),
    "terse_tools": (env.POLICY, env.TOOLS_TERSE),
    "no_policy": (env.MINIMAL_SYSTEM, env.TOOLS_FULL),
}


def pass_hat_k(n: int, c: int, k: int) -> float:
    """tau-bench's pass^k: probability that k i.i.d. trials ALL succeed, estimated from c/n."""
    return math.comb(c, k) / math.comb(n, k)


def pass_at_k(n: int, c: int, k: int) -> float:
    """Codex-paper pass@k: probability that at least one of k trials succeeds."""
    return 1.0 - math.comb(n - c, k) / math.comb(n, k)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-url", default=os.getenv("OPENAI_BASE_URL", "http://localhost:8080/v1"))
    ap.add_argument("--model", default=os.getenv("MODEL", "mlx-community/Qwen3-8B-4bit"))
    ap.add_argument("--no-thinking", action="store_true",
                    help="send chat_template_kwargs={'enable_thinking': False} (Qwen3 on vLLM / mlx-lm servers)")
    ap.add_argument("--variants", default="full,terse_tools,no_policy")
    ap.add_argument("--trials", type=int, default=4)
    ap.add_argument("--limit", type=int, default=None, help="use only the first N tasks")
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--top-p", type=float, default=1.0)
    ap.add_argument("--show-failures", action="store_true")
    args = ap.parse_args()

    client = OpenAI(base_url=args.base_url, api_key=os.getenv("OPENAI_API_KEY", "not-needed"))
    tasks = env.TASKS[: args.limit] if args.limit else env.TASKS
    n = args.trials
    extra = {"chat_template_kwargs": {"enable_thinking": False}} if args.no_thinking else None
    print(f"model={args.model}  tasks={len(tasks)}  trials={n}  temperature={args.temperature}  top_p={args.top_p}\n", flush=True)

    summary = []
    for vname in args.variants.split(","):
        system, tools = VARIANTS[vname]
        per_task, statuses, t0 = {}, Counter(), time.time()
        tok_in = tok_out = calls = errs = 0
        for task in tasks:
            wins = 0
            for trial in range(n):
                shop = env.Shop()
                r = run_agent(client, args.model, system, task.instruction, tools,
                              env.dispatch(shop), Bounds(), args.temperature, args.top_p,
                              extra_body=extra)
                ok, why = env.grade(task, shop.db, r.answer)
                ok = ok and r.status == "done"
                wins += ok
                statuses[r.status] += 1
                tok_in, tok_out = tok_in + r.prompt_tokens, tok_out + r.completion_tokens
                calls, errs = calls + r.tool_calls, errs + r.tool_errors
                if not ok and args.show_failures:
                    print(f"  FAIL [{vname}] {task.tid} trial {trial}: {why if r.status == 'done' else r.status}")
                    for ev in r.trace:
                        print("     ", str(ev)[:220], flush=True)
            per_task[task.tid] = wins
        episodes = len(tasks) * n
        row = {
            "variant": vname,
            "pass@1": sum(per_task.values()) / episodes,
            **{f"pass^{k}": sum(pass_hat_k(n, c, k) for c in per_task.values()) / len(tasks)
               for k in (2, 4) if k <= n},
            f"pass@{n}": sum(pass_at_k(n, c, n) for c in per_task.values()) / len(tasks),
            "calls/ep": calls / episodes,
            "err/ep": errs / episodes,
            "tok/ep": (tok_in + tok_out) / episodes,
            "sec/ep": (time.time() - t0) / episodes,
            "not_done": episodes - statuses["done"],
            "per_task": per_task,
        }
        summary.append(row)
        print(f"[{vname}] " + "  ".join(f"{k}={v:.3f}" if isinstance(v, float) else f"{k}={v}"
                                       for k, v in row.items() if k not in ("variant", "per_task")))

    cols = [c for c in summary[0] if c not in ("variant", "per_task")]
    print("\n" + "variant".ljust(13) + "".join(c.rjust(10) for c in cols))
    for row in summary:
        print(row["variant"].ljust(13) + "".join(
            (f"{row[c]:.3f}" if isinstance(row[c], float) and c.startswith("pass") else
             f"{row[c]:.1f}" if isinstance(row[c], float) else str(row[c])).rjust(10) for c in cols))
    print("\nsuccesses per task (out of %d):" % n)
    print("task".ljust(20) + "".join(r["variant"].rjust(13) for r in summary))
    for task in tasks:
        print(task.tid.ljust(20) + "".join(str(r["per_task"][task.tid]).rjust(13) for r in summary))


if __name__ == "__main__":
    main()
