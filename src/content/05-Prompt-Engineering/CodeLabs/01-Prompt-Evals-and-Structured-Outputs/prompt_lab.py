"""Prompt evals and structured outputs on a small local model.

Runs four prompt variants over the same labelled test set and reports, for each:
  - valid-output rate (parses as JSON with an allowed category)
  - accuracy (invalid outputs count as wrong), with a 95% bootstrap CI
  - a paired bootstrap CI on the accuracy difference versus the baseline

Variants:
  zero_free         zero-shot instruction, free generation, parse the JSON ourselves
  few_free          + few-shot examples as prior chat turns
  zero_constrained  zero-shot, decoding constrained to the JSON schema (Outlines)
  few_constrained   few-shot + constrained decoding

Usage:
  python prompt_lab.py                                  # Qwen/Qwen3-0.6B, all variants
  python prompt_lab.py --model Qwen/Qwen3-1.7B --variants zero_free,few_free
  python prompt_lab.py --limit 8                        # quick smoke test
"""

import argparse
import json
import random
import re
import time
from typing import Literal

import torch
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer

from tickets import CATEGORIES, split

SYSTEM = (
    "You classify customer-support tickets. "
    "Categories: billing (payments, invoices, refunds, plans), "
    "bug (something is broken or behaves incorrectly), "
    "account_access (login, passwords, 2FA, SSO, permissions to get in), "
    "feature_request (asks for something the product does not do yet). "
    'Reply with JSON only, in the form {"category": "<one of the four>"}.'
)


class TicketLabel(BaseModel):
    category: Literal["billing", "bug", "account_access", "feature_request"]


def build_messages(ticket: str, shots: list[tuple[str, str]]) -> list[dict]:
    msgs = [{"role": "system", "content": SYSTEM}]
    for text, label in shots:  # few-shot examples as prior turns
        msgs.append({"role": "user", "content": f"Ticket: {text}"})
        msgs.append({"role": "assistant", "content": json.dumps({"category": label})})
    msgs.append({"role": "user", "content": f"Ticket: {ticket}"})
    return msgs


def render(tok, msgs) -> str:
    kwargs = {"tokenize": False, "add_generation_prompt": True}
    try:  # Qwen3: turn off the thinking block for a classification task
        return tok.apply_chat_template(msgs, enable_thinking=False, **kwargs)
    except TypeError:
        return tok.apply_chat_template(msgs, **kwargs)


def parse(raw: str) -> str | None:
    """Pull the first JSON object out of free text and validate it."""
    match = re.search(r"\{.*?\}", raw, re.S)
    if not match:
        return None
    try:
        return TicketLabel.model_validate_json(match.group(0)).category
    except Exception:
        return None


def bootstrap_ci(values, n=2000, seed=0):
    rng = random.Random(seed)
    k = len(values)
    means = sorted(sum(rng.choices(values, k=k)) / k for _ in range(n))
    return means[int(0.025 * n)], means[int(0.975 * n)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen3-0.6B")
    ap.add_argument("--variants", default="zero_free,few_free,zero_constrained,few_constrained")
    ap.add_argument("--limit", type=int, default=0, help="use only the first N test items")
    ap.add_argument("--max-new-tokens", type=int, default=24)
    args = ap.parse_args()

    device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
    dtype = torch.bfloat16 if device == "cuda" else torch.float32
    tok = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(args.model, dtype=dtype).to(device).eval()

    pool, test = split()
    random.Random(0).shuffle(test)  # interleave categories so --limit is balanced-ish
    if args.limit:
        test = test[: args.limit]
    variants = args.variants.split(",")

    constrained = None
    if any(v.endswith("constrained") for v in variants):
        import outlines  # imported lazily so free-only runs don't need it

        constrained = outlines.from_transformers(model, tok)

    results = {}
    for variant in variants:
        shots = pool if variant.startswith("few") else []
        correct, valid, t0 = [], [], time.time()
        for ticket, gold in test:
            prompt = render(tok, build_messages(ticket, shots))
            if variant.endswith("constrained"):
                raw = constrained(prompt, output_type=TicketLabel, max_new_tokens=args.max_new_tokens)
            else:
                ids = tok(prompt, return_tensors="pt").to(device)
                with torch.no_grad():
                    out = model.generate(**ids, max_new_tokens=args.max_new_tokens, do_sample=False)
                raw = tok.decode(out[0, ids["input_ids"].shape[1]:], skip_special_tokens=True)
            pred = parse(raw)
            valid.append(int(pred is not None))
            correct.append(int(pred == gold))
        results[variant] = correct
        lo, hi = bootstrap_ci(correct)
        print(
            f"{variant:18s} valid={sum(valid) / len(valid):6.1%}  "
            f"acc={sum(correct) / len(correct):6.1%}  95% CI [{lo:.1%}, {hi:.1%}]  "
            f"({time.time() - t0:.0f}s, n={len(correct)})"
        )

    base = variants[0]
    for variant in variants[1:]:
        diffs = [a - b for a, b in zip(results[variant], results[base])]
        lo, hi = bootstrap_ci(diffs)
        verdict = "significant" if lo > 0 or hi < 0 else "not significant"
        print(f"{variant} vs {base}: diff={sum(diffs) / len(diffs):+.1%}  95% CI [{lo:+.1%}, {hi:+.1%}]  {verdict}")


if __name__ == "__main__":
    main()
