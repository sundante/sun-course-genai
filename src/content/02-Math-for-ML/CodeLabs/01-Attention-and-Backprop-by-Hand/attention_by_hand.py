"""Lab 03-01 - single-head causal attention, forward and backward by hand in NumPy.

Builds a one-layer "model" (attention head + output projection + cross-entropy), derives every
gradient by hand, checks them against central finite differences, and - if PyTorch is installed -
against autograd. Then runs two small experiments: why scores are scaled by 1/sqrt(d_head), and
how temperature reshapes a softmax.

Run:  python attention_by_hand.py            (numpy only)
      python attention_by_hand.py --torch    (also compare with torch autograd)
"""
import argparse

import numpy as np


# ---------------------------------------------------------------------------- forward

def softmax(z, axis=-1):
    z = z - z.max(axis=axis, keepdims=True)          # subtract the row max: same result, no overflow
    e = np.exp(z)
    return e / e.sum(axis=axis, keepdims=True)


def forward(params, X, targets):
    """X: (T, d_model) token embeddings; targets: (T,) next-token ids. Returns loss and a cache."""
    Wq, Wk, Wv, Wo = params["Wq"], params["Wk"], params["Wv"], params["Wo"]
    T, d_head = X.shape[0], Wq.shape[1]

    Q, K, V = X @ Wq, X @ Wk, X @ Wv                 # (T, d_head) each
    S = (Q @ K.T) / np.sqrt(d_head)                  # (T, T) scaled scores
    mask = np.triu(np.ones((T, T), dtype=bool), k=1) # True above the diagonal = future tokens
    S = np.where(mask, -np.inf, S)                   # causal: token t sees tokens <= t
    P = softmax(S)                                   # (T, T) attention weights, rows sum to 1
    O = P @ V                                        # (T, d_head) attention output
    logits = O @ Wo                                  # (T, vocab)
    probs = softmax(logits)
    loss = -np.log(probs[np.arange(T), targets]).mean()   # mean cross-entropy
    cache = dict(X=X, Q=Q, K=K, V=V, P=P, O=O, probs=probs, targets=targets, d_head=d_head)
    return loss, cache


# ---------------------------------------------------------------------------- backward

def backward(params, cache):
    """Every line is one application of the chain rule; shapes are noted on the right."""
    X, Q, K, V, P, O = (cache[k] for k in "X Q K V P O".split())
    probs, targets, d_head = cache["probs"], cache["targets"], cache["d_head"]
    T = X.shape[0]

    dlogits = probs.copy()                           # d(mean CE)/d(logits) = (softmax - onehot) / T
    dlogits[np.arange(T), targets] -= 1
    dlogits /= T                                     # (T, vocab)

    dWo = O.T @ dlogits                              # (d_head, vocab)
    dO = dlogits @ params["Wo"].T                    # (T, d_head)

    dP = dO @ V.T                                    # (T, T)
    dV = P.T @ dO                                    # (T, d_head)

    # softmax backward, row by row: dS = P * (dP - sum(dP * P)). Masked entries have P = 0,
    # so they get zero gradient automatically.
    dS = P * (dP - (dP * P).sum(axis=-1, keepdims=True))
    dS /= np.sqrt(d_head)                            # the forward pass divided by sqrt(d_head)

    dQ = dS @ K                                      # (T, d_head)
    dK = dS.T @ Q                                    # (T, d_head)

    grads = {
        "Wq": X.T @ dQ,                              # (d_model, d_head)
        "Wk": X.T @ dK,
        "Wv": X.T @ dV,
        "Wo": dWo,
    }
    dX = dQ @ params["Wq"].T + dK @ params["Wk"].T + dV @ params["Wv"].T   # X feeds three paths
    return grads, dX


# ---------------------------------------------------------------------------- checks

def finite_difference_check(params, X, targets, grads, eps=1e-6, samples=20, seed=0):
    """Central differences on random entries of every parameter. Returns the worst relative error."""
    rng = np.random.default_rng(seed)
    worst = 0.0
    for name, W in params.items():
        for _ in range(samples):
            idx = tuple(rng.integers(0, s) for s in W.shape)
            old = W[idx]
            W[idx] = old + eps; lp, _ = forward(params, X, targets)
            W[idx] = old - eps; lm, _ = forward(params, X, targets)
            W[idx] = old
            numeric = (lp - lm) / (2 * eps)
            analytic = grads[name][idx]
            rel = abs(numeric - analytic) / max(1e-12, abs(numeric) + abs(analytic))
            worst = max(worst, rel)
    return worst


def torch_check(params, X, targets, grads, dX):
    import torch

    t = {k: torch.tensor(v, requires_grad=True) for k, v in params.items()}
    x = torch.tensor(X, requires_grad=True)
    T, d_head = X.shape[0], params["Wq"].shape[1]
    q, k, v = x @ t["Wq"], x @ t["Wk"], x @ t["Wv"]
    s = (q @ k.T) / d_head ** 0.5
    s = s.masked_fill(torch.triu(torch.ones(T, T, dtype=torch.bool), 1), float("-inf"))
    logits = torch.softmax(s, dim=-1) @ v @ t["Wo"]
    loss = torch.nn.functional.cross_entropy(logits, torch.tensor(targets))
    loss.backward()
    diffs = {k: float((t[k].grad.numpy() - grads[k]).__abs__().max()) for k in params}
    diffs["X"] = float(abs(x.grad.numpy() - dX).max())
    return float(loss.detach()), diffs


# ---------------------------------------------------------------------------- experiments

def scaling_experiment(rng, T=16, trials=200):
    """Unit-variance q and k: the dot product has variance d_head. Without 1/sqrt(d) the softmax saturates."""
    print("\nWhy divide by sqrt(d_head)?  (mean over random unit-variance q, k)")
    print(f"{'d_head':>7} {'score std (raw)':>16} {'max weight raw':>15} {'max weight scaled':>18}")
    for d in (16, 64, 256, 1024):
        stds, raw_max, scaled_max = [], [], []
        for _ in range(trials):
            q = rng.standard_normal(d)
            K = rng.standard_normal((T, d))
            s = K @ q
            stds.append(s.std())
            raw_max.append(softmax(s).max())
            scaled_max.append(softmax(s / np.sqrt(d)).max())
        print(f"{d:>7} {np.mean(stds):>16.1f} {np.mean(raw_max):>15.3f} {np.mean(scaled_max):>18.3f}")
    print("Raw scores grow like sqrt(d_head), so the softmax collapses onto one token (max weight -> 1)\n"
          "and its gradient vanishes; scaling keeps the score std near 1 at every width.")


def temperature_experiment():
    logits = np.array([2.0, 1.0, 0.5, 0.0, -1.0])
    print("\nTemperature reshapes the next-token distribution: softmax(logits / T)")
    for temp in (0.25, 0.7, 1.0, 1.5):
        p = softmax(logits / temp)
        entropy = -(p * np.log2(p)).sum()
        print(f"  T={temp:<4}  p = {np.array2string(p, precision=3)}  entropy = {entropy:.2f} bits")


# ---------------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--torch", action="store_true", help="also compare with PyTorch autograd")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    T, d_model, d_head, vocab = 6, 8, 4, 10
    params = {
        "Wq": rng.standard_normal((d_model, d_head)) * 0.5,
        "Wk": rng.standard_normal((d_model, d_head)) * 0.5,
        "Wv": rng.standard_normal((d_model, d_head)) * 0.5,
        "Wo": rng.standard_normal((d_head, vocab)) * 0.5,
    }
    X = rng.standard_normal((T, d_model))
    targets = rng.integers(0, vocab, size=T)

    loss, cache = forward(params, X, targets)
    grads, dX = backward(params, cache)
    print(f"loss = {loss:.6f}   (uniform guessing would give ln({vocab}) = {np.log(vocab):.6f})")
    print("attention weights (row t = how token t attends to tokens 0..t):")
    print(np.array2string(cache["P"], precision=2, suppress_small=True))

    worst = finite_difference_check(params, X, targets, grads)
    print(f"\nfinite-difference check: worst relative error = {worst:.2e}  ->  {'PASS' if worst < 1e-6 else 'FAIL'}")

    if args.torch:
        tloss, diffs = torch_check(params, X, targets, grads, dX)
        ok = abs(tloss - loss) < 1e-10 and max(diffs.values()) < 1e-10
        print(f"torch autograd: loss {tloss:.6f}; max |grad difference| per tensor:")
        print("  " + ", ".join(f"{k} {v:.1e}" for k, v in diffs.items()) + f"  ->  {'PASS' if ok else 'FAIL'}")

    scaling_experiment(rng)
    temperature_experiment()


if __name__ == "__main__":
    main()
