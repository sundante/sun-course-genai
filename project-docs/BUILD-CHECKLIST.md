# Build Checklist - Learn GenAI

Pages, features, and sections yet to be built, organized by phase.

---

## Phase 2 - Auth & Progress Tracking

- [ ] `/login` - Magic link authentication (Supabase Auth)
- [ ] `/dashboard` - User progress tracking per module
- [ ] Supabase `subscribers` table + email subscription modal (smart gate: show after 5 clicks)
- [ ] Supabase `page_feedback` table + page feedback FAB (thumbs up/down)
- [ ] API: `/api/progress` - Read/write per-module progress
- [ ] API: `/api/subscribe` - Email subscription endpoint
- [ ] API: `/api/feedback` - Page feedback endpoint
- [ ] Audience toggle (Technical / Non-Technical / All) - sticky bar on every content page
  - [ ] Dual-audience content authored for modules 02-06 (only LLM Fundamentals has it today)

---

## Phase 3 - Quiz & Interaction

- [ ] `/quiz/all` - Flashcard quiz mode (all 298+ interview Q&A pairs)
- [ ] `/quiz/[module]` - Per-module quiz mode
- [ ] Quiz state: flip card, mark known/unknown, progress tracking
- [ ] API: `/api/webhooks/stripe` - Payments (if premium tier is added)

---

## Phase 4 - Content Completion

- [ ] Agents module: only 2 concept notes exist - expand to full depth
- [ ] Code Labs: 5 labs listed in mkdocs.yml - verify all are authored and rendering
- [ ] Non-Technical view for modules 02-06 (only LLM Fundamentals has dual-audience content)
- [ ] Code examples for LLM Models, Prompt Engineering, MCP modules (notes-only today)
- [ ] Evaluations and benchmarks section
- [ ] Cost estimation and token budgeting guide
- [ ] `error.tsx` - Custom error boundary page for runtime errors

---

## Phase 5 - Marketing & Growth

- [ ] `(marketing)` route group - landing page, pricing page
- [ ] Open Graph and Twitter card meta on all `/learn` pages
- [ ] Social card image `/assets/social-card.png`
- [ ] `sitemap.xml` generation
- [ ] Analytics integration (Google Analytics `G-STDCPPFR30` already in design)

---

## Already Built

- [x] `/` - Home page (hero, module grid, learning paths, stats strip)
- [x] `/learn/[module]/[slug]` - All 150+ content pages with MDX rendering
- [x] Collapsible sidebar (Level 1: modules, Level 2: sections, smart expand for active page)
- [x] Mobile navigation (Sheet-based drawer)
- [x] Table of contents (sticky right panel, scroll-aware)
- [x] Prev/Next page navigation
- [x] Custom 404 page (`not-found.tsx`)
- [x] Under-development placeholder for login, dashboard, quiz routes
- [x] GitHub star button in header (all pages)
- [x] Header with social links

---

## Supabase Tables Needed

| Table | Purpose | Key columns |
|-------|---------|-------------|
| `subscribers` | Email list | email, name, role, background_type, country, source, confirmed |
| `page_feedback` | Per-page ratings | page_slug, rating, message, email |
| `auth.users` | Auth identities (built-in) | email, created_at |

Note: if a DB trigger on `auth.users` references a dropped `profiles` table, OTP calls return 500. Fix: Supabase -> Database -> Triggers -> delete any trigger pointing to `profiles`.
