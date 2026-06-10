import fs from "fs";
import path from "path";
import matter from "gray-matter";
import { getNavigationTree, getPageRef, getPrevNext } from "./nav";
import type { PageContent, PageRef, TocItem } from "@/types/content";

const DOCS_DIR = path.join(process.cwd(), "../docs");

function extractToc(markdown: string): TocItem[] {
  const toc: TocItem[] = [];
  const headingRegex = /^(#{1,3})\s+(.+)$/gm;
  let match;
  while ((match = headingRegex.exec(markdown)) !== null) {
    const level = match[1].length;
    const text = match[2].trim().replace(/\*\*/g, "");
    const id = text
      .toLowerCase()
      .replace(/[^\w\s-]/g, "")
      .replace(/\s+/g, "-")
      .replace(/-+/g, "-");
    toc.push({ id, text, level });
  }
  return toc;
}

export function getAllPages(): PageRef[] {
  return getNavigationTree().flatPages;
}

export function getPage(moduleSlug: string, slug: string): PageContent | null {
  const ref = getPageRef(moduleSlug, slug);
  if (!ref) return null;

  const absPath = path.join(DOCS_DIR, ref.filePath);
  if (!fs.existsSync(absPath)) return null;

  const raw = fs.readFileSync(absPath, "utf-8");
  const { content } = matter(raw);
  const toc = extractToc(content);

  return {
    ...ref,
    rawContent: content,
    toc,
  };
}

export function getPageWithNavigation(moduleSlug: string, slug: string) {
  const page = getPage(moduleSlug, slug);
  if (!page) return null;
  const { prev, next } = getPrevNext(page.href);
  return { page, prev, next };
}
