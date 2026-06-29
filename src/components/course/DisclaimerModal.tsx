"use client";

import { useState, useEffect } from "react";

const STORAGE_KEY = "genai_disclaimer_v1";
export const OPEN_DISCLAIMER_EVENT = "open-disclaimer-modal";

export function DisclaimerModal() {
  const [modalOpen, setModalOpen] = useState(false);

  useEffect(() => {
    const seen = localStorage.getItem(STORAGE_KEY);
    if (!seen) setModalOpen(true);

    function handleOpen() { setModalOpen(true); }
    window.addEventListener(OPEN_DISCLAIMER_EVENT, handleOpen);
    return () => window.removeEventListener(OPEN_DISCLAIMER_EVENT, handleOpen);
  }, []);

  function dismiss() {
    localStorage.setItem(STORAGE_KEY, "1");
    setModalOpen(false);
  }

  if (!modalOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm"
      onClick={(e) => { if (e.target === e.currentTarget) dismiss(); }}
    >
      <div className="relative w-full max-w-lg bg-white rounded-2xl shadow-2xl border border-sun-yellow-bdr overflow-hidden">
        <div className="h-1 w-full bg-sun-yellow" />

        <div className="px-8 pt-7 pb-8">
          <p className="text-xs font-semibold uppercase tracking-widest text-sun-amber mb-2">
            A note before you start
          </p>
          <h2 className="text-2xl font-bold text-sun-dark mb-5 leading-tight">
            Built with the Tools<br />You&apos;re Learning
          </h2>

          <p className="text-sm text-sun-muted leading-relaxed mb-4">
            The concepts, examples, and explanations in this course were drafted using
            Generative AI - the same technology you&apos;re here to understand. Each page
            was reviewed before publishing, but AI makes mistakes, knowledge evolves,
            and no single source tells the whole story.
          </p>

          <div className="bg-sun-bg rounded-xl p-4 mb-5 border border-sun-yellow-bdr">
            <p className="text-xs font-semibold uppercase tracking-wider text-sun-amber mb-2.5">
              What this means for you
            </p>
            <ul className="space-y-1.5 text-sm text-sun-dark">
              <li className="flex gap-2">
                <span className="text-sun-amber shrink-0">→</span>
                Use this as a starting point, not a final word
              </li>
              <li className="flex gap-2">
                <span className="text-sun-amber shrink-0">→</span>
                Cross-reference anything that matters to your work
              </li>
              <li className="flex gap-2">
                <span className="text-sun-amber shrink-0">→</span>
                Curiosity and critical thinking are the skills that compound fastest
              </li>
            </ul>
          </div>

          <p className="text-sm text-sun-muted leading-relaxed mb-6">
            Learning in the age of Generative AI isn&apos;t about finding one authoritative
            source - it&apos;s about triangulating across many.
          </p>

          <button
            onClick={dismiss}
            className="w-full bg-sun-yellow hover:bg-sun-yellow/80 text-sun-dark font-semibold py-3 px-6 rounded-xl transition-colors text-sm"
          >
            I&apos;m curious - let&apos;s explore
          </button>

          <p className="text-center text-xs text-sun-muted mt-3">
            You can always revisit this from the footer of any page.
          </p>
        </div>
      </div>
    </div>
  );
}
