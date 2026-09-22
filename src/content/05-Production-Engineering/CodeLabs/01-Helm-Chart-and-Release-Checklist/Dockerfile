# Multi-stage GPU inference image for the FastAPI + vLLM serving endpoint (Module 09)

# ---- Stage 1: build/install with full CUDA devel toolkit ----
FROM nvidia/cuda:12.1.0-devel-ubuntu22.04 AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 python3.11-venv python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY requirements.txt .
RUN python3.11 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ---- Stage 2: slim runtime image, no compiler/toolkit ----
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    && rm -rf /var/lib/apt/lists/*

# Copy only the built virtualenv from the builder stage - no devel toolkit, no build cache
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
# Build context is expected to include the Module 09 serve.py alongside this
# Dockerfile (e.g. `cp ../../../08-Serving-and-Inference/CodeLabs/01-FastAPI-vLLM-Endpoint/serve.py .`
# before `docker build`) - kept as a separate file rather than duplicated here
# so the two labs share one source of truth.
COPY serve.py .

# Model weights are mounted at runtime, not baked into the image -
# see Notes/01-Docker-for-GPU-Inference.mdx for why.
ENV MODEL_PATH=/models/current
VOLUME ["/models"]

EXPOSE 8000
CMD ["python3.11", "serve.py"]
