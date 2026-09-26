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
- [ ] 01 LLM Foundations + Model Landscape 2026 page
- [ ] 02 PyTorch for LLMs + GPT-from-scratch lab
- [ ] 03 Pretraining at Scale (new)
- [ ] 04 Post-training & Reasoning (new)
- [ ] 05 Fine-Tuning Lab (Qwen3, TRL SFT/DPO/GRPO)
- [ ] 06 Evaluation & Benchmarks (new)
- [ ] 07 Inference & Serving (deduped, vLLM V1 lab)
- [ ] 08 Production Engineering
- [ ] 09 Cloud Platforms

## Phase 3 - Applications track (modules 10-11)
- [ ] 10 Prompt & Context Engineering (fold in 01/11)
- [ ] 11 RAG

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
