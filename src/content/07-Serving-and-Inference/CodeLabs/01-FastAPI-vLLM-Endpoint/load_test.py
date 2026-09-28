"""Concurrent load test for the FastAPI + vLLM /generate endpoint.

Fires a configurable number of concurrent requests against a running
serve.py instance and reports the artifact described in the
08-Serving-and-Inference gap analysis: tokens/sec under load, p50/p95
per-request latency, and time-to-first-token (TTFT) - the same metrics
covered conceptually in Notes/03-Batching-Concurrency-and-Latency.mdx
and Notes/04-Streaming-and-TTFT.mdx.

Usage:
    python load_test.py --url http://localhost:8000/generate --concurrency 16 --requests 64
    python load_test.py --concurrency 1 --requests 5   # baseline, no contention
"""

import argparse
import asyncio
import json
import statistics
import time

import httpx

PROMPTS = [
    "Explain the difference between a list and a tuple in Python.",
    "Write a short product description for a wireless keyboard.",
    "What are three benefits of code review?",
    "Summarize why continuous batching improves LLM serving throughput.",
    "Give two tips for writing a clear commit message.",
    "What is the difference between TCP and UDP?",
    "Explain what a load balancer does in one paragraph.",
    "List three common causes of a memory leak in a long-running service.",
]


def parse_args():
    parser = argparse.ArgumentParser(description="Load test the /generate endpoint.")
    parser.add_argument("--url", type=str, default="http://localhost:8000/generate")
    parser.add_argument("--concurrency", type=int, default=16,
                         help="Number of requests in flight simultaneously.")
    parser.add_argument("--requests", type=int, default=64,
                         help="Total number of requests to fire across the whole run.")
    parser.add_argument("--max-tokens", type=int, default=128)
    parser.add_argument("--stream", action="store_true", default=True)
    parser.add_argument("--warmup-requests", type=int, default=2,
                         help="Requests run first and excluded from reported stats "
                              "(discards one-time CUDA warm-up cost).")
    return parser.parse_args()


class RequestResult:
    __slots__ = ("ttft_s", "total_latency_s", "output_tokens", "success")

    def __init__(self):
        self.ttft_s = None
        self.total_latency_s = None
        self.output_tokens = 0
        self.success = False


async def run_one_request(client: httpx.AsyncClient, url: str, prompt: str,
                           max_tokens: int) -> RequestResult:
    result = RequestResult()
    payload = {"prompt": prompt, "max_tokens": max_tokens, "stream": True}
    start = time.monotonic()

    try:
        async with client.stream("POST", url, json=payload, timeout=120) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data = line[len("data: "):]
                if data == "[DONE]":
                    break
                chunk = json.loads(data)
                if result.ttft_s is None:
                    result.ttft_s = time.monotonic() - start
                # Rough token count via whitespace split - good enough for a
                # throughput estimate without requiring the server's tokenizer.
                result.output_tokens += max(1, len(chunk.get("delta", "").split()))
        result.total_latency_s = time.monotonic() - start
        result.success = True
    except (httpx.HTTPError, json.JSONDecodeError) as exc:
        print(f"Request failed: {exc}")

    return result


async def bounded_request(semaphore: asyncio.Semaphore, client: httpx.AsyncClient,
                           url: str, prompt: str, max_tokens: int) -> RequestResult:
    async with semaphore:
        return await run_one_request(client, url, prompt, max_tokens)


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    idx = min(len(sorted_vals) - 1, int(round(pct / 100 * (len(sorted_vals) - 1))))
    return sorted_vals[idx]


async def main():
    args = parse_args()
    semaphore = asyncio.Semaphore(args.concurrency)

    async with httpx.AsyncClient() as client:
        if args.warmup_requests > 0:
            print(f"Running {args.warmup_requests} warm-up request(s) (excluded from stats)...")
            warmup_tasks = [
                run_one_request(client, args.url, PROMPTS[i % len(PROMPTS)], args.max_tokens)
                for i in range(args.warmup_requests)
            ]
            await asyncio.gather(*warmup_tasks)

        print(f"Firing {args.requests} requests at concurrency={args.concurrency}...")
        wall_start = time.monotonic()
        tasks = [
            bounded_request(semaphore, client, args.url, PROMPTS[i % len(PROMPTS)], args.max_tokens)
            for i in range(args.requests)
        ]
        results = await asyncio.gather(*tasks)
        wall_elapsed_s = time.monotonic() - wall_start

    successful = [r for r in results if r.success]
    failed_count = len(results) - len(successful)

    if not successful:
        print("All requests failed - is serve.py running at --url?")
        return

    ttfts_ms = [r.ttft_s * 1000 for r in successful if r.ttft_s is not None]
    latencies_ms = [r.total_latency_s * 1000 for r in successful]
    total_tokens = sum(r.output_tokens for r in successful)
    aggregate_tok_s = total_tokens / wall_elapsed_s if wall_elapsed_s > 0 else 0.0

    print()
    print("=" * 68)
    print(f"{'Metric':<38}{'Value':>30}")
    print("=" * 68)
    print(f"{'Concurrency':<38}{args.concurrency:>30}")
    print(f"{'Requests (succeeded / failed)':<38}{f'{len(successful)} / {failed_count}':>30}")
    print(f"{'Wall-clock time (s)':<38}{wall_elapsed_s:>30.2f}")
    print(f"{'Total output tokens':<38}{total_tokens:>30}")
    print(f"{'Aggregate throughput (tok/s)':<38}{aggregate_tok_s:>30.2f}")
    print(f"{'TTFT p50 (ms)':<38}{percentile(ttfts_ms, 50):>30.1f}")
    print(f"{'TTFT p95 (ms)':<38}{percentile(ttfts_ms, 95):>30.1f}")
    print(f"{'Per-request latency p50 (ms)':<38}{percentile(latencies_ms, 50):>30.1f}")
    print(f"{'Per-request latency p95 (ms)':<38}{percentile(latencies_ms, 95):>30.1f}")
    if len(latencies_ms) > 1:
        print(f"{'Per-request latency stdev (ms)':<38}{statistics.stdev(latencies_ms):>30.1f}")
    print("=" * 68)


if __name__ == "__main__":
    asyncio.run(main())
