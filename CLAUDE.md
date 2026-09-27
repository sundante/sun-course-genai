@AGENTS.md

# Project Conventions

## File Naming - Content Files

All content files under `src/content/` use zero-padded numeric prefixes (`01-`, `02-`, etc.).

- When files are deleted, **renumber the remaining files** so there are no gaps (e.g. if `01` and `02` are deleted, rename `03→01`, `04→02`, etc.)
- Keep `nav.yml` in sync with any file renames - it is the single source of truth for navigation
- Module folders are numbered in nav order (`01-LLM-Foundations` ... `17-Agent-Engineering`); a new top-level module needs a title -> slug entry in `MODULE_SLUG_MAP` (`src/lib/content/nav.ts`) - the build throws if one is missing. The module's content folder is derived from its pages, so there is no second map to update
- Moving or renaming a page changes its URL. Add the old -> new `/learn/...` path to `src/lib/content/legacy-redirects.json`; the 404 page forwards old URLs from that map (static export has no server-side redirects)
- Run `npm run check:content` after any content change: broken links, em dashes, numbering gaps, pages missing from `nav.yml`, invalid fence YAML

## Note Template & Course Fences

Every concept note follows this shape (module `INDEX.mdx` pages use the same `objectives` fence with `scope: module`):

1. `# Title` and a one-line definition
2. An `objectives` fence - 3-5 measurable "you will be able to..." outcomes, prerequisites, estimated time
3. The body (Mermaid per the Diagrams section; `audience-biz` / `audience-tech` divs where used)
4. `## Check Yourself` + a `quiz` fence (3-5 questions)
5. `## Exercises` + an `exercise` fence (derivations or hands-on tasks, with hidden solutions)
6. `## Study Notes`, then `## References` (primary sources with year + link)

Fences hold YAML and are rendered by `remarkCourseFences.ts` -> `CourseFences.tsx` / `Quiz.tsx`. String fields are Markdown (links to `.mdx` files are rewritten like any other link). Content is compiled as plain Markdown (`format: "md"`), so JSX components cannot be used in `.mdx` files - add a fence type instead.

```objectives
scope: page            # or "module" on INDEX pages
time: 45 min
outcomes:
  - Derive a model's KV-cache size from its configuration
prerequisites:
  - "[Attention Mechanisms](03-Attention-Mechanisms.mdx) - Q/K/V"
```

```quiz
- q: "Question text (Markdown)"
  options: ["first", "second", "third"]
  answer: 2              # 1-based number of the correct option
  explain: "Why - shown after answering"
- q: "Free-text question"
  answer: "Model answer, revealed on click"
```

```exercise
- title: Short title
  task: |
    Markdown task description
  hints: ["optional hint"]
  solution: |
    Markdown solution, hidden until clicked
```

Reference implementation: `src/content/07-Serving-and-Inference/Notes/01-KV-Cache-and-Inference-Optimization.mdx`.

## Punctuation

- Always use `-` (hyphen-dash) instead of the em dash character (U+2014) in all prose and content files - `npm run check:content` fails on any em dash under `src/`
- This applies to MDX content, component copy, and any user-facing text throughout the site

## Sidebar Numbering

- **Module-level** headings (e.g. "01. LLM Foundations") - rendered in `Sidebar.tsx > ModuleSection`, number is `NavModule.number` (1-based nav.yml order, computed in `nav.ts`)
- **Track labels** (Foundations, Building Models, Serving & Production, Building Apps, Agents, Review) - `- track: Name` entries in `nav.yml`, rendered unnumbered above the first module of each track (`Sidebar.tsx > ModuleList`, `CurriculumTiles.tsx`)
- **Sub-concept leaf items** (e.g. "01 What Are AI Agents") - rendered in `Sidebar.tsx > NavLeaf`, index passed from `.map((child, i) => ...)` inside `NavSection`
- Section group labels (Concepts, Code Labs, etc.) are **not** numbered - they are structural groupings only

## Project Tracking

- `vibes/status.md` is the single source of truth for project status - feature inventory, backlog, known issues, and handover notes for the next session
- `vibes/status.html` is a polished, collapsible human-readable view of the same content
- Update `vibes/status.md` after every successful build/coding session (refresh affected sections + append a Changelog entry); regenerate `vibes/status.html` only on demand, not automatically
- **Always update the relevant tracker doc after every completed build** - not just `vibes/status.md`. If a session works against a dedicated checklist, check off every item actually completed in that session, in the same commit/session the work was done - don't defer it or batch it later. Once a dedicated checklist is fully complete and no longer useful as a live tracker, delete it (don't let finished checklists linger) - capture the outcome in `vibes/status.md`'s Changelog instead
- When a session touches a tracked checklist, still add the one-line `vibes/status.md` Changelog entry summarizing what was completed and which checklist it updated - the checklist has the detail, the changelog entry is the pointer

## Asset Color Scheme

- Generate all assets (HTML pages, dashboards, diagrams, standalone UI mockups, etc.) with **light mode as the default look**, regardless of the viewer's system `prefers-color-scheme`
- Always include an explicit on-page toggle (e.g. via a `data-theme` attribute) to switch to dark mode - never ship a dark-only or light-only asset, and never let system preference silently override the light default

## Diagrams & Visual Explanations

- For architecture, pipeline, flow, state-machine, lifecycle, or comparison content, prefer a **Mermaid diagram** over prose-only explanations or ASCII-art box diagrams - not just black markdown windows with text content
- Mermaid already works with **zero setup** - ` ```mermaid ` fenced code blocks in any `.mdx` file are auto-rendered by `MermaidDiagram.tsx` via `MdxComponents.tsx`; no new dependency or wiring is needed
- **House style to imitate:** `src/content/12-Agent-Foundations/Notes/01-What-Are-AI-Agents.mdx`, `02-Anatomy-of-an-AI-Agent.mdx`, `05-Agent-Memory.mdx` - emoji-labeled nodes, explicit per-node `style X fill:#... stroke:#...` overrides layered on the base theme, one `mindmap` for a component taxonomy. Match this look and feel; don't invent a new visual style per page.
- Pick the diagram type to match the content, not habit:
  - `flowchart LR` / `flowchart TD` - pipelines, architectures, decision flows
  - `stateDiagram-v2` - lifecycles / state machines (e.g. connection states, session states)
  - `sequenceDiagram` - protocol or call flows between actors/services
  - `mindmap` - taxonomies / component breakdowns
- Colors are handled by the shared warm/earth-tone theme in `MermaidDiagram.tsx` (`themeVariables` cScale palette) - only add per-node `style` overrides when distinguishing categories/stages within one diagram, matching the reference files above; don't hand-roll a new palette
- **Still use a table, not a diagram**, for genuinely tabular attribute comparisons (e.g. Framework Comparison, PEFT Methods Comparison, Model Family Comparison) - tables read better than diagrams when the content is a grid of attributes x options
- **ASCII is fine** for conventional directory-tree listings (e.g. `src/`, file trees) - these are a documentation convention, not a diagram substitute
- Skip diagram conversion for `Interview-Questions/*.mdx` and `All_Questions.mdx` - Q&A prose format, not diagram-shaped content
