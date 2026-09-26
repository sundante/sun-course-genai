#!/usr/bin/env node
// Content integrity checks for src/content. Exits non-zero on any error.
//   - internal .md/.mdx links resolve to a page listed in nav.yml
//   - no em dashes in content or site source (house style)
//   - numeric filename prefixes have no gaps within a directory
//   - every .mdx file under src/content is reachable from nav.yml (lab README.mdx files excepted)
//   - ```quiz / ```objectives / ```exercise fences contain valid YAML
import fs from "node:fs";
import path from "node:path";
import yaml from "js-yaml";

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
    for (const value of Object.values(entry)) {
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

  for (const m of prose.matchAll(/\]\(([^)\s]+)\)/g)) {
    const url = m[1];
    if (/^[a-z]+:/i.test(url) || url.startsWith("#")) continue;
    const target = url.split("#")[0];
    if (!target.endsWith(".md") && !target.endsWith(".mdx")) continue;
    const resolved = path.normalize(path.join(path.dirname(rel), target)).replace(/\\/g, "/");
    const candidates = resolved.endsWith(".md") ? [resolved, `${resolved}x`] : [resolved];
    if (!candidates.some((c) => navPaths.has(c))) errors.push(`broken link in ${rel}: ${url}`);
  }

  for (const { lang, body } of fences) {
    if (!["quiz", "objectives", "exercise"].includes(lang)) continue;
    try {
      yaml.load(body);
    } catch (e) {
      errors.push(`invalid ${lang} YAML in ${rel}: ${e.message.split("\n")[0]}`);
    }
  }
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
