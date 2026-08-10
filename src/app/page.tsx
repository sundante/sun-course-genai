import Link from "next/link";
import { getNavigationTree } from "@/lib/content/nav";
import { ThemeToggle } from "@/components/course/ThemeToggle";
import { CurriculumTiles } from "@/components/course/CurriculumTiles";

const LEARNING_PATHS = [
  { label: "A", title: "Conceptual",     desc: "New to GenAI - start here for a guided conceptual overview of the full stack." },
  { label: "B", title: "Interview Prep", desc: "Accelerated deep-dive through Q&A banks to ace GenAI engineering interviews." },
  { label: "C", title: "Hands-On",       desc: "Code labs across 4 agent frameworks: LangChain, LangGraph, CrewAI, GCP ADK." },
  { label: "D", title: "Full Sequence",  desc: "Complete curriculum from LLMs to Platform Breadth and PyTorch fundamentals - the recommended path." },
];

const FEATURES = [
  { icon: "01", title: "180+ deep-dive notes",  desc: "Zero fluff, dual-audience (business and technical) explanations for every concept." },
  { icon: "02", title: "370+ interview Q&A",     desc: "Pulled from real hiring loops, organized by module for targeted prep." },
  { icon: "03", title: "Hands-on code labs",     desc: "LangChain, LangGraph, CrewAI and GCP ADK - ship real agents, not slides." },
  { icon: "04", title: "Real benchmarks",        desc: "Base-vs-tuned comparisons with actual numbers, not just theory." },
];

const PATH_STEPS = [
  { n: "1", label: "Foundations",     desc: "LLMs, Prompts, RAG, MCP" },
  { n: "2", label: "Agentic Systems", desc: "Agents, multi-agent design" },
  { n: "3", label: "Production Skills", desc: "Fine-tuning, serving, ops" },
  { n: "4", label: "Platform Mastery", desc: "Cloud AI stacks, PyTorch" },
];

const STATS: [string, string][] = [
  ["180+", "Deep-dive notes"],
  ["12", "Modules"],
  ["370+", "Interview Q&A"],
  ["Free", "Always"],
];

const LANDING_NAV = [
  { href: "#features", label: "Features" },
  { href: "#path", label: "Path" },
  { href: "#curriculum", label: "Curriculum" },
  { href: "#paths", label: "Learning Paths" },
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
      <header className="bg-white border-b border-sun-yellow px-4 sm:px-6 h-14 flex items-center justify-between gap-3 sticky top-0 z-40">
        <a href="#top" className="font-bold text-sun-dark tracking-tight text-sm shrink-0">
          Learn GenAI
        </a>
        <nav className="hidden lg:flex items-center gap-5 text-xs font-semibold">
          {LANDING_NAV.map((item) => (
            <a
              key={item.href}
              href={item.href}
              className="text-sun-dark hover:text-sun-amber transition-colors"
            >
              {item.label}
            </a>
          ))}
        </nav>
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <a
            href="https://github.com/sundante/sun-course-genai"
            target="_blank" rel="noopener noreferrer"
            className="hidden sm:inline-flex items-center gap-1.5 text-xs font-semibold bg-sun-yellow text-zinc-900 hover:bg-sun-yellow-dk rounded-md px-2.5 py-1.5 transition-colors"
          >
            <StarSvg /> Github
          </a>
          <a
            href="https://suryaprakash.sunmintz.com/"
            target="_blank" rel="noopener noreferrer"
            className="hidden sm:inline-flex items-center text-xs font-semibold bg-sun-yellow text-zinc-900 hover:bg-sun-yellow-dk rounded-md px-3 py-1.5 transition-colors"
          >
            Author
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

      {/* Hero - full-width, centered, decorative radial glow behind the
          headline (theme-reactive via --sun-yellow-dim, no fixed colors) */}
      <section id="top" className="relative overflow-hidden px-4 sm:px-6 pt-14 pb-10 sm:pt-20 sm:pb-14 scroll-mt-14">
        <div
          className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[420px]"
          style={{ background: "radial-gradient(circle at 50% 0%, var(--sun-yellow-dim), transparent 65%)" }}
          aria-hidden="true"
        />
        <div className="max-w-3xl mx-auto text-center">
          <span className="inline-flex items-center text-xs font-bold uppercase tracking-widest text-sun-amber bg-sun-yellow-dim border border-sun-yellow-bdr rounded-full px-3 py-1">
            Generative AI to Agentic AI
          </span>
          <h1 className="mt-4 text-4xl sm:text-5xl font-bold tracking-tight leading-[1.1] text-sun-dark">
            Master the Full Modern{" "}
            <span className="text-sun-amber">GenAI Stack</span>
          </h1>
          <p className="mt-4 text-base sm:text-lg text-sun-muted leading-relaxed max-w-2xl mx-auto">
            A structured, practical curriculum from foundational LLMs to fully autonomous Agentic systems - built by an engineer who shipped this stuff in production, not just read about it.
          </p>
          <div className="mt-7 flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link
              href="/learn/llm-models/index"
              className="inline-flex items-center justify-center text-sm font-semibold bg-sun-yellow text-zinc-900 hover:bg-sun-yellow-dk rounded-lg px-6 py-2.5 shadow-glass-sm transition-colors w-full sm:w-auto"
            >
              Start Learning →
            </Link>
            <Link
              href="/quiz/all"
              className="inline-flex items-center justify-center text-sm font-semibold text-sun-dark border border-glass-card-border hover:border-sun-yellow-bdr hover:bg-glass-panel-bg rounded-lg px-6 py-2.5 transition-colors w-full sm:w-auto"
            >
              Practice Quiz
            </Link>
          </div>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-x-8 gap-y-2 text-sm text-sun-muted">
            {STATS.map(([stat, label], i) => (
              <span key={label} className="inline-flex items-center gap-2">
                {i > 0 && <span className="hidden sm:inline text-glass-card-border">|</span>}
                <span className="font-bold text-sun-dark">{stat}</span> {label}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* Feature grid */}
      <section id="features" className="px-4 sm:px-6 pb-12 sm:pb-16 scroll-mt-20">
        <div className="max-w-6xl mx-auto grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
          {FEATURES.map((f) => (
            <div
              key={f.title}
              className="p-4 sm:p-5 rounded-xl border border-glass-card-border bg-glass-card-bg backdrop-blur-glass-sm shadow-glass-sm"
            >
              <span className="text-xs font-mono text-sun-amber font-semibold">{f.icon}</span>
              <div className="font-semibold text-sun-dark text-sm mt-2 mb-1">{f.title}</div>
              <div className="text-xs text-sun-muted leading-relaxed">{f.desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Your Path - horizontal stepper connecting the feature grid to the
          curriculum browser below */}
      <section id="path" className="px-4 sm:px-6 pb-12 sm:pb-16 scroll-mt-20">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-xs font-bold uppercase tracking-widest text-sun-muted mb-4 text-center">Your Path</h2>
          <div className="relative grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="hidden lg:block absolute top-4 left-[12.5%] right-[12.5%] h-px bg-glass-card-border" aria-hidden="true" />
            {PATH_STEPS.map((step) => (
              <div key={step.n} className="relative flex flex-col items-center text-center gap-2">
                <span className="flex items-center justify-center w-8 h-8 rounded-full bg-sun-yellow text-zinc-900 text-xs font-bold shrink-0 shadow-glass-sm z-10">
                  {step.n}
                </span>
                <div>
                  <div className="font-semibold text-sun-dark text-sm">{step.label}</div>
                  <div className="text-xs text-sun-muted mt-0.5">{step.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Curriculum browser */}
      <section id="curriculum" className="px-4 sm:px-6 pb-14 sm:pb-20 scroll-mt-20">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-5">
            <h2 className="text-xs font-bold uppercase tracking-widest text-sun-muted mb-2">Curriculum</h2>
            <p className="text-2xl font-bold text-sun-dark tracking-tight">Eleven modules, start to finish</p>
          </div>
          <CurriculumTiles modules={modules} />
        </div>
      </section>

      {/* Learning paths */}
      <section id="paths" className="px-4 sm:px-6 pb-14 sm:pb-20 scroll-mt-20">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-xs font-bold uppercase tracking-widest text-sun-muted mb-4 text-center">Learning Paths</h2>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
            {LEARNING_PATHS.map((path) => (
              <div key={path.label} className="p-4 sm:p-5 rounded-xl border border-glass-card-border bg-glass-card-bg backdrop-blur-glass-sm shadow-glass-sm">
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

      {/* CTA banner */}
      <section id="start" className="px-4 sm:px-6 pb-14 sm:pb-20 scroll-mt-20">
        <div className="max-w-6xl mx-auto rounded-2xl bg-zinc-900 text-white px-6 sm:px-10 py-10 sm:py-12 text-center">
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight mb-2">Ready to go from GenAI to Agentic AI?</h2>
          <p className="text-white/70 text-sm sm:text-base max-w-xl mx-auto mb-6">
            100% free, always up to date, built from production experience - not a rehash of documentation.
          </p>
          <Link
            href="/learn/llm-models/index"
            className="inline-flex items-center justify-center text-sm font-semibold bg-sun-yellow text-zinc-900 hover:bg-sun-yellow-dk rounded-lg px-6 py-2.5 transition-colors"
          >
            Start Learning →
          </Link>
        </div>
      </section>

      {/* Footer - theme-invariant dark bg, fixed text colors */}
      <footer className="bg-zinc-900 text-white/60 px-4 sm:px-6 py-5 mt-auto">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
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
