import type { NavItem } from "@/types/content";

// A module's sections in nav.yml: concept groups (named freely - "Concepts", "Core Pipeline", ...)
// plus these fixed, non-concept sections. No fs imports: client components use it.
export const NON_CONCEPT_SECTIONS = new Set(["Code Labs", "Case Studies", "Projects", "Review"]);

export function leafPages(items: NavItem[]): NavItem[] {
  return items.flatMap((item) => (item.children ? leafPages(item.children) : [item]));
}

/** Concept notes of a module, in order, across all of its concept groups */
export function conceptPages(items: NavItem[]): NavItem[] {
  return items.filter((item) => item.children && !NON_CONCEPT_SECTIONS.has(item.title)).flatMap((item) => leafPages(item.children!));
}
