"use client";

import { OPEN_DISCLAIMER_EVENT } from "./DisclaimerModal";

export function DisclaimerNote() {
  function openModal() {
    window.dispatchEvent(new CustomEvent(OPEN_DISCLAIMER_EVENT));
  }

  return (
    <div className="px-6 py-4 flex items-center justify-center gap-1.5 text-xs text-sun-coral-text/80">
      <span className="text-sun-coral">⚡</span>
      <span>
        <strong className="font-semibold text-sun-coral-text">AI-assisted content</strong>
        {" "}- always verify, always explore multiple perspectives
      </span>
      <span className="mx-1 text-sun-coral-bdr">·</span>
      <button
        onClick={openModal}
        className="text-sun-coral hover:text-sun-coral-text underline underline-offset-2 transition-colors font-medium whitespace-nowrap"
      >
        Why this matters ↗
      </button>
    </div>
  );
}
