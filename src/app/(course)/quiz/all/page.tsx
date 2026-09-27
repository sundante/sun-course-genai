import Link from "next/link";
import { getQuizIndex } from "@/lib/content/quizzes";

export const metadata = { title: "Quizzes | Learn GenAI" };

export default function QuizAllPage() {
  const index = getQuizIndex().filter((entry) => entry.questions > 0);
  const total = index.reduce((sum, entry) => sum + entry.questions, 0);

  // Group by track, keeping nav order
  const tracks: { track: string; entries: typeof index }[] = [];
  for (const entry of index) {
    const track = entry.module.track ?? "Other";
    const group = tracks.find((t) => t.track === track);
    if (group) group.entries.push(entry);
    else tracks.push({ track, entries: [entry] });
  }

  return (
    <div className="flex flex-col min-h-full">
      <div className="bg-white border-b border-sun-yellow px-6 lg:px-8 py-3">
        <p className="text-xs font-bold uppercase tracking-widest text-sun-amber mb-0.5">Practice</p>
        <h1 className="text-base font-bold text-sun-dark tracking-tight leading-tight">
          Module quizzes · {total} questions
        </h1>
      </div>

      <div className="flex-1 px-6 lg:px-8 py-6 max-w-5xl">
        <p className="text-sm text-sun-muted mb-6">
          Each quiz collects the <em>Check Yourself</em> questions from a module&apos;s pages. Multiple-choice
          questions are graded as you answer; open questions reveal a model answer.
        </p>
        {tracks.map(({ track, entries }) => (
          <section key={track} className="mb-8">
            <h2 className="text-xs font-bold uppercase tracking-widest text-sun-muted mb-3">{track}</h2>
            <ul className="grid gap-3 sm:grid-cols-2">
              {entries.map(({ module: mod, questions, pages }) => (
                <li key={mod.slug}>
                  <Link
                    href={`/quiz/${mod.slug}`}
                    className="block rounded-xl border border-glass-card-border bg-glass-card-bg shadow-glass-sm px-4 py-3 hover:border-sun-yellow-bdr transition-colors"
                  >
                    <span className="block text-xs font-bold text-sun-amber tabular-nums">
                      {String(mod.number).padStart(2, "0")}
                    </span>
                    <span className="block text-sm font-semibold text-sun-dark">{mod.title}</span>
                    <span className="block text-xs text-sun-muted mt-1">
                      {questions} questions · {pages} {pages === 1 ? "page" : "pages"}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        ))}
      </div>
    </div>
  );
}
