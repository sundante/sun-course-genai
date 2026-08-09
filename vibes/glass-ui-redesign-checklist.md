# Glassmorphism / "Liquid Glass" UI Redesign - Checklist

Tracks execution of `vibes/GLASS-UI-REDESIGN.md`. Sections are ordered by dependency - 1-3 are
foundational and should be done first; 4-9 depend on them; 10-11 close out the effort. Check off
each `[ ]` item as it's completed **in the same session the work was done**, per `CLAUDE.md` >
"Project Tracking". Once every section is checked off and verified, delete this file and record
the outcome in `vibes/status.md`'s Changelog (matching how `diagram-conversion-checklist.md` was
retired) - do not let it linger once it's no longer a live tracker.

---

## Section 1 — Design Token System ✅ DONE 2026-07-22
- [x] Blur radii tokens added to `src/app/globals.css` as `--blur-glass-sm/md/lg` in `@theme
      inline` (8/16/28px) - generates `blur-glass-*`/`backdrop-blur-glass-*` utilities once used
- [x] Glass bg/border opacity tokens per surface elevation (panel, nav, card, modal) + a scrim
      token, each with light + dark pairs (`--glass-*-bg`/`--glass-*-border`)
- [x] Dark-mode color pairs defined for every existing `--color-sun-*` token, via a `:root`/`.dark`
      runtime-variable indirection (`--sun-*` → `.dark { --sun-*: ... }`) aliased through
      `@theme inline`, same pattern already used for `--font-sans`
- [x] Shadow/glow tokens added (`--shadow-glass-sm/md/lg`, `--shadow-glass-glow`), light + dark
      pairs (dark uses black-based shadows + a softer glow since shadows barely read on dark bg)
- [x] **Bonus fix, in scope:** the shadcn `:root` HSL block (`--background`, `--border`,
      `--ring`, ...) had no `@theme` mapping, so Tailwind v4 was silently dropping every
      `bg-background`/`border-input`/`ring-ring` utility used in `src/components/ui/*.tsx` -
      these are real, currently-used classes, not future glass work, so fixing the mapping was
      necessary token-system work, not scope creep. Now wired via `--shadcn-*` runtime vars with
      `.dark` pairs, verified in built CSS (`bg-background` now emits
      `hsl(var(--shadcn-background))` instead of nothing).
- [x] `body` background/color switched from hardcoded hex to `var(--sun-bg)`/`var(--sun-dark)`
      (root-level only, not component work)
- [x] Verified: `npm run build` succeeds (108 static pages), dev server returns 200 on `/` and a
      sample content page, generated CSS contains the `.dark{...}` override block and working
      `bg-background`/`border-input`/`ring-ring`/`bg-sun-yellow` rules
- **Note for later sections:** new `--color-glass-*`/`--shadow-glass-*`/`--blur-glass-*` tokens
  are tree-shaken out of the shipped CSS until a component actually uses the corresponding
  utility class (e.g. `bg-glass-panel-bg`, `shadow-glass-md`) - this is expected Tailwind v4 JIT
  behavior, not a bug. No visual/dark-mode toggle exists yet (Section 2/3) - light mode is
  unchanged and is what currently ships.

## Section 2 — Dark Mode Infrastructure ✅ DONE 2026-07-22
- [x] Hand-rolled `.dark` class + localStorage (`theme` key) instead of `next-themes` - no new
      dependency needed for a single boolean toggle; logic lives in
      `src/components/course/ThemeToggle.tsx`
- [x] No-flash-of-wrong-theme inline `<script>` added to `src/app/layout.tsx` `<head>` - reads
      `localStorage.getItem("theme")` and adds `.dark` to `<html>` before hydration; defaults to
      light (no system `prefers-color-scheme` check, per the locked-in requirement)
- [x] `.dark:` Tailwind variant (already declared as `@custom-variant dark (&:is(.dark *))` in
      Section 1) verified working: toggling adds/removes `.dark` on `<html>`, confirmed the
      `.dark{...}` token overrides from Section 1 are present in built CSS and apply to `body`
      (background/text color) immediately
- **Known limitation, expected at this stage:** most components (`Header`, `Sidebar`,
  `MobileNav`, both modals, `AgentUseCaseMindmap`, the landing page) still hardcode `bg-white`
  rather than a token, so toggling dark mode right now only visibly changes the page
  background/text - not chrome/cards. That's Sections 4/5/8/9's job.

## Section 3 — Theme Toggle Component ✅ DONE 2026-07-22
- [x] Toggle control built in `src/components/course/ThemeToggle.tsx` - keyboard operable
      (native `<button>`), `aria-pressed`, `aria-label`/`title` describing the action about to
      happen ("Switch to dark/light mode")
- [x] Wired into `Header.tsx` (course/lesson/quiz pages) as an always-visible icon button next to
      the flex spacer - not inside the `hidden sm:flex`/`hidden md:flex` groups, so it's visible
      on mobile too
- [x] Also wired into `src/app/page.tsx`'s separate inline header markup (the landing page does
      not reuse `Header.tsx`) - otherwise the toggle would be invisible on `/`, the page a visitor
      sees first
- [x] Defaults to light mode; persists preference via `localStorage["theme"]` across reload
- [x] Hydration-safe: server/first-client-render shows a neutral `aria-hidden` placeholder icon
      (moon, disabled) until mount, then swaps to the real interactive button - avoids a
      hydration-mismatch warning since build-time HTML has no access to the visitor's stored
      preference
- [x] Verified: `npm run build` succeeds (108 pages), confirmed in built HTML that the
      pre-hydration inline script and the placeholder button both render correctly on `/` and a
      course page; dev server 200s on both routes
- **Not separately verified on a real mobile viewport/touch device** - logic is viewport-agnostic
  (no `hidden` classes on the button itself) but only checked via curl/build output, not an actual
  browser

## Section 4 — Core Chrome Components ✅ DONE 2026-07-22

- [x] `Header.tsx` glass treatment (light + dark) - `bg-white` → `bg-glass-nav-bg
      backdrop-blur-glass-md`, `shadow-sm` → `shadow-glass-sm`; kept the `border-b-2
      border-sun-yellow` brand accent as-is
- [x] `Sidebar.tsx` glass treatment (light + dark) - desktop `aside` `bg-white` →
      `bg-glass-nav-bg backdrop-blur-glass-md`; WIP footer note `bg-sun-bg/60` → `bg-glass-panel-bg
      backdrop-blur-glass-sm`. Mobile variant (rendered inside `sheet.tsx`) intentionally left
      solid - that's Section 5's job
- [x] `MobileNav.tsx` glass treatment (light + dark) - trigger bar `bg-white` → `bg-glass-nav-bg
      backdrop-blur-glass-md`; the `Sheet`/`SheetContent` drawer itself is unchanged (Section 5)
- [x] `PageNav.tsx` glass treatment (light + dark) - the actual visual chrome is the sticky
      bottom-bar wrapper in `learn/[module]/[slug]/page.tsx` (`bg-sun-bg` → `bg-glass-nav-bg
      backdrop-blur-glass-md`); also updated `PageNav.tsx`'s own default `className` fallback
      (used by any future caller that doesn't pass one) to a glass-panel look for consistency
- [x] `TableOfContents.tsx` glass treatment (light + dark) - wrapped the sticky container in
      `bg-glass-panel-bg backdrop-blur-glass-sm border border-glass-panel-border rounded-lg
      shadow-glass-sm`
- [x] Verified via Playwright screenshots (desktop 1440×900 + mobile 390×844, light + dark,
      scrolled state) against the dev server on `/learn/llm-models/notes-01-llm-fundamentals`:
      no layout shift, no console errors, glass panels legible in both themes. `npm run build`
      also confirmed all new `bg-glass-nav-bg`/`backdrop-blur-glass-md`/`shadow-glass-sm`/
      `border-glass-panel-border` utilities emit correctly in built CSS.
- **Found, not fixed (out of Section 4 scope):** the lesson-page dark title banner (`bg-sun-dark`
  div in `page.tsx`, hardcoded `text-white`) is illegible in dark mode - `--sun-dark` inverts to a
  near-white value in `.dark`, so a light bg renders under white text. Pre-existing, not
  introduced by this section (chrome components were already `bg-white` before). Belongs to
  Section 8 (Page-Level Layouts) - flag it there.

## Section 5 — Modals & Overlays
- [ ] `AudienceOnboardingModal.tsx` glass scrim/panel (light + dark)
- [ ] `DisclaimerModal.tsx` glass scrim/panel (light + dark)
- [ ] shadcn `sheet.tsx` (mobile drawer) glass treatment (light + dark)

## Section 6 — shadcn UI Primitives
- [ ] Audit existing `variant=` prop usage across content pages before changing defaults
- [ ] `card.tsx` glass variant
- [ ] `button.tsx` glass variant
- [ ] `badge.tsx` glass variant
- [ ] `progress.tsx` glass variant
- [ ] `separator.tsx` glass variant
- [ ] Confirm no existing consumer broke

## Section 7 — MDX / Content Rendering Layer
- [ ] `MdxComponents.tsx` updated for glass-styled tables/code blocks/callouts
- [ ] `.prose` overrides in `globals.css` updated
- [ ] Spot-checked representative sample of `.mdx` files across all modules (headings, tables,
      code fences, mermaid diagram containers) in both themes

## Section 8 — Page-Level Layouts
- [ ] Landing page (`app/page.tsx`) glass/backdrop treatment
- [ ] Lesson page (`learn/[module]/[slug]`) background/hero treatment
- [ ] Quiz page (`quiz/[module]`) treatment
- [ ] Quiz page (`quiz/all`) treatment
- [ ] `not-found.tsx` treatment

## Section 9 — AgentUseCaseMindmap.tsx
- [ ] Node/panel glass styling matched to token system (light + dark)
- [ ] Verified no visual/functional regressions in the mindmap interaction

## Section 10 — Cross-Cutting QA Pass
- [ ] Full site walkthrough in light mode
- [ ] Full site walkthrough in dark mode
- [ ] Contrast/accessibility check on glass-over-content surfaces
- [ ] Mobile performance check (backdrop-blur GPU cost, especially mobile Safari)
- [ ] Target browser support check

## Section 11 — Status Doc Sync
- [ ] `vibes/status.md` "What's Built" section updated to describe the new glass system
- [ ] `vibes/status.md` Changelog entry added
- (Note: `DESIGN-SYSTEM.md`/`UI-COMPONENTS.md`/`PAGE-LAYOUTS.md` were deleted 2026-07-22 as
      stale - don't recreate them here unless a real need arises)

---

## Changelog

- **2026-07-22** - Checklist created alongside `vibes/GLASS-UI-REDESIGN.md`. No sections started
  yet.
- **2026-07-22** - Section 4 (Core Chrome Components) done: `Header.tsx`, `Sidebar.tsx`,
  `MobileNav.tsx`, `PageNav.tsx` (+ its sticky wrapper in `learn/[module]/[slug]/page.tsx`), and
  `TableOfContents.tsx` moved from solid `bg-white` to the Section 1 glass-nav/glass-panel tokens.
  Verified with Playwright screenshots (light/dark, desktop/mobile) - no regressions. Found but
  left unfixed (belongs to Section 8): the dark-mode lesson-page title banner is illegible since
  `--sun-dark` inverts to near-white but the banner text stays hardcoded `text-white`.
