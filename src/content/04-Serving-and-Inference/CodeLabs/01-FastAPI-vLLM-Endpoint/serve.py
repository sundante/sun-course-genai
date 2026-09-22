"""FastAPI + vLLM serving endpoint for a small open instruction model.

Demonstrates, in one runnable file, the mechanics covered in the
08-Serving-and-Inference Notes: loading a model behind vLLM's
AsyncLLMEngine (Paged Attention + continuous batching under the hood),
and exposing it through a FastAPI /generate endpoint that supports both
streaming (Server-Sent Events, token-by-token) and non-streaming
(single JSON response) modes.

Default base model is the same ~1.5B parameter instruction model used
in 07-Fine-Tuning-Lab's QLoRA code lab, small enough to serve on a
single consumer/free-tier GPU. Point --model at a local merged
QLoRA-adapter checkpoint from that lab, or any other causal LM, to
serve a fine-tuned model instead.

Usage:
    python serve.py
    python serve.py --model Qwen/Qwen2.5-1.5B-Instruct --port 8000
    python serve.py --model ./qwen2.5-1.5b-support-bot-merged --port 8000

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
from vllm import AsyncEngineArgs, SamplingParams
from vllm.engine.async_llm_engine import AsyncLLMEngine

# Populated at startup by the lifespan handler below.
engine: AsyncLLMEngine | None = None
served_model_name: str = ""


class GenerateRequest(BaseModel):
    prompt: str
    max_tokens: int = 256
    temperature: float = 0.7
    top_p: float = 0.95
    stream: bool = True


def parse_args():
    parser = argparse.ArgumentParser(description="Serve a model with vLLM + FastAPI.")
    parser.add_argument("--model", type=str, default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.85)
    parser.add_argument("--max-model-len", type=int, default=4096)
    parser.add_argument("--max-num-seqs", type=int, default=32,
                         help="Continuous batching cap on sequences per scheduling step.")
    parser.add_argument("--enable-prefix-caching", action="store_true", default=True)
    parser.add_argument("--quantization", type=str, default=None,
                         help="e.g. 'awq' or 'gptq' if --model is a pre-quantized checkpoint.")
    return parser.parse_args()


def build_engine(args) -> AsyncLLMEngine:
    engine_args = AsyncEngineArgs(
        model=args.model,
        gpu_memory_utilization=args.gpu_memory_utilization,
        max_model_len=args.max_model_len,
        max_num_seqs=args.max_num_seqs,
        enable_prefix_caching=args.enable_prefix_caching,
        quantization=args.quantization,
    )
    return AsyncLLMEngine.from_engine_args(engine_args)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine, served_model_name
    args = app.state.cli_args
    print(f"Loading model '{args.model}' into vLLM AsyncLLMEngine...")
    engine = build_engine(args)
    served_model_name = args.model
    print("Model loaded. Server ready.")
    yield
    print("Shutting down.")


app = FastAPI(title="vLLM + FastAPI Inference Endpoint", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok", "model": served_model_name}


async def _generate_tokens(prompt: str, sampling_params: SamplingParams, request_id: str):
    """Async generator yielding newly generated text deltas as they're produced.

    vLLM's AsyncLLMEngine.generate() yields a RequestOutput per decode step
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


@app.post("/generate")
async def generate(req: GenerateRequest):
    request_id = str(uuid.uuid4())
    sampling_params = SamplingParams(
        max_tokens=req.max_tokens,
        temperature=req.temperature,
        top_p=req.top_p,
    )

    if req.stream:
        return StreamingResponse(
            _sse_stream(req.prompt, sampling_params, request_id),
            media_type="text/event-stream",
        )

    # Non-streaming path: consume the full generator, return one JSON response.
    start = time.monotonic()
    full_text = ""
    async for delta in _generate_tokens(req.prompt, sampling_params, request_id):
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
