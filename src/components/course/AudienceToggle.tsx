"use client";

import { useEffect, useState } from "react";

type Mode = "all" | "tech" | "biz";

const STORAGE_KEY = "genai_mode";

const MODES: { value: Mode; label: string; title: string }[] = [
  { value: "all", label: "All", title: "Show all content" },
  { value: "tech", label: "Technical", title: "Show technical content only" },
  { value: "biz", label: "Non-Technical", title: "Show non-technical content only" },
];

function applyMode(mode: Mode) {
  if (typeof document === "undefined") return;
  if (mode === "all") {
    document.body.removeAttribute("data-audience");
  } else {
    document.body.dataset.audience = mode;
  }
}

export function AudienceToggle() {
  const [mode, setMode] = useState<Mode>("all");

  useEffect(() => {
    const saved = (localStorage.getItem(STORAGE_KEY) as Mode | null) ?? "all";
    setMode(saved);
    applyMode(saved);
  }, []);

  function handleSelect(next: Mode) {
    setMode(next);
    applyMode(next);
    localStorage.setItem(STORAGE_KEY, next);
  }

  return (
    <div className="sticky top-0 z-20 bg-sun-bg border-b border-sun-yellow-bdr flex items-center gap-2 py-2 mb-6 -mx-6 lg:-mx-8 px-6 lg:px-8">
      <span className="text-xs text-sun-muted shrink-0">View as:</span>
      <div className="flex items-center gap-1">
        {MODES.map(({ value, label, title }) => (
          <button
            key={value}
            title={title}
            onClick={() => handleSelect(value)}
            className={`text-xs px-2.5 py-1 rounded-full transition-colors ${
              mode === value
                ? "bg-sun-yellow text-sun-dark font-semibold"
                : "text-sun-muted hover:text-sun-dark hover:bg-sun-yellow-dim"
            }`}
          >
            {label}
          </button>
        ))}
      </div>
      {mode !== "all" && (
        <span className="text-xs text-sun-muted ml-1">
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
    </div>
  );
}
