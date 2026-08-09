"use client";

import { useState, useEffect } from "react";
import { DISCLAIMER_DISMISSED_EVENT } from "./DisclaimerModal";
import { AUDIENCE_STORAGE_KEY, AUDIENCE_CHANGED_EVENT, applyAudienceMode, type AudienceMode } from "./AudienceToggle";

const ONBOARDING_KEY = "genai_audience_v1";
const DISCLAIMER_KEY = "genai_disclaimer_v1";

export function AudienceOnboardingModal() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    // Always sync body attribute from stored preference
    const stored = localStorage.getItem(AUDIENCE_STORAGE_KEY) as AudienceMode | null;
    if (stored && ["all", "tech", "biz"].includes(stored)) {
      applyAudienceMode(stored);
    }

    // Listen for inline toggle changes to keep body in sync across all pages
    function onAudienceChanged(e: Event) {
      const mode = (e as CustomEvent<{ mode: AudienceMode }>).detail?.mode;
      if (mode) applyAudienceMode(mode);
    }
    window.addEventListener(AUDIENCE_CHANGED_EVENT, onAudienceChanged);

    // Decide whether to show the onboarding splash
    if (localStorage.getItem(ONBOARDING_KEY)) {
      return () => window.removeEventListener(AUDIENCE_CHANGED_EVENT, onAudienceChanged);
    }

    if (localStorage.getItem(DISCLAIMER_KEY)) {
      // Disclaimer already seen — show splash now
      setOpen(true);
    } else {
      // Wait for disclaimer to be dismissed first
      function onDisclaimerDismissed() {
        setOpen(true);
        window.removeEventListener(DISCLAIMER_DISMISSED_EVENT, onDisclaimerDismissed);
      }
      window.addEventListener(DISCLAIMER_DISMISSED_EVENT, onDisclaimerDismissed);
      return () => {
        window.removeEventListener(DISCLAIMER_DISMISSED_EVENT, onDisclaimerDismissed);
        window.removeEventListener(AUDIENCE_CHANGED_EVENT, onAudienceChanged);
      };
    }

    return () => window.removeEventListener(AUDIENCE_CHANGED_EVENT, onAudienceChanged);
  }, []);

  function choose(mode: AudienceMode) {
    localStorage.setItem(AUDIENCE_STORAGE_KEY, mode);
    localStorage.setItem(ONBOARDING_KEY, "1");
    applyAudienceMode(mode);
    window.dispatchEvent(new CustomEvent(AUDIENCE_CHANGED_EVENT, { detail: { mode } }));
    setOpen(false);
  }

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-glass-scrim backdrop-blur-glass-sm">
      <div className="relative w-full max-w-xl bg-glass-modal-bg backdrop-blur-glass-md rounded-2xl shadow-glass-lg border border-glass-modal-border overflow-hidden">
        <div className="h-1 w-full bg-sun-yellow" />

        <div className="px-8 pt-7 pb-8">
          <p className="text-xs font-semibold uppercase tracking-widest text-sun-amber mb-2">
            Personalise your experience
          </p>
          <h2 className="text-2xl font-bold text-sun-dark mb-2 leading-tight">
            How would you like to<br />explore this course?
          </h2>
          <p className="text-sm text-sun-muted mb-6">
            Pages with dual-audience content will show or hide sections based on your choice. You can change this any time.
          </p>

          <div className="grid grid-cols-2 gap-3 mb-5">
            {/* Business card */}
            <button
              onClick={() => choose("biz")}
              className="group text-left rounded-xl border-2 border-sun-yellow-bdr hover:border-blue-400 hover:bg-blue-50 transition-all p-4"
            >
              <div className="text-2xl mb-2">🏢</div>
              <p className="font-semibold text-sun-dark text-sm mb-1 group-hover:text-blue-700">Business</p>
              <p className="text-xs text-sun-muted leading-relaxed">
                Strategy, concepts and real-world applications - no code required
              </p>
              <div className="mt-3 flex items-center gap-1">
                <span className="inline-block w-2 h-3 rounded-sm bg-blue-400" />
                <span className="text-[10px] text-sun-muted">Blue sections visible</span>
              </div>
            </button>

            {/* Technical card */}
            <button
              onClick={() => choose("tech")}
              className="group text-left rounded-xl border-2 border-sun-yellow-bdr hover:border-sun-yellow hover:bg-sun-yellow-dim transition-all p-4"
            >
              <div className="text-2xl mb-2">⚙️</div>
              <p className="font-semibold text-sun-dark text-sm mb-1 group-hover:text-sun-amber">Technical</p>
              <p className="text-xs text-sun-muted leading-relaxed">
                Code, APIs and implementation details - hands-on and in-depth
              </p>
              <div className="mt-3 flex items-center gap-1">
                <span className="inline-block w-2 h-3 rounded-sm bg-sun-yellow" />
                <span className="text-[10px] text-sun-muted">Yellow sections visible</span>
              </div>
            </button>
          </div>

          <div className="text-center">
            <button
              onClick={() => choose("all")}
              className="text-sm text-sun-muted hover:text-sun-dark transition-colors underline underline-offset-2"
            >
              Show me everything
            </button>
            <p className="text-xs text-sun-muted mt-2 opacity-60">
              This preference is saved in your browser and applies across all pages.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
