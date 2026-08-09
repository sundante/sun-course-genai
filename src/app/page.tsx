import Link from "next/link";
import { getNavigationTree } from "@/lib/content/nav";
import { ThemeToggle } from "@/components/course/ThemeToggle";
import { CurriculumTiles } from "@/components/course/CurriculumTiles";

const LEARNING_PATHS = [
  { label: "A", title: "Conceptual",     desc: "New to GenAI — start here for a guided conceptual overview of the full stack." },
  { label: "B", title: "Interview Prep", desc: "Accelerated deep-dive through Q&A banks to ace GenAI engineering interviews." },
  { label: "C", title: "Hands-On",       desc: "Code labs across 4 agent frameworks: LangChain, LangGraph, CrewAI, GCP ADK." },
  { label: "D", title: "Full Sequence",  desc: "Complete curriculum from LLMs to Platform Breadth and PyTorch fundamentals — the recommended path." },
];

function StarSvg() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
    </svg>
  );
}

export default function HomePage() {
  const { modules } = getNavigationTree();

  return (
    <div className="min-h-screen flex flex-col bg-sun-bg">
      {/* Header */}
      <header className="bg-glass-nav-bg backdrop-blur-glass-md border-b-2 border-sun-yellow px-4 sm:px-6 h-13 flex items-center justify-between gap-3 sticky top-0 z-40 shadow-glass-sm">
        <span className="font-bold text-sun-dark tracking-tight text-sm">Learn GenAI</span>
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <a
            href="https://github.com/sundante/sun-course-genai"
            target="_blank" rel="noopener noreferrer"
            className="hidden sm:inline-flex items-center gap-1.5 text-xs font-semibold bg-sun-yellow text-zinc-900 hover:bg-sun-yellow-dk rounded-md px-2.5 py-1 transition-colors"
          >
            <StarSvg /> Github
          </a>
          <a
            href="https://sunmintz.com/"
            target="_blank" rel="noopener noreferrer"
            className="inline-flex items-center text-xs font-semibold bg-sun-yellow text-zinc-900 hover:bg-sun-yellow-dk rounded-md px-3 py-1.5 transition-colors"
          >
            sunmintz.com
          </a>
        </div>
      </header>

      {/* Hero - intentionally theme-invariant (bg-zinc-900, not the reactive
          --sun-dark token, which inverts to near-white in dark mode and would
          make the hardcoded text-white illegible - same fix as the lesson-page
          title banner, see Section 4/8 in vibes/glass-ui-redesign-checklist.md) */}
      <section className="bg-zinc-900 text-white px-4 sm:px-6 py-10 border-b-2 border-sun-yellow">
        <div className="max-w-3xl mx-auto text-center">
          <p className="text-xs font-bold uppercase tracking-widest text-sun-yellow mb-3">
            Learn AI: Generative AI to Agentic AI
          </p>
          <h1 className="text-3xl sm:text-4xl font-bold mb-3 tracking-tight leading-tight">
            Master the Full Modern{" "}
            <span className="text-sun-yellow">GenAI Stack</span>
          </h1>
          <p className="text-white/70 text-sm sm:text-base mb-6 leading-relaxed max-w-xl mx-auto">
            A structured, practical curriculum from foundational LLMs to fully autonomous Agentic systems.
          </p>

          <div className="flex flex-wrap justify-center gap-2 mb-7">
            {["LLMs", "Prompts", "RAG", "MCP", "Agents", "Agentic AI"].map((pill, i, arr) => (
              <span key={pill} className="flex items-center gap-1.5 text-xs font-medium text-white/80">
                <span className="bg-white/10 border border-white/20 rounded px-2 py-0.5">{pill}</span>
                {i < arr.length - 1 && <span className="text-sun-yellow text-xs">→</span>}
              </span>
            ))}
          </div>

          <div className="flex gap-3 justify-center flex-wrap">
            <Link
              href="/learn/llm-models/index"
              className="inline-flex items-center text-sm font-semibold bg-sun-yellow text-zinc-900 hover:bg-sun-yellow-dk rounded-lg px-5 py-2 transition-colors"
            >
              Start Learning
            </Link>
            <Link
              href="/quiz/all"
              className="inline-flex items-center text-sm font-semibold text-white border border-white/25 hover:border-white/60 hover:bg-white/10 rounded-lg px-5 py-2 transition-colors"
            >
              Practice Quiz
            </Link>
          </div>
        </div>
      </section>

      {/* Module grid - expandable/collapsible tiles, each a single toggle button
          revealing that module's Concepts as clickable links */}
      <section className="px-4 sm:px-6 py-8 bg-sun-bg">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-xs font-bold uppercase tracking-widest text-sun-muted mb-5">Curriculum</h2>
          <CurriculumTiles modules={modules} />
        </div>
      </section>

      {/* Stats strip - bg-sun-yellow is theme-invariant, so the text inside
          uses fixed zinc-900 rather than the reactive text-sun-dark token,
          which would invert to near-white and be unreadable on yellow in dark
          mode (same class of bug as the hero/banner fixes above) */}
      <section className="bg-sun-yellow px-4 sm:px-6 py-5">
        <div className="max-w-5xl mx-auto flex flex-wrap justify-center sm:justify-between gap-4">
          {[["180+", "Deep-dive notes"], ["12", "Modules"], ["370+", "Interview Q&A"], ["Free", "Always"]].map(([stat, label]) => (
            <div key={label} className="text-center">
              <div className="text-xl font-bold text-zinc-900">{stat}</div>
              <div className="text-xs font-medium text-zinc-900/70">{label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Learning paths */}
      <section className="px-4 sm:px-6 py-8 bg-sun-bg border-t border-sun-yellow-bdr">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-xs font-bold uppercase tracking-widest text-sun-muted mb-4">Learning Paths</h2>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {LEARNING_PATHS.map((path) => (
              <div key={path.label} className="p-4 rounded-xl border border-glass-card-border bg-glass-card-bg backdrop-blur-glass-sm shadow-glass-sm">
                <div className="w-7 h-7 rounded-full bg-sun-yellow text-zinc-900 text-xs font-bold flex items-center justify-center mb-2">
                  {path.label}
                </div>
                <div className="font-semibold text-sun-dark text-sm mb-1">{path.title}</div>
                <div className="text-xs text-sun-muted leading-relaxed">{path.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer - theme-invariant dark bg, same fix as hero/banner above */}
      <footer className="bg-zinc-900 text-white/60 px-4 sm:px-6 py-6 mt-auto border-t-2 border-sun-yellow">
        <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
          <span>
            © 2026{" "}
            <a href="https://sunmintz.com/" className="text-sun-yellow hover:text-white transition-colors">
              sunmintz.com
            </a>. Built by Suryaprakash Singh.
          </span>
          <div className="flex items-center gap-4">
            <a href="https://github.com/sundante/sun-course-genai" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">GitHub</a>
            <a href="https://www.linkedin.com/in/suryaprakash-s-singh/" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">LinkedIn</a>
            <a href="https://x.com/sunsindante" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">X / Twitter</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
