"use client";

import { createContext, useCallback, useContext, useId, useMemo, useState, type ReactNode } from "react";
import { Check, RotateCcw, X } from "lucide-react";

// Interactive rendering of a ```quiz fence (see remarkCourseFences.ts). The server
// renders the question/option/explanation Markdown; these components only add state.

type Result = "correct" | "incorrect" | "revealed";

interface QuizState {
  results: Record<string, Result>;
  record: (id: string, result: Result | null) => void;
  resetKey: number;
}

const QuizContext = createContext<QuizState | null>(null);

interface QuestionState {
  answer: number | null; // 1-based; null for free-text questions
  selected: number | null;
  revealed: boolean;
  select: (index: number) => void;
}

const QuestionContext = createContext<QuestionState | null>(null);

export function QuizBlock({ children, total }: { children: ReactNode; total: number }) {
  const [results, setResults] = useState<Record<string, Result>>({});
  const [resetKey, setResetKey] = useState(0);

  const record = useCallback((id: string, result: Result | null) => {
    setResults((prev) => {
      const next = { ...prev };
      if (result) next[id] = result;
      else delete next[id];
      return next;
    });
  }, []);

  const graded = Object.values(results).filter((r) => r !== "revealed");
  const correct = graded.filter((r) => r === "correct").length;
  const value = useMemo(() => ({ results, record, resetKey }), [results, record, resetKey]);

  return (
    <QuizContext.Provider value={value}>
      <div className="cf-quiz my-6 rounded-xl border border-glass-card-border bg-glass-card-bg shadow-glass-sm overflow-hidden">
        <div className="not-prose flex items-center justify-between gap-3 px-4 py-2.5 border-b border-glass-card-border bg-glass-panel-bg">
          <span className="text-xs font-bold uppercase tracking-widest text-sun-amber">Check yourself</span>
          <div className="flex items-center gap-3">
            <span className="text-xs text-sun-muted tabular-nums" aria-live="polite">
              {Object.keys(results).length} / {total} answered
              {graded.length > 0 && ` · ${correct} correct`}
            </span>
            {Object.keys(results).length > 0 && (
              <button
                type="button"
                onClick={() => {
                  setResults({});
                  setResetKey((k) => k + 1);
                }}
                className="inline-flex items-center gap-1 text-xs font-semibold text-sun-muted hover:text-sun-amber transition-colors"
              >
                <RotateCcw className="h-3 w-3" aria-hidden="true" /> Reset
              </button>
            )}
          </div>
        </div>
        <ol className="cf-quiz-list list-none m-0 p-0 divide-y divide-glass-card-border">{children}</ol>
      </div>
    </QuizContext.Provider>
  );
}

export function QuizQuestion({ children, answer }: { children: ReactNode; answer?: string }) {
  const quiz = useContext(QuizContext);
  const id = useId();
  const [selected, setSelected] = useState<number | null>(null);
  const [revealed, setRevealed] = useState(false);
  const [seenReset, setSeenReset] = useState(quiz?.resetKey ?? 0);
  const correctIndex = answer ? Number(answer) : null;

  // Reset local state when the block-level Reset is pressed
  if (quiz && quiz.resetKey !== seenReset) {
    setSeenReset(quiz.resetKey);
    setSelected(null);
    setRevealed(false);
  }

  const select = useCallback(
    (index: number) => {
      if (correctIndex === null) {
        setRevealed(true);
        quiz?.record(id, "revealed");
        return;
      }
      setSelected(index);
      setRevealed(true);
      quiz?.record(id, index === correctIndex ? "correct" : "incorrect");
    },
    [correctIndex, id, quiz]
  );

  const value = useMemo(
    () => ({ answer: correctIndex, selected, revealed, select }),
    [correctIndex, selected, revealed, select]
  );

  return (
    <QuestionContext.Provider value={value}>
      <li className="cf-question m-0 px-4 py-4 [&>*:first-child]:mt-0">
        {children}
        {correctIndex === null && !revealed && (
          <button
            type="button"
            onClick={() => select(0)}
            className="not-prose mt-2 text-xs font-semibold text-sun-amber border border-sun-yellow-bdr hover:bg-sun-yellow-dim rounded-md px-3 py-1.5 transition-colors"
          >
            Show answer
          </button>
        )}
      </li>
    </QuestionContext.Provider>
  );
}

export function QuizPrompt({ children }: { children: ReactNode }) {
  return <div className="cf-prompt font-semibold text-sun-dark mb-2 [&_p]:my-1">{children}</div>;
}

export function QuizOption({ children, index }: { children: ReactNode; index: string }) {
  const q = useContext(QuestionContext);
  const n = Number(index);
  if (!q) return <div>{children}</div>;

  const isCorrect = q.revealed && n === q.answer;
  const isWrongPick = q.revealed && n === q.selected && n !== q.answer;
  const state = isCorrect
    ? "border-emerald-500 bg-emerald-500/10 text-sun-dark"
    : isWrongPick
      ? "border-sun-coral-bdr bg-sun-coral-dim text-sun-coral-text"
      : "border-glass-card-border hover:border-sun-yellow-bdr hover:bg-sun-yellow-dim text-sun-dark";

  return (
    <button
      type="button"
      onClick={() => q.select(n)}
      aria-pressed={q.selected === n}
      className={`cf-option w-full flex items-start gap-2.5 text-left text-sm rounded-lg border px-3 py-2 my-1.5 transition-colors ${state}`}
    >
      <span className="shrink-0 w-5 text-xs font-mono font-bold text-sun-muted pt-px">
        {String.fromCharCode(64 + n)}
      </span>
      <span className="flex-1 min-w-0 [&_p]:m-0">{children}</span>
      {isCorrect && <Check className="h-4 w-4 shrink-0 text-emerald-600 dark:text-emerald-400" aria-label="Correct" />}
      {isWrongPick && <X className="h-4 w-4 shrink-0" aria-label="Incorrect" />}
    </button>
  );
}

/** Explanation (and free-text model answer) - shown once the question is answered. */
export function QuizReveal({ children, label }: { children: ReactNode; label: string }) {
  const q = useContext(QuestionContext);
  if (!q?.revealed) return null;
  return (
    <div className="mt-3 rounded-lg border-l-2 border-sun-yellow bg-glass-panel-bg px-3 py-2 text-sm [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
      <span className="not-prose block text-[10px] font-bold uppercase tracking-widest text-sun-muted mb-1">{label}</span>
      {children}
    </div>
  );
}
