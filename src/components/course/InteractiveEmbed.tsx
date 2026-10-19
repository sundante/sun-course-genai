"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import { Play, X } from "lucide-react";

// ```interactive fence (remarkCourseFences.ts -> CourseDiv "cf-interactive").
// The article shows a poster (a screenshot of the lab) with a play button, never a live iframe:
// labs are full-width two-pane layouts that only work at full screen size. Clicking opens the lab
// in a full-viewport <dialog> (top layer, native Esc + focus trap). The iframe exists only while
// the dialog is open, so closing it also stops the lab and its video. There is deliberately no
// "open in new tab" link: the lab is a pop-up over the course page, never a page of its own.
export function InteractiveEmbed({
  src,
  title,
  poster,
  posterDark,
  children,
}: {
  src: string;
  title: string;
  poster?: string;
  posterDark?: string;
  children?: ReactNode;
}) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
    if (!open) return;
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    // Esc pressed while focus is inside the lab iframe never reaches this dialog; the lab posts a message instead
    const onMessage = (e: MessageEvent) => {
      if (e.origin === window.location.origin && e.data?.type === "lab:close") setOpen(false);
    };
    window.addEventListener("message", onMessage);
    return () => {
      document.body.style.overflow = overflow;
      window.removeEventListener("message", onMessage);
    };
  }, [open]);

  return (
    <figure className="not-prose my-6 overflow-hidden rounded-xl border border-glass-card-border bg-glass-card-bg shadow-glass-sm">
      <button
        type="button"
        onClick={() => setOpen(true)}
        aria-haspopup="dialog"
        aria-label={`Open the interactive lab: ${title}`}
        className="group relative block aspect-video w-full cursor-pointer overflow-hidden bg-sun-bg"
      >
        {poster ? (
          <>
            {/* eslint-disable-next-line @next/next/no-img-element -- static export, plain files under public/ */}
            <img
              src={poster}
              alt=""
              loading="lazy"
              className={`absolute inset-0 h-full w-full object-cover object-top transition-transform duration-300 group-hover:scale-[1.015] ${posterDark ? "dark:hidden" : ""}`}
            />
            {posterDark && (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={posterDark}
                alt=""
                loading="lazy"
                className="absolute inset-0 hidden h-full w-full object-cover object-top transition-transform duration-300 group-hover:scale-[1.015] dark:block"
              />
            )}
          </>
        ) : (
          <span className="absolute inset-0 grid place-items-center bg-sun-surface text-lg font-bold text-sun-dark">{title}</span>
        )}
        <span className="absolute inset-0 bg-glass-scrim opacity-40 transition-opacity group-hover:opacity-25" aria-hidden="true" />
        <span className="absolute inset-0 grid place-items-center" aria-hidden="true">
          <span className="flex flex-col items-center gap-3">
            <span className="grid h-20 w-20 place-items-center rounded-full bg-sun-yellow text-zinc-900 shadow-glass-lg ring-8 ring-sun-yellow/30 transition-transform group-hover:scale-110">
              <Play className="ml-1 h-9 w-9 fill-current" />
            </span>
            <span className="rounded-full bg-zinc-900/80 px-4 py-1.5 text-sm font-semibold text-white">Open the full-screen lab</span>
          </span>
        </span>
      </button>
      <div className="border-t border-glass-card-border px-4 py-2">
        <span className="block truncate text-xs font-bold uppercase tracking-widest text-sun-amber">Interactive · {title}</span>
      </div>
      {children && (
        <figcaption className="border-t border-glass-card-border px-4 py-2 text-sm text-sun-muted [&_p]:m-0 [&_a]:text-sun-amber [&_a]:underline [&_a]:underline-offset-2">
          {children}
        </figcaption>
      )}

      <dialog
        ref={dialogRef}
        aria-label={title}
        onClose={() => setOpen(false)}
        className="fixed inset-0 m-0 h-dvh max-h-none w-screen max-w-none border-0 bg-sun-bg p-0 text-sun-dark backdrop:bg-glass-scrim"
      >
        {open && (
          <div className="flex h-full flex-col">
            <div className="flex items-center justify-between gap-3 border-b border-glass-card-border bg-glass-nav-bg px-4 py-1.5">
              <span className="truncate text-xs font-bold uppercase tracking-widest text-sun-amber">Interactive · {title}</span>
              <button
                type="button"
                onClick={() => setOpen(false)}
                autoFocus
                aria-label="Close the lab"
                title="Close (Esc)"
                className="grid h-8 w-8 shrink-0 place-items-center rounded-full border border-glass-card-border text-sun-dark transition-colors hover:border-sun-coral hover:bg-sun-coral hover:text-white"
              >
                <X className="h-4 w-4" aria-hidden="true" />
              </button>
            </div>
            <iframe
              src={src}
              title={title}
              allow="autoplay; encrypted-media; fullscreen; picture-in-picture"
              allowFullScreen
              className="block min-h-0 w-full flex-1 border-0 bg-sun-bg"
            />
          </div>
        )}
      </dialog>
    </figure>
  );
}
