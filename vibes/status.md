# Learn GenAI - Project Status

**URL:** https://learngenai.sunmintz.com
**Stack:** Next.js 16.2.9 (App Router, static export) - TypeScript (strict) - Tailwind CSS 4 - MDX (`next-mdx-remote/rsc`) - shadcn/ui - Mermaid
**Deploy:** Static export (`out/`) -> manual GitHub Actions FTP push -> Hostinger, served at `sunmintz.com/learngenai/`
**Last updated:** 2026-07-21
**Last commit at time of writing:** `e5f3191` (2026-06-29 - "updated deployment yaml")
**Content inventory verified:** `find src/content -name '*.mdx' | wc -l` -> **109 files** (previous tracker said 107 -> stale)

> This file is the raw source of truth for project status. It is updated as part of
> every successful build/coding session (see **Changelog** at the bottom). The
> polished, collapsible human-readable view is `vibes/status.html`, regenerated on
> request from whatever this file says at the time - it is not auto-synced, so don't
> trust it blindly for the latest state.

---

## 1. Deployment

**Target:** `sunmintz.com/learngenai/` (static export, no Node server at runtime)
**Method:** `next build` (static export) -> FTP upload of `out/` via GitHub Actions -> Hostinger shared hosting

### Why static export works

- `next.config.ts`: `output: "export"` -> pure static HTML/CSS/JS, no server needed
- `trailingSlash: true` -> every route emits as `route/index.html` (Apache-friendly)
- `images: { unoptimized: true }` -> no Node image-optimization server required

### Current workflow (`.github/workflows/deploy.yml`)

```yaml
name: Deploy to Hostinger
on:
  workflow_dispatch:        # manual trigger only - no auto-deploy on push/merge
jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - actions/checkout@v4
      - actions/setup-node@v4 (node-version: 20, cache: npm)
      - run: npm ci
      - run: npm run build
      - uses: SamKirkland/FTP-Deploy-Action@v4.3.5
        with:
          server: ${{ secrets.FTP_SERVER }}
          username: ${{ secrets.FTP_USERNAME }}
          password: ${{ secrets.FTP_PASSWORD }}
          port: 21
          local-dir: ./out/
          server-dir: /domains/sunmintz.com/public_html/learngenai/
          exclude: [**/.DS_Store, **/*.txt]
          dangerous-clean-slate: false
```

**Required GitHub repo secrets (Settings -> Secrets -> Actions):**

| Secret | Purpose |
| --- | --- |
| `FTP_SERVER` | FTP hostname from Hostinger hPanel |
| `FTP_USERNAME` | FTP account username |
| `FTP_PASSWORD` | FTP account password |

Note: `server-dir` is hardcoded directly in the YAML (`/domains/sunmintz.com/public_html/learngenai/`), it is **not** read from a secret. (The previous tracker doc claimed a `FTP_HOST` secret and a `FTP_SERVER_DIR` secret - both wrong; see **Known Issues** below, now corrected in this doc.)

### Local/manual deploy fallback

```bash
npm run build
# FTP the CONTENTS of ./out/ (not the folder itself) to /domains/sunmintz.com/public_html/learngenai/
```

Remote root should look like:

```text
/domains/sunmintz.com/public_html/learngenai/
  index.html
  _next/
  404.html
  learn/
  quiz/
  favicon.ico
```

### Deploy history notes

- Workflow was iterated on heavily in June: briefly deleted and recreated, switched from an auto-trigger to manual-only (`workflow_dispatch`), had CI-breaking issues fixed (untracked `package-lock.json`/`tsconfig.json` blocking npm cache and path-alias resolution).
- Most recent change (2026-06-29, commit `e5f3191`) removed an `environment` choice dropdown from the manual trigger, simplifying it back to a bare `workflow_dispatch` with no inputs.
- **No CI runs on push/PR** - lint, typecheck, and build are not verified automatically before merge. The only automation is the manual deploy trigger.

---

## 2. What's Built

### Core App
- Next.js App Router scaffolded with TypeScript (strict mode) + Tailwind CSS 4
- Static export configured (`output: "export"`)
- Inter + JetBrains Mono via `next/font/google`
- Design system: sun-yellow color tokens, prose overrides, audience-toggle CSS (see `vibes/DESIGN-SYSTEM.md`)

### Navigation & Content Pipeline
- `src/content/nav.yml` - single source of truth for nav, MkDocs-style tree
- `src/lib/content/nav.ts` - parses `nav.yml`, builds `NavModule[]` + flat `PageRef[]`, computes prev/next, module-level cache
- `src/lib/content/loader.ts` - reads raw `.mdx` per page, extracts TOC via heading regex (`extractToc`), exposes `getPage` / `getAllPages` / `getPageWithNavigation`
- `src/lib/content/remarkRewriteMdLinks.ts` - build-time remark plugin rewriting cross-content links
- MDX pipeline (`src/app/(course)/learn/[module]/[slug]/page.tsx`): `next-mdx-remote/rsc`'s `MDXRemote` with `remark-gfm`, `remarkRewriteMdLinks`, `rehype-raw`, `rehype-slug`, `rehype-autolink-headings` (wrap), `rehype-highlight`; `parseFrontmatter: false`, format `"md"`
- Slug-collision prevention - subdirectory paths included in generated slugs
- **Automatic WIP detection** - `isStubFile()` in `src/lib/content/nav.ts` flags any content file with fewer than 8 non-heading/non-empty body lines as `wip: true`; this is computed from content length, not a manual flag per file

### Pages
- Homepage - hero, module grid, stats strip, learning paths, footer
- Course content pages - `/learn/[module]/[slug]`
- 404 page
- Quiz pages - `/quiz/all`, `/quiz/[module]` - **stubs only**, render `<UnderDevelopment>` placeholder; `quiz/[module]` has hardcoded `generateStaticParams` for 7 module slugs but no actual quiz data/logic

### UI Components (`src/components/course/`)
- `Header` - sticky, social links, GitHub star button
- `Sidebar` - collapsible icon-rail mode (`CollapsedRail`, 2-letter module abbreviations), expandable modules, active-link tracking via `usePathname`; `ModuleSection` renders numbered top-level modules (`01. LLM Models` ... `07. Knowledge Check`); `NavLeaf` renders numbered leaf items and an italic "WIP" badge for stub pages
- `MobileNav` - sheet drawer for mobile
- `AudienceToggle` - All / Technical / Non-Technical modes, persists to `localStorage`
- `AudienceOnboardingModal`, `DisclaimerModal`, `DisclaimerNote`
- `TableOfContents` - sticky, IntersectionObserver-based active heading tracking, independently scrollable
- `PageNav` - prev/next footer
- `UnderDevelopment` - animated placeholder for WIP/stub pages
- `MermaidDiagram`, `AgentUseCaseMindmap`
- `MdxComponents` - custom component overrides for MDX rendering
- `src/components/ui/` - shadcn/ui primitives: button, sheet, card, badge, progress, separator

### Course Content - 109 `.mdx` files across 7 modules

| Module | Dir | Contents |
| --- | --- | --- |
| 01 - LLM Models | `01-LLM-Models/` | Overview + 12 notes (Fundamentals -> Architecture -> Attention -> Model Types -> KV Cache/Inference -> Training -> Fine-Tuning -> GPU/Hardware -> Failure Modes -> Production Deployment -> Prompting Strategies -> Q&A Bank) |
| 02 - Prompt Engineering | `02-Prompts/` | Overview + 6 notes (Basics, Core Techniques, Advanced Techniques, Production, Optimization/Automation, Q&A Bank) + Resources |
| 03 - RAG | `03-RAGs/` | Overview + 12 notes (Fundamentals -> Embeddings/Vector Stores -> Chunking/Indexing -> Retrieval Strategies -> RAG Types -> Evaluation/Failure Modes -> System Design -> Vertex AI RAG -> Production -> Scaling -> Q&A Bank) + 2 System Designs (Simple RAG Pipeline, Agentic RAG Hybrid) + Resources |
| 04 - MCP | `04-MCP/` | Overview + 9 notes (The Problem -> Definition -> The Solution -> Components -> Capabilities -> Why It Matters -> Architecture Deep-Dive -> Getting Started -> Q&A Bank) + Implementation |
| 05 - AI Agents | `05-Agents/` | Overview + 6 concept notes (What Are AI Agents, Anatomy, Memory, Capabilities, Use Cases, Enterprise vs Personal) + Code Labs (Agent Types + GCP ADK / LangChain / LangGraph / CrewAI, each with Fundamentals + Simple Agent + Complex Agent) |
| 06 - Agentic AI | `06-Agentic-AI/` | Overview + 12 notes (Agentic Concepts -> Agent Loop -> Tool Use -> Memory/State -> Planning/Reasoning -> Architectural Patterns -> Design Patterns -> Multi-Agent Systems -> Agent Frameworks -> System Design -> Evaluation/Observability -> Q&A Bank) + 4 System Designs (Insurance Claims Processor, Prior Authorization, Smart Diagnostic Assistant x2) + Code Labs matrix (Architectures: Sequential/Parallel/Hierarchical/Orchestrator-Subagent/Pipeline/Adversarial-Debate/Reflexion, each x4 frameworks; Agentic Systems: Research Assistant/Document Processor/Autonomous Task Planner/Code Review System, each x4 frameworks) |
| Knowledge Check | `Interview-Questions/` + `All_Questions.mdx` | Per-module question banks (01-06) + aggregate "All Questions" |

**Most recently active area:** Chapter 05 (AI Agents) - Anatomy of an AI Agent, Agent Memory, Agent Use Cases, and Enterprise vs Personal Agents notes were all added/updated on 2026-06-29, the same day as the last commit.

**Naming convention:** zero-padded numeric prefixes (`01-`, `02-`, ...) at module and file level; `INDEX.mdx` per module overview; `Notes/`, `SystemDesigns/`, `CodeLabs/`, `Resources/`, `Implementation/` as topic subfolders. See root `CLAUDE.md` for the renumbering rule when files are deleted.

---

## 3. Backlog

### Near-term
- [ ] **Quiz feature** - both `/quiz/all` and `/quiz/[module]` are fully stubbed (`<UnderDevelopment>` only); a `QuizCard` type already exists in `src/types/content.ts` with no consumer yet - it's a forward-looking stub for this feature
- [ ] **Search** - no full-text search across content exists yet
- [ ] **Progress tracking** - no "mark lesson complete" mechanism (localStorage-first was the original intent)
- [ ] **Wire lint/build into CI** - currently only a manual deploy workflow exists; nothing runs `npm run lint` or `next build` automatically on push/PR, so regressions can reach `main` unchecked

### Content
- [ ] More system-design case studies (only RAG and Agentic AI modules have them so far)
- [ ] Runnable code labs - embed via CodeSandbox / StackBlitz instead of static code blocks
- [ ] Video embeds for visual/architecture concepts
- [x] ~~Convert ASCII-art diagrams / un-diagrammed architecture-flow prose to Mermaid across content~~ - **DONE 2026-07-22**, all 9 phases complete (tracking checklist has since been deleted - see Changelog); house rule remains at root `CLAUDE.md` > "Diagrams & Visual Explanations"

### Future (post-maturity)
- [ ] User auth + accounts (Clerk or Auth.js)
- [ ] Bookmarks - save and resume lessons
- [ ] Persistent progress sync across devices
- [ ] Interactive MDX components - `<QuizWidget />`, `<CodePlayground />`
- [ ] Comment/discussion threads per lesson

### Test coverage (not previously tracked)
- [ ] **No automated tests exist anywhere in the repo** - no Jest/Vitest/Playwright config, no test dependencies in `package.json`. `test-results/.last-run.json` is a stray leftover artifact from an ad-hoc external tool run, not a real suite (see Known Issues).

---

## 4. Known Issues / Discrepancies

1. **Deploy secrets doc drift (now fixed in this doc)** - the previous tracker documented `FTP_HOST` and `FTP_SERVER_DIR` as required secrets; the actual workflow uses `FTP_SERVER` and hardcodes the server directory in the YAML. Anyone rotating credentials should check the live workflow file, not assume old docs are correct.
2. **Stale predecessor tracker** - the old root `STATUS.md` undercounted content (107 vs. actual 109 `.mdx` files) and listed "deploy to learngenai.sunmintz.com (set up CI/CD)" as still to-do even though the deploy workflow already existed and had been edited as recently as the last commit. It has been deleted and replaced by this file + `vibes/status.html`, both now living in `vibes/` per project convention.
3. **`test-results/.last-run.json`** at repo root is a leftover artifact (`{"status": "failed", "failedTests": []}`), likely from an ad-hoc Playwright MCP run rather than a checked-in suite. Safe to delete when noticed; harmless if left, but don't mistake it for real test signal.
4. **`README.md`** is still the unedited default `create-next-app` boilerplate - no project-specific setup instructions live there. All real project docs currently live in `CLAUDE.md`, `AGENTS.md`, and `vibes/`.
5. **No staging environment** - deploys go straight to production via manual trigger; no rollback mechanism beyond re-running an older commit's workflow.
6. ~~**`extractToc()` TOC-generation bug (fixed 2026-07-22)**~~ - `src/lib/content/loader.ts`'s `extractToc()` was a naive line regex with two bugs: (a) it wasn't fenced-code-block-aware, so Python/YAML comment lines like `# Define a tool` inside ` ``` ` blocks were misparsed as real headings (334 false positives found across content); (b) it didn't dedupe repeated heading text the way the actual renderer's `rehype-slug` does, so pages with repeated headings (e.g. `### Concept` used as a template heading many times per file) produced duplicate `id`s in the TOC, causing a React "two children with the same key" crash in `TableOfContents.tsx` and silently broken TOC links/scroll-spy for every occurrence past the first. Fixed by making `extractToc()` skip ` ``` ` fenced regions and generate ids via `github-slugger` (added as a direct dependency - it's what `rehype-slug` uses under the hood), so TOC ids now match the rendered DOM's anchor ids exactly, including the `-1`, `-2` dedup suffixes.

---

## 5. Handover Notes (read this first if picking up a new session)

**Where things left off:** The last 4 commits (all 2026-06-29) focused on Chapter 05 (AI Agents) - adding Agent Anatomy, Agent Memory, and Enterprise vs Personal Agents notes, updating the Agent Use Cases page, and simplifying the deploy workflow YAML (removed an unused `environment` input). There has been a **~3-week gap** with no commits between 2026-06-29 and 2026-07-21 (today).

**Suggested next steps, in priority order:**
1. Decide whether to wire `npm run lint` (and ideally `next build`) into a CI check on PRs/push - currently nothing automated guards `main` before a manual deploy.
2. Pick one near-term backlog item to unblock next: Quiz feature is the most visible gap (routes exist but are pure placeholders), and `QuizCard` in `src/types/content.ts` is already scaffolded for it.
3. If rotating or auditing deploy credentials, use the secret names in this file (`FTP_SERVER`/`FTP_USERNAME`/`FTP_PASSWORD`), not any older doc.
4. Sanity-check `nav.yml` against `src/content/` before adding new content - it's the single source of truth for navigation and must stay in sync with file renames/renumbering per `CLAUDE.md`.
5. Re-verify content counts (`find src/content -name '*.mdx' | wc -l`) whenever content is added/removed, and update this file's header count - the previous tracker went stale on exactly this number.

**Process going forward:**
- `vibes/status.md` (this file): update after every successful build/coding session - refresh affected sections + append a one-line Changelog entry below.
- `vibes/status.html`: regenerate on demand only (not tied to every session) - reflects whatever this file says at generation time.

---

## 6. Project Structure

```
src/
  app/
    layout.tsx                        root layout (fonts, DisclaimerModal, AudienceOnboardingModal)
    page.tsx                          homepage
    not-found.tsx                     404
    (course)/
      layout.tsx                      header + sidebar shell
      learn/[module]/[slug]/page.tsx  course content pages
      quiz/all/page.tsx               quiz stub
      quiz/[module]/page.tsx          quiz stub
  components/
    ui/                               shadcn primitives (button, sheet, card, badge, progress, separator)
    course/                           Header, Sidebar, MobileNav, AudienceToggle, AudienceOnboardingModal,
                                      DisclaimerModal, DisclaimerNote, TableOfContents, PageNav,
                                      UnderDevelopment, MermaidDiagram, AgentUseCaseMindmap, MdxComponents
  lib/
    utils.ts                          cn() helper
    content/
      nav.ts                          navigation tree from nav.yml, isStubFile() WIP detection
      loader.ts                       reads .mdx files, extracts TOC
      remarkRewriteMdLinks.ts         build-time cross-link rewriting
  types/
    content.ts                        NavItem, NavModule, NavigationTree, PageRef, PageContent, TocItem, QuizCard
  content/                            109 .mdx source files (compiled to HTML at build time)
    nav.yml
    01-LLM-Models/
    02-Prompts/
    03-RAGs/
    04-MCP/
    05-Agents/
    06-Agentic-AI/
    Interview-Questions/
    All_Questions.mdx

vibes/                                design specs & project tracking
  DESIGN-SYSTEM.md
  UI-COMPONENTS.md
  PAGE-LAYOUTS.md
  BUILD-PROMPT.md
  status.md                          this file
  status.html                        polished collapsible status view

.github/workflows/deploy.yml          manual FTP deploy to Hostinger
```

---

## Changelog

- **2026-07-21** - Full repo audit performed; replaced stale root `STATUS.md` with this file, moved into `vibes/`; corrected deploy-secret documentation drift; added Backlog/Known Issues/Handover structure; created `vibes/status.html` companion view.
- **2026-07-22** - Added `CLAUDE.md` > "Diagrams & Visual Explanations" house rule (prefer Mermaid over ASCII-art/prose for architecture/pipeline/flow/state-machine/comparison content); audited all 110 `.mdx` content files and created `vibes/diagram-conversion-checklist.md` (9-phase priority checklist) to track the conversion; no diagrams converted yet, this session was prep only.
- **2026-07-22** - Added `CLAUDE.md` > "Project Tracking" instruction to always update the relevant tracker doc (not just `status.md`) after every completed build. Started executing `vibes/diagram-conversion-checklist.md`: Phase 1 complete - converted all 12 ASCII diagrams in `06-Agentic-AI/Notes/06-Architectural-Patterns.mdx` to Mermaid (flowchart/sequenceDiagram), verified rendering via the dev server. Checklist and its own Changelog updated to reflect Phase 1 done; Phase 2 (MCP architecture + lifecycle) is next.
- **2026-07-22** - Fixed a pre-existing, unrelated bug surfaced while testing: `extractToc()` in `src/lib/content/loader.ts` generated duplicate/incorrect TOC ids (React key-collision crash + broken TOC links on any page with repeated headings, e.g. `### Concept`) and picked up 334 false-positive "headings" from inside fenced code blocks (Python/YAML comments) across the content tree. Fixed by making `extractToc()` fence-aware and switching it to `github-slugger` (added as a direct dependency) so generated ids match `rehype-slug`'s actual DOM ids exactly, including dedup suffixes (`concept`, `concept-1`, `concept-2`, ...). Verified against `01-LLM-Models/Notes/01-LLM-Fundamentals.mdx` (5x `### Concept`) and `06-Agentic-AI/Notes/02-The-Agent-Loop.mdx` (code-fence comments) - no duplicate ids, no bogus headings, and the dev-server-rendered DOM ids match exactly. See Known Issues #6.
- **2026-07-22** - Phase 2 of `vibes/diagram-conversion-checklist.md` complete: converted all 5 ASCII diagrams in `04-MCP/Notes/04-Components.mdx` and `07-Architecture-Deep-Dive.mdx` to Mermaid - 2 nested Host/Client/Server `flowchart TD` box diagrams, 1 `stateDiagram-v2` session lifecycle (CONNECTING → INITIALIZING → ACTIVE → TERMINATED), 1 `sequenceDiagram` for the stdio startup handshake, and 1 `flowchart TD` for the full 5-stage session lifecycle (found while converting, one more than the checklist's original estimate). Verified both pages render 200 with the expected diagram counts via the dev server. Checklist updated to mark Phase 2 done; Phase 3 (RAG module) is next.
- **2026-07-22** - Phase 3 of `vibes/diagram-conversion-checklist.md` complete: converted all 21 ASCII diagrams across the 9-file RAG module (`Notes/01,02,04,05,06,08,09` + both `SystemDesigns/*.mdx`) to Mermaid - the canonical RAG pipeline, HyDE/multi-query/step-back retrieval flows, the Naive→Advanced→Modular→Agentic→GraphRAG→Multimodal evolution ladder, the Modular RAG router, GraphRAG's entity-extraction pipeline, a RAG failure-taxonomy `mindmap`, the full production architecture (ingest/query/feedback), the 100M-doc-scale architecture, a failure-cascade fallback diagram, the 3-way GCP stack comparison (Vertex AI Search vs RAG Engine vs Custom RAG), and both SystemDesigns' end-to-end ingestion+query architectures. Left one JSON-schema-shaped field listing as ASCII per the CLAUDE.md table/schema exception. Verified all 9 pages render 200 with matching diagram counts via the dev server. Checklist updated to mark Phase 3 done; Phase 4 (Agentic AI core notes: Agent Loop, System Design, Multi-Agent Systems, Memory & State, Evaluation) is next.
- **2026-07-22** - Phase 4 of `vibes/diagram-conversion-checklist.md` complete: converted all 21 ASCII diagrams across the 5 Agentic AI core notes - `02-The-Agent-Loop.mdx` (4, including an `xychart-beta` bar chart replacing a hand-drawn ASCII token-growth plot - the first non-flowchart chart type used in the conversion effort), `10-Agentic-System-Design.mdx` (4, including the 6-layer production architecture), `08-Multi-Agent-Systems.mdx` (6, including a `sequenceDiagram` for the event-driven state pattern), `04-Memory-and-State.mdx` (2), and `11-Evaluation-and-Observability.mdx` (5 - these had been authored as ASCII earlier in this same session before the house rule existed, now brought into line). Verified all 5 pages render 200 with matching diagram counts via the dev server. Checklist updated to mark Phase 4 done; Phase 5 (Agentic AI SystemDesigns - finishing 2 partially-converted files, fully converting 2 zero-mermaid ones) is next.
- **2026-07-22** - Phase 5 of `vibes/diagram-conversion-checklist.md` complete, finishing all diagram conversion work in the 06-Agentic-AI module: `insurance-claims-processor.mdx` and `prior-authorization.mdx` had their System Architecture Overview and state-machine ASCII replaced with cross-references to equivalent mermaid diagrams already in the same file (avoiding duplication) and their Data Flow ASCII converted to new `flowchart TD` diagrams; `smart-diagnostic-assistant-interview-answer-1.mdx` and `-2.mdx` (previously zero mermaid) were fully converted, including one large 5-subgraph architecture diagram and a 5-stage orchestrator-subagent flow with parallel fan-out. Verified all 4 pages render 200 with matching diagram counts via the dev server. **All of 06-Agentic-AI (Notes + SystemDesigns) is now fully on Mermaid.** Phase 6 (LLM Models module) is next.
- **2026-07-22** - Phase 6 of `vibes/diagram-conversion-checklist.md` complete: converted 6 ASCII diagrams in `01-LLM-Models/Notes/08-GPU-and-Hardware.mdx` (Data Parallelism, Tensor Parallelism, Pipeline Parallelism - the latter as a `sequenceDiagram` using a `par` block to show micro-batch overlap across GPUs) and `07-Fine-Tuning.mdx` (the prompting→full-fine-tune parameter-modification spectrum, the RLHF 3-stage pipeline, and the Multi-Head Fine-Tuning shared-encoder architecture). Left worked-example ASCII (loss-masking illustration, VRAM arithmetic, GPU memory hierarchy listing) as text since it's not diagram-shaped content. Verified both pages render 200 with matching diagram counts via the dev server. Phase 7 (Prompts module: Tree of Thought/Self-Consistency, Defense Layers) is next.
- **2026-07-22** - Phase 7 of `vibes/diagram-conversion-checklist.md` complete: converted 8 diagrams across `02-Prompts/Notes/03-Advanced-Techniques.mdx` (Standard CoT vs. Tree of Thought branching/backtrack, Self-Consistency majority vote, Prompt Chaining pipeline, Least-to-Most decomposition) and `04-Prompt-Engineering-for-Production.mdx` (the prompt lifecycle, a newly authored Defense Layers diagram for a section that previously had no diagram, and an `xychart-beta` bar chart replacing the ASCII attention-distribution illustration). Left the historical-arc year list and the `prompts/` directory-tree listing as text/ASCII per the CLAUDE.md exceptions. Verified both pages render 200 with matching diagram counts via the dev server. Phase 8 (low-priority CodeLabs README bulk pass) is next; Phase 9 (mixed ASCII/mermaid, 16 individually-low-priority files) still remains after that.
- **2026-07-22** - Phase 8 of `vibes/diagram-conversion-checklist.md` complete: converted all 11 CodeLabs README diagrams to `flowchart TD`/`LR`, matching the master pattern diagrams from Phase 1 - 7 under `06-Agentic-AI/CodeLabs/02-Architectures/{01-Sequential...07-Reflexion}/README.mdx` and 4 under `03-Agentic-Systems/{Research-Assistant, Document-Processor, Autonomous-Task-Planner, Code-Review-System}/README.mdx`. Discovered these 11 files aren't registered in `nav.yml` and therefore aren't routed/renderable through the dev server - verified instead by confirming zero remaining ASCII box-drawing characters and syntax parity with dozens of already-confirmed diagrams from earlier phases. Phase 9 (16 individually low-priority files with mixed ASCII/mermaid across Agentic AI, LLM Models, and MCP) is the last remaining phase.
- **2026-07-22** - **Phase 9 complete - the entire `vibes/diagram-conversion-checklist.md` (all 9 phases) is now done.** Converted diagrams across all 16 remaining files: `06-Agentic-AI/Notes` (07-Design-Patterns, 05-Planning-and-Reasoning, 03-Tool-Use-and-Function-Calling, 01-Agentic-Concepts - 7 diagrams total), `01-LLM-Models/Notes` (02-Architecture, 04-Model-Architecture-Types, 05-KV-Cache-and-Inference-Optimization, 06-Training-and-Pretraining, 09-Failure-Modes-and-Tricky-Issues, 10-Production-Deployment - 15 diagrams total, including several `sequenceDiagram`s for speculative/continuous-batching timelines and `xychart-beta` bars for accuracy-by-position and static-batch-slot charts), `04-MCP/Notes` (01-The-Problem, 02-Definition, 03-The-Solution, 05-Capabilities, 06-Why-MCP-Matters - 11 diagrams total, including a full six-primitives `mindmap` and a circular network-effect flywheel), and `05-Agents/Notes/06-Enterprise-vs-Personal-Agents.mdx` (the last ASCII holdout in that module). Verified all 16 pages render 200 with matching diagram counts via the dev server. **Every ASCII diagram identified in the original full-repo audit has now been converted to Mermaid**, closing out the entire diagram-conversion initiative started earlier in this session.
- **2026-07-22** - Deleted `vibes/diagram-conversion-checklist.md` now that all 9 phases are complete and it's no longer a live tracker (per user request). Added a `CLAUDE.md` > "Project Tracking" note: once a dedicated checklist is fully complete, delete it rather than letting it linger - the outcome lives in this Changelog instead. The house rule itself (`CLAUDE.md` > "Diagrams & Visual Explanations" - prefer Mermaid going forward) remains in place permanently; only the now-finished tracking checklist was removed.
