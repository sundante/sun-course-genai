"use client";

import { useEffect, useState, type ReactNode } from "react";
import { ExternalLink, Maximize2, Minimize2 } from "lucide-react";

// ```interactive fence (remarkCourseFences.ts -> CourseDiv "cf-interactive").
// Labs are full-width two-pane layouts that stack below ~960px, which is wider than the
// article column. Theatre view pins the same <figure> over the viewport, so the lab gets
// its side-by-side layout. Only classes change, so the iframe (and a playing video) is never reloaded.
export function InteractiveEmbed({
  src,
  title,
  height,
  children,
}: {
  src: string;
  title: string;
  height: number;
  children?: ReactNode;
}) {
  const [theatre, setTheatre] = useState(false);

  useEffect(() => {
    if (!theatre) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setTheatre(false);
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = overflow;
      window.removeEventListener("keydown", onKey);
    };
  }, [theatre]);

  const button =
    "inline-flex shrink-0 items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold transition-colors";

  return (
    <figure
      className={
        theatre
          ? "not-prose fixed inset-0 z-[60] m-0 flex flex-col bg-sun-bg"
          : "not-prose my-6 overflow-hidden rounded-xl border border-glass-card-border bg-glass-card-bg shadow-glass-sm"
      }
    >
      <div className="flex items-center justify-between gap-3 border-b border-glass-card-border px-4 py-2">
        <span className="truncate text-xs font-bold uppercase tracking-widest text-sun-amber">Interactive · {title}</span>
        <div className="flex items-center gap-2">
          <a
            href={src}
            target="_blank"
            rel="noopener"
            className={`${button} border border-glass-card-border text-sun-dark hover:border-sun-yellow`}
          >
            <ExternalLink className="h-3 w-3" aria-hidden="true" /> New tab
          </a>
          <button
            type="button"
            onClick={() => setTheatre((t) => !t)}
            aria-pressed={theatre}
            className={`${button} bg-sun-yellow text-zinc-900 hover:bg-sun-yellow/80`}
          >
            {theatre ? (
              <><Minimize2 className="h-3 w-3" aria-hidden="true" /> Exit theatre (Esc)</>
            ) : (
              <><Maximize2 className="h-3 w-3" aria-hidden="true" /> Theatre view: video + visuals side by side</>
            )}
          </button>
        </div>
      </div>
      <iframe
        src={src}
        title={title}
        loading="lazy"
        allow="autoplay; encrypted-media; fullscreen; picture-in-picture"
        allowFullScreen
        className={`block w-full border-0 bg-sun-bg ${theatre ? "min-h-0 flex-1" : ""}`}
        style={theatre ? undefined : { height }}
      />
      {children && !theatre && (
        <figcaption className="border-t border-glass-card-border px-4 py-2 text-sm text-sun-muted [&_p]:m-0 [&_a]:text-sun-amber [&_a]:underline [&_a]:underline-offset-2">
          {children}
        </figcaption>
      )}
    </figure>
  );
}
