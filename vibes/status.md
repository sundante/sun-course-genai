# Status — Learn AI: Generative AI to Agentic AI

Last updated: 2026-04-26

---

## Site

| Property | Value |
|----------|-------|
| URL | https://learngenai.sunmintz.com |
| Hosting | GitHub Pages (`gh-pages` branch) |
| Framework | MkDocs Material |
| Deploy | GitHub Actions → `mkdocs gh-deploy --force` on push to `main` |
| Analytics | Google Analytics (`G-STDCPPFR30`) |

---

## Curriculum Topics

| # | Topic | Notes | Q&A | Status |
|---|-------|-------|-----|--------|
| 01 | LLM Models | 12 files — Fundamentals through Production Deployment | 68+ | Complete |
| 02 | Prompt Engineering | 4 files (Basics, Core, Advanced, Production) | ✓ | Complete |
| 03 | RAG | 12 files — fundamentals through GCP production | 80+ | Complete |
| 04 | MCP | 8 files (Problem → Getting Started) | ✓ | Complete |
| 05 | Agents | Conceptual notes + 4 frameworks (ADK, LangChain, LangGraph, CrewAI) | ✓ | Complete |
| 06 | Agentic AI | 6 concept files + system designs + code labs | ✓ | Complete |

---

## Site Features

### Audience Toggle (shipped 2026-04-26)
- 3-way toggle: **All / Technical / Non-Technical** — sticky bar on every content page
- Pilot with full dual content: `01-LLM-Models/Notes/01-LLM-Fundamentals.md`
- All other pages: locked to Technical with "Non-Technical coming soon" message
- Yellow left bar = Technical content · Blue left bar = Non-Technical content
- Persisted in `localStorage` across navigation and refresh
- See `vibes/audience-toggle.md` for full implementation notes

### Signup & Auth (shipped 2026-04-26)
- Supabase magic-link signup modal
- Fields: name, email, role, profession, background, age, topics, country, city
- Tag-picker chip UI for topics of interest
- Smart interaction gate: shows after 5 clicks, 30-day cool-down after dismissal
- FAB button: "Stay Updated" (bottom-right, always visible)
- Close (×) always visible — users are never blocked from content

### Design
- Theme: MkDocs Material, custom Solar Yellow (`#FFDA47`) + white/dark
- Font: Inter (text), JetBrains Mono (code)
- Right-side TOC renamed "On this page"
- Custom header with GitHub + sunmintz.com CTAs

---

## Content Breakdown

### 01 — LLM Models (12 files)
- `01-LLM-Fundamentals.md` — **Dual-audience (Technical + Non-Technical)** · Tokens, context window, sampling, model types, open vs proprietary
- `02-Architecture.md` — Transformer architecture, positional encoding (RoPE/ALiBi/sinusoidal), Pre-LN, SwiGLU FFN
- `03-Attention-Mechanisms.md` — Q/K/V math, multi-head, Flash Attention 1/2/3, GQA/MQA, sliding window
- `04-Model-Architecture-Types.md` — Encoder-only, Decoder-only, Encoder-Decoder, MoE
- `05-KV-Cache-and-Inference-Optimization.md` — KV cache math, paged attention, speculative decoding, continuous batching
- `06-Training-and-Pretraining.md` — Data curation, BPE, CLM/MLM, Chinchilla scaling laws, distributed training
- `07-Fine-Tuning.md` — SFT, RLHF, DPO, LoRA, QLoRA
- `08-GPU-and-Hardware.md` — VRAM estimation, quantization, tensor/pipeline/data parallelism, ZeRO
- `09-Failure-Modes-and-Tricky-Issues.md` — Hallucination, lost in middle, sycophancy, repetition
- `10-Production-Deployment.md` — vLLM/TGI/Triton, latency budget, prefix caching, cost optimization
- `11-Prompting-Strategies.md` — Chat templates, CoT, system prompts, prompt injection
- `12-Interview-QA-Bank.md` — 68+ Q&A pairs (Easy/Medium/Hard)

### 02 — Prompt Engineering (4 files)
- Basics, Core Techniques (CoT, few-shot, ReAct), Advanced (ToT, meta-prompting), Production

### 03 — RAG (12 files)
- Full pipeline: fundamentals → embeddings → chunking → retrieval → evaluation → Vertex AI → production → scaling

### 04 — MCP (8 files)
- Problem → Definition → Solution → Components → Capabilities → Why It Matters → Architecture → Getting Started

### 05 — Agents
- Conceptual notes: Agent Fundamentals, Agent Patterns
- Framework deep-dives (Fundamentals + Simple + Complex): GCP ADK, LangChain, LangGraph, CrewAI

### 06 — Agentic AI (6 concept files + system designs + code labs)
- Concepts, Architectural Patterns, Design Patterns, Multi-Agent Systems, System Design, Evaluation
- System Designs: Insurance Claims Processor, Prior Authorization, Smart Diagnostic Assistant (×2)
- Code Labs: Architecture Patterns (7 × 4 frameworks), Agentic Systems (4 × 4 frameworks)

---

## What's Not Done Yet

- Non-Technical view for pages 02–06 (only LLM Fundamentals has it today)
- Code examples for 01-LLM-Models, 02-Prompts, 04-MCP (notes-only)
- Evaluations / benchmarks section
- Cost estimation / token budgeting guide
