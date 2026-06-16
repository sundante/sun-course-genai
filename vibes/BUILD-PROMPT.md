# Build Prompt: Learn GenAI - Next.js Course Site from Scratch

Use this prompt verbatim when starting a fresh rebuild in a new Claude Code session.

---

## THE PROMPT

---

You are building a Next.js 16 static course website from scratch. The project already exists at the current working directory with all course content and configuration files in place. Your job is to write all the application code in `src/` from zero.

## What already exists - do not touch these

- `content/` - all course markdown files
- `content/nav.yml` - navigation structure (MkDocs format)
- `next.config.ts` - already configured for static export
- `package.json` and `package-lock.json` - all dependencies installed
- `tsconfig.json`, `postcss.config.mjs`, `components.json`
- `.github/workflows/` - CI/CD deploy pipeline
- `project-docs/` - design specification files you must read before writing any code
- `CLAUDE.md`, `AGENTS.md`

## Step 0 - Read the design specs first

Before writing a single line of code, read these three files in full:

1. `project-docs/DESIGN-SYSTEM.md` - color tokens, typography, CSS patterns, audience toggle CSS
2. `project-docs/UI-COMPONENTS.md` - exact markup for every component
3. `project-docs/PAGE-LAYOUTS.md` - page layout structure, data flow, TypeScript types

Also read `content/nav.yml` to understand the navigation structure.

## What to build

A Next.js 16 App Router site with:

- Homepage with hero, module grid, stats strip, learning paths, footer
- Course content pages that render markdown files as styled web pages
- Collapsible sidebar navigation driven by nav.yml
- Sticky header with social links
- Mobile navigation drawer
- Audience toggle (Technical / Non-Technical / All view modes)
- Table of contents with active heading tracking
- Prev/next page navigation
- 404 page

## Architecture decisions

### URL structure

```
/                                  homepage
/learn/[module]/[slug]             course page
/quiz/all                          placeholder (UnderDevelopment component)
/quiz/[module]                     placeholder (UnderDevelopment component)
```

With `basePath: "/learngenai"` in next.config.ts all routes are served under `/learngenai/`.

### Slug generation - CRITICAL

The slug for a page URL is derived from its file path in `content/nav.yml`, NOT just the filename. You must include the subdirectory in the slug to avoid collisions.

Rule: take the file path relative to the module's root directory, strip the `.md` extension, split by `/`, kebab-case each segment, join with `-`.

Examples:
```
nav.yml filePath               module       slug
------------------------------ ------------ ---------------------------------
01-LLM-Models/INDEX.md         llm-models   index
01-LLM-Models/Notes/01-LLM-Fundamentals.md  llm-models  01-llm-fundamentals
05-Agents/INDEX.md             agents       index
05-Agents/GCP-ADK/INDEX.md    agents       gcp-adk-index
05-Agents/GCP-ADK/02-Simple-Agent.md  agents  gcp-adk-02-simple-agent
05-Agents/LangChain/02-Simple-Agent.md agents  langchain-02-simple-agent
```

The module directory prefix (e.g. `05-Agents/`) must be stripped before computing the slug. Each module's root directory is the first path segment in the filePaths listed under that module in nav.yml (e.g. `05-Agents`, `01-LLM-Models`, `03-RAGs`, etc.).

### Markdown cross-link rewriting - CRITICAL

The markdown content files contain relative links to other `.md` files (left over from a MkDocs/GitHub Pages migration). These look like:

```markdown
[RAG](../../03-RAGs/INDEX.md)
[Architectural Patterns](../Notes/06-Architectural-Patterns.md)
```

These will 404 in the browser. You must write a **remark plugin** that runs at build time and rewrites these links to proper `/learn/module/slug` URLs.

The plugin receives the current file's path (e.g. `06-Agentic-AI/CodeLabs/02-Architectures.md`) and the full flat page list. For each markdown link whose `url` ends in `.md`:
1. Resolve the url relative to the current file's directory using Node.js `path.resolve`
2. Normalize to a path relative to the `content/` directory
3. Look up that normalized path in the flat pages list by `filePath`
4. If found, rewrite the link's `url` to `matchingPage.href`
5. If not found, leave the link unchanged (it may be a PDF or external resource)

### nav.yml parsing

The nav.yml uses MkDocs format. Parse it with `js-yaml`. The structure is:

```yaml
nav:
  - Home: index.md
  - LLM Models:
    - Overview: 01-LLM-Models/INDEX.md
    - Concepts:
      - LLM Fundamentals: 01-LLM-Models/Notes/01-LLM-Fundamentals.md
    ...
```

- Skip the `Home` entry (it maps to the homepage, not a course page)
- For each top-level section (LLM Models, RAG, etc.) look up its slug in a hardcoded `MODULE_SLUG_MAP`
- Recursively parse children: if value is a string it's a leaf page (filePath), if value is an array it's a section with children
- Build two outputs: `modules[]` (tree structure for sidebar) and `flatPages[]` (linear order for prev/next)

MODULE_SLUG_MAP:
```ts
const MODULE_SLUG_MAP: Record<string, string> = {
  "LLM Models":        "llm-models",
  "Prompt Engineering":"prompt-engineering",
  "RAG":               "rag",
  "MCP":               "mcp",
  "Agents":            "agents",
  "Agentic AI":        "agentic-ai",
  "Knowledge Check":   "knowledge-check",
};
```

## Build order

Build in this exact sequence - each step depends on the previous:

### 1. `src/types/content.ts`

Define these interfaces (exact spec in PAGE-LAYOUTS.md):
- `NavItem`, `NavModule`, `NavigationTree`
- `PageRef`, `PageContent`, `TocItem`
- `QuizCard` (for future use)

### 2. `src/lib/utils.ts`

```ts
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
export function cn(...inputs: ClassValue[]) { return twMerge(clsx(inputs)); }
```

### 3. `src/lib/content/nav.ts`

Functions:
- `filePathToSlug(filePath: string, moduleRootDir: string): string` - implements the slug rule above
- `getNavigationTree(): NavigationTree` - parses nav.yml, cached
- `getPageRef(moduleSlug: string, slug: string): PageRef | undefined`
- `getPrevNext(href: string): { prev?: PageRef; next?: PageRef }`

Also export `MODULE_DIR_MAP` (maps module slug back to its root dir, needed by the remark plugin):
```ts
// e.g. "agents" → "05-Agents", "llm-models" → "01-LLM-Models"
// Derive this by inspecting the first filePath in each module's pages
```

### 4. `src/lib/content/loader.ts`

Functions:
- `extractToc(markdown: string): TocItem[]` - parses h1-h3 headings, generates id via kebab-case
- `getPage(moduleSlug: string, slug: string): PageContent | null`
- `getAllPages(): PageRef[]`
- `getPageWithNavigation(moduleSlug: string, slug: string)`

### 5. `src/lib/content/remarkRewriteMdLinks.ts`

A remark plugin factory:

```ts
import type { Plugin } from "unified";
import type { Root } from "mdast";
import { visit } from "unist-util-visit";
import path from "path";
import type { PageRef } from "@/types/content";

export function remarkRewriteMdLinks(
  currentFilePath: string,  // e.g. "06-Agentic-AI/CodeLabs/02-Architectures.md"
  flatPages: PageRef[]
): Plugin<[], Root> {
  return () => (tree) => {
    visit(tree, "link", (node) => {
      if (!node.url.endsWith(".md")) return;
      // resolve relative url against current file
      const dir = path.dirname(currentFilePath);
      const resolved = path.normalize(path.join(dir, node.url));
      // find matching page
      const match = flatPages.find(p => p.filePath === resolved.replace(/\\/g, "/"));
      if (match) node.url = match.href;
    });
  };
}
```

Note: `unist-util-visit` is already available via the rehype/remark plugin chain in the installed packages. Check `node_modules/` to confirm.

### 6. `src/app/globals.css`

Copy this exactly - it has the Tailwind imports, theme tokens, prose overrides, and audience toggle CSS. All values are in `project-docs/DESIGN-SYSTEM.md`.

Required sections:
- `@import "tailwindcss"`, `@import "tw-animate-css"`, `@import "shadcn/tailwind.css"`
- `@custom-variant dark`
- `@plugin "@tailwindcss/typography"`
- `@theme inline` block with all `--color-sun-*` variables
- Body, selection, prose overrides
- `:root` CSS custom properties (shadcn tokens)
- `body[data-audience="tech"] .audience-biz { display: none; }` etc.

### 7. `src/components/ui/` - copy all existing shadcn components

These are correct and do not need to be rebuilt: `button.tsx`, `sheet.tsx`, `card.tsx`, `badge.tsx`, `progress.tsx`, `separator.tsx`.

If rebuilding from scratch without existing files, install them via shadcn CLI or copy from a fresh install.

### 8. `src/components/course/` - rebuild all 7 components

Implement each one exactly as specified in `project-docs/UI-COMPONENTS.md`:
1. `AudienceToggle.tsx`
2. `TableOfContents.tsx`
3. `PageNav.tsx`
4. `UnderDevelopment.tsx`
5. `Sidebar.tsx` (most complex - read the spec carefully)
6. `MobileNav.tsx`
7. `Header.tsx`

### 9. App pages

In this order:
1. `src/app/layout.tsx` - root layout with fonts
2. `src/app/not-found.tsx` - uses UnderDevelopment
3. `src/app/page.tsx` - homepage
4. `src/app/(course)/layout.tsx` - course layout wrapper
5. `src/app/(course)/learn/[module]/[slug]/page.tsx` - course content page (pass `currentFilePath` to remark plugin)
6. `src/app/(course)/quiz/all/page.tsx` - UnderDevelopment stub
7. `src/app/(course)/quiz/[module]/page.tsx` - UnderDevelopment stub

### 10. Copy static assets

- `src/app/favicon.ico` - copy from existing or use any ico file

## Verification after building

Run these checks before declaring done:

```bash
npm run build
```

Must complete with 0 errors and generate an `/out/` directory.

Then check:

1. `out/learn/agents/` - must contain ~16 distinct HTML files (not just 4), confirming slug collisions are resolved
2. `out/learn/llm-models/index/index.html` - must exist
3. `out/learn/agents/gcp-adk-02-simple-agent/index.html` - must exist
4. `out/learn/agents/langchain-02-simple-agent/index.html` - must exist (different from gcp-adk version)

Then run dev server and manually verify:

```bash
npm run dev
```

Navigate to `http://localhost:3000/learngenai/`:
- [ ] Homepage loads with module cards
- [ ] "Start Learning" navigates to LLM Models overview
- [ ] Sidebar shows all modules, expands/collapses, highlights active page
- [ ] Mobile: sidebar is hidden, "Menu" button opens drawer
- [ ] AudienceToggle switches modes, persists on page reload
- [ ] Cross-links inside content pages navigate to correct pages (not 404)
- [ ] Prev/next footer navigation works across all modules
- [ ] Table of contents tracks active heading while scrolling
- [ ] 404 page shows UnderDevelopment component

## Common pitfalls

- Do not use `path.basename()` alone for slugs - it causes collisions (see Slug Generation section)
- The `_cache` in nav.ts must be module-level, not inside the function, to survive between calls in dev mode
- `getNavigationTree()` is called in both server components and build functions - it must work without `window` or browser APIs
- Pass `currentFilePath` from the page component down into the MDX options so the remark plugin can resolve relative links
- The `format: "md"` option in MDXRemote options is required - content files are plain markdown, not `.mdx`
- `AudienceToggle` must be `"use client"` and check `typeof document === "undefined"` before touching the DOM
- `Sidebar` must be `"use client"` for `usePathname()` and `useState()`
- The course layout's `<main>` needs `overflow-y-auto` with `flex-1 min-w-0` - without `min-w-0` content can overflow flex container
- `unist-util-visit` may need to be imported differently depending on ESM/CJS - check what version is installed

---

End of prompt.
