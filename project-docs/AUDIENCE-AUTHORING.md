# Audience Toggle - Authoring Guide

The site has a "View as" toggle on every content page with three modes:

- **All** - both sections visible (default)
- **Technical** - non-technical sections hidden, yellow left bar marks technical sections
- **Non-Technical** - technical sections hidden, blue left bar marks non-technical sections

The user's preference is saved in `localStorage` (key: `genai_mode`) and restored on every page load.

---

## How to tag content

Wrap any section in one of these two div wrappers. The `markdown="1"` attribute is required - it tells the MDX renderer to parse the content inside as Markdown.

```html
<div class="audience-biz" markdown="1">

Plain-language explanation - no jargon, real-world analogies, business impact.
Write as if explaining to a smart non-engineer.

</div>

<div class="audience-tech" markdown="1">

Full technical depth: math, code, internals, trade-offs.
Write as if explaining to a senior engineer.

</div>
```

Blank lines before and after the opening and closing div tags are required for Markdown parsing to work correctly inside them.

Untagged content (plain Markdown with no div wrapper) is always visible in all modes - use it for headings, shared context, and anything that applies to both audiences.

---

## Pattern from module 01 (reference implementation)

File: `docs/01-LLM-Models/Notes/01-LLM-Fundamentals.md`

```markdown
## What Is a Large Language Model

<div class="audience-biz" markdown="1">

Think of an LLM as an incredibly well-read assistant...

</div>

<div class="audience-tech" markdown="1">

### Concept

A Large Language Model is a neural network trained to predict the next token...

</div>

---

## Key Concepts: Tokens, Context, Temperature

### Tokens

<div class="audience-biz" markdown="1">

AI models don't read text the way you do. They break everything into small chunks called tokens...

</div>

<div class="audience-tech" markdown="1">

LLMs operate on tokens - subword units produced by a tokenizer - not characters or words...

</div>
```

---

## Which pages should get dual-audience content

| Page type | Add audience divs? |
|-----------|-------------------|
| Concept/overview notes (01-*, INDEX.md) | Yes |
| Interview Q&A banks | Yes (biz = plain answer, tech = deep answer) |
| Code labs | No - tech audience only |
| Framework deep-dives (ADK, LangChain, etc.) | No - tech audience only |
| System design pages | Optional - summary section in biz |

---

## Color coding reference

- Yellow left bar (`border-left: 2.5px solid #FFDA47`) = `audience-tech`
- Blue left bar (`border-left: 2.5px solid #3b82f6`) = `audience-biz`

The toggle legend in the UI shows a color swatch indicating which sections are currently visible.
