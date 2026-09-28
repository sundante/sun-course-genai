import fs from "fs";
import path from "path";
import type { NavItem, NavModule } from "@/types/content";
import { getNavigationTree } from "./nav";

// Counts derived from nav.yml + the content files, so the home page never hand-types
// "180+ notes" style numbers that drift out of date.

const CONTENT_DIR = path.join(process.cwd(), "src/content");

// Questions in the Q&A banks: "**Q12**", "**Q12:**", "**Q:", "### Q3" headings, or "- q:" entries
// in banks written as ```quiz fences
const QUESTION_LINE = /^(\*\*Q\d*[:.* ]|### Q\d|- q:)/;

export interface ModuleStats {
  concepts: number;
  labs: number;
  questions: number;
}

function leaves(items: NavItem[]): NavItem[] {
  return items.flatMap((item) => (item.children ? leaves(item.children) : [item]));
}

function group(items: NavItem[], title: string): NavItem[] {
  return items.flatMap((item) => {
    if (!item.children) return [];
    return item.title === title ? leaves(item.children) : group(item.children, title);
  });
}

function countQuestions(filePath: string | undefined): number {
  if (!filePath) return 0;
  const full = path.join(CONTENT_DIR, filePath);
  if (!fs.existsSync(full)) return 0;
  return fs.readFileSync(full, "utf-8").split("\n").filter((line) => QUESTION_LINE.test(line.trim())).length;
}

export function getModuleStats(mod: NavModule): ModuleStats {
  const concepts = group(mod.items, "Concepts");
  const banks = concepts.filter((item) => item.title.includes("Q&A"));
  return {
    concepts: concepts.length - banks.length,
    labs: group(mod.items, "Code Labs").length,
    questions: banks.reduce((sum, bank) => sum + countQuestions(bank.filePath), 0),
  };
}

export interface CourseStats {
  modules: number;
  tracks: string[];
  concepts: number;
  labs: number;
  questions: number;
  byModule: Record<string, ModuleStats>;
}

// Capstone projects and the review hub are not teaching modules
const NON_TEACHING = new Set(["capstones", "knowledge-check"]);

/** Course-wide totals, over teaching modules only (not the capstones or the Knowledge Check hub). */
export function getCourseStats(): CourseStats {
  const { modules } = getNavigationTree();
  const teaching = modules.filter((mod) => !NON_TEACHING.has(mod.slug));
  const byModule = Object.fromEntries(teaching.map((mod) => [mod.slug, getModuleStats(mod)]));
  const sum = (key: keyof ModuleStats) => Object.values(byModule).reduce((total, s) => total + s[key], 0);
  return {
    modules: teaching.length,
    tracks: [...new Set(teaching.map((mod) => mod.track).filter((t): t is string => Boolean(t)))],
    concepts: sum("concepts"),
    labs: sum("labs"),
    questions: sum("questions"),
    byModule,
  };
}
