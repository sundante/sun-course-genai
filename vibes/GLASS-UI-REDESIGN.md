# Glassmorphism / "Liquid Glass" UI Redesign - Plan

Persisted from the effort-estimation planning session on 2026-07-22. This is the reference plan;
day-to-day execution is tracked in `vibes/glass-ui-redesign-checklist.md`. Once execution is
fully complete, fold the outcome into this file's own status line and delete the checklist per
`CLAUDE.md` > "Project Tracking" convention.

**Status: IN PROGRESS.** Sections 1-3 (Design Token System, Dark Mode Infrastructure, Theme
Toggle Component) are done - see `vibes/glass-ui-redesign-checklist.md` for details. The toggle
is live in the header on every page; dark mode currently only visibly affects page
background/text since chrome components still hardcode `bg-white` (Sections 4/5/8/9). Sections
4-11 not started.

---

## Decisions Locked In

- **Dark mode is in scope**, with a user-facing toggle, **defaulting to light mode** - consistent
  with the existing `CLAUDE.md` > "Asset Color Scheme" convention already used for generated
  assets.
- Execution is broken into **section-level plans** below (one per work area), each independently
  checkable off in the checklist - even though the original estimate was scoped as a single
  big-bang number.

---

## Current State (recon baseline, 2026-07-22)

- **Styling:** Tailwind CSS v4 + shadcn/ui primitives (`class-variance-authority`,
  `tailwind-merge`). Global tokens live in `src/app/globals.css` (118 lines) as `--color-sun-*`
  custom properties plus a legacy shadcn HSL block. Only one existing design token beyond color:
  `--radius: 0.5rem`. No spacing/blur/glass-opacity token system yet.
- **No dark mode today** - zero `next-themes`, zero `.dark` class usage, zero
  `prefers-color-scheme` handling anywhere in the codebase. Built from scratch, not extended.
- **No animation library** - no framer-motion; only Tailwind's `tw-animate-css` utility plugin.
- **Components:** 19 files, ~1,863 LOC, split across `src/components/course/` (13 app-specific)
  and `src/components/ui/` (6 shadcn primitives).
- **Pages/layouts:** 5 distinct page types - root layout, landing page, course-content/lesson
  (MDX, dynamic route), quiz (per-module + all-questions), 404.
- **Content volume:** 110 `.mdx` files, all rendered through one shared `MdxComponents.tsx` +
  `.prose` CSS block - a single centralized touchpoint, not 110x work.
- **Deploy target:** Next.js 16.2.9, static export (`out/` present) - `backdrop-filter` is pure
  CSS so this doesn't block the effect, but there's no server-side theme cookie trick; the toggle
  must be client-side (localStorage) with a no-flash-of-wrong-theme guard.
- **Design docs:** `vibes/DESIGN-SYSTEM.md`, `UI-COMPONENTS.md`, `PAGE-LAYOUTS.md` were deleted
  2026-07-22 as stale (see `vibes/status.md` Changelog) - `src/app/globals.css` and the component
  source files are now the sole source of truth for the current flat/solid-color look. Section 11
  below is scoped down accordingly: there are no separate spec docs to keep in sync anymore.

---

## Section-Level Plans

Each section below is independently executable and checkable off in
`vibes/glass-ui-redesign-checklist.md`. Sections are ordered by dependency (1-3 are foundational;
everything else depends on them), not by priority.

### 1. Design Token System — 1.5 days
**Goal:** a single source of truth for every glass-specific value so no component hand-rolls its
own opacity/blur numbers.
**Files:** `src/app/globals.css`.
**Approach:** define blur radii (`--glass-blur-sm/md/lg`), glass bg/border opacity per surface
elevation (panel, modal, card, nav), dark-mode color pairs for every existing `--color-sun-*`
token, shadow/glow tokens.
**Done when:** tokens exist and are documented; no component work has started yet.

### 2. Dark Mode Infrastructure — 1.5 days
**Goal:** working theme switching with no flash-of-wrong-theme on static export.
**Files:** `src/app/layout.tsx`, new theme provider/util (`next-themes` or hand-rolled
`data-theme` + localStorage).
**Approach:** inline script in root layout executed before hydration; wire `.dark:` Tailwind
variants site-wide.
**Done when:** switching theme via a manual class toggle (before the UI control exists) applies
dark tokens with no flicker on reload.

### 3. Theme Toggle Component — 0.5 day
**Goal:** user-facing control to switch themes, defaulting to light.
**Files:** likely lives in `src/components/course/Header.tsx`, or a new
`ThemeToggle.tsx`.
**Approach:** accessible control (keyboard operable, `aria-pressed`), persists preference via the
infra from Section 2.
**Done when:** toggle is visible in the header, works on desktop + mobile, persists across reload.

### 4. Core Chrome Components — 3 days
**Goal:** glass treatment for the components visible on every page.
**Files:** `Header.tsx`, `Sidebar.tsx` (212 lines, largest/most complex nav), `MobileNav.tsx`,
`PageNav.tsx`, `TableOfContents.tsx`.
**Approach:** glass panel backgrounds, blur, border treatment, verified in both themes.
**Done when:** all five render correctly with glass styling in light + dark, no layout shift.

### 5. Modals & Overlays — 1 day
**Goal:** glass modal/scrim treatment.
**Files:** `AudienceOnboardingModal.tsx`, `DisclaimerModal.tsx`, shadcn `sheet.tsx` (mobile
drawer).
**Approach:** built on existing Radix primitives; contrast-checked in both themes.
**Done when:** all three open/close correctly with glass backdrop in both themes.

### 6. shadcn UI Primitives — 1.5 days
**Goal:** glass variants for shared primitives without breaking existing consumers.
**Files:** `card.tsx`, `button.tsx`, `badge.tsx`, `progress.tsx`, `separator.tsx`.
**Approach:** restyle as glass variants; audit `variant=` prop usage across the 110 content pages
before changing defaults.
**Done when:** no existing `variant=` consumer breaks; new glass variant available where needed.

### 7. MDX / Content Rendering Layer — 1.5 days
**Goal:** glass treatment for prose elements without breaking readability.
**Files:** `MdxComponents.tsx`, `.prose` overrides in `globals.css`.
**Approach:** tables, code blocks, blockquotes/callouts get glass treatment; single centralized
change, but spot-check a representative sample of the 110 `.mdx` files (headings, tables, code
fences, mermaid diagram containers).
**Done when:** sampled pages render prose elements legibly in both themes.

### 8. Page-Level Layouts — 2 days
**Goal:** glass/backdrop treatment at the page-composition level.
**Files:** `app/page.tsx` (landing, 179 lines - likely the most visually ambitious page), lesson
page background/hero treatment, quiz pages, `not-found.tsx`.
**Done when:** all 5 page types render with consistent glass backdrop treatment in both themes.

### 9. AgentUseCaseMindmap.tsx — 1.5 days
**Goal:** bespoke glass treatment for the one hand-built, non-Tailwind-driven component.
**Files:** `AgentUseCaseMindmap.tsx` (549 lines, custom SVG mindmap - largest component in the
codebase).
**Note:** highest-uncertainty item; can't reuse the token system as directly as Tailwind-class
components.
**Done when:** mindmap nodes/panels match the glass system visually in both themes.

### 10. Cross-Cutting QA Pass — 1.5 days
**Goal:** catch what section-by-section work misses.
**Approach:** full site walkthrough in both themes - contrast/accessibility check (glass-on-glass
text legibility is the #1 glassmorphism failure mode), mobile performance check (backdrop-blur is
GPU-costly, especially stacked/nested blur on mobile Safari), browser support check.
**Done when:** no contrast failures, no jarring mobile perf issues, works in target browsers.

### 11. Status Doc Sync — 0.5 day
**Goal:** keep `vibes/status.md` accurate now that it's the sole design/tracking doc.
**Files:** `vibes/status.md`.
**Approach:** update the "What's Built" section to describe the new glass system (colors, tokens,
dark mode); add a Changelog entry. No separate `DESIGN-SYSTEM.md`/`UI-COMPONENTS.md`/
`PAGE-LAYOUTS.md` exist anymore (deleted 2026-07-22 as stale) - don't recreate them unless a
future need for byte-for-byte rebuild specs justifies the maintenance cost.
**Done when:** `status.md` matches the shipped implementation, not the pre-redesign state.

---

## Total Estimate

**~16.5 engineering-days** of focused build+verify work (build + in-browser verification + fix
contrast/regressions), not calendar time.

## Key Risks

- **Accessibility/contrast tuning is where glassmorphism estimates usually blow past their
  number** - translucent panels over varied MDX content need per-surface contrast validation, not
  a one-time check. Expect at least one rework cycle on Sections 4, 7, and 8.
- **`AgentUseCaseMindmap.tsx` (Section 9)** is the single highest-uncertainty item.
- **Static export + no flash-of-wrong-theme (Section 2)** is a known solved pattern but easy to
  get subtly wrong on first pass.
- **No framer-motion today** - if "liquid" (animated, fluid) glass motion is wanted beyond static
  blur/transparency, add ~1-1.5 days for a motion library + interaction polish (not included in
  the estimate above, which assumes static glass panels with simple CSS transitions).
