"use client";

import { useEffect } from "react";
import legacyRedirects from "@/lib/content/legacy-redirects.json";

// Static export can't issue server-side redirects, so pages that moved in the course
// restructure are forwarded from the 404 page instead. The map (old -> new /learn/ path)
// is generated when content moves; see vibes/status.md.
const REDIRECTS: Record<string, string> = legacyRedirects;

export function LegacyRedirect() {
  useEffect(() => {
    const { pathname, search, hash } = window.location;
    const at = pathname.indexOf("/learn/");
    if (at === -1) return;
    const target = REDIRECTS[pathname.slice(at).replace(/\/+$/, "")];
    if (target) window.location.replace(`${pathname.slice(0, at)}${target}/${search}${hash}`);
  }, []);
  return null;
}
