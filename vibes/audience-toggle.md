# Audience Toggle — SHIPPED ✓

## What Was Built
A persistent 3-way "View as" toggle bar on every content page, letting readers
filter content by audience without leaving the page.

**Toggle:** `All | Technical | Non-Technical`
**Pilot page with full content:** LLM Fundamentals
**All other pages:** locked to Technical, "Non-Technical view coming soon" message

---

## Final Design Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Label for plain-language mode | Non-Technical | Inclusive — works for PMs, students, recruiters, execs |
| Default mode | All | Shows everything on first visit |
| Toggle placement | Sticky bar, top of content area | Always accessible while scrolling |
| Content granularity | Block-level (H2/H3 sections) | Simpler to author and maintain |
| Visual markers | Colored left-edge border on content blocks | Consistent with admonition pattern |
| Mode persistence | localStorage (`genai_mode`) | Survives navigation and refresh |

---

## Color System

| Color | Meaning |
|-------|---------|
| Yellow (`#FFDA47`) left border | Technical content block |
| Blue (`#3b82f6`) left border | Non-Technical content block |

Button left edges mirror content block colors — self-describing, no separate legend needed.

---

## How Content Is Tagged

In any `.md` file, wrap sections in audience divs:

```html
<div class="audience-biz" markdown="1">
Plain-language explanation — no jargon, real-world analogies.
</div>

<div class="audience-tech" markdown="1">
### Concept
Full technical depth: math, code, internals, tradeoffs.
</div>
```

Untagged content (tables, key takeaways, comparison sections) is always visible in all modes.

---

## Files Changed

| File | What Changed |
|------|-------------|
| `mkdocs.yml` | Added `attr_list` + `md_in_html` extensions |
| `docs/overrides/main.html` | Toggle bar CSS + JS (sticky, SPA-aware, localStorage) |
| `docs/stylesheets/extra.css` | `body.mode-tech/biz` show/hide rules + left-border styles |
| `docs/01-LLM-Models/Notes/01-LLM-Fundamentals.md` | Full rewrite with `audience-biz` + `audience-tech` blocks |

---

## Extending to New Pages

To add Non-Technical support to any page:
1. Add `PILOT_SEG` detection in `buildBar()` JS OR generalize the pilot check
2. Wrap sections in `<div class="audience-biz" markdown="1">` and `<div class="audience-tech" markdown="1">`
3. Write the plain-language version for each major section

LLM Fundamentals is the reference implementation.
