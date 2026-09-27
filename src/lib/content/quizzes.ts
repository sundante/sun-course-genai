import fs from "fs";
import path from "path";
import yaml from "js-yaml";
import type { NavModule, PageRef } from "@/types/content";
import { getNavigationTree } from "./nav";

// Module quizzes are assembled from the ```quiz fences already in each page (see
// remarkCourseFences.ts), so a question lives in exactly one place: the note it checks.

const CONTENT_DIR = path.join(process.cwd(), "src/content");
const QUIZ_FENCE = /^```quiz[^\n]*\n([\s\S]*?)^```\s*$/gm;
const LINK = /(\]\()([^)\s]+)(\))/g;

export interface PageQuiz {
  page: PageRef;
  fences: string[];
  questions: number;
}

export interface ModuleQuiz {
  module: NavModule;
  pages: PageQuiz[];
  questions: number;
  /** A Markdown document of every page's quiz fences, with links relative to `basePath`. */
  markdown: string;
  /** The file the Markdown's relative links resolve against (the module's first page). */
  basePath: string;
}

function countQuestions(fence: string): number {
  try {
    const data = yaml.load(fence);
    return Array.isArray(data) ? data.length : 0;
  } catch {
    return 0;
  }
}

/** Re-base relative links written for `fromFile` so they resolve from `toFile`. */
function rebaseLinks(text: string, fromFile: string, toFile: string): string {
  const fromDir = path.posix.dirname(fromFile);
  const toDir = path.posix.dirname(toFile);
  if (fromDir === toDir) return text;
  return text.replace(LINK, (match, open: string, url: string, close: string) => {
    if (/^[a-z]+:/i.test(url) || url.startsWith("#") || url.startsWith("/")) return match;
    const [target, anchor] = url.split("#");
    const moved = path.posix.relative(toDir, path.posix.join(fromDir, target)) || ".";
    return `${open}${moved}${anchor ? `#${anchor}` : ""}${close}`;
  });
}

function modulePages(mod: NavModule): PageRef[] {
  return getNavigationTree().flatPages.filter((p) => p.module === mod.slug);
}

export function getModuleQuiz(moduleSlug: string): ModuleQuiz | null {
  const mod = getNavigationTree().modules.find((m) => m.slug === moduleSlug);
  if (!mod) return null;
  const refs = modulePages(mod);
  const basePath = refs[0]?.filePath ?? "";

  const pages: PageQuiz[] = [];
  for (const page of refs) {
    const full = path.join(CONTENT_DIR, page.filePath);
    if (!fs.existsSync(full)) continue;
    const fences = [...fs.readFileSync(full, "utf-8").matchAll(QUIZ_FENCE)].map((m) => m[1]);
    const questions = fences.reduce((sum, f) => sum + countQuestions(f), 0);
    if (questions > 0) pages.push({ page, fences, questions });
  }

  const markdown = pages
    .map(({ page, fences }) => {
      const link = path.posix.relative(path.posix.dirname(basePath), page.filePath);
      const body = fences.map((f) => "```quiz\n" + rebaseLinks(f, page.filePath, basePath) + "```").join("\n\n");
      return `## [${page.title}](${link})\n\n${body}`;
    })
    .join("\n\n");

  return { module: mod, pages, questions: pages.reduce((s, p) => s + p.questions, 0), markdown, basePath };
}

/** Question counts per module, for the quiz index. */
export function getQuizIndex(): { module: NavModule; questions: number; pages: number }[] {
  return getNavigationTree().modules.map((mod) => {
    const quiz = getModuleQuiz(mod.slug);
    return { module: mod, questions: quiz?.questions ?? 0, pages: quiz?.pages.length ?? 0 };
  });
}
