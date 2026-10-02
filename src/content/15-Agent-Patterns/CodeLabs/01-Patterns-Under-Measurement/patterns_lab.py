"""Code Lab 15-01 - agent patterns under measurement: which kinds of feedback actually help?

Coding problems from HumanEval (the ones whose docstrings contain examples). Each strategy may
use the docstring examples as *visible* tests; grading uses HumanEval's *hidden* tests.

    python patterns_lab.py --no-thinking --limit 5                  # smoke test
    python patterns_lab.py --no-thinking                            # 40 problems, all strategies
    python patterns_lab.py --no-thinking --strategies single,test_feedback --limit 68   # all eligible

Strategies
  single         one attempt
  self_refine    attempt -> the model reviews its own code (no execution) -> revised attempt
  test_feedback  attempt -> run visible tests -> feed failures back -> retry (up to 2 retries)
  best_of_n      3 attempts -> keep the first that passes the visible tests (else the first)

WARNING: this runs model-generated code on your machine (in a subprocess with a timeout).
Run it in a container or VM if that is not acceptable to you.
"""

import argparse
import doctest
import json
import os
import random
import re
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor

from datasets import load_dataset
from openai import OpenAI

SYSTEM = ("You are an expert Python programmer. Complete the function. Reply with one ```python code block "
          "containing the complete function definition (and any imports or helpers it needs).")


# ---------------------------------------------------------------------------
# Problems, code extraction and execution
# ---------------------------------------------------------------------------

def load_problems(limit: int, seed: int) -> list[dict]:
    """HumanEval problems whose docstrings contain >>> examples; the examples become visible tests."""
    ds = load_dataset("openai/openai_humaneval", split="test")
    parser = doctest.DocTestParser()
    probs = []
    for r in ds:
        visible = []
        for e in parser.get_examples(r["prompt"]):
            want = "\n".join(l for l in e.want.splitlines() if l.strip() not in ('"""', "'''")).strip()
            if want:
                visible.append((e.source.strip(), want))
        if visible:
            probs.append({**r, "visible": visible})
    # drop problems whose own reference solution fails its docstring examples (HumanEval has a few)
    probs = [p for p in probs if visible_check(p["prompt"] + p["canonical_solution"], p)[0]]
    random.Random(seed).shuffle(probs)
    return probs[:limit]


def extract_code(text: str, prompt: str) -> str:
    blocks = re.findall(r"```(?:python)?\n(.*?)```", text or "", re.S)
    code = max(blocks, key=len) if blocks else (text or "")
    # keep the prompt's imports (typing etc.) available
    imports = "\n".join(l for l in prompt.splitlines() if l.startswith(("import ", "from ")))
    return imports + "\n\n" + code


def run_python(program: str, timeout: float = 10.0) -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "prog.py")
        open(path, "w").write(program)
        try:
            p = subprocess.run([sys.executable, path], capture_output=True, text=True, timeout=timeout, cwd=d)
        except subprocess.TimeoutExpired:
            return False, "Timed out (possible infinite loop)."
        return p.returncode == 0, (p.stderr or p.stdout)[-1500:]


def visible_check(code: str, prob: dict) -> tuple[bool, str]:
    """Run the docstring examples; report every failing example (what an evaluator would show)."""
    program = code + "\n\nfailures = []\n"
    for src, want in prob["visible"]:
        program += (f"try:\n    _got = ({src})\n    if _got != ({want}):\n"
                    f"        failures.append({src!r} + ' returned ' + repr(_got) + ', expected ' + {want!r})\n"
                    f"except Exception as _e:\n    failures.append({src!r} + ' raised ' + repr(_e))\n")
    program += ("import sys\nif failures:\n    print('Failed examples:\\n' + '\\n'.join(failures), file=sys.stderr)"
                "\n    sys.exit(1)\n")
    return run_python(program)


def hidden_check(code: str, prob: dict) -> bool:
    ok, _ = run_python(code + "\n\n" + prob["test"] + f"\n\ncheck({prob['entry_point']})\n")
    return ok


# ---------------------------------------------------------------------------
# Model calls
# ---------------------------------------------------------------------------

class LLM:
    def __init__(self, base_url, model, extra):
        self.client = OpenAI(base_url=base_url, api_key=os.getenv("OPENAI_API_KEY", "not-needed"))
        self.model, self.extra = model, extra

    def chat(self, messages, stats) -> str:
        r = self.client.chat.completions.create(model=self.model, messages=messages, temperature=0.8,
                                                top_p=0.95, max_tokens=1200, extra_body=self.extra)
        stats["calls"] += 1
        if r.usage:
            stats["tokens"] += r.usage.prompt_tokens + r.usage.completion_tokens
        return r.choices[0].message.content or ""


def first_attempt(llm, prob, stats) -> tuple[list, str]:
    msgs = [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"Complete this function:\n\n```python\n{prob['prompt']}```"}]
    reply = llm.chat(msgs, stats)
    return msgs + [{"role": "assistant", "content": reply}], extract_code(reply, prob["prompt"])


def single(llm, prob, stats):
    return first_attempt(llm, prob, stats)[1]


def self_refine(llm, prob, stats):
    msgs, code = first_attempt(llm, prob, stats)
    msgs.append({"role": "user", "content": "Review your solution carefully for bugs and unhandled edge cases "
                 "against the specification. Then reply with the corrected complete function in one ```python "
                 "block (or the same code if it is already correct)."})
    return extract_code(llm.chat(msgs, stats), prob["prompt"])


def test_feedback(llm, prob, stats, retries=2):
    msgs, code = first_attempt(llm, prob, stats)
    for _ in range(retries):
        ok, err = visible_check(code, prob)
        stats["test_runs"] += 1
        if ok:
            break
        msgs.append({"role": "user", "content": "Running the examples from the docstring against your code "
                     f"failed:\n\n{err}\n\nFix the function and reply with the complete corrected function "
                     "in one ```python block."})
        reply = llm.chat(msgs, stats)
        msgs.append({"role": "assistant", "content": reply})
        code = extract_code(reply, prob["prompt"])
    return code


def best_of_n(llm, prob, stats, n=3):
    candidates = [first_attempt(llm, prob, stats)[1] for _ in range(n)]
    for c in candidates:
        stats["test_runs"] += 1
        if visible_check(c, prob)[0]:
            return c
    return candidates[0]


STRATEGIES = {"single": single, "self_refine": self_refine, "test_feedback": test_feedback, "best_of_n": best_of_n}


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def bootstrap_ci(xs, iters=5000, seed=0):
    rng = random.Random(seed)
    means = sorted(sum(rng.choice(xs) for _ in xs) / len(xs) for _ in range(iters))
    return means[int(0.025 * iters)], means[int(0.975 * iters)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-url", default=os.getenv("OPENAI_BASE_URL", "http://localhost:8080/v1"))
    ap.add_argument("--model", default=os.getenv("MODEL", "mlx-community/Qwen3-8B-4bit"))
    ap.add_argument("--no-thinking", action="store_true")
    ap.add_argument("--strategies", default="single,self_refine,test_feedback,best_of_n")
    ap.add_argument("--limit", type=int, default=40)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--workers", type=int, default=1, help="parallel problems (if your server batches)")
    args = ap.parse_args()

    extra = {"chat_template_kwargs": {"enable_thinking": False}} if args.no_thinking else None
    llm = LLM(args.base_url, args.model, extra)
    probs = load_problems(args.limit, args.seed)
    print(f"model={args.model}  problems={len(probs)}\n", flush=True)

    results = {}
    for name in args.strategies.split(","):
        fn = STRATEGIES[name]
        t0 = time.time()

        def solve(prob):
            stats = {"calls": 0, "tokens": 0, "test_runs": 0}
            code = fn(llm, prob, stats)
            return hidden_check(code, prob), stats

        with ThreadPoolExecutor(args.workers) as ex:
            out = list(ex.map(solve, probs))
        passed = [int(ok) for ok, _ in out]
        lo, hi = bootstrap_ci(passed)
        results[name] = passed
        n = len(probs)
        print(f"[{name:13s}] pass={sum(passed)/n:.3f} [{lo:.3f}, {hi:.3f}]  "
              f"calls/prob={sum(s['calls'] for _, s in out)/n:.2f}  "
              f"tokens/prob={sum(s['tokens'] for _, s in out)/n:.0f}  "
              f"sec/prob={(time.time()-t0)/n:.1f}", flush=True)

    if "single" in results:
        base = results["single"]
        print("\npaired difference vs single (95% bootstrap CI):")
        for name, passed in results.items():
            if name == "single":
                continue
            diffs = [a - b for a, b in zip(passed, base)]
            lo, hi = bootstrap_ci(diffs)
            print(f"  {name:13s} {sum(diffs)/len(diffs):+.3f} [{lo:+.3f}, {hi:+.3f}]  "
                  f"(fixed {sum(d > 0 for d in diffs)}, broke {sum(d < 0 for d in diffs)})")
    json.dump({k: v for k, v in results.items()}, open("results.json", "w"))


if __name__ == "__main__":
    main()
