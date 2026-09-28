"""Train the small GPT in model.py on character-level (byte-level) text.

    python train.py                             # Tiny Shakespeare, default ~9.5M-param model (GPU recommended)
    python train.py --preset tiny --steps 400   # CPU smoke test (~10 seconds on a laptop)
    python train.py --compile             # torch.compile the model (GPU recommended)

What it demonstrates: byte-level tokenization, random-window batching, AdamW with
decoupled weight decay, warmup + cosine LR schedule, gradient clipping, bf16 autocast
on GPUs, torch.compile, periodic validation, safetensors checkpoints, and sampling.
"""
import argparse
import math
import os
import time
import urllib.request

import torch
from safetensors.torch import save_file

from model import GPT, GPTConfig

DATA_URL = "https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt"

PRESETS = {
    # ~9.5M params: the default; a few thousand steps on one GPU
    "small": dict(n_layer=6, n_head=6, n_kv_head=2, d_model=384, block_size=256),
    # ~0.4M params: CPU smoke test - loss falls from ~5.5 (= ln 256, uniform guessing) to ~1.9 in 400 steps
    "tiny": dict(n_layer=2, n_head=4, n_kv_head=2, d_model=128, block_size=64),
}


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--preset", choices=PRESETS, default="small")
    p.add_argument("--data", default="data/input.txt")
    p.add_argument("--steps", type=int, default=3000)
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--min-lr", type=float, default=1e-4)
    p.add_argument("--warmup", type=int, default=100)
    p.add_argument("--weight-decay", type=float, default=0.1)
    p.add_argument("--grad-clip", type=float, default=1.0)
    p.add_argument("--eval-every", type=int, default=250)
    p.add_argument("--eval-batches", type=int, default=20)
    p.add_argument("--out", default="checkpoints")
    p.add_argument("--compile", action="store_true")
    p.add_argument("--seed", type=int, default=1337)
    return p.parse_args()


def load_bytes(path: str) -> torch.Tensor:
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        print(f"downloading Tiny Shakespeare -> {path}")
        urllib.request.urlretrieve(DATA_URL, path)
    raw = open(path, "rb").read()
    # Byte-level "tokenizer": every byte is a token, vocab size 256. No OOV, no training.
    return torch.tensor(list(raw), dtype=torch.long)


def get_batch(data: torch.Tensor, block_size: int, batch_size: int, device):
    ix = torch.randint(len(data) - block_size - 1, (batch_size,))
    x = torch.stack([data[i : i + block_size] for i in ix])
    y = torch.stack([data[i + 1 : i + 1 + block_size] for i in ix])  # targets = inputs shifted by one
    return x.to(device, non_blocking=True), y.to(device, non_blocking=True)


def lr_at(step: int, args) -> float:
    """Linear warmup, then cosine decay to min_lr."""
    if step < args.warmup:
        return args.lr * (step + 1) / args.warmup
    progress = (step - args.warmup) / max(1, args.steps - args.warmup)
    return args.min_lr + 0.5 * (args.lr - args.min_lr) * (1 + math.cos(math.pi * min(progress, 1.0)))


def build_optimizer(model: GPT, args):
    # Decay matrices only; norms and embeddings-as-vectors are left undecayed (common practice)
    decay = [p for p in model.parameters() if p.dim() >= 2]
    no_decay = [p for p in model.parameters() if p.dim() < 2]
    groups = [{"params": decay, "weight_decay": args.weight_decay}, {"params": no_decay, "weight_decay": 0.0}]
    fused = torch.cuda.is_available()  # fused AdamW kernel on CUDA
    return torch.optim.AdamW(groups, lr=args.lr, betas=(0.9, 0.95), fused=fused)


@torch.no_grad()
def evaluate(model, splits, args, device, autocast):
    model.eval()
    out = {}
    for name, data in splits.items():
        losses = []
        for _ in range(args.eval_batches):
            x, y = get_batch(data, model.cfg.block_size, args.batch_size, device)
            with autocast:
                _, loss = model(x, y)
            losses.append(loss.item())
        out[name] = sum(losses) / len(losses)
    model.train()
    return out


def main():
    args = parse_args()
    torch.manual_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    # bf16 autocast on GPUs that support it; plain fp32 on CPU. bf16 needs no GradScaler.
    use_bf16 = device.type == "cuda" and torch.cuda.is_bf16_supported()
    autocast = torch.autocast(device_type=device.type, dtype=torch.bfloat16, enabled=use_bf16)
    if device.type == "cuda":
        torch.backends.cuda.matmul.allow_tf32 = True

    data = load_bytes(args.data)
    split = int(0.9 * len(data))
    splits = {"train": data[:split], "val": data[split:]}

    cfg = GPTConfig(**PRESETS[args.preset])
    model = GPT(cfg).to(device)
    print(f"device={device} bf16={use_bf16} params={model.num_params() / 1e6:.2f}M preset={args.preset}")
    train_model = torch.compile(model) if args.compile else model
    optimizer = build_optimizer(model, args)

    start = time.time()
    for step in range(args.steps):
        for group in optimizer.param_groups:
            group["lr"] = lr_at(step, args)

        x, y = get_batch(splits["train"], cfg.block_size, args.batch_size, device)
        with autocast:
            _, loss = train_model(x, y)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), args.grad_clip)
        optimizer.step()

        if step % 50 == 0:
            tok_s = (step + 1) * args.batch_size * cfg.block_size / (time.time() - start)
            print(f"step {step:5d} | loss {loss.item():.4f} | grad-norm {grad_norm:.2f} | lr {lr_at(step, args):.2e} | {tok_s:,.0f} tok/s")
        if (step + 1) % args.eval_every == 0 or step == args.steps - 1:
            losses = evaluate(model, splits, args, device, autocast)
            print(f"eval  {step + 1:5d} | train {losses['train']:.4f} | val {losses['val']:.4f}")

    # safetensors: no pickle, so loading a checkpoint cannot execute code
    os.makedirs(args.out, exist_ok=True)
    state = {k: v.contiguous() for k, v in model.state_dict().items() if k != "lm_head.weight"}  # tied to embed
    save_file(state, os.path.join(args.out, "model.safetensors"), metadata={k: str(v) for k, v in vars(cfg).items()})
    print(f"saved {args.out}/model.safetensors")

    prompt = torch.tensor([list(b"ROMEO:")], device=device)
    sample = model.generate(prompt, max_new_tokens=300, temperature=0.8, top_k=50)
    print("\n--- sample ---\n" + bytes(sample[0].tolist()).decode("utf-8", errors="replace"))


if __name__ == "__main__":
    main()
