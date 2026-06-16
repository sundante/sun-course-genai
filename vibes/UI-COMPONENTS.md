# UI Components Reference

Exact implementation specs for every course component. When rebuilding, replicate these precisely. All components live in `src/components/course/`.

---

## Header (`Header.tsx`)

**File:** `src/components/course/Header.tsx`
**Type:** Server component (no `"use client"`)

### Behavior

- Sticky top of every course page (z-40)
- Height: `h-13` (3.25rem)
- White background with 2px yellow bottom border + shadow

### Structure (left to right)

1. **Logo** - "Learn GenAI" text link to `/`
2. **Flex spacer** fills remaining space
3. **GitHub Star button** - always visible, yellow bg
4. **sunmintz.com button** - yellow bg, hidden on mobile (`hidden sm:inline-flex`)
5. **Social icons group** - hidden on mobile (`hidden md:flex`), separated by left border
6. **App nav group** - separated by left border (`hidden sm:flex`)

### Exact markup

```tsx
<header className="sticky top-0 z-40 bg-white border-b-2 border-sun-yellow shadow-sm">
  <div className="flex items-center h-13 px-4 gap-3">

    {/* Logo */}
    <Link href="/" className="font-bold text-sun-dark text-sm tracking-tight shrink-0">
      Learn GenAI
    </Link>

    <div className="flex-1" />

    {/* GitHub Star - always visible */}
    <a
      href="https://github.com/sundante/sun-course-genai"
      target="_blank" rel="noopener noreferrer"
      className="inline-flex items-center gap-1.5 text-xs font-semibold bg-sun-yellow text-sun-dark hover:bg-sun-yellow-dk rounded-md px-2.5 py-1 transition-colors shrink-0"
    >
      <StarIcon /> {/* 13x13 SVG star */}
      Github
    </a>

    {/* sunmintz.com - hidden on mobile */}
    <a
      href="https://sunmintz.com/"
      target="_blank" rel="noopener noreferrer"
      className="hidden sm:inline-flex items-center gap-1.5 text-xs font-semibold bg-sun-yellow text-sun-dark hover:bg-sun-yellow-dk rounded-md px-2.5 py-1 transition-colors shrink-0"
    >
      sunmintz.com
    </a>

    {/* Social icons - hidden on mobile, separated by left border */}
    <div className="hidden md:flex items-center gap-1 border-l border-sun-yellow-bdr pl-3 ml-1">
      <a href="https://github.com/sundante" target="_blank" rel="noopener noreferrer"
         className="p-1.5 text-sun-muted hover:text-sun-dark hover:bg-sun-yellow-dim rounded transition-colors" title="GitHub">
        <GitHubIcon /> {/* 15x15 */}
      </a>
      <a href="https://www.linkedin.com/in/suryaprakash-s-singh/" target="_blank" rel="noopener noreferrer"
         className="p-1.5 text-sun-muted hover:text-sun-dark hover:bg-sun-yellow-dim rounded transition-colors" title="LinkedIn">
        <LinkedInIcon /> {/* 15x15 */}
      </a>
      <a href="https://x.com/sunsindante" target="_blank" rel="noopener noreferrer"
         className="p-1.5 text-sun-muted hover:text-sun-dark hover:bg-sun-yellow-dim rounded transition-colors" title="X / Twitter">
        <XIcon /> {/* 14x14 */}
      </a>
    </div>

    {/* App nav - hidden on mobile, separated by left border */}
    <div className="hidden sm:flex items-center gap-1 border-l border-sun-yellow-bdr pl-3 ml-1">
      <Link href="/quiz/all" className={cn(buttonVariants({ variant: "ghost", size: "sm" }), "text-xs")}>
        Quiz
      </Link>
    </div>
  </div>
</header>
```

### SVG icons (inline, no external library for logo icons)

```tsx
// Star (GitHub Star button, 13x13)
<svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
</svg>

// GitHub (social icon, 15x15)
<svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
  <path d="M12 2C6.477 2 2 6.477 2 12c0 4.418 2.865 8.166 6.839 9.489..." />
</svg>

// LinkedIn (social icon, 15x15)
// X/Twitter (social icon, 14x14)
// SunIcon (13x13, circle + rays - used elsewhere if needed)
```

Get full SVG paths from `src/components/course/Header.tsx` in the current codebase.

---

## Sidebar (`Sidebar.tsx`)

**File:** `src/components/course/Sidebar.tsx`
**Type:** `"use client"` - uses `usePathname`, `useState`

### Desktop behavior

- Hidden on mobile, visible on `lg:` and up (`hidden lg:block`)
- Sticky, full viewport height minus header: `h-[calc(100vh-3.5rem)] sticky top-14`
- Width: `w-64` expanded, `w-12` collapsed
- Smooth transition: `transition-all duration-200`
- Right border: `border-r border-sun-yellow-bdr`
- Overflow: `overflow-hidden` on outer, `overflow-y-auto` on inner scroll area

### Collapsed state (CollapsedRail)

Shows only icon buttons, one per module:
- Expand button at top: `PanelLeftOpen` icon, `p-1.5 mb-2` ghost style
- Module buttons: `w-9 h-9 rounded-md text-[10px] font-bold`
  - Active: `bg-sun-yellow text-sun-dark`
  - Inactive: `text-sun-muted hover:text-sun-dark hover:bg-sun-yellow-dim`
- Module abbreviation: first 2 initials (multi-word) or first 3 chars (single word), uppercase

### Expanded state

- Collapse button (top-right): `PanelLeftClose` icon, ghost style, `px-3 pt-3 pb-1 flex justify-end`
- Scroll area: `flex-1 overflow-y-auto px-4 pb-5`

### Module section (`ModuleSection`)

Top-level expandable module:
```tsx
<button className="flex items-center gap-1.5 w-full text-left text-xs font-bold uppercase tracking-widest text-sun-dark py-2 px-1 hover:text-sun-amber transition-colors">
  {open ? <ChevronDown h-3.5 w-3.5> : <ChevronRight h-3.5 w-3.5>}
  {mod.title}
</button>
```

Open by default if any child matches current path (`containsPath(mod.items, pathname)`).

### Nav section (`NavSection` - sub-sections)

Sub-section header (when has children):
```tsx
<button className="flex items-center gap-1.5 w-full text-left text-xs font-semibold uppercase tracking-wider text-sun-muted py-1.5 px-1 hover:text-sun-dark transition-colors">
  {open ? <ChevronDown> : <ChevronRight>}   {/* h-3.5 w-3.5 */}
  {item.title}
</button>
// Children indented with:
<div className="pl-2 border-l border-sun-yellow-bdr space-y-0.5">
```

### Leaf link (`NavLeaf`)

```tsx
<Link
  href={item.href}
  className={`block text-sm py-1 px-3 rounded-md transition-colors leading-snug ${
    active
      ? "bg-sun-yellow-dim text-sun-amber font-semibold"
      : "text-sun-muted hover:text-sun-dark hover:bg-sun-yellow-dim"
  }`}
>
  {item.title}
</Link>
```

Active detection: `pathname === item.href` (exact match via `usePathname()`).

### Mobile mode (`mobile` prop)

When `mobile={true}`, renders without the collapse rail - just scrollable module sections:
```tsx
<div className="py-5 px-4">
  {nav.modules.map(mod => <ModuleSection ... />)}
</div>
```

---

## MobileNav (`MobileNav.tsx`)

**File:** `src/components/course/MobileNav.tsx`
**Type:** `"use client"`

### Behavior

- Only visible on mobile/tablet - `lg:hidden`
- Full-width bar below header with "Contents" label + "Menu" button
- Clicking "Menu" opens a left Sheet drawer

### Bar markup

```tsx
<div className="lg:hidden flex items-center justify-between px-5 py-3 border-b border-sun-yellow-bdr bg-white">
  <span className="text-sm font-medium text-sun-muted">Contents</span>
  <button
    onClick={() => setOpen(true)}
    className="flex items-center gap-2 text-sm font-semibold text-sun-dark hover:text-sun-amber transition-colors"
  >
    <Menu className="h-4 w-4" />
    Menu
  </button>
</div>
```

### Sheet drawer

```tsx
<Sheet open={open} onOpenChange={setOpen}>
  <SheetContent side="left" className="p-0 w-96">
    <SheetHeader className="px-5 py-4 border-b border-sun-yellow-bdr">
      <SheetTitle className="text-base font-bold text-sun-dark">Navigation</SheetTitle>
    </SheetHeader>
    <div className="overflow-y-auto h-full pb-12">
      <Sidebar nav={nav} mobile />
    </div>
  </SheetContent>
</Sheet>
```

Uses `Sheet` from `src/components/ui/sheet.tsx` (Base UI / shadcn).

---

## AudienceToggle (`AudienceToggle.tsx`)

**File:** `src/components/course/AudienceToggle.tsx`
**Type:** `"use client"` - uses `useState`, `useEffect`, `localStorage`

### Behavior

- Three modes: `"all"`, `"tech"`, `"biz"`
- Persists to `localStorage` under key `"genai_mode"`
- Sets `document.body.dataset.audience` to `"tech"` or `"biz"` (or removes attribute for "all")
- CSS in `globals.css` handles content visibility (see DESIGN-SYSTEM.md)

### Position

Sticky at the top of the content area, above the article:

```tsx
<div className="sticky top-0 z-20 bg-sun-bg border-b border-sun-yellow-bdr flex items-center gap-2 py-2 mb-6 -mx-6 lg:-mx-8 px-6 lg:px-8">
```

The negative margins (`-mx-6 lg:-mx-8`) and matching padding make it span the full content column width, bleeding to edges. Adjust to match the content area's horizontal padding.

### Toggle buttons

```tsx
<span className="text-xs text-sun-muted shrink-0">View as:</span>
<div className="flex items-center gap-1">
  {MODES.map(({ value, label }) => (
    <button
      key={value}
      onClick={() => handleSelect(value)}
      className={`text-xs px-2.5 py-1 rounded-full transition-colors ${
        mode === value
          ? "bg-sun-yellow text-sun-dark font-semibold"
          : "text-sun-muted hover:text-sun-dark hover:bg-sun-yellow-dim"
      }`}
    >
      {label}
    </button>
  ))}
</div>
```

### Active mode indicator

When mode is not "all", shows a colored square + "= visible":

```tsx
{mode !== "all" && (
  <span className="text-xs text-sun-muted ml-1">
    {mode === "tech" ? (
      <span className="flex items-center gap-1">
        <span className="inline-block w-2 h-3 rounded-sm bg-sun-yellow" /> = visible
      </span>
    ) : (
      <span className="flex items-center gap-1">
        <span className="inline-block w-2 h-3 rounded-sm bg-blue-400" /> = visible
      </span>
    )}
  </span>
)}
```

---

## TableOfContents (`TableOfContents.tsx`)

**File:** `src/components/course/TableOfContents.tsx`
**Type:** `"use client"` - uses `IntersectionObserver`

### Position

Right sidebar on desktop, hidden on mobile. Rendered conditionally only when `page.toc.length > 0`.

Layout context: `<aside className="hidden lg:block w-64 shrink-0">` in the course page.

### Sticky positioning

```tsx
<div className="sticky top-20 py-2">
```

### Structure

```tsx
<p className="text-xs font-bold uppercase tracking-widest text-sun-muted mb-4 px-1">
  On this page
</p>
<ul className="space-y-0.5">
  {toc.map((item, i) => (
    <li key={...} style={{ paddingLeft: `${(item.level - 1) * 10}px` }}>
      <a
        href={`#${item.id}`}
        className={`block text-sm py-1 px-2 rounded-md transition-colors leading-snug line-clamp-2 ${
          active
            ? "text-sun-amber font-semibold bg-sun-yellow-dim"
            : "text-sun-muted hover:text-sun-dark hover:bg-sun-yellow-dim"
        }`}
      >
        {item.text}
      </a>
    </li>
  ))}
</ul>
```

### Active heading detection

IntersectionObserver with `rootMargin: "0px 0px -60% 0px"` - a heading becomes active when it enters the top 40% of the viewport.

```ts
const observer = new IntersectionObserver(
  (entries) => {
    const visible = entries.filter(e => e.isIntersecting);
    if (visible.length) setActiveId(visible[0].target.id);
  },
  { rootMargin: "0px 0px -60% 0px", threshold: 0 }
);
```

### Indentation

Level 1 headings: `paddingLeft: 0`
Level 2 headings: `paddingLeft: 10px`
Level 3 headings: `paddingLeft: 20px`
Formula: `(item.level - 1) * 10` px

---

## PageNav (`PageNav.tsx`)

**File:** `src/components/course/PageNav.tsx`
**Type:** Server component

### Position

Rendered inside a sticky footer bar at the bottom of the course page:

```tsx
<div className="sticky bottom-0 z-10 bg-sun-bg border-t-2 border-sun-yellow px-6 lg:px-8 py-3">
  <PageNav prev={prev} next={next} className="flex justify-between" />
</div>
```

### Props

```ts
interface Props {
  prev?: PageRef;   // previous page in the flat linear order
  next?: PageRef;   // next page in the flat linear order
  className?: string;
}
```

### Markup

```tsx
<nav className={className ?? "flex justify-between mt-12 pt-6 border-t border-sun-yellow-bdr"}>

  {/* Previous */}
  {prev ? (
    <Link
      href={prev.href}
      className="group flex items-center gap-2 text-sm text-sun-muted hover:text-sun-dark transition-colors max-w-[45%]"
    >
      <ChevronLeft className="h-4 w-4 shrink-0 text-sun-yellow group-hover:text-sun-yellow-dk" />
      <div>
        <div className="text-xs uppercase tracking-wider mb-0.5">Previous</div>
        <div className="font-medium line-clamp-2">{prev.title}</div>
      </div>
    </Link>
  ) : <div />}

  {/* Next */}
  {next && (
    <Link
      href={next.href}
      className="group flex items-center gap-2 text-sm text-sun-muted hover:text-sun-dark transition-colors text-right max-w-[45%]"
    >
      <div>
        <div className="text-xs uppercase tracking-wider mb-0.5">Next</div>
        <div className="font-medium line-clamp-2">{next.title}</div>
      </div>
      <ChevronRight className="h-4 w-4 shrink-0 text-sun-yellow group-hover:text-sun-yellow-dk" />
    </Link>
  )}

</nav>
```

The `className` override replaces the default border+margin style. In the sticky footer, `className="flex justify-between"` is passed.

---

## UnderDevelopment (`UnderDevelopment.tsx`)

**File:** `src/components/course/UnderDevelopment.tsx`
**Type:** `"use client"` - uses `useRouter`

Used for: 404 page, quiz stub pages, any incomplete feature.

### Props

```ts
interface Props {
  title?: string;        // default: "Under Development"
  description?: string;  // default: "This page is being built. Check back soon."
}
```

### Markup

```tsx
<div className="min-h-screen bg-sun-bg flex items-center justify-center px-4">
  <div className="text-center max-w-md">

    {/* Animated yellow bars */}
    <div className="flex items-end justify-center gap-2 mb-10 h-16">
      <div className="w-4 bg-sun-yellow rounded-sm animate-bounce" style={{ height: "2.5rem", animationDelay: "0ms" }} />
      <div className="w-4 bg-sun-yellow rounded-sm animate-bounce" style={{ height: "3.5rem", animationDelay: "150ms" }} />
      <div className="w-4 bg-sun-yellow rounded-sm animate-bounce" style={{ height: "2rem",   animationDelay: "300ms" }} />
      <div className="w-4 bg-sun-yellow rounded-sm animate-bounce" style={{ height: "4rem",   animationDelay: "100ms" }} />
      <div className="w-4 bg-sun-yellow rounded-sm animate-bounce" style={{ height: "2.5rem", animationDelay: "250ms" }} />
    </div>

    <h1 className="text-2xl font-bold text-sun-dark mb-3">{title}</h1>
    <p className="text-sun-muted text-sm mb-8 leading-relaxed">{description}</p>

    <div className="flex items-center justify-center gap-3">
      {/* Ghost back button */}
      <button
        onClick={() => router.back()}
        className="inline-flex items-center gap-1.5 text-sm font-medium text-sun-muted hover:text-sun-dark border border-sun-yellow-bdr hover:border-sun-yellow hover:bg-sun-yellow-dim rounded-md px-4 py-2 transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        Go Back
      </button>

      {/* Yellow home button */}
      <Link
        href="/"
        className="inline-flex items-center gap-1.5 text-sm font-semibold bg-sun-yellow text-sun-dark hover:bg-sun-yellow-dk rounded-md px-4 py-2 transition-colors"
      >
        <Home className="h-4 w-4" />
        Go Home
      </Link>
    </div>

  </div>
</div>
```
