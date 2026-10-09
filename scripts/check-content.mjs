#!/usr/bin/env node
// Content integrity checks for src/content. Exits non-zero on any error.
//   - internal .md/.mdx links resolve to a page listed in nav.yml, and #anchors to a heading on that page
//   - no em dashes in content or site source (house style)
//   - numeric filename prefixes have no gaps within a directory
//   - every .mdx file under src/content is reachable from nav.yml (lab README.mdx files excepted)
//   - ```quiz / ```objectives / ```exercise fences contain valid YAML
//   - objectives prerequisites link only to pages at or before the page in nav order
//     (a prerequisite marked "optional" or "later" may point ahead)
import fs from "node:fs";
import path from "node:path";
import yaml from "js-yaml";
import GithubSlugger from "github-slugger";

const ROOT = process.cwd();
const CONTENT = path.join(ROOT, "src/content");
const errors = [];
const warnings = [];

function walk(dir, exts) {
  const out = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) out.push(...walk(full, exts));
    else if (exts.some((e) => entry.name.endsWith(e))) out.push(full);
  }
  return out;
}

// nav.yml leaf file paths
const navPaths = new Set();
function collect(entries) {
  for (const entry of entries) {
    if (typeof entry === "string") continue;
    for (const [key, value] of Object.entries(entry)) {
      if (key === "track") continue; // `- track: Name` is a group label, not a page
      if (typeof value === "string") {
        // nav.ts skips the "Home" entry; the landing page is src/app/page.tsx, not a content file
        if (value === "index.mdx") continue;
        if (fs.existsSync(path.join(CONTENT, value))) navPaths.add(value);
        else errors.push(`nav.yml entry points to a missing file: ${value}`);
      }
      else if (Array.isArray(value)) collect(value);
    }
  }
}
collect(yaml.load(fs.readFileSync(path.join(CONTENT, "nav.yml"), "utf-8")).nav);

const mdxFiles = walk(CONTENT, [".mdx"]);
const navOrder = new Map([...navPaths].map((p, i) => [p, i]));

// Heading ids per page, generated the way rehype-slug does (github-slugger, fences skipped)
const anchorCache = new Map();
function anchorsOf(rel) {
  if (anchorCache.has(rel)) return anchorCache.get(rel);
  const slugger = new GithubSlugger();
  const ids = new Set();
  let inFence = false;
  for (const line of fs.readFileSync(path.join(CONTENT, rel), "utf-8").split("\n")) {
    if (/^```/.test(line.trim())) { inFence = !inFence; continue; }
    const m = !inFence && line.match(/^#{1,6}\s+(.+)/);
    if (m) ids.add(slugger.slug(m[1].replace(/[*_`]/g, "").trim()));
  }
  anchorCache.set(rel, ids);
  return ids;
}

// Strip fenced code blocks, returning prose-only text plus the fences themselves
function splitFences(text) {
  const fences = [];
  const prose = text.replace(/^```([\w-]*)[^\n]*\n([\s\S]*?)^```\s*$/gm, (_, lang, body) => {
    fences.push({ lang, body });
    return "";
  });
  return { prose, fences };
}

for (const file of mdxFiles) {
  const rel = path.relative(CONTENT, file).replace(/\\/g, "/");
  const text = fs.readFileSync(file, "utf-8");
  const { prose, fences } = splitFences(text);

  if (!navPaths.has(rel)) {
    // Lab README.mdx files are GitHub-facing docs, not site pages; their relative links target GitHub
    if (path.basename(rel) === "README.mdx") continue;
    warnings.push(`not in nav.yml: ${rel}`);
  }

  // Course fences hold Markdown strings (prerequisites, explanations, solutions), so their links count too
  const linkText = prose + fences.filter((f) => ["quiz", "objectives", "exercise"].includes(f.lang)).map((f) => f.body).join("\n");
  for (const m of linkText.matchAll(/\]\(([^)\s]+)\)/g)) {
    const url = m[1];
    if (/^[a-z]+:/i.test(url) || url.startsWith("#")) continue;
    const [target, anchor] = url.split("#");
    if (!target.endsWith(".md") && !target.endsWith(".mdx")) continue;
    const resolved = path.normalize(path.join(path.dirname(rel), target)).replace(/\\/g, "/");
    const candidates = resolved.endsWith(".md") ? [resolved, `${resolved}x`] : [resolved];
    const page = candidates.find((c) => navPaths.has(c));
    if (!page) errors.push(`broken link in ${rel}: ${url}`);
    else if (anchor && !anchorsOf(page).has(anchor)) errors.push(`broken anchor in ${rel}: ${url}`);
  }

  for (const { lang, body } of fences) {
    if (!["quiz", "objectives", "exercise"].includes(lang)) continue;
    let data;
    try {
      data = yaml.load(body);
    } catch (e) {
      errors.push(`invalid ${lang} YAML in ${rel}: ${e.message.split("\n")[0]}`);
      continue;
    }
    // Same rules remarkCourseFences.ts enforces at render time
    const problem = fenceProblem(lang, data);
    if (problem) errors.push(`invalid ${lang} block in ${rel}: ${problem}`);
    else if (lang === "objectives" && navOrder.has(rel)) {
      for (const prereq of data.prerequisites ?? []) {
        if (/\b(optional|later)\b/i.test(String(prereq))) continue;
        for (const m of String(prereq).matchAll(/\]\(([^)\s#]+\.mdx)/g)) {
          const target = path.normalize(path.join(path.dirname(rel), m[1])).replace(/\\/g, "/");
          if (navOrder.get(target) > navOrder.get(rel)) errors.push(`prerequisite comes later in the course: ${rel} -> ${m[1]}`);
        }
      }
    }
  }
}

// Text fields must parse as strings: an unquoted "Label: rest" line becomes a YAML map and
// renders as "[object Object]"
function isText(v) {
  return typeof v === "string" || typeof v === "number";
}

function badText(list, name) {
  const i = (list ?? []).findIndex((v) => !isText(v));
  return i === -1 ? null : `${name} ${i + 1} is not a string (quote it if it contains ": ")`;
}

function fenceProblem(lang, data) {
  if (lang === "objectives") {
    if (!Array.isArray(data?.outcomes) || !data.outcomes.length) return "`outcomes` must be a non-empty list";
    return badText(data.outcomes, "outcome") ?? badText(data.prerequisites, "prerequisite");
  }
  if (lang === "quiz") {
    if (!Array.isArray(data) || !data.length) return "expected a non-empty list of questions";
    for (const [i, q] of data.entries()) {
      if (!q?.q) return `question ${i + 1} has no \`q\``;
      const text = badText([q.q, ...(q.explain === undefined ? [] : [q.explain])], `question ${i + 1} text`)
        ?? badText(q.options, `question ${i + 1} option`)
        ?? (Array.isArray(q.options) ? null : badText([q.answer], `question ${i + 1} answer`));
      if (text) return text;
      if (Array.isArray(q.options)) {
        if (!Number.isInteger(q.answer) || q.answer < 1 || q.answer > q.options.length) {
          return `question ${i + 1}: \`answer\` must be the 1-based number of the correct option`;
        }
      } else if (q.answer === undefined) {
        return `question ${i + 1} needs \`options\` + \`answer\`, or a free-text \`answer\``;
      }
    }
    return null;
  }
  const items = Array.isArray(data) ? data : [data];
  const missing = items.findIndex((item) => !item?.task);
  if (missing !== -1) return `exercise ${missing + 1} has no \`task\``;
  for (const [i, item] of items.entries()) {
    const fields = [item.task, ...(item.title === undefined ? [] : [item.title]), ...(item.solution === undefined ? [] : [item.solution])];
    const text = badText(fields, `exercise ${i + 1} field`) ?? badText(item.hints, `exercise ${i + 1} hint`);
    if (text) return text;
  }
  return null;
}

// Em dashes in content and site source
for (const file of [...walk(CONTENT, [".mdx", ".yml"]), ...walk(path.join(ROOT, "src"), [".tsx", ".ts"])]) {
  const lines = fs.readFileSync(file, "utf-8").split("\n");
  lines.forEach((line, i) => {
    if (line.includes("—")) errors.push(`em dash: ${path.relative(ROOT, file)}:${i + 1}`);
  });
}

// Numbering gaps: within each directory, NN- prefixes must run 01..N
function checkNumbering(dir) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  const nums = entries
    .map((e) => /^(\d{2})-/.exec(e.name)?.[1])
    .filter(Boolean)
    .map(Number)
    .sort((a, b) => a - b);
  // Report only the first gap per directory
  const gapAt = [...new Set(nums)].findIndex((n, i) => n !== i + 1);
  if (gapAt !== -1) {
    const pad = (n) => String(n).padStart(2, "0");
    errors.push(`numbering gap in ${path.relative(ROOT, dir)}: expected ${pad(gapAt + 1)}, found ${pad([...new Set(nums)][gapAt])}`);
  }
  for (const e of entries) if (e.isDirectory()) checkNumbering(path.join(dir, e.name));
}
checkNumbering(CONTENT);

for (const w of warnings) console.warn(`warn  ${w}`);
for (const e of errors) console.error(`error ${e}`);
console.log(`\n${mdxFiles.length} files checked: ${errors.length} errors, ${warnings.length} warnings`);
process.exit(errors.length ? 1 : 0);
