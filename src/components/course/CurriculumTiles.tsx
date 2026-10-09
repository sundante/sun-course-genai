"use client";

import { useState } from "react";
import Link from "next/link";
import { ChevronRight } from "lucide-react";
import type { NavModule } from "@/types/content";

import type { ModuleStats } from "@/lib/content/stats";
import { MODULE_META, type ModuleMeta } from "@/lib/content/moduleMeta";
import { conceptPages } from "@/lib/content/navSections";

function countLabel(n: number, singular: string, plural = `${singular}s`): string {
  return `${n} ${n === 1 ? singular : plural}`;
}

function DetailBody({ mod, meta, stats }: { mod: NavModule; meta: ModuleMeta; stats?: ModuleStats }) {
  const overviewHref = mod.items[0]?.href ?? `/learn/${mod.slug}/index`;
  const concepts = conceptPages(mod.items);

  return (
    <div>
      <div className="flex items-start justify-between gap-3 mb-2">
        <span className="text-xs font-mono text-sun-muted">{String(mod.number).padStart(2, "0")}</span>
        <span className="text-xs font-semibold text-sun-amber bg-sun-yellow-dim px-2 py-0.5 rounded-full">
          {meta.subtitle}
        </span>
      </div>
      <Link
        href={overviewHref}
        className="font-semibold text-sun-dark text-base mb-1.5 block hover:text-sun-amber hover:underline transition-colors"
      >
        {mod.title}
      </Link>
      <p className="text-xs text-sun-muted leading-relaxed mb-2.5">{meta.description}</p>
      {stats && (
        <div className="flex flex-wrap gap-2 mb-3">
          {stats.concepts > 0 && <span className="text-xs bg-glass-panel-bg text-sun-muted rounded px-2 py-0.5">{countLabel(stats.concepts, "note")}</span>}
          {stats.labs > 0 && <span className="text-xs bg-glass-panel-bg text-sun-muted rounded px-2 py-0.5">{countLabel(stats.labs, "code lab")}</span>}
          {stats.questions > 0 && <span className="text-xs bg-glass-panel-bg text-sun-muted rounded px-2 py-0.5">{stats.questions} Q&amp;A</span>}
          {stats.concepts === 0 && <span className="text-xs bg-glass-panel-bg text-sun-wip rounded px-2 py-0.5">In development</span>}
        </div>
      )}

      {concepts.length > 0 && (
        <ul className="mb-2.5 space-y-0.5 border-t border-glass-card-border pt-2.5">
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
  );
}

export function CurriculumTiles({ modules, stats }: { modules: NavModule[]; stats: Record<string, ModuleStats> }) {
  // Hover and click/tap are tracked separately: a real click is always preceded
  // by a synthetic mouseenter (both in browsers' hover-emulation on touch and in
  // Playwright's click()), so deriving "active" purely from one shared toggle
  // meant a click immediately closed what the hover had just opened - breaking
  // tap-to-open on mobile entirely. Hover always wins while it's active; moving
  // the mouse away falls back to whatever's pinned (or nothing).
  const [hovered, setHovered] = useState<string | null>(null);
  const [pinned, setPinned] = useState<string | null>(null);
  const active = hovered ?? pinned;
  const [showDescriptions, setShowDescriptions] = useState(false);
  const displayModules = modules.filter((mod) => MODULE_META[mod.slug]);
  const activeModule = displayModules.find((mod) => mod.slug === active) ?? null;

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs text-sun-muted">
          Hover (or tap) a module to preview it - the topic list slides in on the right.
        </p>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setShowDescriptions(true)}
            disabled={showDescriptions}
            className="text-xs font-semibold text-sun-muted hover:text-sun-amber border border-glass-card-border hover:border-sun-yellow rounded-md px-3 py-1.5 transition-colors disabled:opacity-40 disabled:cursor-default disabled:hover:text-sun-muted disabled:hover:border-glass-card-border"
          >
            Expand all
          </button>
          <button
            type="button"
            onClick={() => setShowDescriptions(false)}
            disabled={!showDescriptions}
            className="text-xs font-semibold text-sun-muted hover:text-sun-amber border border-glass-card-border hover:border-sun-yellow rounded-md px-3 py-1.5 transition-colors disabled:opacity-40 disabled:cursor-default disabled:hover:text-sun-muted disabled:hover:border-glass-card-border"
          >
            Collapse all
          </button>
        </div>
      </div>

      <div
        className="flex flex-col md:flex-row gap-3 md:gap-4"
        onMouseLeave={() => setHovered(null)}
      >
        {/* Vertical module list - shrinks to a rail on desktop once something is active */}
        <div className={`w-full transition-all duration-300 ease-out ${active ? "md:w-64 md:shrink-0" : "md:flex-1"}`}>
          <div className="rounded-xl border border-glass-card-border bg-glass-card-bg backdrop-blur-glass-sm shadow-glass-sm divide-y divide-glass-card-border overflow-hidden">
            {displayModules.map((mod, i) => {
              const meta = MODULE_META[mod.slug];
              const trackStart = mod.track && mod.track !== displayModules[i - 1]?.track;
              const isActive = active === mod.slug;
              const overviewHref = mod.items[0]?.href ?? `/learn/${mod.slug}/index`;
              return (
                <div key={mod.slug}>
                  {trackStart && (
                    <div className="px-4 pt-3 pb-1.5 text-[10px] font-bold uppercase tracking-[0.18em] text-sun-amber bg-glass-panel-bg/50">
                      {mod.track}
                    </div>
                  )}
                  <div
                    onMouseEnter={() => setHovered(mod.slug)}
                    className={`w-full flex items-center gap-1 pr-2 transition-colors ${
                      isActive ? "bg-glass-panel-bg" : "hover:bg-glass-panel-bg/70"
                    }`}
                  >
                    <Link
                      href={overviewHref}
                      onFocus={() => setHovered(mod.slug)}
                      className="flex-1 min-w-0 text-left pl-4 py-2.5 flex items-center gap-3 group"
                    >
                      <span className="text-xs font-mono text-sun-muted w-6 shrink-0">{String(mod.number).padStart(2, "0")}</span>
                      <span className="font-semibold text-sun-dark text-sm flex-1 truncate group-hover:text-sun-amber group-hover:underline">{mod.title}</span>
                      {!active && (
                        <span className="hidden md:inline text-xs font-semibold text-sun-amber bg-sun-yellow-dim px-2 py-0.5 rounded-full shrink-0">
                          {meta.subtitle}
                        </span>
                      )}
                    </Link>
                    <button
                      type="button"
                      onClick={() => {
                        setPinned((prev) => (prev === mod.slug ? null : mod.slug));
                        setHovered(null);
                      }}
                      aria-expanded={isActive}
                      aria-label={isActive ? `Collapse ${mod.title} preview` : `Preview ${mod.title}`}
                      className="shrink-0 p-1.5 rounded-md hover:bg-glass-panel-bg cursor-pointer"
                    >
                      <ChevronRight
                        className={`h-4 w-4 text-sun-muted shrink-0 transition-transform duration-150 ${
                          isActive ? "rotate-90 md:rotate-0 md:text-sun-amber" : ""
                        }`}
                        aria-hidden="true"
                      />
                    </button>
                  </div>

                  {showDescriptions && (
                    <p className="px-4 pb-3 -mt-1 text-xs text-sun-muted leading-relaxed">
                      {meta.description}
                    </p>
                  )}

                  {/* Mobile fallback - no hover available, so the detail renders inline on tap */}
                  {isActive && (
                    <div className="md:hidden border-t border-glass-card-border bg-glass-panel-bg px-4 py-4">
                      <DetailBody mod={mod} meta={meta} stats={stats[mod.slug]} />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Desktop-only detail panel - expands to the right of the shrunk list */}
        <div
          className={`hidden md:block overflow-hidden transition-all duration-300 ease-out ${
            active ? "md:flex-1 opacity-100" : "md:w-0 opacity-0"
          }`}
        >
          {activeModule && (
            <div className="h-full rounded-xl border border-sun-yellow bg-glass-card-bg backdrop-blur-glass-sm shadow-glass-md p-4">
              <DetailBody mod={activeModule} meta={MODULE_META[activeModule.slug]} stats={stats[activeModule.slug]} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
