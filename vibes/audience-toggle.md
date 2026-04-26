# Plan: Audience Toggle — Business / Technical / Both

## Context
The curriculum is currently written for a technical audience only. The goal is to make
it accessible to both technical and non-technical (business) readers on the same page,
using a persistent 3-way toggle. No color coding — content just appears or disappears
based on the selected mode. Pilot scope: LLM Fundamentals page only.

---

## User Decisions
- Content: I write both versions (business + technical) for LLM Fundamentals
- Toggle placement: Sticky bar at the top of the content area (not in global header)
- Granularity: Block-level — entire H3/H2 subsections tagged, not individual paragraphs

---

## How It Works

### Content tagging in Markdown (HTML divs with `markdown="1"`)
```html
<div class="audience-biz" markdown="1">
Plain-language explanation using real-world analogy.
No jargon — accessible to a PM, recruiter, or exec.
</div>

<div class="audience-tech" markdown="1">
### Original technical depth
Full technical content: math, code, internals, tradeoffs.
</div>
```
Untagged content (tables, summaries, key takeaways) is always shown in all modes.

### CSS show/hide via body class
```css
/* All (default) — everything visible */
/* Technical mode */
body.mode-tech .audience-biz { display: none; }
/* Business mode */
body.mode-biz  .audience-tech { display: none; }
```

### Toggle bar UI
```
┌─────────────────────────────────────────────────┐
│  View as:  [ All ]  [ Technical ]  [ Business ]  │  ← sticky, top of content
└─────────────────────────────────────────────────┘
# LLM Fundamentals
content...
```
- Persisted in `localStorage` as `genai_mode` (`all` | `tech` | `biz`)
- Default: `all`
- Re-applied on every SPA navigation (Material's `document$` subscribe)

---

## Files to Edit

### 1. `mkdocs.yml`
Add two markdown extensions (needed for `markdown="1"` inside HTML divs):
```yaml
markdown_extensions:
  - attr_list
  - md_in_html
  # ... existing extensions unchanged
```

### 2. `docs/overrides/main.html`
Add inside `{% block extrahead %}`:
- CSS for `.su-audience-bar`, `.su-aud-btn`, `.su-aud-btn.active`
- Sticky bar styles: `position: sticky; top: 56px; z-index: 100`

Add inside `{% block scripts %}`:
- JS IIFE that:
  1. Reads `genai_mode` from localStorage on init, applies body class
  2. Injects the toggle bar DOM into `.md-content__inner` on each page
  3. Handles button clicks → updates body class + localStorage
  4. Uses `document$.subscribe()` to re-inject on SPA navigation

### 3. `docs/stylesheets/extra.css`
Add:
```css
body.mode-tech .audience-biz { display: none; }
body.mode-biz  .audience-tech { display: none; }
```

### 4. `docs/01-LLM-Models/Notes/01-LLM-Fundamentals.md`
Rewrite with tagged blocks for each major section:

| Section | Business block content | Tech block |
|---------|----------------------|------------|
| What Is an LLM | "Think of it like a very sophisticated autocomplete..." | Existing: next-token predictor, autoregressive generation |
| Tokens | "AI reads in chunks, not words — affects cost and quirky behavior" | Existing: BPE internals, arithmetic failures, tiktoken code |
| Context Window | "Every AI has a working memory limit — bigger = more expensive" | Existing: O(n²) math, scaling approaches table |
| Sampling Parameters | "You can tune how predictable or creative the AI's answers are" | Existing: softmax/logits, top-p/top-k math |
| Types of LLMs | "Three types: generators, classifiers, translators — generators won" | Existing: decoder/encoder/seq2seq architecture details |
| Open Source vs Proprietary | Keep as-is (table already accessible) — untagged | Keep as-is — untagged |
| Study Notes | Keep as-is — untagged | Keep as-is — untagged |

---

## Verification
1. `mkdocs serve` locally
2. Open LLM Fundamentals — default shows everything (All mode)
3. Click Technical → business blocks disappear, all technical depth remains
4. Click Business → code blocks, math sections disappear, only plain-language content shows
5. Navigate to another page and back — toggle state persists (localStorage)
6. Refresh page — toggle state still active
7. Check dark mode — toggle bar adapts to Material dark theme
