"""QLoRA fine-tuning script for a small open instruction model.

Demonstrates, in one runnable file, every mechanic covered in the
07-Fine-Tuning-Lab Notes: loading a base model in 4-bit NF4 via
bitsandbytes, attaching a LoRA adapter via peft, formatting and masking
an instruction dataset so loss is only computed on completion tokens,
and running a real training loop (transformers.Trainer) that saves a
small, portable adapter checkpoint.

Default base model is a ~1.5B parameter instruction model small enough
to fine-tune on a single consumer/free-tier GPU (e.g. a T4 or a 4090)
with 4-bit quantization. Swap --base-model for any other causal LM.

Usage:
    python train_qlora.py
    python train_qlora.py --epochs 3 --batch-size 4 --lr 2e-4
    python train_qlora.py --data-file my_instructions.jsonl --output-dir ./qlora-adapter
"""

import argparse
import json
import os

import torch
from datasets import Dataset, load_dataset
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    DataCollatorForSeq2Seq,
    Trainer,
    TrainingArguments,
)

# A tiny built-in instruction dataset used when --data-file is not provided.
# Swap in any (instruction, response) JSONL file via --data-file for a real run -
# this exists so the script is runnable end-to-end with zero external downloads
# beyond the base model itself.
DEMO_EXAMPLES = [
    {"instruction": "How do I reset my account password?",
     "response": "Go to Settings > Security > Reset Password, then follow the emailed link. "
                  "The link expires after 30 minutes."},
    {"instruction": "My payment failed but I was still charged. What do I do?",
     "response": "This is usually a temporary authorization hold that clears within 3-5 business "
                  "days. If it hasn't cleared after 5 days, contact billing support with your "
                  "transaction ID."},
    {"instruction": "Can I export my data before closing my account?",
     "response": "Yes. Go to Settings > Data > Export All Data. The export is emailed as a ZIP "
                  "file within 24 hours, and is available for 7 days after account closure."},
    {"instruction": "The app crashes every time I open the reports tab.",
     "response": "Try clearing the app cache first (Settings > Storage > Clear Cache). If the "
                  "crash continues, please send the crash log from Settings > Support > Diagnostics "
                  "so we can investigate."},
    {"instruction": "How do I upgrade from the free plan to Pro?",
     "response": "Go to Settings > Billing > Change Plan, select Pro, and confirm payment. The "
                  "upgrade takes effect immediately and you're billed a prorated amount for the "
                  "remainder of the current cycle."},
    {"instruction": "Is there a way to invite teammates to my workspace?",
     "response": "Yes, go to Settings > Team > Invite Members and enter their email addresses. "
                  "Invited members appear as Pending until they accept."},
    {"instruction": "I'm being charged twice a month for the same subscription.",
     "response": "That usually means two subscriptions are active on the account. Check Settings "
                  "> Billing > Active Subscriptions - if you see a duplicate, cancel one and "
                  "contact billing support for a refund of the overlap."},
    {"instruction": "How long is data retained after I delete a project?",
     "response": "Deleted projects are recoverable for 30 days from Settings > Trash, after which "
                  "they are permanently purged and cannot be restored."},
]


def parse_args():
    parser = argparse.ArgumentParser(description="QLoRA fine-tune a small causal LM.")
    parser.add_argument("--base-model", type=str, default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument("--data-file", type=str, default=None,
                         help="JSONL file with 'instruction'/'response' fields. "
                              "Falls back to a small built-in demo dataset if omitted.")
    parser.add_argument("--output-dir", type=str, default="./qlora-adapter")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--grad-accum-steps", type=int, default=4)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--lora-r", type=int, default=16)
    parser.add_argument("--lora-alpha", type=int, default=32)
    parser.add_argument("--lora-dropout", type=float, default=0.05)
    parser.add_argument("--eval-fraction", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def load_instruction_dataset(data_file: str | None) -> Dataset:
    """Load an instruction/response dataset from a JSONL file, or fall back to the demo set."""
    if data_file:
        return load_dataset("json", data_files=data_file, split="train")

    print("No --data-file provided - using the small built-in demo dataset "
          f"({len(DEMO_EXAMPLES)} examples). Pass --data-file for a real training run.")
    return Dataset.from_list(DEMO_EXAMPLES)


def build_tokenize_fn(tokenizer, max_length: int):
    """Returns a function that formats + tokenizes one example with masked prompt tokens."""

    def tokenize_example(example):
        prompt_messages = [{"role": "user", "content": example["instruction"]}]
        prompt_text = tokenizer.apply_chat_template(
            prompt_messages, tokenize=False, add_generation_prompt=True
        )
        full_text = prompt_text + example["response"] + tokenizer.eos_token

        prompt_ids = tokenizer(prompt_text, add_special_tokens=False)["input_ids"]
        full = tokenizer(
            full_text, truncation=True, max_length=max_length, add_special_tokens=False
        )

        labels = full["input_ids"].copy()
        prompt_len = min(len(prompt_ids), len(labels))
        labels[:prompt_len] = [-100] * prompt_len  # mask prompt tokens out of the loss
        full["labels"] = labels
        return full

    return tokenize_example


def load_quantized_base_model(base_model: str, device_map: str = "auto"):
    """Load the base model in 4-bit NF4 with BF16 compute dtype, prepped for k-bit training."""
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        quantization_config=bnb_config,
        device_map=device_map,
    )
    model = prepare_model_for_kbit_training(model)
    return model


def attach_lora(model, r: int, alpha: int, dropout: float):
    lora_config = LoraConfig(
        r=r,
        lora_alpha=alpha,
        lora_dropout=dropout,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    return model


def main():
    args = parse_args()

    tokenizer = AutoTokenizer.from_pretrained(args.base_model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    raw_ds = load_instruction_dataset(args.data_file)
    tokenize_fn = build_tokenize_fn(tokenizer, args.max_length)
    tokenized_ds = raw_ds.map(tokenize_fn, remove_columns=raw_ds.column_names)

    split = tokenized_ds.train_test_split(test_size=args.eval_fraction, seed=args.seed)
    train_ds, eval_ds = split["train"], split["test"]
    print(f"train examples: {len(train_ds)} | held-out eval examples: {len(eval_ds)}")

    model = load_quantized_base_model(args.base_model)
    model = attach_lora(model, args.lora_r, args.lora_alpha, args.lora_dropout)

    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer, model=model, padding=True, label_pad_token_id=-100
    )

    training_args = TrainingArguments(
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum_steps,
        learning_rate=args.lr,
        bf16=torch.cuda.is_available(),
        logging_steps=1,
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=2,
        optim="paged_adamw_32bit" if torch.cuda.is_available() else "adamw_torch",
        report_to=[],
        seed=args.seed,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        data_collator=data_collator,
    )

    trainer.train()

    final_metrics = trainer.evaluate()
    print(f"Final eval loss: {final_metrics.get('eval_loss'):.4f}")

    os.makedirs(args.output_dir, exist_ok=True)
    model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)

    with open(os.path.join(args.output_dir, "train_config.json"), "w") as f:
        json.dump(vars(args), f, indent=2)

    print(f"Adapter saved to {args.output_dir}")


if __name__ == "__main__":
    main()
