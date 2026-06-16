# Learn GenAI — Project Status

**URL:** https://learngenai.sunmintz.com  
**Stack:** Next.js 16 · TypeScript · Tailwind CSS · MDX · shadcn/ui  
**Deploy:** Static export (`out/`) → learngenai.sunmintz.com subdomain

---

## Deployment — Hostinger (Manual FTP)

**Target:** `learngenai.sunmintz.com`  
**Method:** Static export → FTP upload → no Node.js server needed

### One-time Hostinger setup

1. hPanel → **Domains → Subdomains** → create `learngenai.yourdomain.com`
2. Note the folder path it creates (e.g. `/public_html/learngenai/`)
3. hPanel → **Files → FTP Accounts** → note host, username, password, port 21

### GitHub Actions deploy (manual trigger)

Workflow: `.github/workflows/deploy.yml` — triggered manually via **Actions → Deploy to Hostinger → Run workflow**.

Required GitHub repository secrets (Settings → Secrets → Actions):

| Secret | Value |
| --- | --- |
| `FTP_HOST` | FTP hostname from hPanel (e.g. `ftp.yourdomain.com`) |
| `FTP_USERNAME` | FTP account username |
| `FTP_PASSWORD` | FTP account password |
| `FTP_SERVER_DIR` | Remote path (e.g. `/public_html/learngenai/`) |

### Local deployment (fallback)

```bash
npm run build
# Then FTP the CONTENTS of /out/ (not the folder itself) to /public_html/learngenai/
# Use FileZilla or any FTP client
```

The remote root must look like:

```text
/public_html/learngenai/
  index.html        ← homepage
  _next/            ← JS/CSS chunks
  404.html
  learn/
  quiz/
  favicon.ico
```

### Why it works

- `output: "export"` → pure static HTML/CSS/JS, no server needed
- `trailingSlash: true` → each route is `route/index.html`, Apache serves it correctly
- `images: { unoptimized: true }` → no Node image server required

---

## What's Built

### Core App
- [x] Next.js App Router scaffolded with TypeScript + Tailwind
- [x] Static export configured (`output: "export"`)
- [x] Inter + JetBrains Mono fonts via next/font/google
- [x] Design system — sun-yellow color tokens, prose overrides, audience toggle CSS

### Navigation & Content Pipeline
- [x] `src/content/nav.yml` drives all navigation (MkDocs-style)
- [x] `src/lib/content/nav.ts` — parses nav.yml, generates slugs, prev/next
- [x] `src/lib/content/loader.ts` — reads `.mdx` files, extracts TOC
- [x] `src/lib/content/remarkRewriteMdLinks.ts` — rewrites cross-links at build time
- [x] Slug collision prevention — subdirectory paths included in slugs

### Pages
- [x] Homepage — hero, module grid, stats strip, learning paths, footer
- [x] Course content pages — `/learn/[module]/[slug]`
- [x] 404 page
- [x] Quiz pages — `/quiz/all`, `/quiz/[module]` (stubs, under development)

### UI Components
- [x] `Header` — sticky, social links, GitHub star button
- [x] `Sidebar` — collapsible rail, expandable modules, active link tracking
- [x] `MobileNav` — sheet drawer for mobile
- [x] `AudienceToggle` — All / Technical / Non-Technical modes, persists to localStorage
- [x] `TableOfContents` — sticky, IntersectionObserver active heading tracking
- [x] `PageNav` — prev/next navigation footer
- [x] `UnderDevelopment` — animated placeholder for WIP pages

### Course Content (105 files → 103 HTML pages)
- [x] 01 — LLM Models (12 notes + Q&A)
- [x] 02 — Prompt Engineering (6 notes + Q&A)
- [x] 03 — RAG (12 notes + system designs + Q&A)
- [x] 04 — MCP (9 notes + Q&A)
- [x] 05 — Agents (LangChain, LangGraph, CrewAI, GCP ADK)
- [x] 06 — Agentic AI (12 notes + system designs + code labs + Q&A)
- [x] Knowledge Check — all interview questions

---

## What's Next

### Near-term
- [ ] Deploy to learngenai.sunmintz.com (set up CI/CD, DNS)
- [ ] Quiz feature — interactive Q&A with score tracking
- [ ] Search — full-text search across all content
- [ ] Progress tracking — mark lessons complete (localStorage first)

### Content
- [ ] Add more system design case studies
- [ ] Code lab pages — embed runnable code (CodeSandbox / StackBlitz)
- [ ] Video embeds for visual concepts

### Future (when site matures)
- [ ] User auth + accounts (Clerk or Auth.js)
- [ ] Bookmarks — save and resume lessons
- [ ] Persistent progress sync across devices
- [ ] Interactive MDX components — `<QuizWidget />`, `<CodePlayground />`
- [ ] Comment/discussion threads per lesson

---

## Project Structure

```
src/
  app/
    layout.tsx                        root layout
    page.tsx                          homepage
    not-found.tsx                     404
    (course)/
      layout.tsx                      header + sidebar shell
      learn/[module]/[slug]/page.tsx  course content pages
      quiz/all/page.tsx               quiz stub
      quiz/[module]/page.tsx          quiz stub
  components/
    ui/                               shadcn (button, sheet, card, badge, progress, separator)
    course/                           Header, Sidebar, MobileNav, AudienceToggle,
                                      TableOfContents, PageNav, UnderDevelopment
  lib/
    utils.ts                          cn() helper
    content/
      nav.ts                          navigation tree from nav.yml
      loader.ts                       reads .mdx files, extracts TOC
      remarkRewriteMdLinks.ts         build-time cross-link rewriting
  types/
    content.ts                        NavItem, NavModule, NavigationTree, PageRef, PageContent, TocItem
  content/                            105 .mdx source files (compiled to HTML at build time)
    nav.yml
    01-LLM-Models/
    02-Prompts/
    03-RAGs/
    04-MCP/
    05-Agents/
    06-Agentic-AI/
    Interview-Questions/
    All_Questions.mdx

vibes/                                design specs & rebuild reference
  DESIGN-SYSTEM.md
  UI-COMPONENTS.md
  PAGE-LAYOUTS.md
  BUILD-PROMPT.md
```
