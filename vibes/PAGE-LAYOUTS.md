# Page Layouts

Exact layout structure for every page type in the app. When rebuilding, follow these precisely.

---

## Root Layout (`src/app/layout.tsx`)

Wraps everything. Loads fonts, sets metadata.

```tsx
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans", display: "swap" });
const jetbrainsMono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono", display: "swap" });

export const metadata: Metadata = {
  metadataBase: new URL("https://learngenai.sunmintz.com"),
  title: "Learn GenAI",
  description: "...",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable}`}>
      <body>{children}</body>
    </html>
  );
}
```

---

## Course Layout (`src/app/(course)/layout.tsx`)

Wraps all pages under `(course)/` - the learn pages and quiz pages.

```
┌─────────────────────────────────────────────────────────┐
│  HEADER (sticky, h-13, z-40, white, 2px yellow border)  │
├─────────────────────────────────────────────────────────┤
│  MOBILE NAV BAR (lg:hidden, white bar with Menu button) │
├──────────────┬──────────────────────────────────────────┤
│              │                                           │
│   SIDEBAR    │           MAIN (children)                 │
│  (lg:block)  │      (flex-1, overflow-y-auto)           │
│   w-64/w-12  │                                           │
│   sticky     │                                           │
│   h-[calc    │                                           │
│   100vh-3.5  │                                           │
│   rem]       │                                           │
└──────────────┴──────────────────────────────────────────┘
```

```tsx
export default function CourseLayout({ children }) {
  const nav = getNavigationTree();
  return (
    <div className="min-h-screen bg-sun-bg overflow-x-hidden">
      <Header />
      <MobileNav nav={nav} />
      <div className="flex h-[calc(100vh-3.5rem)] overflow-hidden">
        <Sidebar nav={nav} />
        <main className="flex-1 min-w-0 overflow-y-auto flex flex-col">
          {children}
        </main>
      </div>
    </div>
  );
}
```

Key details:
- `overflow-hidden` on the flex row clips the sidebar and main independently
- `overflow-y-auto` on `<main>` makes only the content scroll, not the page
- `h-[calc(100vh-3.5rem)]` = viewport height minus header height (h-13 = 3.25rem, but 3.5rem is used to account for the mobile nav bar too)
- `min-w-0` on main prevents flex overflow

---

## Course Content Page (`src/app/(course)/learn/[module]/[slug]/page.tsx`)

```
┌─────────────────────────────────────────────────────────────────┐
│  DARK TITLE BANNER (bg-sun-dark, 2px yellow border-b)           │
│  Module label (xs, yellow, uppercase, tracking-widest)          │
│  Page h1 (base, bold, white)                                    │
├──────────────────────────────────────┬──────────────────────────┤
│  CONTENT AREA (flex-1, px-6 lg:px-8, py-6)                     │
│                                      │                           │
│  AUDIENCE TOGGLE (sticky top, full   │  TABLE OF CONTENTS       │
│  width, above article)               │  (hidden lg:block w-64)  │
│                                      │  sticky top-20           │
│  <article>                           │                           │
│    <div class="prose prose-base      │                           │
│     max-w-none">                     │                           │
│      <MDXRemote ... />               │                           │
│    </div>                            │                           │
│  </article>                          │                           │
│                                      │                           │
├──────────────────────────────────────┴──────────────────────────┤
│  PREV/NEXT FOOTER (sticky bottom, bg-sun-bg, 2px yellow border) │
│  [← Previous Title]               [Next Title →]                │
└─────────────────────────────────────────────────────────────────┘
```

```tsx
return (
  <div className="flex flex-col min-h-full">

    {/* Dark title banner */}
    <div className="bg-sun-dark border-b-2 border-sun-yellow px-6 lg:px-8 py-3">
      <p className="text-xs font-bold uppercase tracking-widest text-sun-yellow mb-0.5">
        {moduleLabel}   {/* e.g. "Llm Models" → prettified */}
      </p>
      <h1 className="text-base font-bold text-white tracking-tight leading-tight">
        {page.title}
      </h1>
    </div>

    {/* Content row */}
    <div className="flex gap-8 flex-1 px-6 lg:px-8 py-6">
      <div className="flex-1 min-w-0">
        <AudienceToggle />
        <article>
          <div className="prose prose-base max-w-none">
            <MDXRemote source={page.rawContent} options={mdxOptions} />
          </div>
        </article>
      </div>
      {page.toc.length > 0 && (
        <aside className="hidden lg:block w-64 shrink-0">
          <TableOfContents toc={page.toc} />
        </aside>
      )}
    </div>

    {/* Sticky prev/next footer */}
    <div className="sticky bottom-0 z-10 bg-sun-bg border-t-2 border-sun-yellow px-6 lg:px-8 py-3">
      <PageNav prev={prev} next={next} className="flex justify-between" />
    </div>

  </div>
);
```

### MDX options

```ts
const mdxOptions = {
  parseFrontmatter: false,
  mdxOptions: {
    format: "md" as const,
    remarkPlugins: [remarkGfm],
    rehypePlugins: [
      rehypeSlug,
      [rehypeAutolinkHeadings, { behavior: "wrap" }],
      rehypeHighlight,
    ],
  },
};
```

Used via `next-mdx-remote/rsc`:
```tsx
import { MDXRemote } from "next-mdx-remote/rsc";
```

### Module label formatting

```ts
const moduleLabel = module
  .split("-")
  .map(w => w.charAt(0).toUpperCase() + w.slice(1))
  .join(" ");
// "llm-models" → "Llm Models"
```

### Static params

```ts
export async function generateStaticParams() {
  const pages = getAllPages();
  return pages.map(p => ({ module: p.module, slug: p.slug }));
}
```

---

## Homepage (`src/app/page.tsx`)

**Type:** Server component. Loads `getNavigationTree()` for the module grid.

```
┌─────────────────────────────────────────────────────────┐
│  HEADER (white, h-13, yellow border - inline, not       │
│  shared with course layout - homepage has its own)      │
├─────────────────────────────────────────────────────────┤
│  HERO (bg-sun-dark, yellow border-b-2)                  │
│  - Breadcrumb label (xs yellow uppercase)               │
│  - H1: "Master the Full Modern GenAI Stack"             │
│    "GenAI Stack" in text-sun-yellow                     │
│  - Subtitle (white/70)                                  │
│  - Stack pills: LLMs → Prompts → RAG → MCP → Agents    │
│  - CTAs: "Start Learning" (yellow) + "Practice Quiz"    │
│    (ghost white border)                                  │
├─────────────────────────────────────────────────────────┤
│  MODULE GRID (bg-sun-bg)                                │
│  - Section label: "Curriculum"                          │
│  - 3-col grid (1 mobile, 2 sm, 3 lg)                   │
│  - Each card: number, subtitle badge, title, desc, tags │
├─────────────────────────────────────────────────────────┤
│  STATS STRIP (bg-sun-yellow)                            │
│  - 4 stats: 150+ notes, 4 frameworks, 298+ Q&A, Free   │
├─────────────────────────────────────────────────────────┤
│  LEARNING PATHS (bg-sun-bg, yellow border-t)            │
│  - Section label: "Learning Paths"                      │
│  - 4-col grid (2 mobile, 4 lg): A B C D paths          │
├─────────────────────────────────────────────────────────┤
│  FOOTER (bg-sun-dark, yellow border-t-2)                │
│  - "© 2026 sunmintz.com. Built by Suryaprakash Singh." │
│  - Links: GitHub | LinkedIn | X / Twitter               │
└─────────────────────────────────────────────────────────┘
```

### Homepage header

The homepage has its own inline `<header>` (not the shared `Header` component which is for the course layout). It is simpler:

```tsx
<header className="bg-white border-b-2 border-sun-yellow px-4 sm:px-6 h-13 flex items-center justify-between gap-3 sticky top-0 z-40">
  <span className="font-bold text-sun-dark tracking-tight text-sm">Learn GenAI</span>
  <div className="flex items-center gap-2">
    <a href="https://github.com/sundante/sun-course-genai" target="_blank" rel="noopener noreferrer"
       className="hidden sm:inline-flex items-center gap-1.5 text-xs font-semibold bg-sun-yellow text-sun-dark hover:bg-sun-yellow-dk rounded-md px-2.5 py-1 transition-colors">
      <StarSvg /> Github
    </a>
    <a href="https://sunmintz.com/" target="_blank" rel="noopener noreferrer"
       className="inline-flex items-center text-xs font-semibold bg-sun-yellow text-sun-dark hover:bg-sun-yellow-dk rounded-md px-3 py-1.5 transition-colors">
      sunmintz.com
    </a>
  </div>
</header>
```

Note: no social icons, no quiz link - homepage header is minimal.

### Hero section

```tsx
<section className="bg-sun-dark text-white px-4 sm:px-6 py-10 border-b-2 border-sun-yellow">
  <div className="max-w-3xl mx-auto text-center">
    <p className="text-xs font-bold uppercase tracking-widest text-sun-yellow mb-3">
      Learn AI: Generative AI to Agentic AI
    </p>
    <h1 className="text-3xl sm:text-4xl font-bold mb-3 tracking-tight leading-tight">
      Master the Full Modern{" "}
      <span className="text-sun-yellow">GenAI Stack</span>
    </h1>
    <p className="text-white/70 text-sm sm:text-base mb-6 leading-relaxed max-w-xl mx-auto">
      A structured, practical curriculum from foundational LLMs to fully autonomous Agentic systems.
    </p>

    {/* Stack pills with arrows between */}
    <div className="flex flex-wrap justify-center gap-2 mb-7">
      {["LLMs","Prompts","RAG","MCP","Agents","Agentic AI"].map((pill, i, arr) => (
        <span key={pill} className="flex items-center gap-1.5 text-xs font-medium text-white/80">
          <span className="bg-white/10 border border-white/20 rounded px-2 py-0.5">{pill}</span>
          {i < arr.length - 1 && <span className="text-sun-yellow text-xs">→</span>}
        </span>
      ))}
    </div>

    <div className="flex gap-3 justify-center flex-wrap">
      <Link href="/learn/llm-models/index"
            className="inline-flex items-center text-sm font-semibold bg-sun-yellow text-sun-dark hover:bg-sun-yellow-dk rounded-lg px-5 py-2 transition-colors">
        Start Learning
      </Link>
      <Link href="/quiz/all"
            className="inline-flex items-center text-sm font-semibold text-white border border-white/25 hover:border-white/60 hover:bg-white/10 rounded-lg px-5 py-2 transition-colors">
        Practice Quiz
      </Link>
    </div>
  </div>
</section>
```

### Module grid card

```tsx
<Link
  href={href}  {/* /learn/{mod.slug}/{firstPageSlug} */}
  className="group block p-4 rounded-xl border border-sun-yellow-bdr bg-white hover:border-sun-yellow hover:shadow-md hover:-translate-y-0.5 transition-all duration-150"
>
  <div className="flex items-start justify-between mb-2">
    <span className="text-xs font-mono text-sun-muted">{meta.num}</span>   {/* "01", "02", ... */}
    <span className="text-xs font-semibold text-sun-amber bg-sun-yellow-dim px-2 py-0.5 rounded-full">
      {meta.subtitle}   {/* "The Engine", "The Interface", ... */}
    </span>
  </div>
  <h3 className="font-semibold text-sun-dark mb-1.5 group-hover:text-sun-amber transition-colors">
    {mod.title}
  </h3>
  <p className="text-xs text-sun-muted leading-relaxed mb-3">{meta.description}</p>
  <div className="flex gap-2">
    <span className="text-xs bg-gray-100 text-sun-muted rounded px-2 py-0.5">{meta.notes}</span>
    <span className="text-xs bg-gray-100 text-sun-muted rounded px-2 py-0.5">{meta.qa}</span>
  </div>
</Link>
```

Module metadata (hardcoded constants, not from nav.yml):

```ts
const MODULE_META = {
  "llm-models":         { num: "01", subtitle: "The Engine",    description: "...", notes: "12 notes", qa: "68+ Q&A" },
  "prompt-engineering": { num: "02", subtitle: "The Interface", description: "...", notes: "6 notes",  qa: "65+ Q&A" },
  "rag":                { num: "03", subtitle: "The Memory",    description: "...", notes: "12 notes", qa: "80+ Q&A" },
  "mcp":                { num: "04", subtitle: "The Protocol",  description: "...", notes: "9 notes",  qa: "40+ Q&A" },
  "agents":             { num: "05", subtitle: "The Actors",    description: "...", notes: "8 notes",  qa: "50+ Q&A" },
  "agentic-ai":         { num: "06", subtitle: "The Systems",   description: "...", notes: "12 notes", qa: "60+ Q&A" },
};
```

Get full description strings from `src/app/page.tsx` in the existing codebase.

### Stats strip

```tsx
<section className="bg-sun-yellow px-4 sm:px-6 py-5">
  <div className="max-w-5xl mx-auto flex flex-wrap justify-center sm:justify-between gap-4">
    {[["150+","Deep-dive notes"],["4","Agent frameworks"],["298+","Interview Q&A"],["Free","Always"]].map(([stat, label]) => (
      <div key={label} className="text-center">
        <div className="text-xl font-bold text-sun-dark">{stat}</div>
        <div className="text-xs font-medium text-sun-dark/70">{label}</div>
      </div>
    ))}
  </div>
</section>
```

### Learning paths

```tsx
<section className="px-4 sm:px-6 py-8 bg-sun-bg border-t border-sun-yellow-bdr">
  <div className="max-w-5xl mx-auto">
    <h2 className="text-xs font-bold uppercase tracking-widest text-sun-muted mb-4">Learning Paths</h2>
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      {LEARNING_PATHS.map(path => (
        <div key={path.label} className="p-4 rounded-xl border border-sun-yellow-bdr bg-white">
          <div className="w-7 h-7 rounded-full bg-sun-yellow text-sun-dark text-xs font-bold flex items-center justify-center mb-2">
            {path.label}
          </div>
          <div className="font-semibold text-sun-dark text-sm mb-1">{path.title}</div>
          <div className="text-xs text-sun-muted leading-relaxed">{path.desc}</div>
        </div>
      ))}
    </div>
  </div>
</section>
```

```ts
const LEARNING_PATHS = [
  { label: "A", title: "Conceptual",     desc: "New to GenAI - start here for a guided overview" },
  { label: "B", title: "Interview Prep", desc: "Accelerated deep-dive through Q&A banks" },
  { label: "C", title: "Hands-On",       desc: "Code labs across 4 frameworks" },
  { label: "D", title: "Full Sequence",  desc: "Complete curriculum from LLMs to Agentic AI" },
];
```

### Footer

```tsx
<footer className="bg-sun-dark text-white/60 px-4 sm:px-6 py-6 mt-auto border-t-2 border-sun-yellow">
  <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
    <span>
      © 2026{" "}
      <a href="https://sunmintz.com/" className="text-sun-yellow hover:text-white transition-colors">
        sunmintz.com
      </a>. Built by Suryaprakash Singh.
    </span>
    <div className="flex items-center gap-4">
      <a href="https://github.com/sundante/sun-course-genai" target="_blank" rel="noopener noreferrer"
         className="hover:text-white transition-colors">GitHub</a>
      <a href="https://www.linkedin.com/in/suryaprakash-s-singh/" target="_blank" rel="noopener noreferrer"
         className="hover:text-white transition-colors">LinkedIn</a>
      <a href="https://x.com/sunsindante" target="_blank" rel="noopener noreferrer"
         className="hover:text-white transition-colors">X / Twitter</a>
    </div>
  </div>
</footer>
```

---

## 404 Page (`src/app/not-found.tsx`)

```tsx
import { UnderDevelopment } from "@/components/course/UnderDevelopment";

export default function NotFound() {
  return <UnderDevelopment title="Page Not Found" description="This page doesn't exist or has moved." />;
}
```

---

## Content Architecture

### URL structure

```
/                                     → homepage (src/app/page.tsx)
/learn/[module]/[slug]               → course page (src/app/(course)/learn/[module]/[slug]/page.tsx)
/quiz/all                            → quiz overview (stub)
/quiz/[module]                       → module quiz (stub)
```

With `basePath: "/learngenai"` in next.config.ts, all routes are prefixed:
```
https://yourdomain.com/learngenai/
https://yourdomain.com/learngenai/learn/llm-models/index/
```

### Data flow

```
content/nav.yml
    ↓ parsed by
src/lib/content/nav.ts (getNavigationTree)
    ↓ returns NavigationTree { modules[], flatPages[] }
    ↓
src/lib/content/loader.ts (getPage, getPageWithNavigation)
    ↓ reads markdown files from content/
    ↓ returns PageContent { rawContent, toc, prev, next }
    ↓
src/app/(course)/learn/[module]/[slug]/page.tsx
    ↓ renders with MDXRemote
    ↓
Browser
```

### Types (`src/types/content.ts`)

```ts
interface NavItem {
  title: string;
  href: string;
  filePath?: string;
  children?: NavItem[];
}

interface NavModule {
  title: string;
  slug: string;
  items: NavItem[];
}

interface NavigationTree {
  modules: NavModule[];
  flatPages: PageRef[];
}

interface PageRef {
  title: string;
  href: string;
  filePath: string;
  module: string;
  slug: string;
}

interface PageContent extends PageRef {
  rawContent: string;
  toc: TocItem[];
}

interface TocItem {
  id: string;
  text: string;
  level: number;  // 1, 2, or 3
}
```
