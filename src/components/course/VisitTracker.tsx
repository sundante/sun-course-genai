"use client";

import { useEffect } from "react";

/** Last lesson page opened, for the course map's "You are here" pin. Browser-only. */
export const LAST_VISIT_KEY = "genai_last_visit";

export interface LastVisit {
  href: string;
  title: string;
  module: string;
}

/** Records the current lesson page as the last visit. No UI. */
export function VisitTracker(visit: LastVisit) {
  const { href, title, module } = visit;
  useEffect(() => {
    try {
      localStorage.setItem(LAST_VISIT_KEY, JSON.stringify({ href, title, module }));
    } catch {
      // Storage blocked (private mode, disabled site data) - the map just shows no pin
    }
  }, [href, title, module]);
  return null;
}
