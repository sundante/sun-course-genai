import fs from "fs";
import path from "path";
import yaml from "js-yaml";
import type { NavItem, NavModule, NavigationTree, PageRef } from "@/types/content";

const CONTENT_DIR = path.join(process.cwd(), "src/content");

const MODULE_SLUG_MAP: Record<string, string> = {
  "LLM Models": "llm-models",
  "Prompt Engineering": "prompt-engineering",
  "RAG": "rag",
  "MCP": "mcp",
  "AI Agents": "agents",
  "Agentic AI": "agentic-ai",
  "Knowledge Check": "knowledge-check",
};

// Maps module slug → root directory prefix in content/
export const MODULE_DIR_MAP: Record<string, string> = {
  "llm-models": "01-LLM-Models",
  "prompt-engineering": "02-Prompts",
  "rag": "03-RAGs",
  "mcp": "04-MCP",
  "agents": "05-Agents",
  "agentic-ai": "06-Agentic-AI",
  "knowledge-check": "",
};

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

type NavYaml = { nav: NavEntry[] };
type NavEntry = string | Record<string, string | NavEntry[]>;

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

  for (const entry of parsed.nav) {
    if (typeof entry === "string") continue;

    for (const [title, value] of Object.entries(entry)) {
      if (title === "Home") continue;

      const moduleSlug = MODULE_SLUG_MAP[title];
      if (!moduleSlug) continue;

      const moduleRootDir = MODULE_DIR_MAP[moduleSlug] ?? "";
      const entries = Array.isArray(value) ? value : [];
      const items = parseItems(entries, moduleSlug, moduleRootDir, flatPages);

      modules.push({ title, slug: moduleSlug, items });
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
