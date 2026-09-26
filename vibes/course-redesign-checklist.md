# Course Redesign Checklist (2026 edition)

Live tracker for the full-course redesign. Plan of record: 17 modules in 5 tracks (Foundations, Building Models, Serving & Production, Building Apps, Agents) + Capstones + Knowledge Check. Delete this file once every phase is complete and record the outcome in `vibes/status.md` Changelog.

Research rule (Phases 2-4): every new claim about a model, spec, API, or version is verified against a primary source and cited in the note's References section.

## Phase 0 - Correctness & hygiene (no file moves)

### Factual errors (fix at source + propagated Q&A copies)
- [x] Adam memory "10 bytes/param" -> 16 B/param mixed precision (01/08, 01/12 Q42 + cheat sheet)
- [x] "1B GPU-hours ~ $1-3M" cost claim (01/06)
- [x] "LoRA makes forgetting theoretically impossible" (01/09, 01/12 Q40/Q48)
- [x] KV-cache math inconsistencies (01/05 code comments, 01/12 Q25)
- [x] Post-LN formula written as Pre-LN (01/02)
- [x] YaRN description + "Llama 3.1 used YaRN" (01/10, 01/09)
- [x] ChatML attributed to Mistral (01/11)
- [x] GRPO "generative RL" + "RFT" acronym (01/07)
- [x] Unsourced proprietary-internals claims (01/01, 01/05)
- [x] Tokenizer claims: Llama 3 SentencePiece, cl100k as Claude tokenizer (01/01, 01/06)
- [x] FlashAttention listed as sparse attention (01/01)
- [x] MinHash listed as exact dedup (01/06)
- [x] Mixtral "8 experts of 7B each" (01/04)
- [x] NVLink 4 attributed to A100 (01/08)
- [x] HIPAA "four" technical safeguards -> five (05/04)
- [x] Attention memory table per-head vs per-layer (01/03)
- [x] Fabricated MCP spec version "2026-01-01" (09/06, 09/09 Q18)
- [x] AutoGen "HumanProxyAgent" (11/09)

### Broken code
- [x] ADK labs: `InProcessRunner`, `google.adk.types`, sync `create_session`, `InMemoryRunner(session_service=...)` (20 files; all 14 `.py` labs import + wire a Runner on google-adk 2.10.0; not run against a live model)
- [x] LangGraph `SqliteSaver.from_conn_string` without context manager (11/09)
- [x] CrewAI `from crewai_tools import tool` (11/09)
- [x] Deprecated `torch.cuda.amp` / `torch.backends.cuda.sdp_kernel` (02, 01/03) - MNIST lab run end-to-end on CPU; CUDA AMP path not GPU-verified

### Site hygiene
- [x] `remarkRewriteMdLinks.ts`: resolve `.md` -> `.mdx` and preserve `#anchor`
- [x] Wrong Q&A counts in INDEX pages; wrong "06 - Agentic AI" labels
- [x] Em dashes in `.tsx` (quiz pages, AgentUseCaseMindmap)
- [x] CLAUDE.md house-style path `05-Agents` -> `10-Agents`
- [x] Refresh stale `vibes/status.md` sections (folder names, counts, commit)
- [x] Repaired 2 corrupt `.ipynb` files (invalid JSON in metadata tail)
- [x] `scripts/check-content.mjs` + `npm run check:content` (pulled forward from Phase 1)
- Numbering gaps (`08-RAGs/Notes`, `11-Agentic-AI/CodeLabs`) deferred to the Phase 1 restructure, which renumbers both directories

## Phase 1 - Platform & restructure
- [x] Code-fence components: `objectives`, `quiz`, `exercise` (remark plugin + components, schema-checked by `check:content`, worked example in the KV-cache note, documented in CLAUDE.md)
- [x] Derive home tiles / stats / quiz params from nav tree (plus the lesson-header module label)
- [x] Restructure to 17-module layout (git mv, nav.yml, nav.ts maps, track labels) - new overview pages for 03, 04, 06, 15, 16; rewritten 01, 12, 14; regenerated Next Topic footers
- [x] `scripts/check-content.mjs` + `npm run check:content` (done in Phase 0)
- [x] Clear the two numbering gaps during the restructure
- [x] Old URLs of the 62 moved pages forward via the 404 page (`legacy-redirects.json`)
- Deferred to Phase 5: `/quiz/[module]` pages stay stubs until quizzes exist across the course

## Phase 2 - LLM track (modules 01-09)
- [x] 01 LLM Foundations + Model Landscape 2026 page - new Modern Architectures (MLA, fine-grained MoE, local-global attention, sinks, hybrids, native multimodality) and Model Landscape notes (vendor pages checked 2026-09-26); stale current-model tables in notes 01/04 replaced with historical or family-level tables
- [x] 02 PyTorch for LLMs + GPT-from-scratch lab - new PyTorch for LLMs note (APIs checked against torch 2.14); GPT lab run on CPU (tiny preset: loss 5.57 -> 1.85 in 400 steps; --compile path verified); default preset not GPU-verified
- [x] 03 Pretraining at Scale (new) - 5 new chapters (data curation, scaling laws, distributed training, stability/optimizers, accelerators) + 24-question bank; hardware figures from NVIDIA/Google spec pages (dense derived from sparse), worked numbers recomputed in Python
- [x] 04 Post-training & Reasoning (new) - 3 new chapters (preference optimization, RL for LLMs, reasoning models & test-time compute) + 20-question bank; arXiv IDs spot-checked
- [x] 05 Fine-Tuning Lab (Qwen3, TRL SFT/DPO/GRPO) - Lab 01 moved to Qwen3-1.7B, all-linear LoRA, `--no-quantize` CPU path (train + benchmark smoke-tested on CPU with transformers 5.17 / peft 0.21); new Lab 02 SFT -> DPO -> GRPO with TRL 1.14 (all three stages smoke-tested on CPU, reward functions unit-tested); HF ecosystem note gains the post-training stack. Full-size runs not GPU-verified
- [x] 06 Evaluation & Benchmarks (new) - 4 chapters (benchmarks, contamination & leaderboards, LLM-as-judge, building your own evals) + 16-question bank + Eval Harness lab (lm-eval 0.4.13 CLI and paired-bootstrap compare.py smoke-tested on CPU)
- [x] 07 Inference & Serving (deduped, vLLM V1 lab) - new Modern Serving Stack note (goodput, chunked prefill, P/D disaggregation, KV-aware routing/offload, FP8/FP4, speculative decoding, MoE and multi-LoRA serving, Dynamo/llm-d); Quantized Inference rewritten around FP8/FP4 + llm-compressor (AutoAWQ archived May 2025); third copies of engine table/batching removed from Production Deployment; lab moved to V1 `AsyncLLM` (vLLM >= 0.11, API checked against source; not GPU-run) with chat-template requests; QA bank 15 -> 22; `check:content` now validates #anchors
- [x] 08 Production Engineering - new LLM Serving on Kubernetes note (GPU Operator, MIG/time-slicing/DRA [GA 1.34], KServe, LWS, Gateway API Inference Extension, llm-d, queue-depth autoscaling with verified vLLM metric names, cold starts); security note gains OWASP LLM Top 10 (2025), model supply chain, EU AI Act timeline as amended by the July 2026 Digital Omnibus; MLflow stages -> aliases; CUDA 12.8.1 / Ubuntu 24.04 images (tags verified) with PEP 668-safe venv installs; autoscaling advice reconciled; QA 15 -> 21
- [x] 09 Cloud Platforms - Bedrock (auto-enabled model access since Sept 2025, AgentCore GA Oct 2025, cost/customization levers); Azure note -> Microsoft Foundry (Ignite 2025 rename); new Google Cloud Agent Platform note (Vertex AI -> Gemini Enterprise Agent Platform, Apr 2026); comparison table fixed (Spanner <-> Aurora DSQL), GPU clouds added; QA 13 -> 17

## Phase 3 - Applications track (modules 10-11)
- [x] Carry-over from Phase 2: Vertex AI -> Gemini Enterprise Agent Platform naming in the RAG module (old `08-Vertex-AI-RAG` rewritten as cross-cloud `12-Managed-RAG-on-Cloud-Platforms`) and both RAG system designs (no more Gemini 1.5 / `text-embedding-004`). Agent-module system designs still cite Vertex AI Agent Engine / Gemini 1.5 - carried into Phase 4
- [x] 10 Prompt & Context Engineering (fold in 01/11) - Prompting Mechanics folded into Prompt Fundamentals (chat templates, roles/instruction hierarchy, prefill deprecation, batch-invariance non-determinism); new Structured Outputs (constrained decoding, XGrammar/llguidance/Outlines, OpenAI/Anthropic/Gemini APIs, vLLM `structured_outputs` - `guided_*` removed in 0.12), Prompting Reasoning Models (effort controls per provider, reasoning state in tool loops, inverse scaling, CoT unfaithfulness), Context Engineering (lost-in-the-middle/RULER/NoLiMa/context rot, write/select/compress/isolate), Prompt Caching & Cost (provider comparison, break-even); Core/Advanced Techniques corrected (Wei 2023 flipped labels, many-shot ICL, personas evidence, Huang 2024 self-correction); Production rewritten (spotlighting, layered injection defence); Automated Optimization rewritten for DSPy 3.4 (MIPROv2, GEPA - API checked against the installed package); QA 57 -> 48 deduped; new Prompt Evals & Structured Outputs lab (Qwen3-0.6B + Outlines, bootstrap CIs - run end to end on CPU/MPS)
- [x] 11 RAG - restructured to 13 notes: new Grounded Generation & Citations, Agentic & Deep-Research RAG, Long Context vs RAG vs CAG; rewritten Embeddings (ScaNN not HNSW, PQ math, int8/binary quantization, MRL), Chunking (contextual retrieval, late chunking, layout-aware parsing), Retrieval (SPLADE, ColBERT, RRF, domain-sensitive rerankers), Evaluation (hand-computed metrics, RAGAS 0.4 metric API), Advanced Patterns (corrected Self-RAG tokens and Speculative RAG, GraphRAG CLI + LazyGraphRAG/LightRAG/HippoRAG, ColPali), System Design + Production (merged from 3 notes; multi-tenancy consolidated; PoisonedRAG, vec2text), Managed RAG across Google/AWS/Azure (`agentplatform` client, Bedrock Managed KB, Foundry IQ); all LangChain code moved to v1 packages (`langchain_text_splitters`, `langchain_classic`, `create_agent`); QA 80 -> 60; new Retrieval Evaluation lab on BEIR SciFact (BM25 0.662 / SPLADE 0.710 nDCG@10 match published numbers); SD-2 fabricated drug-target facts replaced with illustrative data and real GQL

## Phase 4 - Agents track (modules 12-17)
- [ ] 12 Agent Foundations (merge 10 + 11, one memory taxonomy)
- [ ] 13 MCP & A2A (spec 2025-11-25, FastMCP, OAuth, A2A)
- [ ] 14 Agent Patterns & Multi-Agent
- [ ] 15 Agent Frameworks (current SDKs, pinned labs)
- [ ] 16 Production Agents (security, durable execution, benchmarks)
- [ ] 17 Agent Engineering

## Phase 5 - Pedagogy layer
- [ ] Note template applied everywhere (objectives, quiz, exercise, references)
- [ ] Capstones (3)
- [ ] Q&A dedupe: one bank per module; delete `All_Questions.mdx`
- [ ] `/quiz/[module]` powered by quiz fences
