import fs from "fs";
import path from "path";
import type { PageContent, PageRef, TocItem } from "@/types/content";
import { getNavigationTree, getPrevNext } from "./nav";

const CONTENT_DIR = path.join(process.cwd(), "src/content");

export function extractToc(markdown: string): TocItem[] {
  const toc: TocItem[] = [];
  const lines = markdown.split("\n");
  for (const line of lines) {
    const match = line.match(/^(#{1,3})\s+(.+)/);
    if (!match) continue;
    const level = match[1].length;
    const text = match[2].replace(/[*_`]/g, "").trim();
    const id = text
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, "")
      .trim()
      .replace(/\s+/g, "-");
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
