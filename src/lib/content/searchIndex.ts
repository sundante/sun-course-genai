import fs from "fs";
import path from "path";
import yaml from "js-yaml";
import GithubSlugger from "github-slugger";
import { headingText } from "./loader";
import { getNavigationTree } from "./nav";

const CONTENT_DIR = path.join(process.cwd(), "src/content");

/** One searchable section: a page's intro or the text under one ## / ### heading.
 *  Short keys keep the generated search-index.json small. */
export interface SearchSection {
  /** Unique id */
  id: number;
  /** Page title (from nav.yml) */
  p: string;
  /** Module title */
  m: string;
  /** Section heading - empty for the text before the first ## heading */
  h: string;
  /** Link to the page, with #anchor for heading sections */
  u: string;
  /** Plain text of the section */
  x: string;
  /** Distinct identifiers from its code blocks - searched, never shown */
  c: string;
}

// String fields of the course fences worth searching. Quiz answers and exercise
// solutions/hints are left out so result snippets don't give them away.
const FENCE_FIELDS = ["outcomes", "prerequisites", "q", "options", "explain", "title", "task"];

function isCourseFence(lang: string) {
  return lang === "objectives" || lang === "quiz" || lang === "exercise";
}

/** Code is indexed as its distinct identifiers (LoraConfig, vllm.LLM, ...), not
 *  verbatim - searching a function name still finds the lab, at a fraction of the size */
function codeTerms(body: string): string[] {
  return body.match(/[A-Za-z_][\w.]{3,}/g) ?? [];
}

function fenceText(lang: string, body: string): string {
  let data: unknown;
  try {
    data = yaml.load(body);
  } catch {
    return "";
  }
  const out: string[] = [];
  const walk = (value: unknown, key?: string) => {
    if (Array.isArray(value)) value.forEach((v) => walk(v, key));
    else if (value && typeof value === "object") {
      for (const [k, v] of Object.entries(value)) walk(v, k);
    } else if (typeof value === "string" && key && FENCE_FIELDS.includes(key)) {
      out.push(value);
    }
  };
  walk(data);
  return out.join("\n");
}

/** Markdown line -> plain text (links keep their label, markup is dropped) */
function plain(line: string): string {
  return line
    .replace(/<[^>]+>/g, " ")
    .replace(/!\[([^\]]*)\]\([^)]*\)/g, "$1")
    .replace(/\[([^\]]+)\]\([^)]*\)/g, "$1")
    .replace(/^\s*(>+|[-*+]|\d+\.)\s+/, "")
    .replace(/^\s*\|?[\s:|-]+\|?\s*$/, "") // table separator rows
    .replace(/[|*_`~]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

let _cache: SearchSection[] | null = null;

export function getSearchIndex(): SearchSection[] {
  if (_cache) return _cache;

  const { modules, flatPages } = getNavigationTree();
  const moduleTitle = new Map(modules.map((mod) => [mod.slug, mod.title]));
  const sections: SearchSection[] = [];

  for (const page of flatPages) {
    const file = path.join(CONTENT_DIR, page.filePath);
    if (!fs.existsSync(file)) continue;
    const lines = fs.readFileSync(file, "utf-8").split("\n");
    const m = moduleTitle.get(page.module) ?? "";

    // Same per-page slugger as rehype-slug, fed every heading level in order,
    // so anchors (including -1, -2 duplicate suffixes) match the rendered page
    const slugger = new GithubSlugger();
    let h2 = "";
    let heading = "";
    let anchor = "";
    let text: string[] = [];
    let code = new Set<string>();

    const flush = () => {
      const x = text.join(" ").replace(/\s+/g, " ").trim();
      if (x || heading || code.size) {
        const u = anchor ? `${page.href}#${anchor}` : page.href;
        sections.push({ id: sections.length, p: page.title, m, h: heading, u, x, c: [...code].join(" ") });
      }
      text = [];
      code = new Set();
    };

    let fence: { lang: string; body: string[] } | null = null;
    for (const line of lines) {
      const fenceMatch = line.trim().match(/^```\s*([\w-]*)/);
      if (fenceMatch) {
        if (fence) {
          const body = fence.body.join("\n");
          if (isCourseFence(fence.lang)) text.push(fenceText(fence.lang, body));
          else if (fence.lang !== "mermaid") codeTerms(body).forEach((t) => code.add(t));
          fence = null;
        } else {
          fence = { lang: fenceMatch[1], body: [] };
        }
        continue;
      }
      if (fence) {
        fence.body.push(line);
        continue;
      }

      const h = line.match(/^(#{1,6})\s+(.+?)\s*#*\s*$/);
      if (h) {
        const hText = headingText(h[2]);
        const id = slugger.slug(hText);
        const level = h[1].length;
        // # Title belongs to the intro section; ## and ### start new sections;
        // deeper headings stay in their parent section as text
        if (level === 2 || level === 3) {
          flush();
          // ### sections carry their ## parent, since template headings like
          // "Concept" repeat under every topic
          if (level === 2) h2 = hText;
          heading = level === 3 && h2 ? `${h2} › ${hText}` : hText;
          anchor = id;
        } else if (level > 3) {
          text.push(hText);
        }
        continue;
      }
      const p = plain(line);
      if (p) text.push(p);
    }
    flush();
  }

  _cache = sections;
  return sections;
}
