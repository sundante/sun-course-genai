import fs from "fs";
import path from "path";
import yaml from "js-yaml";
import type { NavItem, NavModule, NavigationTree, PageRef } from "@/types/content";

const CONTENT_DIR = path.join(process.cwd(), "src/content");

type NavYaml = { nav: NavEntry[] };
type NavEntry = string | Record<string, string | NavEntry[]>;

// Module title (as written in nav.yml) → URL slug. Slugs are kept stable across
// restructures so existing /learn/<slug>/... URLs keep working where possible.
const MODULE_SLUG_MAP: Record<string, string> = {
  "LLM Foundations": "llm-models",
  "Prog Langs": "prog-langs",
  "Pretraining at Scale": "pretraining",
  "Post-Training & Reasoning": "post-training",
  "Fine-Tuning Lab": "fine-tuning-lab",
  "Evaluation & Benchmarks": "evaluation",
  "Inference & Serving": "serving-and-inference",
  "Production Engineering": "production-engineering",
  "Cloud Platforms": "platform-breadth",
  "Prompt & Context Engineering": "prompt-engineering",
  "RAG": "rag",
  "Agent Foundations": "agents",
  "MCP & A2A": "mcp",
  "Agent Patterns & Multi-Agent": "agentic-ai",
  "Agent Frameworks": "agent-frameworks",
  "Production Agents": "production-agents",
  "Agent Engineering": "agent-engineering",
  "Capstones": "capstones",
  "Knowledge Check": "knowledge-check",
};

/** A module's root content dir is the top-level folder shared by all of its pages
 *  (e.g. "02-Prog-Langs"), or "" when its pages live in different top-level folders. */
function moduleRootDir(filePaths: string[]): string {
  const roots = new Set(filePaths.map((p) => (p.includes("/") ? p.split("/")[0] : "")));
  return roots.size === 1 ? [...roots][0] : "";
}

function collectFilePaths(entries: NavEntry[]): string[] {
  const out: string[] = [];
  for (const entry of entries) {
    if (typeof entry === "string") continue;
    for (const value of Object.values(entry)) {
      if (typeof value === "string") out.push(value);
      else if (Array.isArray(value)) out.push(...collectFilePaths(value));
    }
  }
  return out;
}

export function filePathToSlug(filePath: string, moduleRootDir: string): string {
  // Strip the module root dir prefix
  let relative = filePath;
  if (moduleRootDir && filePath.startsWith(moduleRootDir + "/")) {
    relative = filePath.slice(moduleRootDir.length + 1);
  }
  // Strip .md/.mdx extension
  relative = relative.replace(/\.mdx?$/, "");
  // Split, kebab-case each segment, join with -
  return relative
    .split("/")
    .map((seg) => seg.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, ""))
    .join("-");
}

let _cache: NavigationTree | null = null;

function isStubFile(filePath: string): boolean {
  const fullPath = path.join(CONTENT_DIR, filePath);
  if (!fs.existsSync(fullPath)) return true;
  const content = fs.readFileSync(fullPath, "utf-8");
  const lines = content.split("\n");
  // Count lines with actual body content (not headings, HR, empty, or table rows)
  const bodyLines = lines.filter((l) => {
    const t = l.trim();
    return t.length > 0 && !t.startsWith("#") && !t.startsWith("---") && !t.startsWith("|") && !t.startsWith(">");
  });
  return bodyLines.length < 8;
}

function parseItems(
  entries: NavEntry[],
  moduleSlug: string,
  moduleRootDir: string,
  flatPages: PageRef[]
): NavItem[] {
  const items: NavItem[] = [];

  for (const entry of entries) {
    if (typeof entry === "string") continue;

    for (const [title, value] of Object.entries(entry)) {
      if (typeof value === "string") {
        // Leaf page
        const filePath = value;
        const slug = filePathToSlug(filePath, moduleRootDir);
        const href = `/learn/${moduleSlug}/${slug}`;
        const wip = isStubFile(filePath);
        const ref: PageRef = { title, href, filePath, module: moduleSlug, slug };
        flatPages.push(ref);
        items.push({ title, href, filePath, wip });
      } else if (Array.isArray(value)) {
        // Section with children
        const children = parseItems(value, moduleSlug, moduleRootDir, flatPages);
        items.push({ title, href: children[0]?.href ?? "#", children });
      }
    }
  }

  return items;
}

export function getNavigationTree(): NavigationTree {
  if (_cache) return _cache;

  const navFile = path.join(CONTENT_DIR, "nav.yml");
  const raw = fs.readFileSync(navFile, "utf-8");
  const parsed = yaml.load(raw) as NavYaml;

  const modules: NavModule[] = [];
  const flatPages: PageRef[] = [];
  let track: string | undefined;

  for (const entry of parsed.nav) {
    if (typeof entry === "string") continue;

    for (const [title, value] of Object.entries(entry)) {
      if (title === "Home") continue;
      // `- track: Name` starts an unnumbered group of modules
      if (title === "track" && typeof value === "string") {
        track = value;
        continue;
      }

      const moduleSlug = MODULE_SLUG_MAP[title];
      if (!moduleSlug) {
        throw new Error(`nav.yml module "${title}" has no slug in MODULE_SLUG_MAP (src/lib/content/nav.ts)`);
      }

      const entries = Array.isArray(value) ? value : [];
      const rootDir = moduleRootDir(collectFilePaths(entries));
      const items = parseItems(entries, moduleSlug, rootDir, flatPages);

      modules.push({ title, slug: moduleSlug, number: modules.length + 1, track, items });
    }
  }

  _cache = { modules, flatPages };
  return _cache;
}

export function getPageRef(moduleSlug: string, slug: string): PageRef | undefined {
  const { flatPages } = getNavigationTree();
  return flatPages.find((p) => p.module === moduleSlug && p.slug === slug);
}

export function getPrevNext(href: string): { prev?: PageRef; next?: PageRef } {
  const { flatPages } = getNavigationTree();
  const idx = flatPages.findIndex((p) => p.href === href);
  if (idx === -1) return {};
  return {
    prev: idx > 0 ? flatPages[idx - 1] : undefined,
    next: idx < flatPages.length - 1 ? flatPages[idx + 1] : undefined,
  };
}
