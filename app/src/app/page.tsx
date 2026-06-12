import Link from "next/link";
import { getNavigationTree } from "@/lib/content/nav";

const MODULE_META: Record<string, { subtitle: string; description: string; notes: string; qa: string; num: string }> = {
  "llm-models":         { num: "01", subtitle: "The Engine",    description: "How LLMs work - architecture, attention, training, inference, and production deployment.", notes: "12 notes", qa: "68+ Q&A" },
  "prompt-engineering": { num: "02", subtitle: "The Interface", description: "Prompting strategies, chain-of-thought, few-shot, and production-grade prompt optimization.", notes: "6 notes",  qa: "65+ Q&A" },
  "rag":                { num: "03", subtitle: "The Memory",    description: "Embeddings, vector stores, chunking, retrieval strategies, and advanced RAG architectures.", notes: "12 notes", qa: "80+ Q&A" },
  "mcp":                { num: "04", subtitle: "The Protocol",  description: "Model Context Protocol - how AI systems talk to tools, APIs, and external services.", notes: "9 notes",  qa: "40+ Q&A" },
  "agents":             { num: "05", subtitle: "The Actors",    description: "Agent fundamentals and patterns across GCP ADK, LangChain, LangGraph, and CrewAI.", notes: "8 notes",  qa: "50+ Q&A" },
  "agentic-ai":         { num: "06", subtitle: "The Systems",   description: "Multi-agent systems, planning, memory, evaluation, and full agentic system design.", notes: "12 notes", qa: "60+ Q&A" },
};

const LEARNING_PATHS = [
  { label: "A", title: "Conceptual",     desc: "New to GenAI - start here for a guided overview" },
  { label: "B", title: "Interview Prep", desc: "Accelerated deep-dive through Q&A banks" },
  { label: "C", title: "Hands-On",       desc: "Code labs across 4 frameworks" },
  { label: "D", title: "Full Sequence",  desc: "Complete curriculum from LLMs to Agentic AI" },
];

const STACK_PILLS = ["LLMs", "Prompts", "RAG", "MCP", "Agents", "Agentic AI"];

export default function HomePage() {
  const nav = getNavigationTree();

  return (
    <div className="min-h-screen flex flex-col">

      {/* ── Header ─────────────────────────────────────────────────────── */}
      <header className="bg-white border-b-2 border-sun-yellow px-4 sm:px-6 h-13 flex items-center justify-between gap-3 sticky top-0 z-40">
        <span className="font-bold text-sun-dark tracking-tight text-sm">Learn GenAI</span>
        <div className="flex items-center gap-2">
          <a
            href="https://github.com/sundante/sun-course-genai"
            target="_blank"
            rel="noopener noreferrer"
            className="hidden sm:inline-flex items-center gap-1.5 text-xs font-semibold bg-sun-yellow text-sun-dark hover:bg-sun-yellow-dk rounded-md px-2.5 py-1 transition-colors"
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" /></svg>
            Github
          </a>
          <a
            href="https://sunmintz.com/"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center text-xs font-semibold bg-sun-yellow text-sun-dark hover:bg-sun-yellow-dk rounded-md px-3 py-1.5 transition-colors"
          >
            sunmintz.com
          </a>
        </div>
      </header>

      {/* ── Hero ───────────────────────────────────────────────────────── */}
      <section className="bg-sun-dark text-white px-4 sm:px-6 py-10 border-b-2 border-sun-yellow">
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

          {/* Stack pills */}
          <div className="flex flex-wrap justify-center gap-2 mb-7">
            {STACK_PILLS.map((pill, i) => (
              <span key={pill} className="flex items-center gap-1.5 text-xs font-medium text-white/80">
                <span className="bg-white/10 border border-white/20 rounded px-2 py-0.5">{pill}</span>
                {i < STACK_PILLS.length - 1 && <span className="text-sun-yellow text-xs">→</span>}
              </span>
            ))}
          </div>

          <div className="flex gap-3 justify-center flex-wrap">
            <Link
              href="/learn/llm-models/index"
              className="inline-flex items-center text-sm font-semibold bg-sun-yellow text-sun-dark hover:bg-sun-yellow-dk rounded-lg px-5 py-2 transition-colors"
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

      {/* ── Module Grid ────────────────────────────────────────────────── */}
      <section className="px-4 sm:px-6 py-8 bg-sun-bg">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-xs font-bold uppercase tracking-widest text-sun-muted mb-4">Curriculum</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {nav.modules.filter(m => MODULE_META[m.slug]).map((mod) => {
              const meta = MODULE_META[mod.slug];
              const firstLeaf = mod.items.find(i => i.filePath);
              const firstSlug = firstLeaf?.filePath?.split("/").pop()?.replace(".md", "").toLowerCase().replace(/_/g, "-");
              const href = firstSlug ? `/learn/${mod.slug}/${firstSlug}` : "#";

              return (
                <Link
                  key={mod.slug}
                  href={href}
                  className="group block p-4 rounded-xl border border-sun-yellow-bdr bg-white hover:border-sun-yellow hover:shadow-md hover:-translate-y-0.5 transition-all duration-150"
                >
                  <div className="flex items-start justify-between mb-2">
                    <span className="text-xs font-mono text-sun-muted">{meta.num}</span>
                    <span className="text-xs font-semibold text-sun-amber bg-sun-yellow-dim px-2 py-0.5 rounded-full">
                      {meta.subtitle}
                    </span>
                  </div>
                  <h3 className="font-semibold text-sun-dark mb-1.5 group-hover:text-sun-amber transition-colors">
                    {mod.title}
                  </h3>
                  <p className="text-xs text-sun-muted leading-relaxed mb-3">{meta.description}</p>
                  <div className="flex gap-2">
                    <span className="text-xs bg-gray-100 text-sun-muted rounded px-2 py-0.5">{meta.notes}</span>
                    <span className="text-xs bg-gray-100 text-sun-muted rounded px-2 py-0.5">{meta.qa}</span>
                  </div>
                </Link>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── Stats Strip ────────────────────────────────────────────────── */}
      <section className="bg-sun-yellow px-4 sm:px-6 py-5">
        <div className="max-w-5xl mx-auto flex flex-wrap justify-center sm:justify-between gap-4">
          {[
            ["150+", "Deep-dive notes"],
            ["4",    "Agent frameworks"],
            ["298+", "Interview Q&A"],
            ["Free", "Always"],
          ].map(([stat, label]) => (
            <div key={label} className="text-center">
              <div className="text-xl font-bold text-sun-dark">{stat}</div>
              <div className="text-xs font-medium text-sun-dark/70">{label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── Learning Paths ─────────────────────────────────────────────── */}
      <section className="px-4 sm:px-6 py-8 bg-sun-bg border-t border-sun-yellow-bdr">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-xs font-bold uppercase tracking-widest text-sun-muted mb-4">Learning Paths</h2>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {LEARNING_PATHS.map((path) => (
              <div key={path.label} className="p-4 rounded-xl border border-sun-yellow-bdr bg-white">
                <div className="w-7 h-7 rounded-full bg-sun-yellow text-sun-dark text-xs font-bold flex items-center justify-center mb-2">
                  {path.label}
                </div>
                <div className="font-semibold text-sun-dark text-sm mb-1">{path.title}</div>
                <div className="text-xs text-sun-muted leading-relaxed">{path.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Footer ─────────────────────────────────────────────────────── */}
      <footer className="bg-sun-dark text-white/60 px-4 sm:px-6 py-6 mt-auto border-t-2 border-sun-yellow">
        <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
          <span>© 2026 <a href="https://sunmintz.com/" className="text-sun-yellow hover:text-white transition-colors">sunmintz.com</a>. Built by Suryaprakash Singh.</span>
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
