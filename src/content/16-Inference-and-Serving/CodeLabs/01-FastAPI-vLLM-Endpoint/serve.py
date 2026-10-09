"""FastAPI + vLLM serving endpoint for a small open instruction model.

Demonstrates, in one runnable file, the mechanics covered in the
Inference & Serving notes (module 08): loading a model behind vLLM's V1
AsyncLLM engine (PagedAttention + continuous batching + prefix caching under
the hood), and exposing it through a FastAPI /generate endpoint that supports
both streaming (Server-Sent Events, token-by-token) and non-streaming (single
JSON response) modes.

vLLM's older V0 engine (AsyncLLMEngine) was removed in vLLM 0.11; this file
uses the V1 AsyncLLM class directly. In production you would usually run
`vllm serve <model>` (an OpenAI-compatible server) - this lab builds the
endpoint by hand so every moving part is visible.

Default base model is Qwen3-1.7B, the same family as the Fine-Tuning Lab, and
small enough to serve on a single consumer/free-tier GPU. Point --model at a
merged checkpoint from that lab to serve a fine-tuned model instead.

Usage:
    python serve.py
    python serve.py --model Qwen/Qwen3-1.7B --port 8000
    python serve.py --model ../../../08-Post-Training/CodeLabs/02-SFT-DPO-GRPO-with-TRL/runs/grpo/merged
    python serve.py --quantization fp8 --kv-cache-dtype fp8   # FP8 weights + KV cache (Hopper or newer)

Requires a CUDA GPU (vLLM does not support CPU-only inference for
this configuration). Once running, the OpenAPI docs are available at
http://localhost:8000/docs.
"""

import argparse
import json
import time
import uuid
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from transformers import AutoTokenizer
from vllm import AsyncEngineArgs, SamplingParams
from vllm.v1.engine.async_llm import AsyncLLM

# Populated at startup by the lifespan handler below.
engine: AsyncLLM | None = None
tokenizer = None
served_model_name: str = ""


class GenerateRequest(BaseModel):
    # Either a raw prompt string, or chat messages rendered with the model's chat template.
    # Instruct models expect their chat format - raw prompts are for base models and tests.
    prompt: str | None = None
    messages: list[dict] | None = None
    max_tokens: int = 256
    temperature: float = 0.7
    top_p: float = 0.95
    stream: bool = True


def parse_args():
    parser = argparse.ArgumentParser(description="Serve a model with vLLM + FastAPI.")
    parser.add_argument("--model", type=str, default="Qwen/Qwen3-1.7B")
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.85)
    parser.add_argument("--max-model-len", type=int, default=4096)
    parser.add_argument("--max-num-seqs", type=int, default=32,
                         help="Continuous batching cap on sequences per scheduling step.")
    parser.add_argument("--enable-prefix-caching", action="store_true", default=True)
    parser.add_argument("--quantization", type=str, default=None,
                         help="e.g. 'fp8' (dynamic FP8 weights on Hopper+), or leave unset for "
                              "pre-quantized checkpoints, whose format vLLM reads from the config.")
    parser.add_argument("--kv-cache-dtype", type=str, default="auto",
                         help="'fp8' halves KV-cache memory on supported GPUs.")
    return parser.parse_args()


def build_engine(args) -> AsyncLLM:
    engine_args = AsyncEngineArgs(
        model=args.model,
        gpu_memory_utilization=args.gpu_memory_utilization,
        max_model_len=args.max_model_len,
        max_num_seqs=args.max_num_seqs,
        enable_prefix_caching=args.enable_prefix_caching,
        quantization=args.quantization,
        kv_cache_dtype=args.kv_cache_dtype,
    )
    return AsyncLLM.from_engine_args(engine_args)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine, tokenizer, served_model_name
    args = app.state.cli_args
    print(f"Loading model '{args.model}' into vLLM AsyncLLM (V1 engine)...")
    engine = build_engine(args)
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    served_model_name = args.model
    print("Model loaded. Server ready.")
    yield
    print("Shutting down.")
    engine.shutdown()  # stops the engine-core background process


app = FastAPI(title="vLLM + FastAPI Inference Endpoint", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok", "model": served_model_name}


async def _generate_tokens(prompt: str, sampling_params: SamplingParams, request_id: str):
    """Async generator yielding newly generated text deltas as they're produced.

    vLLM's AsyncLLM.generate() yields a RequestOutput per engine step
    containing the *cumulative* generated text so far - this function converts
    that into incremental deltas suitable for token-by-token streaming.
    """
    previous_text = ""
    async for request_output in engine.generate(prompt, sampling_params, request_id):
        current_text = request_output.outputs[0].text
        delta = current_text[len(previous_text):]
        previous_text = current_text
        if delta:
            yield delta
    # Final yield ensures any trailing text (e.g. after the loop's last delta
    # computation) is not lost - request_output holds the final state here.


async def _sse_stream(prompt: str, sampling_params: SamplingParams, request_id: str):
    start = time.monotonic()
    is_first_chunk = True
    async for delta in _generate_tokens(prompt, sampling_params, request_id):
        chunk = {"delta": delta}
        if is_first_chunk:
            chunk["ttft_ms"] = round((time.monotonic() - start) * 1000, 1)
            is_first_chunk = False
        yield f"data: {json.dumps(chunk)}\n\n"
    yield "data: [DONE]\n\n"


def build_prompt(req: GenerateRequest) -> str:
    if req.messages:
        return tokenizer.apply_chat_template(
            req.messages, tokenize=False, add_generation_prompt=True,
            enable_thinking=False,  # Qwen3 thinking mode off; ignored by other templates
        )
    if req.prompt is None:
        raise ValueError("send either 'prompt' or 'messages'")
    return req.prompt


@app.post("/generate")
async def generate(req: GenerateRequest):
    request_id = str(uuid.uuid4())
    try:
        prompt = build_prompt(req)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    sampling_params = SamplingParams(
        max_tokens=req.max_tokens,
        temperature=req.temperature,
        top_p=req.top_p,
    )

    if req.stream:
        return StreamingResponse(
            _sse_stream(prompt, sampling_params, request_id),
            media_type="text/event-stream",
        )

    # Non-streaming path: consume the full generator, return one JSON response.
    start = time.monotonic()
    full_text = ""
    async for delta in _generate_tokens(prompt, sampling_params, request_id):
        full_text += delta
    elapsed_s = time.monotonic() - start

    return JSONResponse({
        "text": full_text,
        "model": served_model_name,
        "elapsed_s": round(elapsed_s, 3),
    })


if __name__ == "__main__":
    cli_args = parse_args()
    app.state.cli_args = cli_args
    uvicorn.run(app, host=cli_args.host, port=cli_args.port)
