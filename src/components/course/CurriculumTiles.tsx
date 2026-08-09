"use client";

import { useState } from "react";
import Link from "next/link";
import { ChevronDown } from "lucide-react";
import type { NavItem, NavModule } from "@/types/content";

interface ModuleMeta {
  num: string;
  subtitle: string;
  description: string;
  notes: string;
  qa: string;
}

const MODULE_META: Record<string, ModuleMeta> = {
  "llm-models":              { num: "01", subtitle: "The Engine",       description: "How large language models work under the hood - transformers, attention, training, fine-tuning, and inference optimization.", notes: "12 notes", qa: "68+ Q&A" },
  "prompt-engineering":      { num: "02", subtitle: "The Interface",    description: "The art and science of talking to models - from basics to advanced techniques and production prompt systems.", notes: "6 notes", qa: "65+ Q&A" },
  "rag":                     { num: "03", subtitle: "The Memory",       description: "Retrieval-Augmented Generation - how to give LLMs access to your own knowledge and keep answers grounded.", notes: "12 notes", qa: "80+ Q&A" },
  "mcp":                     { num: "04", subtitle: "The Protocol",     description: "Model Context Protocol - the emerging standard that lets AI models securely interact with tools, APIs, and data sources.", notes: "9 notes", qa: "40+ Q&A" },
  "agents":                  { num: "05", subtitle: "The Actors",       description: "AI agents and frameworks - LangChain, LangGraph, CrewAI, and GCP ADK from simple to complex agent architectures.", notes: "8 notes", qa: "50+ Q&A" },
  "agentic-ai":              { num: "06", subtitle: "The Systems",      description: "Full agentic AI systems - architectural patterns, multi-agent coordination, evaluation, and production deployment.", notes: "12 notes", qa: "60+ Q&A" },
  "fine-tuning-lab":         { num: "07", subtitle: "The Specialist",   description: "Hands-on LoRA/QLoRA fine-tuning - the HuggingFace ecosystem, instruction data, training runs, and a real base-vs-tuned benchmark.", notes: "5 notes", qa: "20+ Q&A" },
  "serving-and-inference":   { num: "08", subtitle: "The Delivery",     description: "Serving models in production - vLLM, paged attention, quantized inference, batching, and streaming latency.", notes: "5 notes", qa: "20+ Q&A" },
  "production-engineering":  { num: "09", subtitle: "The Operations",   description: "Docker, Kubernetes and Helm for GPU inference, model lifecycle and rollout, and security & compliance controls.", notes: "5 notes", qa: "25+ Q&A" },
  "platform-breadth":        { num: "10", subtitle: "The Landscape",    description: "AWS Bedrock, Databricks & Spark, and Azure AI Foundry - a working map across every major cloud AI stack.", notes: "5 notes", qa: "20+ Q&A" },
  "prog-langs":              { num: "11", subtitle: "The Foundation",   description: "PyTorch fundamentals - tensors, autograd, the hand-written training loop, checkpointing, and mixed precision.", notes: "6 notes", qa: "20+ Q&A" },
};

/** Recursively find the "Concepts" group anywhere in a module's item tree
 *  (handles Prog Langs' one-extra-level-deep nesting) and return its leaves. */
function findConcepts(items: NavItem[]): NavItem[] | null {
  for (const item of items) {
    if (item.title === "Concepts" && item.children) return item.children;
    if (item.children) {
      const found = findConcepts(item.children);
      if (found) return found;
    }
  }
  return null;
}

function CurriculumTile({
  mod,
  meta,
  pinned,
  onTogglePin,
}: {
  mod: NavModule;
  meta: ModuleMeta;
  pinned: boolean;
  onTogglePin: () => void;
}) {
  const [hovered, setHovered] = useState(false);
  const open = pinned || hovered;
  const overviewHref = mod.items[0]?.href ?? `/learn/${mod.slug}/index`;
  const concepts = findConcepts(mod.items) ?? [];

  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      className="rounded-xl border border-glass-card-border bg-glass-card-bg backdrop-blur-glass-sm shadow-glass-sm overflow-hidden hover:border-sun-yellow hover:shadow-glass-md transition-all duration-150"
    >
      <button
        type="button"
        onClick={onTogglePin}
        aria-expanded={open}
        className="w-full text-left p-4 cursor-pointer"
      >
        <div className="flex items-start justify-between mb-2">
          <span className="text-xs font-mono text-sun-muted">{meta.num}</span>
          <span className="text-xs font-semibold text-sun-amber bg-sun-yellow-dim px-2 py-0.5 rounded-full">
            {meta.subtitle}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <h3 className="font-semibold text-sun-dark flex-1">{mod.title}</h3>
          <ChevronDown
            className={`h-4 w-4 text-sun-muted shrink-0 transition-transform duration-150 ${open ? "rotate-180" : ""}`}
            aria-hidden="true"
          />
        </div>
        <p className="text-xs text-sun-muted leading-relaxed mt-1.5 mb-3">{meta.description}</p>
        <div className="flex gap-2">
          <span className="text-xs bg-glass-panel-bg text-sun-muted rounded px-2 py-0.5">{meta.notes}</span>
          <span className="text-xs bg-glass-panel-bg text-sun-muted rounded px-2 py-0.5">{meta.qa}</span>
        </div>
      </button>

      <div
        className={`grid transition-all duration-200 ease-out ${
          open ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"
        }`}
      >
        <div className="overflow-hidden">
          <div className="border-t border-glass-card-border bg-glass-panel-bg px-4 py-3">
            {concepts.length > 0 && (
              <ul className="mb-2.5 space-y-0.5">
                {concepts.map((c) => (
                  <li key={c.href}>
                    <Link
                      href={c.href}
                      className="block py-0.5 text-xs text-sun-muted hover:text-sun-amber hover:underline transition-colors"
                    >
                      {c.title}
                    </Link>
                  </li>
                ))}
              </ul>
            )}
            <Link
              href={overviewHref}
              className="inline-flex items-center text-xs font-semibold text-sun-amber hover:underline"
            >
              View full module →
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

export function CurriculumTiles({ modules }: { modules: NavModule[] }) {
  const [pinned, setPinned] = useState<Set<string>>(new Set());
  const displayModules = modules.filter((mod) => MODULE_META[mod.slug]);
  const allOpen = displayModules.length > 0 && displayModules.every((mod) => pinned.has(mod.slug));

  function expandAll() {
    setPinned(new Set(displayModules.map((mod) => mod.slug)));
  }
  function collapseAll() {
    setPinned(new Set());
  }
  function togglePin(slug: string) {
    setPinned((prev) => {
      const next = new Set(prev);
      if (next.has(slug)) next.delete(slug);
      else next.add(slug);
      return next;
    });
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <p className="text-xs text-sun-muted">
          Hover a card for a quick peek, or click to pin it open.
        </p>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={expandAll}
            disabled={allOpen}
            className="text-xs font-semibold text-sun-muted hover:text-sun-amber border border-glass-card-border hover:border-sun-yellow rounded-md px-3 py-1.5 transition-colors disabled:opacity-40 disabled:cursor-default disabled:hover:text-sun-muted disabled:hover:border-glass-card-border"
          >
            Expand all
          </button>
          <button
            type="button"
            onClick={collapseAll}
            disabled={pinned.size === 0}
            className="text-xs font-semibold text-sun-muted hover:text-sun-amber border border-glass-card-border hover:border-sun-yellow rounded-md px-3 py-1.5 transition-colors disabled:opacity-40 disabled:cursor-default disabled:hover:text-sun-muted disabled:hover:border-glass-card-border"
          >
            Collapse all
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {displayModules.map((mod) => (
          <CurriculumTile
            key={mod.slug}
            mod={mod}
            meta={MODULE_META[mod.slug]}
            pinned={pinned.has(mod.slug)}
            onTogglePin={() => togglePin(mod.slug)}
          />
        ))}
      </div>
    </div>
  );
}
