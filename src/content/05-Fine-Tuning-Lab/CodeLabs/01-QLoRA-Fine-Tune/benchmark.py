"""Base-vs-tuned benchmark: quality proxy, tokens/sec, and peak VRAM.

Loads the same base model twice - once untouched, once with the LoRA
adapter from train_qlora.py merged in - and runs both through the same
held-out eval prompts. Prints a single comparison table covering a
quality proxy (ROUGE-L against the reference response), measured
throughput (tokens/sec, with a warm-up pass excluded), and peak VRAM
(read from torch.cuda.max_memory_allocated, not estimated).

Usage:
    python benchmark.py --adapter-dir ./qlora-adapter
    python benchmark.py --adapter-dir ./qlora-adapter --eval-file eval_holdout.jsonl
"""

import argparse
import json
import time

import torch
from datasets import Dataset, load_dataset
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

try:
    import evaluate
    ROUGE = evaluate.load("rouge")
except ImportError:
    ROUGE = None

# Same demo examples as train_qlora.py, used as eval prompts when no --eval-file is given.
DEMO_EVAL_EXAMPLES = [
    {"instruction": "How do I reset my account password?",
     "response": "Go to Settings > Security > Reset Password, then follow the emailed link. "
                  "The link expires after 30 minutes."},
    {"instruction": "Can I export my data before closing my account?",
     "response": "Yes. Go to Settings > Data > Export All Data. The export is emailed as a ZIP "
                  "file within 24 hours, and is available for 7 days after account closure."},
    {"instruction": "Is there a way to invite teammates to my workspace?",
     "response": "Yes, go to Settings > Team > Invite Members and enter their email addresses. "
                  "Invited members appear as Pending until they accept."},
]


def parse_args():
    parser = argparse.ArgumentParser(description="Benchmark base model vs QLoRA-tuned model.")
    parser.add_argument("--base-model", type=str, default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument("--adapter-dir", type=str, required=True,
                         help="Directory containing the saved LoRA adapter from train_qlora.py.")
    parser.add_argument("--eval-file", type=str, default=None,
                         help="JSONL file with 'instruction'/'response' fields. "
                              "Falls back to a small built-in demo eval set if omitted.")
    parser.add_argument("--max-new-tokens", type=int, default=128)
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--gpu-hourly-rate", type=float, default=1.10,
                         help="Used only to compute an illustrative cost-per-1k-requests figure.")
    return parser.parse_args()


def load_eval_set(eval_file: str | None) -> Dataset:
    if eval_file:
        return load_dataset("json", data_files=eval_file, split="train")
    print(f"No --eval-file provided - using {len(DEMO_EVAL_EXAMPLES)} built-in demo eval prompts.")
    return Dataset.from_list(DEMO_EVAL_EXAMPLES)


def load_base(base_model: str):
    tokenizer = AutoTokenizer.from_pretrained(base_model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
        device_map="auto" if torch.cuda.is_available() else None,
    )
    model.eval()
    return model, tokenizer


def load_tuned(base_model: str, adapter_dir: str):
    """Load the base model, attach the adapter, and merge it into a standalone model."""
    model, tokenizer = load_base(base_model)
    peft_model = PeftModel.from_pretrained(model, adapter_dir)
    merged = peft_model.merge_and_unload()
    merged.eval()
    return merged, tokenizer


def generate_response(model, tokenizer, instruction: str, max_new_tokens: int) -> str:
    messages = [{"role": "user", "content": instruction}]
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        output = model.generate(
            **inputs, max_new_tokens=max_new_tokens, do_sample=False,
            pad_token_id=tokenizer.pad_token_id,
        )
    new_tokens = output[0][inputs["input_ids"].shape[1]:]
    return tokenizer.decode(new_tokens, skip_special_tokens=True), new_tokens.shape[0]


def run_eval(model, tokenizer, eval_examples, max_new_tokens: int, warmup: int):
    """Runs generation over every eval example, measuring quality proxy + throughput + VRAM."""
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()

    predictions, references = [], []

    # Warm-up pass: absorbs one-time CUDA kernel compilation cost, excluded from timing.
    for example in eval_examples[:warmup]:
        generate_response(model, tokenizer, example["instruction"], max_new_tokens)

    total_tokens, total_time = 0, 0.0
    for example in eval_examples:
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        start = time.perf_counter()
        text, n_new_tokens = generate_response(model, tokenizer, example["instruction"], max_new_tokens)
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        elapsed = time.perf_counter() - start

        total_tokens += n_new_tokens
        total_time += elapsed
        predictions.append(text)
        references.append(example["response"])

    tokens_per_sec = total_tokens / total_time if total_time > 0 else 0.0
    avg_latency = total_time / len(eval_examples)
    peak_vram_gb = (
        torch.cuda.max_memory_allocated() / 1e9 if torch.cuda.is_available() else 0.0
    )

    quality = ROUGE.compute(predictions=predictions, references=references) if ROUGE else {}

    return {
        "tokens_per_sec": tokens_per_sec,
        "avg_latency_sec": avg_latency,
        "peak_vram_gb": peak_vram_gb,
        "rougeL": quality.get("rougeL", float("nan")),
        "sample_predictions": list(zip(references, predictions))[:2],
    }


def cost_per_1k_requests(tokens_per_sec: float, avg_output_tokens: float, gpu_hourly_rate: float) -> float:
    if tokens_per_sec <= 0:
        return float("nan")
    seconds_per_request = avg_output_tokens / tokens_per_sec
    total_hours = (seconds_per_request * 1000) / 3600
    return total_hours * gpu_hourly_rate


def print_comparison(base_metrics: dict, tuned_metrics: dict, avg_output_tokens: float, gpu_hourly_rate: float):
    base_cost = cost_per_1k_requests(base_metrics["tokens_per_sec"], avg_output_tokens, gpu_hourly_rate)
    tuned_cost = cost_per_1k_requests(tuned_metrics["tokens_per_sec"], avg_output_tokens, gpu_hourly_rate)

    print("\n" + "=" * 72)
    print(f"{'Metric':<28}{'Base':>18}{'Tuned':>18}")
    print("=" * 72)
    print(f"{'ROUGE-L (quality proxy)':<28}{base_metrics['rougeL']:>18.4f}{tuned_metrics['rougeL']:>18.4f}")
    print(f"{'Tokens/sec':<28}{base_metrics['tokens_per_sec']:>18.2f}{tuned_metrics['tokens_per_sec']:>18.2f}")
    print(f"{'Avg latency (sec/req)':<28}{base_metrics['avg_latency_sec']:>18.3f}{tuned_metrics['avg_latency_sec']:>18.3f}")
    print(f"{'Peak VRAM (GB)':<28}{base_metrics['peak_vram_gb']:>18.2f}{tuned_metrics['peak_vram_gb']:>18.2f}")
    print(f"{'Est. cost / 1k requests':<28}{'$' + format(base_cost, '.4f'):>18}{'$' + format(tuned_cost, '.4f'):>18}")
    print("=" * 72)

    print("\nSample completions (reference vs tuned model output):")
    for ref, pred in tuned_metrics["sample_predictions"]:
        print(f"  reference: {ref[:80]}...")
        print(f"  tuned:     {pred[:80]}...\n")


def main():
    args = parse_args()
    eval_ds = load_eval_set(args.eval_file)
    eval_examples = list(eval_ds)
    avg_output_tokens = sum(len(e["response"].split()) for e in eval_examples) / len(eval_examples) * 1.3

    print(f"Evaluating on {len(eval_examples)} held-out prompts.\n")

    print("Loading base model...")
    base_model, base_tokenizer = load_base(args.base_model)
    print("Running base model eval...")
    base_metrics = run_eval(base_model, base_tokenizer, eval_examples, args.max_new_tokens, args.warmup)
    del base_model
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    print("Loading tuned (adapter-merged) model...")
    tuned_model, tuned_tokenizer = load_tuned(args.base_model, args.adapter_dir)
    print("Running tuned model eval...")
    tuned_metrics = run_eval(tuned_model, tuned_tokenizer, eval_examples, args.max_new_tokens, args.warmup)

    print_comparison(base_metrics, tuned_metrics, avg_output_tokens, args.gpu_hourly_rate)


if __name__ == "__main__":
    main()
