"use client";

import { useEffect } from "react";
import { AUDIENCE_STORAGE_KEY, AUDIENCE_CHANGED_EVENT, applyAudienceMode, type AudienceMode } from "./AudienceToggle";

/** Keeps body[data-audience] in sync with the saved preference on every page,
 *  even ones that don't render <AudienceToggle /> themselves. No UI. */
export function AudienceSync() {
  useEffect(() => {
    const stored = localStorage.getItem(AUDIENCE_STORAGE_KEY) as AudienceMode | null;
    if (stored && ["all", "tech", "biz"].includes(stored)) {
      applyAudienceMode(stored);
    }

    function onAudienceChanged(e: Event) {
      const mode = (e as CustomEvent<{ mode: AudienceMode }>).detail?.mode;
      if (mode) applyAudienceMode(mode);
    }
    window.addEventListener(AUDIENCE_CHANGED_EVENT, onAudienceChanged);
    return () => window.removeEventListener(AUDIENCE_CHANGED_EVENT, onAudienceChanged);
  }, []);

  return null;
}
