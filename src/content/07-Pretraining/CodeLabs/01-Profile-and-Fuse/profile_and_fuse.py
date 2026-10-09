"""Lab 04-01 - profile a GPT training step, then fuse its memory-bound tail.

Part A profiles one training step of a small GPT with torch.profiler and prints where the time goes.
Part B benchmarks the elementwise chain at the end of a SwiGLU feed-forward block -
    out = rms_norm(silu(gate) * up + residual) * weight
three ways: eager PyTorch (one kernel per op), torch.compile (fused by Inductor), and - on a CUDA
GPU - a hand-written Triton kernel. Speedups are reported as medians with bootstrap 95% CIs.

Run:  python profile_and_fuse.py                 # auto: cuda if available, else cpu
      python profile_and_fuse.py --device cpu --rows 4096 --cols 4096
"""
import argparse
import statistics
import time

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.profiler import ProfilerActivity, profile


# ----------------------------------------------------------------------------- Part A model

class Block(nn.Module):
    def __init__(self, d: int, heads: int):
        super().__init__()
        self.heads = heads
        self.norm1, self.norm2 = nn.RMSNorm(d), nn.RMSNorm(d)
        self.qkv, self.proj = nn.Linear(d, 3 * d, bias=False), nn.Linear(d, d, bias=False)
        self.gate_up, self.down = nn.Linear(d, 2 * 4 * d, bias=False), nn.Linear(4 * d, d, bias=False)

    def forward(self, x):
        B, T, D = x.shape
        q, k, v = self.qkv(self.norm1(x)).view(B, T, 3, self.heads, D // self.heads).unbind(2)
        a = F.scaled_dot_product_attention(q.transpose(1, 2), k.transpose(1, 2), v.transpose(1, 2), is_causal=True)
        x = x + self.proj(a.transpose(1, 2).reshape(B, T, D))
        gate, up = self.gate_up(self.norm2(x)).chunk(2, dim=-1)
        return x + self.down(F.silu(gate) * up)


class TinyGPT(nn.Module):
    def __init__(self, vocab=8192, d=256, heads=4, layers=4):
        super().__init__()
        self.emb = nn.Embedding(vocab, d)
        self.blocks = nn.ModuleList(Block(d, heads) for _ in range(layers))
        self.norm, self.head = nn.RMSNorm(d), nn.Linear(d, vocab, bias=False)

    def forward(self, idx):
        x = self.emb(idx)
        for b in self.blocks:
            x = b(x)
        return self.head(self.norm(x))


def part_a(device: str, steps: int = 4):
    torch.manual_seed(0)
    model = TinyGPT().to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=3e-4)
    idx = torch.randint(0, 8192, (8, 256), device=device)

    def step():
        loss = F.cross_entropy(model(idx[:, :-1]).flatten(0, 1), idx[:, 1:].flatten())
        loss.backward()
        opt.step()
        opt.zero_grad(set_to_none=True)

    step()                                                   # warm-up outside the profile
    acts = [ProfilerActivity.CPU] + ([ProfilerActivity.CUDA] if device == "cuda" else [])
    with profile(activities=acts) as prof:
        for _ in range(steps):
            step()
        sync(device)
    key = "cuda_time_total" if device == "cuda" else "self_cpu_time_total"
    print(f"\n=== Part A: top operators over {steps} training steps ({device}) ===")
    print(prof.key_averages().table(sort_by=key, row_limit=12, max_name_column_width=40))
    prof.export_chrome_trace("trace.json")
    print("Full timeline written to trace.json - open it at https://ui.perfetto.dev")


# ----------------------------------------------------------------------------- Part B kernels

def tail_eager(gate, up, residual, weight, eps=1e-6):
    h = F.silu(gate) * up + residual                         # 3 elementwise kernels, each a full HBM round trip
    return h * torch.rsqrt(h.pow(2).mean(-1, keepdim=True) + eps) * weight


tail_compiled = torch.compile(tail_eager)                    # Inductor fuses the chain


def make_triton_tail():
    import triton
    import triton.language as tl

    @triton.jit
    def kernel(g_ptr, u_ptr, r_ptr, w_ptr, out_ptr, n_cols, eps, BLOCK: tl.constexpr):
        row = tl.program_id(0)                               # one program per row: the RMS needs the whole row
        cols = tl.arange(0, BLOCK)
        mask = cols < n_cols
        off = row * n_cols + cols
        g = tl.load(g_ptr + off, mask=mask, other=0.0).to(tl.float32)
        u = tl.load(u_ptr + off, mask=mask, other=0.0).to(tl.float32)
        r = tl.load(r_ptr + off, mask=mask, other=0.0).to(tl.float32)
        h = g * tl.sigmoid(g) * u + r                        # everything stays in registers
        rms = tl.sqrt(tl.sum(h * h, axis=0) / n_cols + eps)
        w = tl.load(w_ptr + cols, mask=mask, other=0.0).to(tl.float32)
        tl.store(out_ptr + off, (h / rms * w).to(out_ptr.dtype.element_ty), mask=mask)

    def tail_triton(gate, up, residual, weight, eps=1e-6):
        rows, cols = gate.shape
        out = torch.empty_like(gate)
        kernel[(rows,)](gate, up, residual, weight, out, cols, eps, BLOCK=triton.next_power_of_2(cols))
        return out

    return tail_triton


def sync(device):
    if device == "cuda":
        torch.cuda.synchronize()


def time_once(fn, args, device):
    if device == "cuda":
        start, end = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
        start.record(); fn(*args); end.record(); torch.cuda.synchronize()
        return start.elapsed_time(end)
    t0 = time.perf_counter(); fn(*args)
    return (time.perf_counter() - t0) * 1e3


def bootstrap_ratio_ci(base, other, n_boot=2000, seed=0):
    """95% CI for median(base) / median(other) by resampling trials."""
    g = torch.Generator().manual_seed(seed)
    b, o = torch.tensor(base), torch.tensor(other)
    ratios = []
    for _ in range(n_boot):
        bi = torch.randint(0, len(b), (len(b),), generator=g)
        oi = torch.randint(0, len(o), (len(o),), generator=g)
        ratios.append((b[bi].median() / o[oi].median()).item())
    ratios.sort()
    return ratios[int(0.025 * n_boot)], ratios[int(0.975 * n_boot)]


def part_b(device: str, rows: int, cols: int, trials: int):
    dtype = torch.bfloat16 if device == "cuda" else torch.float32
    torch.manual_seed(0)
    gate, up, residual = (torch.randn(rows, cols, device=device, dtype=dtype) for _ in range(3))
    weight = torch.ones(cols, device=device, dtype=dtype)
    args = (gate, up, residual, weight)

    variants = {"eager": tail_eager, "torch.compile": tail_compiled}
    if device == "cuda":
        variants["triton (hand-written)"] = make_triton_tail()

    ref = tail_eager(*args).float()
    for name, fn in variants.items():                        # warm up (compilation) and check correctness
        for _ in range(3):
            out = fn(*args)
        sync(device)
        err = (out.float() - ref).abs().max().item()
        print(f"{name:>22}: max |diff| vs eager = {err:.2e}")

    times = {name: [] for name in variants}
    for _ in range(trials):                                  # interleave variants so drift affects all equally
        for name, fn in variants.items():
            times[name].append(time_once(fn, args, device))

    nbytes = gate.numel() * gate.element_size()
    print(f"\n=== Part B: fused tail, {rows} x {cols} {str(dtype).split('.')[-1]} on {device}, {trials} trials ===")
    print(f"minimum traffic if fused: 3 inputs + 1 output = {4 * nbytes / 1e6:.0f} MB")
    base = times["eager"]
    for name, t in times.items():
        med = statistics.median(t)
        line = f"{name:>22}: median {med:7.3f} ms"
        if name != "eager":
            lo, hi = bootstrap_ratio_ci(base, t)
            line += f"   speedup vs eager {statistics.median(base) / med:4.2f}x  (95% CI {lo:.2f}-{hi:.2f})"
        print(line)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu", choices=["cuda", "cpu"])
    ap.add_argument("--rows", type=int, default=8192)
    ap.add_argument("--cols", type=int, default=4096)
    ap.add_argument("--trials", type=int, default=30)
    ap.add_argument("--skip-profile", action="store_true")
    args = ap.parse_args()
    print(f"torch {torch.__version__}, device {args.device}")
    if not args.skip_profile:
        part_a(args.device)
    part_b(args.device, args.rows, args.cols, args.trials)


if __name__ == "__main__":
    main()
