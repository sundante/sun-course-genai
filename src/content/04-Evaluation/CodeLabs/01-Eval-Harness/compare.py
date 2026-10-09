"""Evaluate a base model and a candidate (e.g. fine-tuned) model on the same benchmark items,
then compare them properly: per-task scores with 95% CIs, and a *paired* bootstrap on the
per-item differences.

    python compare.py --base Qwen/Qwen3-0.6B --candidate ../../../08-Post-Training/CodeLabs/02-SFT-DPO-GRPO-with-TRL/runs/grpo/merged
    python compare.py --tasks gsm8k,arc_easy --limit 200
    python compare.py --base trl-internal-testing/tiny-Qwen3ForCausalLM \
                      --candidate trl-internal-testing/tiny-Qwen2ForCausalLM-2.5 --limit 8   # CPU smoke test

Uses EleutherAI's lm-evaluation-harness Python API (lm_eval.simple_evaluate).
"""
import argparse
import json
import random
from statistics import mean

import lm_eval
import torch

# Which filter to read for generative tasks (gsm8k logs one row per answer-extraction filter)
PREFERRED_FILTERS = ["flexible-extract", "strict-match", "none"]


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--base", default="Qwen/Qwen3-0.6B")
    p.add_argument("--candidate", required=False, default=None)
    p.add_argument("--tasks", default="gsm8k,arc_easy")
    p.add_argument("--limit", type=int, default=200, help="items per task (None = full task is slow)")
    p.add_argument("--batch-size", default="auto")
    p.add_argument("--max-gen-toks", type=int, default=512)
    p.add_argument("--chat-template", action="store_true", help="apply the model's chat template (instruct models)")
    p.add_argument("--bootstrap", type=int, default=5000)
    p.add_argument("--out", default="comparison.json")
    return p.parse_args()


def run(model_path: str, args) -> dict:
    """Return {task: {doc_id: score}} for one model."""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = "bfloat16" if device == "cuda" else "float32"
    results = lm_eval.simple_evaluate(
        model="hf",
        model_args=f"pretrained={model_path},dtype={dtype}",
        tasks=args.tasks.split(","),
        limit=args.limit,
        batch_size=args.batch_size if device == "cuda" else 4,
        device=device,
        log_samples=True,
        apply_chat_template=args.chat_template,
        gen_kwargs=f"max_gen_toks={args.max_gen_toks}",
    )
    per_task = {}
    for task, samples in results["samples"].items():
        filters = {s["filter"] for s in samples}
        chosen = next(f for f in PREFERRED_FILTERS + sorted(filters) if f in filters)
        rows = [s for s in samples if s["filter"] == chosen]
        metric = rows[0]["metrics"][0]  # acc for multiple choice, exact_match for gsm8k
        per_task[task] = {"metric": f"{metric} ({chosen})", "scores": {s["doc_id"]: float(s[metric]) for s in rows}}
    return per_task


def ci95(scores: list[float], iters: int, rng: random.Random) -> tuple[float, float]:
    means = sorted(mean(rng.choices(scores, k=len(scores))) for _ in range(iters))
    return means[int(0.025 * iters)], means[int(0.975 * iters)]


def paired(base: dict, cand: dict, iters: int, rng: random.Random) -> dict:
    ids = sorted(set(base) & set(cand))
    diffs = [cand[i] - base[i] for i in ids]
    lo, hi = ci95(diffs, iters, rng)
    return {
        "n": len(ids),
        "mean_diff": mean(diffs),
        "ci95": (lo, hi),
        "candidate_better_items": sum(d > 0 for d in diffs),
        "base_better_items": sum(d < 0 for d in diffs),
        "significant": lo > 0 or hi < 0,
    }


def main():
    args = parse_args()
    rng = random.Random(0)
    report = {}
    base = run(args.base, args)
    cand = run(args.candidate, args) if args.candidate else None

    for task, b in base.items():
        entry = {"metric": b["metric"]}
        for name, res in (("base", b), ("candidate", cand[task] if cand else None)):
            if res is None:
                continue
            vals = list(res["scores"].values())
            entry[name] = {"score": mean(vals), "ci95": ci95(vals, args.bootstrap, rng), "n": len(vals)}
        if cand:
            entry["paired"] = paired(b["scores"], cand[task]["scores"], args.bootstrap, rng)
        report[task] = entry

    for task, e in report.items():
        print(f"\n== {task} [{e['metric']}]")
        for name in ("base", "candidate"):
            if name in e:
                lo, hi = e[name]["ci95"]
                print(f"  {name:<9} {e[name]['score']:.3f}  (95% CI {lo:.3f}-{hi:.3f}, n={e[name]['n']})")
        if "paired" in e:
            p = e["paired"]
            lo, hi = p["ci95"]
            verdict = "significant" if p["significant"] else "not significant"
            print(f"  paired diff {p['mean_diff']:+.3f}  (95% CI {lo:+.3f} to {hi:+.3f}) -> {verdict}; "
                  f"candidate better on {p['candidate_better_items']} items, base on {p['base_better_items']}")

    with open(args.out, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
