# Status — GenAI Learning Curriculum

Last updated: 2026-04-21

---

## What's In Here

A general-to-advanced learning resource covering the full modern GenAI stack. Six topics, structured as prose notes + code examples + concept review Q&A.

---

## Topics

| # | Topic | Notes | Q&A Review | Status |
|---|-------|-------|------------|--------|
| 01 | LLM Models | 12 files — Fundamentals through Production Deployment | ✅ 68+ Q&A | Complete |
| 02 | Prompt Engineering | 4 files (Basics, Core, Advanced, Production) | ✅ | Complete |
| 03 | RAG | 12 files — fundamentals through GCP production | ✅ 80+ Q&A | Complete |
| 04 | MCP | 8 files (Problem → Getting Started) | ✅ | Complete |
| 05 | Agents | Conceptual notes + 4 frameworks | ✅ | Complete |
| 06 | Agentic AI | 6 files (Concepts, Arch, Design, Multi-Agent, System Design, Eval) | ✅ | Complete |

---

## Content Breakdown

### 01 — LLM Models (12 files, fully written)
- `01-LLM-Fundamentals.md` — Tokens, context window, sampling parameters, model types, open vs proprietary
- `02-Architecture.md` — Transformer architecture, positional encoding (RoPE/ALiBi/sinusoidal), Pre-LN, SwiGLU FFN
- `03-Attention-Mechanisms.md` — Q/K/V math, multi-head, Flash Attention 1/2/3, GQA/MQA, sliding window
- `04-Model-Architecture-Types.md` — Encoder-only (BERT), Decoder-only (LLaMA/GPT), Encoder-Decoder (T5), MoE, comparison table
- `05-KV-Cache-and-Inference-Optimization.md` — KV cache math, MHA/MQA/GQA, paged attention, speculative decoding, continuous batching
- `06-Training-and-Pretraining.md` — Data curation, BPE tokenization, CLM/MLM objectives, Chinchilla scaling laws, distributed training
- `07-Fine-Tuning.md` — SFT (loss masking), RLHF, DPO, LoRA math, QLoRA (NF4), multi-head fine-tuning
- `08-GPU-and-Hardware.md` — VRAM estimation, quantization (INT8/GPTQ/AWQ/NF4), tensor/pipeline/data parallelism, ZeRO stages
- `09-Failure-Modes-and-Tricky-Issues.md` — Catastrophic forgetting, lost in middle, hallucination taxonomy, sycophancy, repetition
- `10-Production-Deployment.md` — vLLM/TGI/Triton, latency budget, prefix caching, token window workarounds, cost optimization
- `04-Prompting-Strategies.md` — Chat templates (LLaMA-3/Gemma/ChatML), CoT mechanics, system prompts, prompt injection
- `12-Interview-QA-Bank.md` — 68+ Q&A pairs tagged Easy/Medium/Hard across all topics

### 02 — Prompt Engineering
- `01-Prompt-Basics.md` — Anatomy of a prompt, roles, instruction clarity
- `02-Core-Techniques.md` — CoT, few-shot, ReAct, structured output
- `03-Advanced-Techniques.md` — ToT, meta-prompting, prompt compression, self-consistency
- `04-Prompt-Engineering-for-Production.md` — Versioning, evaluation, injection defense

### 03 — RAG (12 files, most complete section)
- `01-RAG-Fundamentals.md` — Pipeline overview, RAG vs fine-tuning
- `02-Embeddings-and-Vector-Stores.md` — Math, HNSW/IVF/PQ, DB comparison
- `03-Chunking-and-Indexing.md` — Fixed/semantic/hierarchical chunking
- `04-Retrieval-Strategies.md` — BM25, hybrid search, RRF, HyDE, reranking
- `05-Advanced-RAG-Patterns.md` — Self-RAG, FLARE, GraphRAG, CRAG, Agentic RAG
- `06-RAG-Evaluation-and-Failure-Modes.md` — RAGAS metrics, LLM-as-Judge, tracing
- `07-RAG-Types-Taxonomy.md` — Naive → Modular → GraphRAG → Multimodal
- `08-RAG-System-Design.md` — Production architecture, latency budgets, 100M docs
- `09-Vertex-AI-RAG.md` — RAG Engine, Vector Search, Grounding API, AlloyDB
- `10-Production-Deployment.md` — Cloud Run vs GKE, CI/CD, monitoring, PII
- `11-Scaling-and-LLM-Issues.md` — Hallucination, lost-in-the-middle, prompt injection
- `12-Interview-QA-Bank.md` — 80+ Q&A pairs, `[Easy]` / `[Medium]` / `[Hard]`

### 04 — MCP (Model Context Protocol)
- `01-The-Problem.md` through `08-Getting-Started.md`
- Covers: why MCP exists, spec primitives, architecture deep-dive, implementation

### 05 — Agents
- Conceptual notes: Agent Fundamentals, Agent Patterns
- Framework notes (Fundamentals + Simple + Complex agent each):
  - **GCP ADK** — Google Cloud-native agent framework
  - **LangChain** — flexible chain-based framework
  - **LangGraph** — stateful graph-based agent orchestration
  - **CrewAI** — role-based multi-agent collaboration

### 06 — Agentic AI
- `01-Agentic-Concepts.md` — What makes a system "agentic", autonomy spectrum, core properties
- `02-Architectural-Patterns.md` — All 8 patterns (Single/Orchestrator/Hierarchical/P2P/Pipeline/Parallel/Debate/Reflexion), HITL
- `03-Design-Patterns.md` — Tool-use, Reflection, Planning (ReAct/Plan-and-Execute/ToT), routing
- `04-Multi-Agent-Systems.md` — Coordination, communication protocols, state management, failure modes
- `05-Agentic-System-Design.md` — Production architecture, reliability, HITL design, memory, cost, security
- `06-Evaluation-and-Observability.md` — Trajectory eval, metrics, LangSmith/Langfuse, debugging

---

## Knowledge Check Q&A (by topic)

| File | Questions |
|------|-----------|
| `Interview-Questions/01-LLM-Models.md` | Fundamentals, classification, architecture, training, hallucination |
| `Interview-Questions/02-Prompt-Engineering.md` | Structure, CoT, ReAct, ToT, injection, evaluation |
| `Interview-Questions/03-RAGs.md` | Pipeline, embeddings, chunking, hybrid search, RAGAS |
| `Interview-Questions/04-MCP.md` | Protocol overview, primitives, architecture, security |
| `Interview-Questions/05-Agents.md` | Agent loop, tool use, ReAct, frameworks, memory, failures |
| `Interview-Questions/06-Agentic-AI.md` | System design, orchestration, HITL, evaluation, state |
| `All_Questions.md` | All Q&A consolidated in a single flat file |

---

## Resources

| File | Topic | Notes |
|------|-------|-------|
| `Resources/01-LLM-Models/Gemma-Handbook.pdf` | LLM Models | Google's Gemma open model reference |
| `Resources/05-Agents/REACT-*.pdf` | Agents | Original ReAct paper |
| `Resources/05-Agents/Building_Applications_with_AI_Agents.pdf` | Agents | Applied agent architectures |
| `Resources/06-Agentic-AI/Agentic_Design_Patterns.pdf` | Agentic AI | Design pattern reference |
| `Resources/06-Agentic-AI/AI_Agents_vs_Agentic_AI.pdf` | Agentic AI | Distinction deep-dive |
| `Resources/06-Agentic-AI/Agentic_Architectural_Patterns_*.pdf` | Agentic AI | Architecture patterns |

---

## Code Examples

| Directory | Contents |
|-----------|---------|
| `Codes/01-Agent-Types/` | Single agents at 3 complexity levels across 4 frameworks |
| `Codes/02-Architectures/` | 7 architectural patterns across 4 frameworks (28 implementations) |
| `Codes/03-Agentic-Systems/` | 4 end-to-end system designs across 4 frameworks (new) |

### 03-Agentic-Systems (new)
- `01-Research-Assistant/` — Orchestrator-Subagent + Parallel fan-out + Reflexion
- `02-Document-Processor/` — Pipeline + Conditional Routing + HITL gate
- `03-Autonomous-Task-Planner/` — Plan-and-Execute + feedback loop + replanning
- `04-Code-Review-System/` — Parallel fan-out + Aggregation + Reflexion

## What's Not Here Yet

- `01-LLM-Models` — notes fully written (12 files); no standalone Codes/ folder yet (code snippets embedded in notes)
- `02-Prompts` — no code examples yet (notes only)
- `04-MCP` — no code examples beyond Getting Started
- Evaluations / benchmarks section
- Cost estimation / token budgeting guide
- OpenAI / Claude / Gemini API integration examples beyond framework snippets
