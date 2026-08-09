# Course Site Design System Playbook

A portable spec for the layout, navigation, UX, UI, and cosmetic conventions used in this project (`sun-course-genai`). Copy this file into any new course-project repo and hand it to Claude/Codex as a build brief — it is written to be self-contained and not dependent on this repo's specific content.

Reference implementation: `sun-course-genai` (Next.js 16, App Router, static export, Tailwind CSS 4, MDX).

---

## 1. Stack Assumptions

- **Next.js (App Router)**, static export (`output: "export"`, `trailingSlash: true`, `images.unoptimized: true`) — no server runtime needed, deployable to any static host.
- **Tailwind CSS 4**, CSS-first config — no `tailwind.config.ts`. All tokens are plain CSS custom properties in `:root` / `.dark`, aliased into Tailwind utilities via `@theme inline`.
- **shadcn/ui** primitives (`button`, `sheet`, `card`, `badge`, `progress`, `separator`), style `"default"`, base color `"zinc"`, icon library `lucide`.
- **MDX** via `next-mdx-remote/rsc`, with `remark-gfm`, `rehype-raw`, `rehype-slug`, `rehype-autolink-headings`, `rehype-highlight`.
- **Mermaid** for all diagrams — zero extra wiring beyond one render component; content authors just write ` ```mermaid ` fences.
- No test framework, no CI gate — this is a docs/course site, not a product app. Add tests only if the new project actually needs them.

---

## 2. Content File Conventions

- Content lives under `src/content/`, organized into **numbered modules**: `01-Module-Name/`, `02-Module-Name/`, etc. Zero-padded, two digits.
- Each module has an `INDEX.mdx` overview file.
- Inside a module, standard subfolders as needed: `Notes/`, `Resources/`, `SystemDesigns/`, `Implementation/`, `CodeLabs/`, and framework/tool-specific subdirectories, each with its own numbered files and optional `INDEX.mdx`.
- **`nav.yml` is the single source of truth for navigation** — not the filesystem. It's an MkDocs-style YAML tree:
  ```yaml
  nav:
    - Home: index.mdx
    - Module Title:
      - Overview: 01-Module-Name/INDEX.mdx
      - Concepts:
        - Topic One: 01-Module-Name/Notes/01-Topic-One.mdx
      - Code Labs:
        - Lab One: 01-Module-Name/CodeLabs/01-Lab-One.mdx
  ```
  - **Top level = modules.**
  - **Second level = group labels** (Concepts, Code Labs, System Designs, etc.) — structural only, never numbered, can nest arbitrarily deep.
  - **Leaves = `Title: relative/path.mdx` pairs.**
- **Renumbering rule**: when a content file is deleted, renumber the remaining files so there are no gaps (`03→01`, `04→02`, ...), and update `nav.yml` to match.
- **Punctuation rule**: always use `-` (hyphen) instead of `—` (em dash) in all prose and content files, and in component copy.
- **WIP detection is automatic, not a frontmatter flag**: count non-heading/non-empty/non-table/non-blockquote body lines in a file; if fewer than ~8, treat the page as a stub (`wip: true`). Render stubs in the sidebar as non-clickable, italicized, with a "WIP" badge — don't hand-maintain a WIP list.

---

## 3. Navigation / Sidebar Architecture

Three-tier component structure, each tier with a distinct numbering rule:

| Tier | Component | Numbered? | Index source |
|---|---|---|---|
| Module (e.g. "01. LLM Models") | `ModuleSection` | Yes | `.map((mod, i) => ...)` at the top-level nav map |
| Group label (e.g. "Concepts", "Code Labs") | `NavSection` | **No** — structural only | n/a |
| Leaf page (e.g. "01 What Are AI Agents") | `NavLeaf` | Yes | `.map((child, i) => ...)` *inside* `NavSection`, i.e. re-starts at 1 within each group |

Behavior rules:
- **Auto-expand on active route**: each section checks whether the current pathname is somewhere inside its subtree (`containsPath()`); if so, it defaults to expanded. Re-checked on every route change so navigating always reveals the active page in the tree.
- **Independent collapse state** per section (local component state), not a single global expand/collapse.
- **Active leaf highlight**: exact pathname match (normalized, trailing slash stripped) gets a distinct background + text color; everything else gets a subtle hover state.
- **WIP leaves**: render as a `<span>` (not a link), italic, with a small trailing pill badge reading "WIP".
- **Whole-sidebar collapse (desktop only)**: a collapsed rail state that shrinks the sidebar to an icon-only strip, showing 2-letter abbreviations of each module title (first letters of each word, capped at 2 chars), with the active module's abbreviation highlighted.
- **Mobile**: sidebar renders inside a slide-out sheet/drawer, skipping the collapse-rail chrome entirely — just the flat list of module sections.
- **Prev/Next navigation**: computed globally across the *entire flattened nav tree* (not per-module) — so "Next" at the end of one module's last page correctly lands on the next module's first page. Render as a two-sided footer bar with left/right chevrons, "Previous"/"Next" micro-labels, and clamped titles.
- **Table of Contents**: sticky, scroll-spy via `IntersectionObserver` (root margin biased so a heading activates before it's fully scrolled past), indented by heading level. Only render the TOC panel if the page actually has headings. TOC extraction must be fence-aware (skip fenced code blocks so comments inside code aren't parsed as headings) and use the same slugger as the heading-ID rehype plugin so anchors match exactly, including duplicate-heading suffixes.

---

## 4. Page Layout

**Root shell**: `Header` (sticky, full-width) → below it, a flex row of `Sidebar` (desktop only, `lg:` breakpoint) + `main` content area (`flex-1 min-w-0 overflow-y-auto`). Mobile gets a hamburger-triggered drawer (`MobileNav`) instead of the persistent sidebar.

**Content page structure** (top to bottom):
1. Dark title banner — module label (small, uppercase, accent color) + page title (large, high-contrast) on a dark background band.
2. A sticky "audience toggle" or similar mode-switch bar directly above the article body, if your content needs an audience/skill-level split (see §7).
3. Article body in a `flex gap-8` row: main content (`flex-1 min-w-0`, wrapped in `.prose`) + optional right-hand TOC sidebar (`hidden lg:block`, fixed width, only rendered when the page has headings).
4. Sticky bottom bar containing Prev/Next navigation, with a small disclaimer/footnote strip beneath it.

**Responsive breakpoints**: use Tailwind's stock breakpoints (`sm`, `md`, `lg`) directly in class names — don't invent custom breakpoints. `lg:` is the cutover point for "desktop chrome" (persistent sidebar + TOC) vs. "mobile chrome" (drawer nav, no TOC).

**No-flash dark mode**: don't pull in a theming library for a single boolean. Instead:
- An inline `<script>` in `<head>` (before hydration) reads a `localStorage` theme key and adds/removes a `.dark` class on `<html>`.
- A `ThemeToggle` component flips the class + persists the choice.
- **Default is always light** — never read or defer to `prefers-color-scheme`. Ship an explicit toggle; don't let the OS silently pick dark mode.

---

## 5. Design Tokens (Cosmetics)

### Token architecture (the key reusable trick)
Declare brand/semantic colors as **plain CSS custom properties in `:root` and `.dark`** (not directly inside `@theme`), then **alias them into Tailwind utilities via `@theme inline`**. This indirection is required in Tailwind v4 so that `.dark` can swap the underlying values at runtime while still getting generated utility classes (`bg-brand-bg`, `text-brand-accent`, etc.). If you skip the alias step, shadcn-style utility classes (`bg-background`, `border-input`, `ring-ring`) get silently dropped by the Tailwind v4 compiler — alias every token you want as a utility.

### Palette shape to replicate
Define light/dark pairs for:
- A primary **accent color** (this project's is a warm yellow, `#FFDA47`) used for the module index numbers, active-state highlights, top border accents, and the `primary`/`ring` shadcn tokens in *both* light and dark mode (i.e. the accent doesn't shift between themes, only its background does).
- A **dark/light text pair** (`sun-dark` / near-white in dark mode) and a **muted text pair** for secondary copy.
- A **background** and **surface** pair (page background vs. card/panel background).
- A **secondary accent** for contrast (this project uses a coral/terracotta) — used sparingly for dividers, WIP badges, or a second audience-mode indicator.
- A **neutral "WIP/disabled" gray** distinct from the muted-text color.

### Glass-morphism tokens (optional but recommended for a premium feel)
Define an **elevation-based token set**, not ad-hoc blur-per-component:
- One bg/border pair per elevation tier: `nav`, `panel`, `card`, `modal`, plus a `scrim` (for modal backdrops) — each with a light and dark value.
- A blur scale: `sm` (~8px), `md` (~16px), `lg` (~28px).
- A matching shadow scale: `shadow-glass-sm/md/lg` plus one "glow" variant (e.g. a soft accent-color glow ring) for emphasis elements.
- Alias all of these through `@theme inline` so they're usable as `bg-glass-nav-bg`, `backdrop-blur-glass-md`, `shadow-glass-sm`, etc.
- Apply consistently: header, sidebar, sticky bottom bar, TOC panel, and any floating panel get the glass treatment; plain content areas (the article body itself) do not — glass is for chrome, not for prose.

### Typography
- One sans font for UI/prose (e.g. Inter) + one monospace font for code (e.g. JetBrains Mono), both loaded via `next/font` with `display: "swap"`, exposed as CSS variables (`--font-sans`, `--font-mono`).
- Use `@tailwindcss/typography`'s `.prose` class for MDX body content rather than hand-styling every element. Override just the handful of `--tw-prose-*` variables needed to match your accent palette (headings, links, inline code background, code-block background, blockquote border) instead of writing custom CSS for every prose element.
- Give `.prose h2` a subtle accent-colored bottom border and `.prose pre` a colored left-border accent — small touches that make MDX content feel branded without custom React components.

### Radius & shape
- Keep a single `--radius` base value for shadcn components; otherwise just use Tailwind's stock `rounded-*` scale (`rounded-md` default, `rounded-lg` for cards/panels, `rounded-full` for pills/badges).

---

## 6. MDX Component Conventions

Keep the MDX component surface **deliberately small**:
- Override only `pre` (the code-block wrapper). Inspect the inner `<code>` element's language class to special-case:
  - `language-mermaid` → render a dedicated `MermaidDiagram` component with the raw fenced text as its value.
  - Any bespoke interactive component you want authors to drop into content → give it its own fake "language" tag (e.g. `` ```my-widget ``) and switch on that in the same `pre` override, rather than inventing MDX shortcode syntax.
  - Everything else falls through to a plain `<pre>` and lets `rehype-highlight` do syntax coloring.
- Don't build custom Callout/Table/Image components unless you actually need interactivity — Tailwind Typography plus a couple of `.prose` CSS overrides covers tables, blockquotes, and images.
- For split-audience content (e.g. "business" vs. "technical" explanations of the same concept), don't build a React component — use a plain `<div class="audience-x" markdown="1">` block in the MDX and toggle visibility purely with CSS (`body[data-audience="x"] .audience-y { display: none }`), flipped by a small client-side toggle component that sets the `data-audience` attribute and persists the choice to `localStorage`. Zero framework overhead, and content authors just wrap prose in a div.

### Mermaid conventions
- **One shared theme config, applied globally** — don't let individual diagrams redefine `themeVariables`. Pick a `theme: "base"` override with a coherent palette (this project uses warm, low-saturation earth tones: sage, slate-blue, sand, lavender, dusty-rose, teal-gray as the `cScale0-7` mindmap branch colors, with a shared muted background/border/text triad for the base canvas).
- **Node styling lives in the content, not the component**: authors add per-node `style NodeId fill:#...,stroke:#...` lines *inside the MDX fence* to distinguish categories within a single diagram, always drawing from the same shared pastel palette rather than inventing new colors per page.
- **Emoji-labeled nodes** for flowcharts/process diagrams: every node label starts with one representative emoji (e.g. 🧠 for reasoning/LLM, 🔧 for tools, 📋 for planning, 🚀 for action, 💾 for memory, 🛡️ for guardrails). Multi-line labels use literal `\n` inside the bracket syntax, not markdown.
- **Shape conventions**: rounded pill nodes `Id(["emoji Label"])` for loop/process stages; plain rectangles `Id["emoji Label"]` for architecture/component boxes; `subgraph NAME["emoji Title"]` for grouping related nodes.
- **Diagram type follows content shape**, not habit:
  - `flowchart LR` — pipelines, sequential processes, decision flows.
  - `flowchart TD` — component-internal architecture, hierarchies.
  - `stateDiagram-v2` — lifecycles / state machines.
  - `sequenceDiagram` — protocol or call flows between actors.
  - `mindmap` — taxonomies / component breakdowns (root branches typically go without emoji, even if child flowcharts on the same page use them).
- **Fallback rendering**: if Mermaid fails to parse or hasn't hydrated yet, show the raw fenced text in a bordered `<pre>` rather than a blank space or error.
- **Skip diagram-ification** for genuinely tabular content (attribute-by-option comparisons) — use a markdown table instead — and for pure Q&A/interview-question content, which is prose-shaped, not diagram-shaped.
- **Anchor a small set of "house style" reference content files** (2-3 files) that new content authors are told to imitate, rather than writing an exhaustive diagram style guide. Pointing at concrete examples is more durable than prose rules.

---

## 7. UX Patterns Worth Reusing

- **Prev/Next footer nav** computed across the flattened, entire nav tree (crossing module boundaries), not scoped per-module.
- **Scroll-spy TOC** using `IntersectionObserver`, fence-aware heading extraction, and a slugger matched exactly to your heading-ID rehype plugin (avoids silent anchor-link breakage from ID-generation mismatches).
- **Audience/skill-level toggle**: a sticky bar above the article body with 2-3 modes (e.g. All / Technical / Non-Technical), persisted client-side, dispatching a custom DOM event other components can listen for, with a brief "Saved" toast on change and a visible colored accent tying the toggle to the currently active mode.
- **Automatic WIP detection** (§2) instead of hand-maintained flags — cheap and self-correcting as content grows.
- **Onboarding/disclaimer modals** mounted once at the root layout (not per-page), shown based on first-visit state.
- Things **intentionally not built** in the reference project that you may or may not need: full-text search, user auth, progress tracking/bookmarks, runnable code sandboxes (CodeSandbox/StackBlitz embeds), automated tests. Don't over-build these speculatively — the reference project ships without them and tracks them as backlog only when there's a concrete need.

---

## 8. Project Tracking Convention (optional, process not code)

If you want the same operating rhythm as the reference project:
- Maintain a single `vibes/status.md` as the source of truth for feature inventory, backlog, and known issues, with a dated Changelog entry appended after every work session.
- Generate a polished `vibes/status.html` companion view only on demand, not automatically.
- For any session-specific checklist (e.g. a redesign rollout plan), check off items in the same session the work was done, and **delete the checklist once fully complete** — capture the outcome as a one-line Changelog entry in `status.md` instead of letting finished checklists linger in the repo.

---

## 9. Adapting This Playbook to a New Project

When bootstrapping a new course project from this playbook:
1. Pick your own accent color pair (replace the yellow/coral here) but keep the *token architecture* (semantic CSS vars aliased via `@theme inline`, light/dark pairs, accent pinned across themes).
2. Keep the three-tier sidebar numbering rule (module numbered, group labels unnumbered, leaves numbered within their group) — it's what makes deep nav trees legible.
3. Keep `nav.yml` (or equivalent) as the sole navigation source of truth, decoupled from the filesystem, so content can be reorganized without breaking numbering.
4. Reuse the Mermaid "shared base theme + per-node overrides in content" pattern rather than hardcoding diagram colors per page.
5. Only add glass-morphism, audience toggles, or other flourishes from this playbook if they genuinely fit the new project's content — they're patterns to draw from, not a mandatory checklist.
