"""Code Lab 18-01 - a minimal coding-agent harness.

The model gets five tools over a workspace directory (list_files, read_file, write_file,
edit_file, run) and works on a small repository task until it calls `finish`. The harness is
where the engineering lives: a workspace per episode, output truncation, bounds, an AGENTS.md
loaded into context, and - in the `verify` variant - a stop hook that runs the visible tests
when the agent tries to finish and hands failures back instead of accepting the claim. The
`verify+repeat` variant adds repeated-call detection: a third identical tool call is refused.

Grading runs hidden tests the agent never sees.

    python harness.py --no-thinking --variants bare --trials 1 --limit 2    # smoke test
    python harness.py --no-thinking                                          # all variants, 8 tasks x 3 trials

`run` executes shell commands in the workspace with a timeout. That is NOT a security sandbox:
run this lab inside a container or VM if you point it at a model you don't control.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field

from openai import OpenAI

from tasks import TASKS

MAX_OUTPUT = 4000          # characters of tool output kept in context (the rest is truncated)
MAX_REPEATS = 2            # identical (tool, arguments) calls allowed in +repeat variants

AGENTS_MD = """# AGENTS.md
- Python 3 project, no external dependencies.
- Run the visible tests with: python tests/test_visible.py  (prints ok on success)
- Keep changes minimal; don't edit files under tests/.
- Call finish only when the change is done and the visible tests pass.
"""

SYSTEM = """You are a coding agent working in a small Python repository.
Use the tools to inspect files, make the change, and run the tests. Make real changes with
write_file or edit_file - describing a change does not make it. When the task is complete,
call finish with a one-line summary.

Project instructions (AGENTS.md):
{agents_md}"""

TOOLS = [
    {"type": "function", "function": {"name": "list_files", "description": "List all files in the workspace.",
                                      "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "read_file", "description": "Read a text file from the workspace.",
                                      "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "write_file", "description": "Create or overwrite a file with the given content.",
                                      "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
                                                     "required": ["path", "content"]}}},
    {"type": "function", "function": {"name": "edit_file",
                                      "description": "Replace one exact occurrence of old_text with new_text in a file. old_text must match exactly once.",
                                      "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "old_text": {"type": "string"},
                                                                                      "new_text": {"type": "string"}},
                                                     "required": ["path", "old_text", "new_text"]}}},
    {"type": "function", "function": {"name": "run", "description": "Run a shell command in the workspace (30 s timeout). Returns exit code and output.",
                                      "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "finish", "description": "Declare the task complete.",
                                      "parameters": {"type": "object", "properties": {"summary": {"type": "string"}}, "required": ["summary"]}}},
]


# ---------------------------------------------------------------------------
# Workspace tools
# ---------------------------------------------------------------------------

class Workspace:
    def __init__(self, task):
        self.root = tempfile.mkdtemp(prefix=f"harness-{task.tid}-")
        for path, content in {**task.files, "tests/test_visible.py": task.visible, "AGENTS.md": AGENTS_MD}.items():
            self._write(path, content)

    def _path(self, rel: str) -> str:
        full = os.path.realpath(os.path.join(self.root, rel))
        if not full.startswith(os.path.realpath(self.root) + os.sep):
            raise ValueError(f"path {rel!r} is outside the workspace")
        return full

    def _write(self, rel, content):
        full = self._path(rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w") as f:
            f.write(content)

    def list_files(self):
        out = []
        for d, _, files in os.walk(self.root):
            out += [os.path.relpath(os.path.join(d, f), self.root) for f in files if "__pycache__" not in d]
        return "\n".join(sorted(out))

    def read_file(self, path):
        with open(self._path(path)) as f:
            return f.read()

    def write_file(self, path, content):
        self._write(path, content)
        return f"wrote {len(content)} characters to {path}"

    def edit_file(self, path, old_text, new_text):
        text = self.read_file(path)
        n = text.count(old_text)
        if n != 1:
            raise ValueError(f"old_text matches {n} times in {path}; it must match exactly once")
        self._write(path, text.replace(old_text, new_text))
        return f"edited {path}"

    def run(self, command, timeout=30):
        # the harness's own interpreter first on PATH, so `python` works and matches the grader's
        path = os.path.dirname(sys.executable) + os.pathsep + os.environ["PATH"]
        env = {"PATH": path, "HOME": self.root, "PYTHONDONTWRITEBYTECODE": "1"}
        try:
            p = subprocess.run(command, shell=True, cwd=self.root, env=env, capture_output=True, text=True, timeout=timeout)
            return f"exit code {p.returncode}\n{p.stdout}{p.stderr}"
        except subprocess.TimeoutExpired:
            return f"timed out after {timeout} s"

    def run_python(self, script: str) -> tuple[bool, str]:
        """Run a test script with this interpreter (grading and the stop hook)."""
        self._write("tests/_check.py", script)
        try:
            p = subprocess.run([sys.executable, "tests/_check.py"], cwd=self.root, capture_output=True, text=True, timeout=30)
            ok, out = p.returncode == 0, (p.stdout + p.stderr)[-1500:]
        except subprocess.TimeoutExpired:
            ok, out = False, "timed out"
        os.remove(self._path("tests/_check.py"))
        return ok, out

    def cleanup(self):
        shutil.rmtree(self.root, ignore_errors=True)


# ---------------------------------------------------------------------------
# The harness loop
# ---------------------------------------------------------------------------

@dataclass
class Episode:
    passed: bool = False
    finished: bool = False
    steps: int = 0
    tool_calls: int = 0
    tokens: int = 0
    hook_rejections: int = 0
    repeats_blocked: int = 0
    trace: list = field(default_factory=list)


def truncate(text: str) -> str:
    if len(text) <= MAX_OUTPUT:
        return text
    return text[:MAX_OUTPUT // 2] + f"\n... [{len(text) - MAX_OUTPUT} characters truncated] ...\n" + text[-MAX_OUTPUT // 2:]


def run_episode(client, model, task, variant, max_steps=25, max_hook_rejections=2, extra_body=None) -> Episode:
    ws, ep, seen = Workspace(task), Episode(), {}
    messages = [{"role": "system", "content": SYSTEM.format(agents_md=AGENTS_MD)},
                {"role": "user", "content": task.instruction}]
    try:
        while ep.steps < max_steps and not ep.finished:
            ep.steps += 1
            resp = client.chat.completions.create(model=model, messages=messages, tools=TOOLS, temperature=1.0,
                                                  max_tokens=2048, extra_body=extra_body)
            ep.tokens += resp.usage.total_tokens if resp.usage else 0
            msg = resp.choices[0].message
            calls = msg.tool_calls or []
            messages.append({"role": "assistant", "content": msg.content or "",
                             **({"tool_calls": [c.model_dump() for c in calls]} if calls else {})})
            if not calls:                       # plain text: nudge the model back to the tools
                messages.append({"role": "user", "content": "Use the tools to make the change, then call finish."})
                continue
            for call in calls:
                ep.tool_calls += 1
                name = call.function.name
                try:
                    args = json.loads(call.function.arguments or "{}")
                    key = (name, json.dumps(args, sort_keys=True))
                    seen[key] = seen.get(key, 0) + 1
                    if "+repeat" in variant and name != "finish" and seen[key] > MAX_REPEATS:
                        ep.repeats_blocked += 1
                        result = (f"Refused: you have already made this exact {name} call {seen[key] - 1} times. "
                                  "Its effect is already applied. Check the current state (read the file, run the tests) "
                                  "and change approach, or call finish if the task is done.")
                    elif name == "finish":
                        result = stop_hook(ws, task, variant, ep, max_hook_rejections)
                    elif name in ("list_files", "read_file", "write_file", "edit_file", "run"):
                        result = getattr(ws, name)(**args)
                    else:
                        result = f"unknown tool {name}"
                except Exception as e:          # bad JSON, bad arguments, file errors -> back to the model
                    result = f"error: {type(e).__name__}: {e}"
                ep.trace.append((name, str(call.function.arguments)[:80], str(result)[:80]))
                messages.append({"role": "tool", "tool_call_id": call.id, "content": truncate(str(result))})
        ep.passed, _ = ws.run_python(task.hidden)
        return ep
    finally:
        ws.cleanup()


def stop_hook(ws, task, variant, ep, max_rejections) -> str:
    """Called when the agent calls finish. `bare` accepts the claim; `verify` checks it first."""
    if variant.startswith("verify") and ep.hook_rejections < max_rejections:
        ok, output = ws.run_python(task.visible)
        if not ok:
            ep.hook_rejections += 1
            return ("Not finished: the visible tests fail. Fix the code and call finish again.\n" + output)
    ep.finished = True
    return "finished"


# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-url", default=os.getenv("OPENAI_BASE_URL", "http://localhost:8080/v1"))
    ap.add_argument("--model", default=os.getenv("MODEL", "mlx-community/Qwen3-8B-4bit"))
    ap.add_argument("--api-key", default=os.getenv("OPENAI_API_KEY", "not-needed"))
    ap.add_argument("--no-thinking", action="store_true", help="Qwen3: chat_template_kwargs enable_thinking=False")
    ap.add_argument("--variants", default="bare,verify,verify+repeat")
    ap.add_argument("--trials", type=int, default=3)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--show-failures", action="store_true")
    args = ap.parse_args()

    client = OpenAI(base_url=args.base_url, api_key=args.api_key, timeout=120)   # a stalled request fails fast and is retried
    extra = {"chat_template_kwargs": {"enable_thinking": False}} if args.no_thinking else None
    tasks = TASKS[: args.limit] if args.limit else TASKS
    print(f"model={args.model}  tasks={len(tasks)}  trials={args.trials}\n", flush=True)

    summary = []
    for variant in args.variants.split(","):
        rows, t0 = [], time.time()
        for task in tasks:
            wins = 0
            for trial in range(args.trials):
                ep = run_episode(client, args.model, task, variant, extra_body=extra)
                wins += ep.passed
                rows.append(ep)
                if args.show_failures and not ep.passed:
                    print(f"  FAIL [{variant}] {task.tid} trial {trial}: finished={ep.finished} steps={ep.steps}")
                    for step in ep.trace:
                        print("     ", step)
            print(f"  [{variant}] {task.tid:16s} {wins}/{args.trials}", flush=True)
        n = len(rows)
        summary.append((variant, sum(e.passed for e in rows) / n, sum(e.finished for e in rows) / n,
                        sum(e.finished and not e.passed for e in rows) / n, sum(e.hook_rejections for e in rows) / n,
                        sum(e.repeats_blocked for e in rows) / n, sum(e.steps for e in rows) / n,
                        sum(e.tokens for e in rows) / n))

    print(f"\n{'variant':15s}{'pass':>6s}{'finished':>10s}{'claimed-but-failed':>20s}{'hook rejects':>14s}"
          f"{'repeats blocked':>17s}{'steps':>7s}{'tokens':>8s}")
    for v, p, fin, cf, hr, rb, st, tok in summary:
        print(f"{v:15s}{p:6.2f}{fin:10.2f}{cf:20.2f}{hr:14.2f}{rb:17.2f}{st:7.1f}{tok:8.0f}")


if __name__ == "__main__":
    main()
