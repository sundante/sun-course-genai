import fs from "fs";
import path from "path";
import yaml from "js-yaml";
import type { NavItem, NavModule, NavigationTree, PageRef } from "@/types/content";

const DOCS_DIR = path.join(process.cwd(), "content");
const NAV_PATH = path.join(DOCS_DIR, "nav.yml");

/** Map from top-level nav section title to URL module slug */
const MODULE_SLUG_MAP: Record<string, string> = {
  "LLM Models": "llm-models",
  "Prompt Engineering": "prompt-engineering",
  RAG: "rag",
  MCP: "mcp",
  Agents: "agents",
  "Agentic AI": "agentic-ai",
  "Knowledge Check": "knowledge-check",
};

function filePathToSlug(filePath: string): string {
  // 01-LLM-Models/Notes/01-LLM-Fundamentals.md → 01-llm-fundamentals
  const base = path.basename(filePath, ".md");
  return base.toLowerCase().replace(/_/g, "-");
}

function buildHref(moduleSlug: string, filePath: string): string {
  const slug = filePathToSlug(filePath);
  if (filePath === "index.md") return "/";
  return `/learn/${moduleSlug}/${slug}`;
}

type MkDocsNavEntry = string | Record<string, string | MkDocsNavEntry[]>;

function parseNavEntry(
  entry: MkDocsNavEntry,
  moduleSlug: string,
  depth = 0
): NavItem | null {
  if (typeof entry === "string") return null; // bare string, skip

  const [title, value] = Object.entries(entry)[0];

  if (typeof value === "string") {
    // Leaf page
    const filePath = value;
    return {
      title,
      href: buildHref(moduleSlug, filePath),
      filePath,
    };
  }

  if (Array.isArray(value)) {
    // Section with children
    const children: NavItem[] = [];
    for (const child of value) {
      const item = parseNavEntry(child, moduleSlug, depth + 1);
      if (item) children.push(item);
    }
    return { title, href: "", children };
  }

  return null;
}

let _cache: NavigationTree | null = null;

export function getNavigationTree(): NavigationTree {
  if (_cache) return _cache;

  const raw = fs.readFileSync(NAV_PATH, "utf-8");
  const config = yaml.load(raw) as { nav: MkDocsNavEntry[] };

  const modules: NavModule[] = [];
  const flatPages: PageRef[] = [];

  for (const topEntry of config.nav) {
    if (typeof topEntry === "string") continue;
    const [title, children] = Object.entries(topEntry)[0];

    if (title === "Home") continue; // skip home

    const moduleSlug = MODULE_SLUG_MAP[title] ?? title.toLowerCase().replace(/\s+/g, "-");

    if (!Array.isArray(children)) continue;

    const items: NavItem[] = [];
    for (const child of children) {
      const item = parseNavEntry(child, moduleSlug);
      if (item) items.push(item);
    }

    modules.push({ title, slug: moduleSlug, items });

    // Collect flat leaf pages
    function collectLeaves(navItems: NavItem[]) {
      for (const item of navItems) {
        if (item.filePath && item.href) {
          flatPages.push({
            title: item.title,
            href: item.href,
            filePath: item.filePath,
            module: moduleSlug,
            slug: filePathToSlug(item.filePath),
          });
        }
        if (item.children) collectLeaves(item.children);
      }
    }
    collectLeaves(items);
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
