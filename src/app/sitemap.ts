import type { MetadataRoute } from "next";
import { getNavigationTree } from "@/lib/content/nav";
import { getQuizIndex } from "@/lib/content/quizzes";
import { SITE_URL } from "@/lib/site";

// Written to out/sitemap.xml at build time. Trailing slashes match next.config's
// trailingSlash: true, so every URL is the canonical one the host serves.
export const dynamic = "force-static";

export default function sitemap(): MetadataRoute.Sitemap {
  const url = (path: string) => `${SITE_URL}${path.replace(/\/?$/, "/")}`;
  const quizzes = getQuizIndex().filter((q) => q.questions > 0);
  return [
    { url: url("/"), priority: 1 },
    { url: url("/map"), priority: 0.8 },
    { url: url("/quiz/all"), priority: 0.5 },
    ...quizzes.map((q) => ({ url: url(`/quiz/${q.module.slug}`), priority: 0.4 })),
    ...getNavigationTree().flatPages.map((page) => ({ url: url(page.href), priority: 0.7 })),
  ];
}
