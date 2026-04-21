# Production Deployment

## Inference Serving Frameworks

### Concept

Running an LLM in production is fundamentally different from running inference in a notebook. Production requires: high throughput, low latency, batching, model management, and hardware efficiency. Specialized serving frameworks exist for this.

**Framework overview:**

| Framework | Primary strengths | Best for |
|-----------|------------------|---------|
| **vLLM** | Paged Attention, highest throughput, OpenAI-compatible API | High-throughput self-hosted serving |
| **TGI (Text Generation Inference)** | HuggingFace integration, Flash Attention, streaming | HuggingFace models, easy deployment |
| **Triton Inference Server** | NVIDIA, supports any model format, enterprise features | NVIDIA-heavy production, non-LLM workloads too |
| **Ollama** | Dead-simple local deployment, GGUF quantized models | Developer machines, prototyping |
| **LMDeploy (turbomind)** | High speed, GQA support, quantization | High throughput on Ascend/NVIDIA |
| **SGLang** | Structured generation, RadixAttention for caching | Complex generation pipelines, structured output |

**vLLM** is the most commonly used in production open-source deployments as of 2024. It implements:
- Paged Attention (see [KV Cache](05-KV-Cache-and-Inference-Optimization.md))
- Continuous batching
- OpenAI-compatible API (drop-in replacement for OpenAI SDK calls)
- Tensor parallelism for multi-GPU

---

## Latency Budget

### Concept

Understanding where latency comes from lets you optimize the right bottleneck.

**Latency components:**
```
Total latency = Queue wait + Prefill time + (N_output_tokens × per-token decode time)

Time-to-First-Token (TTFT) = Queue wait + Prefill time
Tokens-per-second (TPS)    = 1 / per-token-decode-time
```

**Prefill time** (processing input prompt):
- Scales with prompt length
- All input tokens are processed in parallel (like training)
- Bottleneck: compute (matrix multiplications for all tokens simultaneously)
- Typical: 1–5 seconds for 10K tokens on A100

**Decode time** (generating each output token):
- Each token requires one full forward pass through the model
- Must read the entire KV cache for all past tokens
- Bottleneck: memory bandwidth (reading KV cache from HBM)
- Typical: 20–50ms per token for 7B model on A100 → 20–50 TPS

**Queue time:**
- If all GPU capacity is occupied with other requests, your request waits
- Manageable with horizontal scaling and load balancing

**SLO targets (typical):**
- User-facing chat: TTFT < 500ms, TPS > 15 tokens/second (below this feels slow)
- Batch processing: throughput matters, latency is secondary
- Streaming: TTFT is paramount — users see first token immediately

---

## Batching Strategies

### Concept

**Static batching:** Wait for N requests, process all together, return all results.
- Pro: simple, maximum GPU utilization per batch
- Con: short sequences wait for long ones; any finished sequence wastes its slot

**Continuous batching (in-flight batching):** Fill the batch dynamically:
- After each decode step, evict any finished sequences
- Immediately insert the next waiting request
- GPU always runs at full batch capacity

```
Static (4 requests, max 10 tokens):
  Step 1–3:  [A B C D]   A, B finish at step 3
  Step 4–10: [_ _ C D]   2 empty slots wasted

Continuous:
  Step 1–3:  [A B C D]   A, B finish at step 3
  Step 4:    [E F C D]   E, F fill immediately
  Step 5–8:  [E F C D]   full batch throughout
```

**Dynamic batching:** Group incoming requests by similar sequence length to minimize padding waste.

**Chunked prefill:** For very long prompts, process the prefill in chunks to avoid monopolizing GPU during prefill (which would delay other decode steps in the continuous batch).

---

## Caching Hierarchy

### Concept

Multiple layers of caching are possible in LLM serving, each with different trade-offs.

**Level 1 — KV Cache (per-request, in-GPU):**
- Stores computed K/V for all tokens in the active sequence
- Eliminated by sequence completion; re-created per request
- Critical for decode speed (see [KV Cache](05-KV-Cache-and-Inference-Optimization.md))

**Level 2 — Prefix Cache (across requests, in-GPU):**
- Reuses KV cache blocks for shared prompt prefixes across requests
- High ROI for system prompts (often 500–2000 tokens, shared across all users)
- vLLM automatic prefix caching: compute prefix KV once, share blocks across requests
- Savings: a 1000-token system prompt with 1000 requests/minute = 1M prefill tokens/min saved

**Level 3 — Semantic Cache (across requests, external):**
- Cache full responses for semantically similar (or identical) queries
- Tools: GPTCache, Redis with embedding similarity search
- Works for FAQ-style applications where many users ask near-identical questions
- Does NOT help for unique/dynamic queries

**Level 4 — Batch API (offline):**
- For non-real-time workloads, queue requests to be processed at off-peak hours
- 50% cost reduction in OpenAI Batch API
- Latency: hours, but acceptable for document processing, bulk analysis

---

## Token Window Workarounds

### Concept

When documents or conversations exceed the context window, several strategies exist beyond simply refusing to process them.

**Strategy 1: Sliding Window with Overlap**
```
Document: [chunk_1][chunk_2][chunk_3]...

Process:
  Pass 1: context = [chunk_1][chunk_2] → partial answer
  Pass 2: context = [overlap][chunk_2][chunk_3] → partial answer
  Pass 3: context = [overlap][chunk_3][chunk_4] → partial answer
Merge partial answers (map-reduce style)
```

**Strategy 2: Hierarchical Summarization**
```
Long document (500 pages):
  1. Split into 100 sections
  2. Summarize each section (100 LLM calls)
  3. Concatenate summaries → still may be long
  4. Summarize summaries (recursive)
  5. Final response from concise summary
```

Suitable for: document QA, long-form summarization, book analysis.

**Strategy 3: RAG (Retrieval-Augmented Generation)**
Instead of loading the entire document, retrieve only relevant passages (see [RAG section](../../03-RAGs/Notes/01-RAG-Fundamentals.md)). This sidesteps the context window entirely for most questions.

**Strategy 4: Context Compression**
- Use a smaller, faster model to compress/summarize less-relevant context
- LLMLingua, AutoCompressor: compress prompt by 3–20× with minimal information loss
- Selective context: use a classifier to identify irrelevant sentences and drop them

**Strategy 5: Extended Context Models / RoPE Scaling**

For models trained with RoPE positional encoding, you can extend the context window beyond training length by scaling the RoPE frequencies:

```
YaRN (Yet another RoPE extensioN):
  Multiply RoPE base frequency by a scaling factor
  LLaMA-3.1: trained at 8K, YaRN extends to 128K with quality
  
LongLoRA: 
  Fine-tune with sparse attention (shift-short-attention) on longer sequences
  Enables cheap context extension via fine-tuning
```

**Trade-offs:**

| Approach | Latency | Quality | Cost | When to use |
|----------|---------|---------|------|-------------|
| Sliding window | Medium | Good (if overlap right) | Medium | Sequential document processing |
| Hierarchical summarization | High | Lossy (compression artifacts) | High | Very long documents |
| RAG | Low | High (relevant context) | Low | Knowledge-base queries |
| Context compression | Low-medium | Good | Low | Short on context budget |
| Extended context model | Medium-high | Best | Hardware | When exact retrieval matters |

---

## Latency Optimization Tricks

### Concept

A comprehensive list of techniques to reduce perceived and actual latency:

**1. Quantization (2–4× throughput improvement)**
```
BF16 → INT8: ~1.5× faster (memory bandwidth halved)
BF16 → INT4: ~2–4× faster (AWQ/GPTQ with optimized kernels)
Quality tradeoff: acceptable for most tasks at INT4 AWQ
```

**2. Speculative Decoding (2–3× decode speedup)**
- Use a small draft model (1B) to propose K tokens
- Verify with large model in one batch pass
- Most effective for predictable/repetitive output (structured, code)
- See [KV Cache file](05-KV-Cache-and-Inference-Optimization.md) for details

**3. Prompt Caching / Prefix Sharing**
- Cache system prompt KV: saves reprocessing 1000-token system prompts per request
- Anthropic, OpenAI, and vLLM all support this
- Savings: ~90% TTFT reduction for requests where prefix is 90% of the prompt

**4. Streaming Responses**
- Return the first token as soon as it's generated — don't wait for the full response
- Reduces *perceived* latency even though total time is the same
- Implementation: Server-Sent Events (SSE) or WebSocket

**5. Smaller Models for Routing/Triage**
- Classify request complexity with a cheap small model (1B)
- Route simple requests to a small model (7B), complex requests to large model (70B)
- Cascade: try small model first → if low confidence → retry with large model

**6. Flash Attention 2/3**
- Replace standard attention with Flash Attention kernel
- 2–4× faster for long sequences with no quality change

**7. Continuous Batching**
- Already discussed — essential for production throughput

**8. Tensor Parallelism Tuning**
- Split across 2 GPUs: ~1.8× faster (some communication overhead)
- Split across 4 GPUs: ~3.2× faster
- Beyond 8 GPUs: communication overhead often outweighs benefit for 7B models

**9. CUDA Graphs (static shapes)**
- Capture the computation graph for fixed-size batches
- Replay the same graph without Python overhead
- Significant benefit for small batch sizes where CPU overhead is a bottleneck

---

## Cost Optimization

### Concept

At scale, LLM inference cost is significant. Key levers:

**1. Prompt caching ROI:**
```
Without caching:
  1M requests × 1000 token system prompt × $0.01/1K tokens = $10,000/day

With 90% cache hit rate:
  100K uncached × $0.01 + 900K cached × $0.001 = $1,900/day  (81% savings)
```

**2. Smaller models for simple tasks:**
- Classify request complexity → route to appropriate model tier
- 80% of requests may be satisfiable by a 7B model; 20% need 70B
- Cost of 7B vs 70B inference: roughly 8–10× difference in throughput/GPU

**3. Batch API for offline workloads:**
- Background document processing, embedding generation, bulk classification
- OpenAI batch API: 50% discount for 24-hour turnaround
- Self-hosted: run batch jobs during off-peak hours to maximize GPU utilization

**4. Quantization:**
- INT4 inference: ~2–4× higher throughput per GPU → fewer GPUs needed
- Break-even vs quality: most production tasks are acceptable at AWQ INT4

**5. Output length control:**
- `max_new_tokens`: set tight bounds to prevent runaway generation
- Structured output: constrain output to JSON/specific format → predictable shorter outputs

---

## Monitoring and Observability

### Concept

Key metrics to track in production LLM serving:

**Latency metrics:**
- `TTFT p50/p95/p99`: time-to-first-token distribution
- `TPS p50/p95`: tokens per second for decode phase
- `E2E latency p99`: total time from request to response

**Throughput metrics:**
- `tokens_per_second_total`: aggregate throughput across all requests
- `requests_per_second`: request rate
- `queue_depth`: number of waiting requests (early warning for capacity issues)

**Quality metrics:**
- `context_length_distribution`: are requests using more context over time?
- `generation_length_distribution`: output getting longer? (cost signal)
- `cache_hit_rate`: prefix cache effectiveness

**GPU metrics:**
- `gpu_utilization`: should be > 80% in healthy serving
- `gpu_memory_used`: approaching limit → reduce batch size or add GPUs
- `kv_cache_utilization`: paged attention's block utilization

**Tools:**
- vLLM metrics endpoint: Prometheus-compatible `/metrics`
- OpenTelemetry traces for distributed LLM pipelines
- LangSmith / Langfuse for LLM-specific observability (prompt versions, output quality)

### Code

```python
# vLLM server setup and basic usage
# pip install vllm

# Start server (command line):
# python -m vllm.entrypoints.openai.api_server \
#   --model meta-llama/Llama-3.2-1B-Instruct \
#   --tensor-parallel-size 1 \
#   --max-model-len 8192 \
#   --enable-prefix-caching \
#   --quantization awq  # if using AWQ quantized model
#   --port 8000

# Client usage (OpenAI-compatible):
from openai import OpenAI
import time

client = OpenAI(base_url="http://localhost:8000/v1", api_key="placeholder")

# Standard chat completion
def chat_with_timing(messages, model="meta-llama/Llama-3.2-1B-Instruct"):
    start = time.time()
    first_token_time = None
    full_response = ""
    
    # Streaming to measure TTFT
    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=200,
        stream=True,
        temperature=0.7,
    )
    
    for chunk in stream:
        if chunk.choices[0].delta.content:
            if first_token_time is None:
                first_token_time = time.time()
            full_response += chunk.choices[0].delta.content
    
    end = time.time()
    total_tokens = len(full_response.split())  # approximate
    
    print(f"TTFT: {(first_token_time - start)*1000:.0f}ms")
    print(f"Total time: {(end - start)*1000:.0f}ms")
    print(f"TPS (approx): {total_tokens / (end - first_token_time):.1f} tok/s")
    return full_response

result = chat_with_timing([
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Explain transformers in 3 sentences."}
])

# Prefix caching benefit measurement
SYSTEM_PROMPT = "You are a helpful AI assistant specialized in machine learning. " * 50  # ~200 tokens

# First request: cache miss (slower)
t0 = time.time()
r1 = client.chat.completions.create(
    model="meta-llama/Llama-3.2-1B-Instruct",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "What is attention?"}
    ],
    max_tokens=100
)
print(f"First request (cache miss): {(time.time()-t0)*1000:.0f}ms")

# Second request: cache hit (faster prefill)
t0 = time.time()
r2 = client.chat.completions.create(
    model="meta-llama/Llama-3.2-1B-Instruct",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},  # same prefix
        {"role": "user", "content": "What is a transformer?"}
    ],
    max_tokens=100
)
print(f"Second request (cache hit): {(time.time()-t0)*1000:.0f}ms")
# Should be significantly faster due to prefix caching
```

---

## Study Notes

**Must-know for interviews:**
- vLLM is the dominant open-source serving framework: Paged Attention + continuous batching + OpenAI-compatible API
- Latency has two components: TTFT (prefill, compute-bound) and TPS (decode, memory-bandwidth-bound)
- Prefix caching eliminates reprocessing shared system prompts — very high ROI for chatbots
- Speculative decoding: small draft model proposes tokens → large model verifies in one pass → 2–3× speedup
- Token window workarounds: sliding window, hierarchical summarization, RAG, LLMLingua compression, RoPE scaling
- Cost optimization: prompt caching > model routing > quantization > batch API

**Quick recall Q&A:**
- *What is TTFT and what determines it?* Time-to-first-token = queue wait + prefill compute time. Determined by input prompt length and server load.
- *Why is continuous batching better than static batching?* Completed sequences are evicted immediately and new requests fill their slots — no wasted GPU capacity waiting for stragglers.
- *What is chunked prefill?* Processing long prompts in chunks to avoid monopolizing the GPU during prefill, which would delay decode steps for other in-flight requests.
- *When should you use RAG vs sliding window?* RAG when you can identify relevant content via search. Sliding window when you must process a document sequentially without a query.
- *Name 3 ways to improve TTFT.* Prefix caching (eliminate redundant prefill), quantization (faster compute), reduce prompt length (LLMLingua compression).
