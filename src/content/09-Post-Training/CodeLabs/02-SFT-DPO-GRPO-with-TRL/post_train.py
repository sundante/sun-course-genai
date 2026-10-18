"""SFT -> DPO -> GRPO with Hugging Face TRL, on a small open model with LoRA.

The three stages of modern post-training in one script:

    python post_train.py sft  --output-dir runs/sft
    python post_train.py dpo  --model runs/sft/merged --output-dir runs/dpo
    python post_train.py grpo --model runs/dpo/merged --output-dir runs/grpo

    # CPU smoke test of any stage (tiny random model, a handful of examples):
    python post_train.py grpo --model trl-internal-testing/tiny-Qwen3ForCausalLM --smoke

Datasets (downloaded from the Hugging Face Hub):
    sft  - trl-lib/Capybara               multi-turn chat demonstrations
    dpo  - trl-lib/ultrafeedback_binarized (prompt, chosen, rejected) preference pairs
    grpo - openai/gsm8k                    grade-school math with checkable answers

GRPO uses two programmatic rewards (RL with verifiable rewards): the final number
must match the reference answer, and the answer must follow the requested format.
"""
import argparse
import re

import torch
from datasets import load_dataset
from peft import LoraConfig
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import DPOConfig, DPOTrainer, GRPOConfig, GRPOTrainer, SFTConfig, SFTTrainer

SYSTEM_MATH = (
    "Solve the problem. Think step by step, then give the final numeric answer "
    "on its own last line in the form: #### <number>"
)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("stage", choices=["sft", "dpo", "grpo"])
    p.add_argument("--model", default="Qwen/Qwen3-0.6B")
    p.add_argument("--output-dir", default=None)
    p.add_argument("--max-samples", type=int, default=2000)
    p.add_argument("--max-steps", type=int, default=-1)
    p.add_argument("--lr", type=float, default=None)
    p.add_argument("--lora-r", type=int, default=16)
    p.add_argument("--smoke", action="store_true", help="8 examples, 2 steps, no downloads beyond the data")
    args = p.parse_args()
    args.output_dir = args.output_dir or f"runs/{args.stage}"
    if args.smoke:
        args.max_samples, args.max_steps = 8, 2
    return args


def lora(r: int) -> LoraConfig:
    return LoraConfig(r=r, lora_alpha=2 * r, lora_dropout=0.05, target_modules="all-linear", task_type="CAUSAL_LM")


def load_model(name: str):
    """Load the policy explicitly: bf16 on GPUs that support it, fp32 otherwise.
    (Passing a model *name* to the TRL trainers also works; loading it yourself makes the dtype explicit.)"""
    use_bf16 = torch.cuda.is_available() and torch.cuda.is_bf16_supported()
    model = AutoModelForCausalLM.from_pretrained(name, dtype=torch.bfloat16 if use_bf16 else torch.float32)
    tokenizer = AutoTokenizer.from_pretrained(name)
    return model, tokenizer


def common(args, **overrides):
    """Settings shared by all three TRL config classes."""
    kw = dict(
        output_dir=args.output_dir,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
        num_train_epochs=1,
        max_steps=args.max_steps,
        logging_steps=5,
        save_strategy="no",
        report_to=[],
        bf16=torch.cuda.is_available() and torch.cuda.is_bf16_supported(),
    )
    if args.smoke:
        kw.update(per_device_train_batch_size=2, gradient_accumulation_steps=1, logging_steps=1)
    kw.update(overrides)
    return kw


# ---------------------------------------------------------------- SFT
def run_sft(args):
    ds = load_dataset("trl-lib/Capybara", split="train").select(range(args.max_samples))
    config = SFTConfig(
        **common(args, learning_rate=args.lr or 2e-4),
        max_length=1024,
        assistant_only_loss=False,  # set True if the chat template marks assistant spans ({% generation %})
        packing=False,
    )
    model, tok = load_model(args.model)
    trainer = SFTTrainer(model=model, processing_class=tok, args=config, train_dataset=ds, peft_config=lora(args.lora_r))
    trainer.train()
    return trainer


# ---------------------------------------------------------------- DPO
def run_dpo(args):
    ds = load_dataset("trl-lib/ultrafeedback_binarized", split="train").select(range(args.max_samples))
    config = DPOConfig(
        **common(args, learning_rate=args.lr or 5e-6),
        beta=0.1,  # strength of the implicit KL anchor to the reference model
        max_length=1024,
    )
    # With a LoRA adapter, TRL uses the frozen base weights (adapter disabled) as the reference
    # model, so no second copy of the model is loaded.
    model, tok = load_model(args.model)
    trainer = DPOTrainer(model=model, processing_class=tok, args=config, train_dataset=ds, peft_config=lora(args.lora_r))
    trainer.train()
    return trainer


# ---------------------------------------------------------------- GRPO
ANSWER_RE = re.compile(r"####\s*(-?[\d,]*\.?\d+)")


def gsm8k_prompts(split: str, n: int):
    ds = load_dataset("openai/gsm8k", "main", split=split).select(range(n))

    def to_prompt(ex):
        return {
            "prompt": [{"role": "system", "content": SYSTEM_MATH}, {"role": "user", "content": ex["question"]}],
            "solution": ex["answer"].split("####")[-1].strip().replace(",", ""),
        }

    return ds.map(to_prompt, remove_columns=ds.column_names)


def _text(completion) -> str:
    # Conversational datasets yield completions as [{"role": "assistant", "content": ...}]
    return completion[0]["content"] if isinstance(completion, list) else completion


def correctness_reward(completions, solution, **kwargs):
    """1.0 if the #### answer equals the reference number, else 0.0 - a verifiable reward."""
    rewards = []
    for completion, sol in zip(completions, solution):
        m = ANSWER_RE.findall(_text(completion))
        pred = m[-1].replace(",", "") if m else None
        try:
            rewards.append(1.0 if pred is not None and float(pred) == float(sol) else 0.0)
        except ValueError:
            rewards.append(0.0)
    return rewards


def format_reward(completions, **kwargs):
    """0.2 if the last non-empty line is exactly '#### <number>' - rewards following the protocol."""
    out = []
    for completion in completions:
        lines = [l for l in _text(completion).strip().splitlines() if l.strip()]
        out.append(0.2 if lines and re.fullmatch(r"####\s*-?[\d,]*\.?\d+", lines[-1].strip()) else 0.0)
    return out


def run_grpo(args):
    ds = gsm8k_prompts("train", args.max_samples)
    config = GRPOConfig(
        **common(args, learning_rate=args.lr or 1e-5),
        num_generations=2 if args.smoke else 8,  # group size G: samples per prompt
        max_completion_length=32 if args.smoke else 512,
        # TRL's defaults already follow DAPO: token-level loss and no KL term (beta=0.0).
        # Set beta > 0 to add a KL penalty to the reference model.
    )
    if args.smoke:
        config.per_device_train_batch_size = 2  # must be divisible by num_generations
    model, tok = load_model(args.model)
    trainer = GRPOTrainer(
        model=model,
        processing_class=tok,
        reward_funcs=[correctness_reward, format_reward],
        args=config,
        train_dataset=ds,
        peft_config=lora(args.lora_r),
    )
    trainer.train()
    return trainer


def main():
    args = parse_args()
    trainer = {"sft": run_sft, "dpo": run_dpo, "grpo": run_grpo}[args.stage](args)
    # Merge the LoRA adapter so the next stage (or vLLM) can load a plain model
    merged = trainer.model.merge_and_unload()
    merged.save_pretrained(f"{args.output_dir}/merged")
    trainer.processing_class.save_pretrained(f"{args.output_dir}/merged")
    print(f"saved {args.output_dir}/merged")


if __name__ == "__main__":
    main()
