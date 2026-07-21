import fs from "fs";
import path from "path";
import GithubSlugger from "github-slugger";
import type { PageContent, PageRef, TocItem } from "@/types/content";
import { getNavigationTree, getPrevNext } from "./nav";

const CONTENT_DIR = path.join(process.cwd(), "src/content");

export function extractToc(markdown: string): TocItem[] {
  const toc: TocItem[] = [];
  // One slugger per page, matching rehype-slug's per-file instance, so generated
  // ids (including duplicate-heading suffixes like `-1`, `-2`) match the actual
  // DOM anchor ids produced by the MDX renderer exactly.
  const slugger = new GithubSlugger();
  const lines = markdown.split("\n");
  let inFence = false;
  for (const line of lines) {
    // Skip headings-looking lines inside fenced code blocks (e.g. Python/YAML
    // comments like "# Define a tool") - only ``` fences are tracked since
    // that's the only fence style used in this content.
    if (/^```/.test(line.trim())) {
      inFence = !inFence;
      continue;
    }
    if (inFence) continue;

    const match = line.match(/^(#{1,3})\s+(.+)/);
    if (!match) continue;
    const level = match[1].length;
    const text = match[2].replace(/[*_`]/g, "").trim();
    const id = slugger.slug(text);
    toc.push({ id, text, level });
  }
  return toc;
}

export function getPage(moduleSlug: string, slug: string): PageContent | null {
  const { flatPages } = getNavigationTree();
  const ref = flatPages.find((p) => p.module === moduleSlug && p.slug === slug);
  if (!ref) return null;

  const filePath = path.join(CONTENT_DIR, ref.filePath);
  if (!fs.existsSync(filePath)) return null;

  const rawContent = fs.readFileSync(filePath, "utf-8");
  const toc = extractToc(rawContent);

  return { ...ref, rawContent, toc };
}

export function getAllPages(): PageRef[] {
  return getNavigationTree().flatPages;
}

export function getPageWithNavigation(moduleSlug: string, slug: string) {
  const page = getPage(moduleSlug, slug);
  if (!page) return null;
  const { prev, next } = getPrevNext(page.href);
  return { page, prev, next };
}
