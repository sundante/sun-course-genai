# Learn GenAI - Project Status

**URL:** https://learngenai.sunmintz.com
**Stack:** Next.js 16.2.9 (App Router, static export) - TypeScript (strict) - Tailwind CSS 4 - MDX (`next-mdx-remote/rsc`) - shadcn/ui - Mermaid
**Deploy:** Static export (`out/`) -> manual GitHub Actions FTP push -> Hostinger, served at `sunmintz.com/learngenai/`
**Last updated:** 2026-08-10
**Last commit at time of writing:** `69f4c46` (2026-08-10 - "New course tranche + sidebar reorg") - local `dev` branch only, not yet pushed to `origin` or merged to `main`/production at time of writing
**Content inventory verified:** `find src/content -name '*.mdx' | wc -l` -> **154 files** (previous tracker said 147 -> stale, +7 from Module 11 - the final module of the 07-11 tranche)

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
- Design system: sun-yellow color tokens, glassmorphism token system (`--glass-panel/nav/card/modal-bg/border`, `--glass-shadow-sm/md/lg`, `--glass-glow-yellow`, `--blur-glass-sm/md/lg`), full light/dark token pairs for every `--sun-*`/`--glass-*`/`--shadcn-*` custom property, prose overrides (now theme-reactive via `var()` references instead of static hex), audience-toggle CSS (see `src/app/globals.css`)
- Dark mode: user-facing toggle (`ThemeToggle.tsx`), hand-rolled `.dark` class + `localStorage`, no-flash-of-wrong-theme inline script in `layout.tsx`, defaults to light. Glass treatment is live across chrome (`Header`/`Sidebar`/`MobileNav`/`PageNav`/`TableOfContents`), modals/overlays (`AudienceOnboardingModal`/`DisclaimerModal`/`sheet.tsx`), shadcn primitives (`card`/`button`/`badge`/`progress`/`separator` - additive `glass` variant on button/badge, restyled-by-default on the other three since they had zero live consumers), the MDX prose layer (tables/code blocks/inline code/blockquotes), and all page-level layouts (landing, lesson, quiz, not-found). `AgentUseCaseMindmap.tsx`'s structural chrome is glass-token-based; its 15 data-driven category accent colors (agent types/domains/complexity tiers) remain light-mode-only hex by design scope, not oversight - see `vibes/GLASS-UI-REDESIGN.md` Section 9. **All 11 sections of the redesign are complete and browser-verified** (real Playwright + Chromium walkthrough, light/dark x desktop/mobile, 2026-08-10) - see `vibes/GLASS-UI-REDESIGN.md` for the final status; the execution checklist has been deleted per its own retirement rule now that nothing remains pending. Not yet pushed/committed to `main` at time of writing.

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

### Course Content - 154 `.mdx` files across 12 modules

| Module | Dir | Contents |
| --- | --- | --- |
| 01 - LLM Models | `01-LLM-Models/` | Overview + 12 notes (Fundamentals -> Architecture -> Attention -> Model Types -> KV Cache/Inference -> Training -> Fine-Tuning -> GPU/Hardware -> Failure Modes -> Production Deployment -> Prompting Strategies -> Q&A Bank) |
| 02 - Prompt Engineering | `02-Prompts/` | Overview + 6 notes (Basics, Core Techniques, Advanced Techniques, Production, Optimization/Automation, Q&A Bank) + Resources |
| 03 - RAG | `03-RAGs/` | Overview + 12 notes (Fundamentals -> Embeddings/Vector Stores -> Chunking/Indexing -> Retrieval Strategies -> RAG Types -> Evaluation/Failure Modes -> System Design -> Vertex AI RAG -> Production -> Scaling -> Q&A Bank) + 2 System Designs (Simple RAG Pipeline, Agentic RAG Hybrid) + Resources |
| 04 - MCP | `04-MCP/` | Overview + 9 notes (The Problem -> Definition -> The Solution -> Components -> Capabilities -> Why It Matters -> Architecture Deep-Dive -> Getting Started -> Q&A Bank) + Implementation |
| 05 - AI Agents | `05-Agents/` | Overview + 6 concept notes (What Are AI Agents, Anatomy, Memory, Capabilities, Use Cases, Enterprise vs Personal) + Code Labs (Agent Types + GCP ADK / LangChain / LangGraph / CrewAI, each with Fundamentals + Simple Agent + Complex Agent) |
| 06 - Agentic AI | `06-Agentic-AI/` | Overview + 12 notes (Agentic Concepts -> Agent Loop -> Tool Use -> Memory/State -> Planning/Reasoning -> Architectural Patterns -> Design Patterns -> Multi-Agent Systems -> Agent Frameworks -> System Design -> Evaluation/Observability -> Q&A Bank) + 4 System Designs (Insurance Claims Processor, Prior Authorization, Smart Diagnostic Assistant x2) + Code Labs matrix (Architectures: Sequential/Parallel/Hierarchical/Orchestrator-Subagent/Pipeline/Adversarial-Debate/Reflexion, each x4 frameworks; Agentic Systems: Research Assistant/Document Processor/Autonomous Task Planner/Code Review System, each x4 frameworks) |
| 07 - Fine-Tuning Lab | `07-Fine-Tuning-Lab/` | Overview + 4 notes (HuggingFace Ecosystem, LoRA & QLoRA Hands-On, Instruction Data & Training Runs, Benchmarking Base vs Tuned) + Q&A Bank + Code Lab (QLoRA Fine-Tune - runnable `peft`/`bitsandbytes` fine-tune + base-vs-tuned benchmark script) |
| 08 - Serving & Inference | `08-Serving-and-Inference/` | Overview + 4 notes (vLLM & Paged Attention, Quantized Inference, Batching/Concurrency/Latency, Streaming & TTFT) + Q&A Bank + Code Lab (FastAPI + vLLM Endpoint - runnable `AsyncLLMEngine` streaming/non-streaming server + concurrent load-test client) |
| 09 - Production Engineering | `09-Production-Engineering/` | Overview + 4 notes (Docker for GPU Inference, Kubernetes & Helm, Model Lifecycle & Rollout, Security & Compliance) + Q&A Bank + Code Lab (Helm Chart & Release Checklist - multi-stage GPU Dockerfile, templated Helm chart with GPU-aware HPA, one-page release-readiness checklist) |
| 10 - Platform Breadth | `10-Platform-Breadth/` | Overview + 4 notes (AWS Bedrock, Databricks & Spark, Azure AI Foundry, Platform Comparison Table) + Q&A Bank (no Code Lab - table-only content per CLAUDE.md's tabular-comparison guidance) |
| Prog Langs - PyTorch Fundamentals | `11-Prog-Langs/PyTorch/` | Overview + 5 notes (Tensors & Autograd, Dataset & DataLoader, Training Loop From Scratch, Checkpointing & Mixed Precision, Debugging & GPU Memory) + Q&A Bank + Code Lab (Raw PyTorch Classifier - runnable MNIST CNN). Standalone top-level "Prog Langs" nav grouping (sibling to Knowledge Check, positioned last before it) - nested one level deeper than other modules so future language-specific modules (e.g. a TensorFlow or JAX module) can sit alongside PyTorch as siblings, same nesting pattern as `05-Agents/GCP-ADK` etc. |
| Knowledge Check | `Interview-Questions/` + `All_Questions.mdx` | Per-module question banks (01-11, `All_Questions.mdx` not yet updated for 07-11) + aggregate "All Questions" |

**Most recently active area:** Chapter 05 (AI Agents) - Anatomy of an AI Agent, Agent Memory, Agent Use Cases, and Enterprise vs Personal Agents notes were all added/updated on 2026-06-29, the same day as the last commit.

**Naming convention:** zero-padded numeric prefixes (`01-`, `02-`, ...) at module and file level; `INDEX.mdx` per module overview; `Notes/`, `SystemDesigns/`, `CodeLabs/`, `Resources/`, `Implementation/` as topic subfolders. See root `CLAUDE.md` for the renumbering rule when files are deleted.

---

## 3. Backlog

### Near-term
- [x] ~~**Glassmorphism / "Liquid Glass" UI redesign** - whole-site restyle + new dark mode (toggle, defaults to light)~~ - **DONE 2026-08-10**, all 11 sections complete and browser-verified (see `vibes/GLASS-UI-REDESIGN.md` for the plan/final status; the execution checklist has since been deleted per its own retirement rule - see Changelog). Not yet pushed/committed to `main` at time of writing.
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

**Where things left off:** As of 2026-08-10, two large bodies of work landed in the same extended session and are **committed to `dev` locally but not yet pushed to `origin` or merged to `main`** (commit `69f4c46`, "New course tranche + sidebar reorg") - plus a second, larger batch of changes on top of that (the full glass UI redesign, Sections 5-11) that is **still uncommitted** as of this writing. Check `git status`/`git log` before assuming what's actually on disk vs. committed:
1. The 07-11 content tranche (5 new modules: PyTorch Fundamentals, Fine-Tuning Lab, Serving & Inference, Production Engineering, Platform Breadth) plus a sidebar reorg that moved PyTorch into a new "Prog Langs" grouping and renumbered 07-10 - this part is committed (`69f4c46`).
2. The full 11-section Glassmorphism/dark-mode UI redesign (`vibes/GLASS-UI-REDESIGN.md`, now marked COMPLETE) - **not yet committed**. 19 files changed: every chrome component, both modals, all 5 shadcn primitives, the MDX prose layer, all page-level layouts, and `AgentUseCaseMindmap.tsx`. Real-browser-verified via a temporary Playwright + Chromium install (not a project dependency - see Known Issues if you need to re-verify visually).

**Suggested next steps, in priority order:**
1. **Commit the uncommitted glass-redesign work**, then decide whether to push `dev` to `origin` and/or merge to `main` for production deploy - nothing has been pushed or deployed yet.
2. Decide whether to wire `npm run lint` (and ideally `next build`) into a CI check on PRs/push - currently nothing automated guards `main` before a manual deploy.
3. Pick one near-term backlog item to unblock next: Quiz feature is the most visible gap (routes exist but are pure placeholders), and `QuizCard` in `src/types/content.ts` is already scaffolded for it.
4. If rotating or auditing deploy credentials, use the secret names in this file (`FTP_SERVER`/`FTP_USERNAME`/`FTP_PASSWORD`), not any older doc.
5. Sanity-check `nav.yml` against `src/content/` before adding new content - it's the single source of truth for navigation, and (as of the 07-11 tranche) `src/lib/content/nav.ts`'s `MODULE_SLUG_MAP`/`MODULE_DIR_MAP` must also be updated for any new top-level module or its pages silently fail to render - see Changelog for the bug this caused on Module 07.
6. Re-verify content counts (`find src/content -name '*.mdx' | wc -l`) whenever content is added/removed, and update this file's header count.

**Process going forward:**
- `vibes/status.md` (this file): update after every successful build/coding session - refresh affected sections + append a one-line Changelog entry below.
- `vibes/status.html`: regenerate on demand only (not tied to every session) - reflects whatever this file says at generation time.

---

## 6. Project Structure

```
src/
  app/
    layout.tsx                        root layout (fonts, no-flash theme script, DisclaimerModal, AudienceOnboardingModal)
    page.tsx                          homepage (own inline header, incl. ThemeToggle)
    not-found.tsx                     404 (renders UnderDevelopment)
    globals.css                       design tokens (sun-*/glass-*/shadcn-* incl. light+dark pairs), .prose overrides
    (course)/
      layout.tsx                      header + sidebar shell
      learn/[module]/[slug]/page.tsx  course content pages (dark title banner, sticky glass footer nav)
      quiz/all/page.tsx               quiz stub (renders UnderDevelopment)
      quiz/[module]/page.tsx          quiz stub (renders UnderDevelopment)
  components/
    ui/                               shadcn primitives - button, badge (additive `glass` variant), card, progress,
                                      separator (restyled glass-by-default, zero live consumers), sheet (mobile drawer)
    course/                           Header, Sidebar, MobileNav, ThemeToggle, AudienceToggle, AudienceOnboardingModal,
                                      DisclaimerModal, DisclaimerNote, TableOfContents, PageNav,
                                      UnderDevelopment, MermaidDiagram, AgentUseCaseMindmap, MdxComponents
  lib/
    utils.ts                          cn() helper
    content/
      nav.ts                          navigation tree from nav.yml, MODULE_SLUG_MAP/MODULE_DIR_MAP, isStubFile() WIP detection
      loader.ts                       reads .mdx files, extracts TOC
      remarkRewriteMdLinks.ts         build-time cross-link rewriting
  types/
    content.ts                        NavItem, NavModule, NavigationTree, PageRef, PageContent, TocItem, QuizCard
  content/                            154 .mdx source files across 12 modules (compiled to HTML at build time)
    nav.yml
    01-LLM-Models/
    02-Prompts/
    03-RAGs/
    04-MCP/
    05-Agents/
    06-Agentic-AI/
    07-Fine-Tuning-Lab/
    08-Serving-and-Inference/
    09-Production-Engineering/
    10-Platform-Breadth/
    11-Prog-Langs/PyTorch/            nested one level deeper - future language modules are siblings here
    Interview-Questions/
    All_Questions.mdx

vibes/                                project tracking & active plans
  status.md                          this file - the sole live source of truth
  status.html                        polished collapsible status view (regenerated on demand, not auto-synced)
  GLASS-UI-REDESIGN.md               glassmorphism/dark-mode redesign plan - COMPLETE, all 11 sections shipped
  design-system-playbook.md          portable layout/nav/UX spec, reusable across projects (not a task tracker)

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
- **2026-07-22** - Scoped a whole-site Glassmorphism/"Liquid Glass" UI redesign (with new dark mode + toggle, defaulting to light) at the user's request. Produced an effort estimate (~17 eng-days) via codebase recon (styling architecture, component/page inventory, existing design docs), then persisted it as `vibes/GLASS-UI-REDESIGN.md` (11 section-level plans: design tokens, dark-mode infra, theme toggle, core chrome, modals, shadcn primitives, MDX rendering layer, page layouts, the AgentUseCaseMindmap component, cross-cutting QA, design-doc sync) with a companion `vibes/glass-ui-redesign-checklist.md` for execution tracking. No implementation started yet - Backlog/Near-term updated with a pointer.
- **2026-07-22** - Cleaned out `vibes/` per user request: deleted `BUILD-PROMPT.md` (severely stale - referenced a nonexistent top-level `content/`/`project-docs/` layout, `.md` content files instead of the actual `.mdx`, a `basePath` no longer in `next.config.ts`, and only 7 of the current 13 components), plus `DESIGN-SYSTEM.md`, `UI-COMPONENTS.md`, and `PAGE-LAYOUTS.md` (accurate for what they covered but stale - missing newer color tokens, both modals, and 6 of 13 components; user chose to delete rather than refresh, `status.md` + source files are now the sole reference). Also removed the stray `.DS_Store`. Updated dangling references in this file's Project Structure section and in `vibes/GLASS-UI-REDESIGN.md`/`glass-ui-redesign-checklist.md` (Section 11 rescoped from "Design Doc Sync" to "Status Doc Sync" since there are no more separate spec docs to keep in lockstep; total estimate revised to ~16.5 days).
- **2026-07-22** - Implemented Section 1 (Design Token System) of the glass UI redesign in `src/app/globals.css`: added light/dark pairs for every `--color-sun-*` token via a `:root`/`.dark` runtime-variable indirection (mirrors the existing `--font-sans` pattern so utilities stay reactive to theme changes instead of baking in a static value); added glass surface tokens per elevation (panel/nav/card/modal + scrim) and shadow/glow/blur tokens, all with dark pairs. Also fixed a pre-existing bug found along the way: the shadcn `:root` HSL block (`--background`, `--border`, `--ring`, etc.) had no `@theme` mapping, so Tailwind v4 was silently dropping every `bg-background`/`border-input`/`ring-ring` utility already used in `src/components/ui/*.tsx` (button, sheet, badge) - these are real currently-used classes, so the fix was in-scope token-system work. `body` background/color now reads from the new tokens. Verified via `npm run build` (108 pages, 0 errors) and dev-server 200s; new glass-specific utilities (`shadow-glass-*`, `backdrop-blur-glass-*`, `bg-glass-*`) are defined but won't appear in shipped CSS until a component references them (Tailwind v4 JIT tree-shaking - expected, not a bug). No dark-mode toggle exists yet (Section 2/3 next) - light mode is unchanged visually. `vibes/glass-ui-redesign-checklist.md` Section 1 checked off.
- **2026-07-22** - Implemented Sections 2-3 (Dark Mode Infrastructure, Theme Toggle Component) of the glass UI redesign. Hand-rolled dark mode instead of adding `next-themes` (a single boolean toggle didn't justify a new dependency): a no-flash-of-wrong-theme inline `<script>` in `src/app/layout.tsx`'s `<head>` reads `localStorage["theme"]` and adds `.dark` to `<html>` before hydration, defaulting to light with no `prefers-color-scheme` check (per the locked-in requirement). New `src/components/course/ThemeToggle.tsx` is the toggle - keyboard-operable, `aria-pressed`, hydration-safe (renders a neutral disabled placeholder until mount to avoid a hydration-mismatch warning, since static-export HTML has no access to the visitor's stored preference at build time). Wired into both `Header.tsx` (course/lesson/quiz pages) as an always-visible icon button and into `src/app/page.tsx`'s own separate header markup (the landing page doesn't reuse `Header.tsx`, so it needed its own copy or the toggle would be invisible on `/`). Verified via `npm run build` (108 pages) and inspecting the built HTML for the pre-hydration script and placeholder button; **not yet verified in an actual browser** (no browser tool available this session) - only curl/build-output checked. Known limitation, expected at this stage: most chrome components (`Header`, `Sidebar`, `MobileNav`, both modals, `AgentUseCaseMindmap`, the landing page body) still hardcode `bg-white`, so toggling dark mode right now only visibly changes page background/text, not chrome - that's Sections 4/5/8/9. `vibes/glass-ui-redesign-checklist.md` Sections 2-3 checked off.
- **2026-08-09** - Shipped Module 07 (PyTorch Fundamentals), the first of the `vibes/genai-course-gap-analysis.md` 07-11 content tranche: new `07-PyTorch-Fundamentals/` with `INDEX.mdx` + 5 Notes files (Tensors & Autograd, Dataset & DataLoader, Training Loop From Scratch, Checkpointing & Mixed Precision, Debugging & GPU Memory) + a 15-Q&A review bank, all following the `audience-biz`/`audience-tech` split and Mermaid house style from `05-Agents`. Added one hands-on Code Lab (`CodeLabs/01-Raw-PyTorch-Classifier`) - a real, runnable raw-PyTorch CNN (`model.py`/`train.py`/`requirements.txt`) that trains an MNIST classifier end-to-end with a custom Dataset/DataLoader pipeline, a hand-written training loop, resumable checkpointing, and `autocast`/`GradScaler` mixed precision (auto-disabled on CPU). Added a complementary cross-topic `Interview-Questions/07-PyTorch-Fundamentals.mdx`. Wired the new module into `nav.yml` (top-level block after Agentic AI, plus a Knowledge Check line) and verified it parses as valid YAML with `python3 -c "import yaml; yaml.safe_load(...)"`; confirmed every new file referenced in the nav block exists on disk. `All_Questions.mdx` was intentionally left untouched (out of scope per the task instructions - it's a freeform aggregate file, not enumerated as a required edit) and the dev-server-render check was not run this session (no dev server started); both left unchecked in `vibes/modules-07-11-checklist.md`, all other Module 07 items checked off. Module 08 (Fine-Tuning & PEFT Lab) is next.
- **2026-08-09** - Verified Module 07 with an actual `next build`: the module's 8 new pages were silently missing from both `.next/server/app/learn/` and the static `out/` export, because `nav.yml` alone does not register a new module - `src/lib/content/nav.ts` hardcodes a separate `MODULE_SLUG_MAP`/`MODULE_DIR_MAP` (title -> URL slug -> content directory) that every module must also be added to. Added the `"PyTorch Fundamentals": "pytorch-fundamentals"` / `"pytorch-fundamentals": "07-PyTorch-Fundamentals"` entries; rebuilt and confirmed all 8 pages now generate (117 total pages, up from 109) in both the server build and the static export used for deployment. Updated `vibes/modules-07-11-checklist.md` with this as a new required step for every remaining module (08-11) and checked off Module 07's "dev server renders, no MDX errors" item accordingly.
- **2026-08-10** - Shipped Module 08 (Fine-Tuning & PEFT Lab), the second of the `vibes/genai-course-gap-analysis.md` 07-11 content tranche: new `08-Fine-Tuning-Lab/` with `INDEX.mdx` + 4 Notes files (HuggingFace Ecosystem, LoRA & QLoRA Hands-On, Instruction Data & Training Runs, Benchmarking Base vs Tuned) + a 15-Q&A review bank, following the `audience-biz`/`audience-tech` split and Mermaid house style, deliberately linking back to (not re-deriving) the LoRA math and VRAM/quantization formulas already covered in `01-LLM-Models/Notes/07-Fine-Tuning.mdx` and `08-GPU-and-Hardware.mdx` - added short "Hands-On Lab" cross-reference sections to both of those files pointing into the new module. Added one hands-on Code Lab (`CodeLabs/01-QLoRA-Fine-Tune`) - a real, runnable QLoRA fine-tune (`train_qlora.py`: 4-bit NF4 loading via `bitsandbytes`, a `peft` `LoraConfig`, masked instruction-tuning loss, `Trainer`-based training with a built-in demo dataset fallback) plus a `benchmark.py` that loads base vs adapter-merged model and prints a measured (not estimated) base-vs-tuned comparison table - ROUGE-L quality proxy, tokens/sec with warm-up excluded, peak VRAM via `torch.cuda.max_memory_allocated()`, and an illustrative cost-per-1k-requests figure. Added a complementary cross-topic `Interview-Questions/08-Fine-Tuning-Lab.mdx`. Wired the new module into `nav.yml` (top-level block after PyTorch Fundamentals, plus a Knowledge Check line) and into `src/lib/content/nav.ts`'s `MODULE_SLUG_MAP`/`MODULE_DIR_MAP` from the start this time (the step Module 07 initially missed) - verified with a full `next build`: all 7 new module pages (index, 4 notes, Q&A bank, codelab landing) plus the new Knowledge Check page render with zero errors, 125 total pages generated. Verified nav.yml is valid YAML, every referenced file path exists on disk, both Python scripts pass `py_compile`, and zero em-dashes across all new content. `All_Questions.mdx` was intentionally left untouched, same as Module 07 (out of scope, not enumerated in the task instructions) and left unchecked in `vibes/modules-07-11-checklist.md`; all other Module 08 items checked off. Module 09 (Serving & Inference) is next.
- **2026-08-10** - Shipped Module 09 (Serving & Inference), the third of the `vibes/genai-course-gap-analysis.md` 07-11 content tranche: new `09-Serving-and-Inference/` with `INDEX.mdx` + 4 Notes files (vLLM & Paged Attention, Quantized Inference, Batching/Concurrency/Latency, Streaming & TTFT) + a 15-Q&A review bank, following the `audience-biz`/`audience-tech` split and Mermaid house style, deliberately linking back to (not re-deriving) the KV-cache/Paged-Attention theory in `01-LLM-Models/Notes/05-KV-Cache-and-Inference-Optimization.mdx` and the NF4/`bitsandbytes` training-time quantization covered in `08-Fine-Tuning-Lab/Notes/02-LoRA-and-QLoRA-Hands-On.mdx`, contrasting it against GPTQ/AWQ serving-time quantization instead. Added one hands-on Code Lab (`CodeLabs/01-FastAPI-vLLM-Endpoint`) - a real FastAPI server (`serve.py`) backed by a vLLM `AsyncLLMEngine`, exposing a `/generate` endpoint with both SSE streaming (per-chunk TTFT reporting) and non-streaming responses, plus a `load_test.py` client that fires bounded-concurrency async requests and reports aggregate tokens/sec, p50/p95 per-request latency, and p50/p95 TTFT with warm-up requests excluded - the "record tokens/sec under load" artifact called out in the gap analysis. Added a complementary cross-topic `Interview-Questions/09-Serving-and-Inference.mdx`, and a short cross-reference note in `01-LLM-Models/Notes/10-Production-Deployment.mdx` pointing into the new module. Wired the new module into `nav.yml` (top-level block after Fine-Tuning Lab, plus a Knowledge Check line) and into `src/lib/content/nav.ts`'s `MODULE_SLUG_MAP`/`MODULE_DIR_MAP` from the start - verified with a full `next build`: all 7 new module pages (index, 4 notes, Q&A bank, codelab landing) plus the new Knowledge Check page render with zero errors, 133 total pages generated. Verified nav.yml is valid YAML, every referenced file path exists on disk, both Python scripts pass `py_compile`, and zero em-dashes across all new content. `All_Questions.mdx` was intentionally left untouched, same as Modules 07-08 (out of scope, not enumerated in the task instructions) and left unchecked in `vibes/modules-07-11-checklist.md`; all other Module 09 items checked off. Module 10 (Production Engineering) is next.
- **2026-08-10** - Shipped Module 10 (Production Engineering), the fourth of the `vibes/genai-course-gap-analysis.md` 07-11 content tranche: new `10-Production-Engineering/` with `INDEX.mdx` + 4 Notes files (Docker for GPU Inference, Kubernetes & Helm, Model Lifecycle & Rollout, Security & Compliance) + an 18-Q&A review bank, following the `audience-biz`/`audience-tech` split and Mermaid house style. Added one hands-on Code Lab (`CodeLabs/01-Helm-Chart-and-Release-Checklist`) - a multi-stage GPU-inference `Dockerfile` (CUDA `-devel` build stage, `-runtime` final stage) packaging the Module 09 FastAPI+vLLM `serve.py`, a real Helm chart (`Chart.yaml`, `values.yaml`, templated `deployment.yaml`/`service.yaml`/`hpa.yaml` with GPU requests=limits and a GPU-utilization-based HPA), and a standalone `release-readiness-checklist.md` - the "first 90 days" artifact named in the gap-analysis doc. Added a complementary cross-topic `Interview-Questions/10-Production-Engineering.mdx`. Wired the module into `nav.yml` and `src/lib/content/nav.ts`'s `MODULE_SLUG_MAP`/`MODULE_DIR_MAP` - verified with a full `next build`: all 7 new module pages render with zero errors, 141 total pages generated. Verified nav.yml and both Helm `Chart.yaml`/`values.yaml` parse as valid YAML, every referenced file path exists on disk, and zero em-dashes across all new content. **Note:** this module's build was originally delegated to a background agent, which was interrupted mid-session by an account-level session limit after completing only `Notes/01-Docker-for-GPU-Inference.mdx` (verified complete and kept as-is); the remaining files (Notes 02-05, INDEX, CodeLabs, nav wiring) were written directly in the main session following the same conventions and verified identically. `All_Questions.mdx` left untouched, same as Modules 07-09. Module 11 (Platform Breadth) is next and is the last module in this tranche.
- **2026-08-10** - Shipped Module 11 (Platform Breadth), the fifth and final module of the `vibes/genai-course-gap-analysis.md` 07-11 content tranche: new `11-Platform-Breadth/` with `INDEX.mdx` + 4 Notes files (AWS Bedrock, Databricks & Spark, Azure AI Foundry, Platform Comparison Table) + a 15-Q&A review bank, following the `audience-biz`/`audience-tech` split and Mermaid house style. This module has no Code Lab by design (per CLAUDE.md's "table, not diagram, for tabular attribute comparisons" guidance and the gap-analysis doc's own scoping) - the artifact is the Vertex AI ↔ Bedrock ↔ Azure AI Foundry comparison table itself, covering model access/RAG/guardrails, data platform, and MLOps equivalents across all three clouds, plus a note on how to use it credibly in an interview (name the capability, then the products, then one real architectural difference - not just recite a vocabulary mapping). Added a complementary cross-topic `Interview-Questions/11-Platform-Breadth.mdx`. Wired the module into `nav.yml` and `src/lib/content/nav.ts`'s `MODULE_SLUG_MAP`/`MODULE_DIR_MAP` - verified with a full `next build`: all 6 new module pages render with zero errors, 148 total pages generated. Verified nav.yml is valid YAML and zero em-dashes across all new content. **This module (and the rest of the tranche after Module 10's interruption) was built directly in the main session rather than via a background agent**, since an account-level session limit had interrupted the prior background-agent attempt at Module 10. `All_Questions.mdx` left untouched, same as Modules 07-10. **The full 07-11 tranche from `vibes/genai-course-gap-analysis.md` is now complete** - 5 new modules, 45 new content files, 154 total `.mdx` files across 12 modules. `vibes/modules-07-11-checklist.md` deleted per CLAUDE.md's rule to remove a finished checklist once it's no longer a live tracker - this changelog entry is now the record of what shipped.
- **2026-08-10** - Reordered the sidebar into a more logical learning/upskilling sequence and moved PyTorch Fundamentals into a new "Prog Langs" grouping, per user request. Renumbered module directories: `08-Fine-Tuning-Lab` -> `07-Fine-Tuning-Lab`, `09-Serving-and-Inference` -> `08-Serving-and-Inference`, `10-Production-Engineering` -> `09-Production-Engineering`, `11-Platform-Breadth` -> `10-Platform-Breadth`, and `07-PyTorch-Fundamentals` -> `11-Prog-Langs/PyTorch/` (nested one level deeper, same pattern as `05-Agents/GCP-ADK` etc., so future language-specific modules can sit alongside it as siblings under `Prog Langs`). Matching renames applied to `Interview-Questions/*.mdx` (07-11 renumbered accordingly, PyTorch's file became `11-PyTorch-Fundamentals.mdx`). Used a staging-directory technique (`mv X _tmp`, shift the rest down, `mv _tmp` into final spot) to avoid collisions during the renumbering. Bulk-updated every cross-reference across all touched content files (`.mdx`, `.py`, `Dockerfile`) via `sed` on the unique old directory names (safe because each was a distinct full string, not just a numeric prefix, so no double-transformation risk regardless of order) - fixed a handful of resulting ugly anchor-text artifacts by hand (e.g. `[11-Prog-Langs/PyTorch: ...]` -> `[PyTorch Fundamentals: ...]`) and manually corrected the 4 relative links inside PyTorch's own `INDEX.mdx` that needed an extra `../` for its new nesting depth. Rebuilt `nav.yml` with the new order (01-06 unchanged, then Fine-Tuning Lab -> Serving & Inference -> Production Engineering -> Platform Breadth, then a new top-level `Prog Langs` section containing nested `PyTorch Fundamentals`, then Knowledge Check last as always) and reordered/renumbered the Knowledge Check interview-question links to match, with PyTorch's link now last before the section ends. Updated `src/lib/content/nav.ts`'s `MODULE_SLUG_MAP`/`MODULE_DIR_MAP`: removed the old `pytorch-fundamentals` entry, added `"Prog Langs": "prog-langs"` / `"prog-langs": "11-Prog-Langs"`, and shifted the other four modules' directory mappings down by one. Verified via a full `next build`: still 148 total pages (zero lost or duplicated), confirmed all 8 PyTorch pages now serve at `/learn/prog-langs/pytorch-*` and the old `/learn/pytorch-fundamentals/*` route no longer exists, confirmed `fine-tuning-lab` correctly occupies the old module-08 slot. Grepped the full content tree for any remaining old-numbered path references and em-dashes - both clean. Checked `Sidebar.tsx`, the homepage, and the quiz stub page for hardcoded module slugs/counts that might need updating - none found, sidebar numbering and abbreviations are computed dynamically from `nav.yml` order/titles so no further changes were needed there.
- **2026-08-10** - Updated this file's stale header (`Last commit at time of writing` still pointed at `e5f3191` from 2026-06-29; corrected to `69f4c46`, noted it's local-only on `dev` at time of writing, not yet pushed/merged to `main`). Audited all files in `vibes/` for done-vs-pending status at user request and deleted `vibes/genai-course-gap-analysis.md` - all 5 of its shortlist items (PyTorch Fundamentals, Fine-Tuning Lab, Serving & Inference, Production Engineering, Platform Breadth) are now shipped, so it had become a fully-actioned checklist rather than a live reference, matching the precedent already set for `modules-07-11-checklist.md`. Kept `vibes/GLASS-UI-REDESIGN.md` and `vibes/glass-ui-redesign-checklist.md` - only Sections 1-4 of 11 are done, still an active tracker. Kept `vibes/design-system-playbook.md` - it's a portable reference spec meant to persist across projects, not a task checklist, so it has no "done" state to retire.
- **2026-08-10** - Implemented Sections 5-9 of the glass UI redesign (`vibes/glass-ui-redesign-checklist.md`) at user request, continuing from Sections 1-4 (done 2026-07-22). **Section 5 (Modals & Overlays):** `AudienceOnboardingModal.tsx`/`DisclaimerModal.tsx` scrim+panel and shadcn `sheet.tsx` (mobile drawer overlay + all 4 side variants) converted to glass tokens. **Section 6 (shadcn Primitives):** audited `variant=` usage first - found zero live consumers of `<Card>`/`<Button>`/`<Badge>`/`<Progress>`/`<Separator>` as JSX (only `buttonVariants({variant:"ghost"})` used once in `Header.tsx`), so `button.tsx`/`badge.tsx` got an additive `glass` variant (non-breaking) while `card.tsx`/`progress.tsx`/`separator.tsx` (no prior variant system, zero consumers) were restyled directly rather than given an unused variant enum. **Section 7 (MDX/Prose Layer):** converted every `.prose` CSS custom property in `globals.css` from static hex to the `sun-*`/`glass-*` token references (so prose text is now theme-reactive), added glass border/shadow chrome to code blocks (kept background solid/theme-matched, not translucent, to protect code legibility per the plan's own risk callout), added new glass-treated `.prose table`/`.prose thead` rules. **Section 8 (Page-Level Layouts):** landing page, lesson page, and the shared `UnderDevelopment` component (covers both quiz routes + `not-found.tsx`) converted to glass tokens. **Found and fixed a real, previously-undiagnosed dark-mode contrast bug in the process**: many elements paired a theme-invariant fixed background (`bg-sun-yellow`, or an intentionally-fixed dark banner) with the *reactive* `text-sun-dark`/`text-white` tokens, which invert per-theme - so a yellow button's text would go near-white-on-yellow in dark mode, and the lesson-page title banner (flagged but not fixed back in Section 4) had literally illegible white-on-near-white text. Fixed every instance found (lesson-page banner, landing-page header/hero/footer/buttons/stats, `UnderDevelopment`'s "Go Home" button) by pairing fixed backgrounds with fixed `text-zinc-900`/`text-white` instead of reactive tokens. **Section 9 (AgentUseCaseMindmap.tsx):** converted all structural chrome (panel/tab-bar/card/table backgrounds, borders, primary text across all 4 sub-components) to glass tokens; deliberately left the 15 data-driven category accent colors (4 agent types, 8 domains, 3 complexity tiers) as light-mode hex by documented scope decision (a proper dark-mode palette for 15 distinct semantic hues is separate, larger work), matching the plan's own flag of this component as highest-uncertainty. **Section 10 (QA):** could only be done as static analysis - grepped the full component tree for every remaining `bg-white`/`bg-black`/`text-white` and manually confirmed each is an intentional fixed-color pairing, not a reactive-token bug (this is exactly the technique that caught the contrast bug above) - but an actual browser walkthrough (light/dark), mobile performance check, and cross-browser check were **not done**, since no browser/screenshot tool was available in this session; left honestly unchecked in the checklist rather than claimed. Verified all of the above via `npm run build` (148 pages, 0 errors, unchanged from before this session) after every section. **Section 11 (Status Doc Sync)** done in this same entry - `vibes/status.md`'s "What's Built" and `vibes/GLASS-UI-REDESIGN.md`'s status header both updated to reflect Sections 1-9 complete, Section 10 partial. The checklist is intentionally not deleted yet - Section 10's browser-based items remain genuinely open for the next session with real browser access.
- **2026-08-10** - Completed Section 10 (Cross-Cutting QA Pass) of the glass UI redesign for real, closing out the glass-ui-redesign effort entirely. The user pushed back on marking Section 10 done via static analysis alone, so this session installed a working browser: `npx playwright install chromium --with-deps` (network access confirmed available, install succeeded), started the dev server, and ran a real Playwright script capturing screenshots across light/dark x desktop (1440x900)/mobile (390x844) for the landing page, a lesson page, a fine-tuning-lab index, a code-lab page with tables, the new Prog Langs nested module, quiz-all, the disclaimer modal, the mobile nav drawer, and all 4 tabs of `AgentUseCaseMindmap.tsx` - 24+ screenshots total, manually reviewed. **This caught 3 real bugs the build-only/static-grep verification had missed:** (1) a malformed CSS comment in Section 7's `.prose` block (`sun-*/glass-*` contains a literal `*/`, closing the CSS comment early) broke dev-mode CSS parsing entirely and 500'd every page - `next build` had silently tolerated it, so "the build passes" was not sufficient proof the CSS was valid; fixed by respacing the comment. (2) Section 7 only overrode 10 of Tailwind Typography's ~19 CSS custom properties - missing `--tw-prose-bold` (among others: `lead`/`counters`/`bullets`/`quotes`/`quote-borders`/`captions`/`kbd`/`kbd-shadows`) left bold table-header text nearly invisible against dark glass table backgrounds in dark mode; also found `--tw-prose-blockquote-border` (used in the original Section 7 pass) isn't a real Typography variable - the correct name is `--tw-prose-quote-borders` - fixed by adding the complete, correctly-named variable set. (3) three more instances of the recurring fixed-yellow-bg-plus-reactive-text bug beyond what Section 8 had already fixed: `AudienceToggle.tsx`'s active pill, `Sidebar.tsx`'s collapsed-rail active module badge, and `DisclaimerModal.tsx`'s primary CTA button - all fixed, then a final `grep -rn "bg-sun-yellow.*text-sun-dark"` across all of `src/` confirmed zero remaining instances. Rebuilt and re-ran the full screenshot pass a second time to confirm every fix - all pages clean, zero console errors beyond the expected/documented hydration-mismatch noise from the no-flash-of-wrong-theme script. **`vibes/glass-ui-redesign-checklist.md` is now deleted** - all 11 sections genuinely complete and verified, per its own retirement instruction; `vibes/GLASS-UI-REDESIGN.md`'s status line updated to COMPLETE. The Playwright browser binary and the throwaway verification script/screenshots live in `/tmp`, not committed to the repo.
