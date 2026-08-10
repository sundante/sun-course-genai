"use client";

import { useState, useEffect } from "react";

export type AudienceMode = "all" | "tech" | "biz";

export const AUDIENCE_STORAGE_KEY = "genai_mode";
export const AUDIENCE_CHANGED_EVENT = "audience-changed";

const MODES: { value: AudienceMode; label: string }[] = [
  { value: "all",  label: "All" },
  { value: "tech", label: "Technical" },
  { value: "biz",  label: "Non-Technical" },
];

const HIGHLIGHT_SEEN_KEY = "genai_toggle_highlight_v1";

export function applyAudienceMode(m: AudienceMode) {
  if (typeof document === "undefined") return;
  if (m === "all") {
    document.body.removeAttribute("data-audience");
  } else {
    document.body.dataset.audience = m;
  }
}

export function AudienceToggle() {
  const [mode, setMode] = useState<AudienceMode>("all");
  const [saved, setSaved] = useState(false);
  const [highlight, setHighlight] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const stored = localStorage.getItem(AUDIENCE_STORAGE_KEY) as AudienceMode | null;
    if (stored && ["all", "tech", "biz"].includes(stored)) {
      setMode(stored);
      applyAudienceMode(stored);
    }

    if (!localStorage.getItem(HIGHLIGHT_SEEN_KEY)) {
      localStorage.setItem(HIGHLIGHT_SEEN_KEY, "1");
      setHighlight(true);
      const t = setTimeout(() => setHighlight(false), 7000);
      return () => clearTimeout(t);
    }
  }, []);

  function handleSelect(m: AudienceMode) {
    setMode(m);
    applyAudienceMode(m);
    localStorage.setItem(AUDIENCE_STORAGE_KEY, m);
    window.dispatchEvent(new CustomEvent(AUDIENCE_CHANGED_EVENT, { detail: { mode: m } }));
    setSaved(true);
    setHighlight(false);
    setTimeout(() => setSaved(false), 1800);
  }

  const accentColor = mode === "tech" ? "border-sun-yellow" : mode === "biz" ? "border-blue-400" : "border-transparent";

  return (
    <div className={`sticky top-0 z-20 bg-sun-bg border-b border-sun-yellow-bdr flex items-center gap-2 py-2 mb-6 -mx-6 lg:-mx-8 px-6 lg:px-8 border-l-2 transition-colors ${accentColor}`}>
      <span className="text-xs text-sun-muted shrink-0">View as:</span>
      <div
        className={`relative flex items-center gap-1 rounded-full transition-shadow ${
          highlight ? "ring-2 ring-sun-yellow ring-offset-2 ring-offset-sun-bg animate-pulse" : ""
        }`}
      >
        {highlight && (
          <span className="absolute -top-9 left-0 whitespace-nowrap text-[10px] font-semibold text-zinc-900 bg-sun-yellow rounded-full px-2.5 py-1 shadow-glass-sm animate-bounce">
            👆 Personalize this page
          </span>
        )}
        {MODES.map(({ value, label }) => (
          <button
            key={value}
            onClick={() => handleSelect(value)}
            className={`text-xs px-2.5 py-1 rounded-full transition-colors ${
              mode === value
                ? "bg-sun-yellow text-zinc-900 font-semibold"
                : "text-sun-muted hover:text-sun-dark hover:bg-sun-yellow-dim"
            }`}
          >
            {label}
          </button>
        ))}
      </div>
      {mode !== "all" && (
        <span className="text-xs text-sun-muted ml-1 flex items-center gap-1">
          {mode === "tech" ? (
            <span className="flex items-center gap-1">
              <span className="inline-block w-2 h-3 rounded-sm bg-sun-yellow" /> = visible
            </span>
          ) : (
            <span className="flex items-center gap-1">
              <span className="inline-block w-2 h-3 rounded-sm bg-blue-400" /> = visible
            </span>
          )}
        </span>
      )}
      {saved && (
        <span className="ml-auto text-[10px] text-green-600 font-medium animate-pulse">
          Saved ✓
        </span>
      )}
      {!saved && mode !== "all" && (
        <button
          onClick={() => handleSelect("all")}
          className="ml-auto text-[10px] text-sun-muted hover:text-sun-dark transition-colors"
        >
          Reset
        </button>
      )}
    </div>
  );
}
