# Design System

This document is the authoritative reference for colors, typography, spacing, and CSS patterns used across the Learn GenAI app. Replicate these exactly when rebuilding.

---

## Color Palette

All colors are defined as Tailwind inline theme variables in `src/app/globals.css` under `@theme inline`. Use the utility names below throughout the app - never hardcode hex values.

| Utility class | Variable | Value |
|---|---|---|
| `bg-sun-yellow` / `text-sun-yellow` | `--color-sun-yellow` | `#FFDA47` |
| `bg-sun-yellow-dk` | `--color-sun-yellow-dk` | `#E8C200` |
| `bg-sun-yellow-dim` | `--color-sun-yellow-dim` | `rgba(255, 218, 71, 0.14)` |
| `border-sun-yellow-bdr` | `--color-sun-yellow-bdr` | `rgba(255, 218, 71, 0.38)` |
| `bg-sun-dark` / `text-sun-dark` | `--color-sun-dark` | `#111111` |
| `text-sun-muted` | `--color-sun-muted` | `#666666` |
| `text-sun-amber` / `bg-sun-yellow-dim` (accent) | `--color-sun-amber` | `#7a6000` |
| `bg-sun-bg` | `--color-sun-bg` | `#fafaf9` |
| `bg-sun-surface` | `--color-sun-surface` | `#ffffff` |

### How yellow variants are used

- `sun-yellow` - primary action backgrounds (buttons, active states, badges)
- `sun-yellow-dk` - hover state of yellow buttons
- `sun-yellow-dim` - hover backgrounds, active link backgrounds (very subtle)
- `sun-yellow-bdr` - borders, dividers (semi-transparent yellow)
- `sun-amber` - text on yellow-dim backgrounds (readable amber)
- `sun-muted` - secondary/inactive text
- `sun-dark` - headings, primary text, logo

---

## Typography

### Font loading (`src/app/layout.tsx`)

```tsx
import { Inter, JetBrains_Mono } from "next/font/google";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});
// Apply: <html className={`${inter.variable} ${jetbrainsMono.variable}`}>
```

### Usage rules

- Body/UI text: `font-sans` (Inter) - default, applied at `html` level
- Code blocks, inline code: `font-mono` (JetBrains Mono)
- No separate heading font - headings use Inter with `font-bold` / `font-semibold`

### Text scale in use

| Pattern | Class |
|---|---|
| Page section labels, breadcrumbs | `text-xs font-bold uppercase tracking-widest text-sun-muted` |
| Module labels above page titles | `text-xs font-bold uppercase tracking-widest text-sun-yellow` |
| Nav section headers (modules) | `text-xs font-bold uppercase tracking-widest text-sun-dark` |
| Nav section headers (sub-sections) | `text-xs font-semibold uppercase tracking-wider text-sun-muted` |
| Nav leaf links | `text-sm` |
| Buttons/badges | `text-xs font-semibold` |
| Body content | `text-sm` or `text-base` with `prose` class |
| Page h1 in dark banner | `text-base font-bold text-white tracking-tight leading-tight` |

---

## Prose / Course Content Typography

Applied to the `<article>` wrapper on course pages via `className="prose prose-base max-w-none"`.

Override variables (set in `.prose` block in globals.css):

```css
.prose {
  --tw-prose-headings:          #111111;
  --tw-prose-body:              #1c1c1c;
  --tw-prose-links:             #7a6000;       /* sun-amber */
  --tw-prose-code:              #5a4800;
  --tw-prose-pre-bg:            #1a1a1a;
  --tw-prose-blockquote-border: #FFDA47;
  --tw-prose-hr:                rgba(255, 218, 71, 0.35);
  --tw-prose-th-borders:        rgba(255, 218, 71, 0.3);
  --tw-prose-td-borders:        rgba(0, 0, 0, 0.05);
}

.prose h2 {
  border-bottom: 1px solid rgba(255, 218, 71, 0.35);
  padding-bottom: 0.28rem;
}

.prose h3 {
  color: #5a4800;
}

.prose code:not(pre code) {
  background: rgba(255, 218, 71, 0.14);
  color: #5a4800;
  border-radius: 4px;
  padding: 0.1em 0.35em;
  font-size: 0.82em;
}

.prose pre {
  border-left: 2px solid #FFDA47;
  border-radius: 0 6px 6px 0;
}

.prose blockquote {
  border-left-color: #FFDA47;
}
```

---

## Audience Toggle CSS

This CSS must be present globally. It drives the show/hide behavior when AudienceToggle sets `data-audience` on `<body>`.

Content authors mark blocks in markdown with HTML divs:
- `<div class="audience-tech">` - shown only in Technical mode
- `<div class="audience-biz">` - shown only in Non-Technical mode

```css
/* Visibility control */
body[data-audience="tech"] .audience-biz { display: none; }
body[data-audience="biz"]  .audience-tech { display: none; }

/* Visual treatment for tech content */
.prose .audience-biz {
  border-left: 2.5px solid #3b82f6;   /* blue-500 */
  padding-left: 1.1rem;
  margin-left: 0;
  margin-bottom: 1rem;
}

/* Visual treatment for biz content */
.prose .audience-tech {
  border-left: 2.5px solid #FFDA47;   /* sun-yellow */
  padding-left: 1.1rem;
  margin-left: 0;
  margin-bottom: 1rem;
}
```

---

## Recurring UI Patterns

### Active nav link

```
bg-sun-yellow-dim text-sun-amber font-semibold
```

### Inactive nav link (hover state)

```
text-sun-muted hover:text-sun-dark hover:bg-sun-yellow-dim
```

### Primary CTA button (yellow)

```
bg-sun-yellow text-sun-dark hover:bg-sun-yellow-dk rounded-md px-2.5 py-1 text-xs font-semibold transition-colors
```

### Ghost icon button

```
p-1.5 text-sun-muted hover:text-sun-dark hover:bg-sun-yellow-dim rounded transition-colors
```

### Yellow border dividers

```
border-sun-yellow-bdr        (subtle, semi-transparent)
border-sun-yellow            (strong, full yellow - used for major section borders)
border-b-2 border-sun-yellow (2px bottom border - header, page title banner, footer)
```

### Page section separator pattern

Sticky header: `border-b-2 border-sun-yellow`
Internal dividers: `border border-sun-yellow-bdr`
Footer top: `border-t-2 border-sun-yellow`

### Selection highlight

```css
::selection {
  background: rgba(255, 218, 71, 0.4);
  color: #111111;
}
```

### Scrollbar behavior

All scrollable containers use `overflow-y-auto`. No custom scrollbar styling.

---

## Responsive Breakpoints in Use

| Breakpoint | Width | Pattern |
|---|---|---|
| (default) | mobile | single column, no sidebar |
| `sm:` | 640px | show sunmintz.com header link, 2-col grids |
| `md:` | 768px | show social icons in header |
| `lg:` | 1024px | show sidebar, show TOC, hide MobileNav |
