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

### Audience Toggle
- 3-way toggle: **All / Technical / Non-Technical** — sticky bar on every content page
- Pilot with full dual content: `01-LLM-Models/Notes/01-LLM-Fundamentals.md`
- All other pages: locked to Technical with "Non-Technical coming soon" message
- Yellow left border = Technical content · Blue left border = Non-Technical content
- Persisted in `localStorage` (`genai_mode`) across navigation and refresh

**Authoring — tagging content blocks:**
```html
<div class="audience-biz" markdown="1">
Plain-language explanation — no jargon, real-world analogies.
</div>

<div class="audience-tech" markdown="1">
Full technical depth: math, code, internals, tradeoffs.
</div>
```
Untagged content is always visible in all modes. LLM Fundamentals is the reference implementation.

### Email Subscription
- Supabase `subscribers` table: `name, email, role, background_type, country, source, confirmed`
- Modal form: name (optional), email (required), role, background, country
- On submit → insert to `subscribers` (confirmed: false) → magic link via SMTP for confirmation
- On magic link click → `onAuthStateChange` fires → `confirmed = true`
- Smart interaction gate: shows after 5 clicks, 30-day cool-down after dismissal
- FAB button: "✦ Stay Updated" (fixed bottom-right, always visible)
- Close (×) always visible — users are never blocked from content

### Page Feedback FAB
- Fixed bottom-right, above the Stay Updated button
- 👍 / 👎 rating → opens popup with optional message + optional email
- Submits to Supabase `page_feedback` table: `page_slug, rating, message, email`
- localStorage deduplication per page — collapses to "✓ Thanks!" after voting
- No auth required

### Header
- "a sunmintz initiative" button → sunmintz.com
- Author group: LinkedIn · X (@sunsindante) · GitHub (sundante)

### Social / OG
- Open Graph + Twitter card meta tags on all pages
- Social card image: `/assets/social-card.png`
- Hero banner on home page using same image

### Design
- Theme: MkDocs Material, Solar Yellow (`#FFDA47`) + black/white
- Font: Inter (text), JetBrains Mono (code)
- Custom header CTAs (header CTA injected via JS on DOMContentLoaded)

---

## Supabase Tables

| Table | Purpose | Key columns |
|-------|---------|-------------|
| `subscribers` | Email subscription list | email, name, role, background_type, country, source, confirmed |
| `page_feedback` | Per-page feedback | page_slug, rating, message, email |
| `auth.users` | Auth identities (Supabase built-in) | email, created_at |

RLS enabled on both custom tables. Anon insert policies in place.

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
