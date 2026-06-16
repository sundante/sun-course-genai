@AGENTS.md

# Project Conventions

## File Naming — Content Files

All content files under `src/content/` use zero-padded numeric prefixes (`01-`, `02-`, etc.).

- When files are deleted, **renumber the remaining files** so there are no gaps (e.g. if `01` and `02` are deleted, rename `03→01`, `04→02`, etc.)
- Keep `nav.yml` in sync with any file renames — it is the single source of truth for navigation

## Sidebar Numbering

- **Module-level** headings (e.g. "01. LLM Models") — rendered in `Sidebar.tsx > ModuleSection`, index passed from `.map((mod, i) => ...)`
- **Sub-concept leaf items** (e.g. "01 What Are AI Agents") — rendered in `Sidebar.tsx > NavLeaf`, index passed from `.map((child, i) => ...)` inside `NavSection`
- Section group labels (Concepts, Code Labs, etc.) are **not** numbered — they are structural groupings only
