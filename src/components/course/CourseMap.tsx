"use client";

import { useEffect, useMemo, useSyncExternalStore } from "react";
import Link from "next/link";
import { X } from "lucide-react";
import { Sheet, SheetContent, SheetTitle } from "@/components/ui/sheet";
import type { MapLayout, MapModule, MapRegion, Point } from "@/lib/content/courseMap";
import { LAST_VISIT_KEY, type LastVisit } from "./VisitTracker";

const SERIF = "var(--font-map), Georgia, serif";
const ink = (name: string) => `var(--map-${name})`;

// ── Browser state: selected module (URL hash), last visit, viewport ─────────

const SELECT_EVENT = "coursemap:select";

function subscribeSelection(onChange: () => void) {
  window.addEventListener("hashchange", onChange);
  window.addEventListener(SELECT_EVENT, onChange);
  return () => {
    window.removeEventListener("hashchange", onChange);
    window.removeEventListener(SELECT_EVENT, onChange);
  };
}
const getSelection = () => decodeURIComponent(location.hash.slice(1));

/** Landmarks are plain `#slug` links, so opening needs no code; closing drops the hash */
function closeSelection() {
  history.pushState(null, "", location.pathname + location.search);
  window.dispatchEvent(new Event(SELECT_EVENT));
}

function subscribeStorage(onChange: () => void) {
  window.addEventListener("storage", onChange);
  return () => window.removeEventListener("storage", onChange);
}
function getLastVisitRaw(): string | null {
  try {
    return localStorage.getItem(LAST_VISIT_KEY);
  } catch {
    return null;
  }
}

const MOBILE_QUERY = "(max-width: 767px)";
function subscribeViewport(onChange: () => void) {
  const mq = window.matchMedia(MOBILE_QUERY);
  mq.addEventListener("change", onChange);
  return () => mq.removeEventListener("change", onChange);
}
const getIsMobile = () => window.matchMedia(MOBILE_QUERY).matches;

// ── SVG pieces ───────────────────────────────────────────────────────────────

function Compass({ at, r }: { at: Point; r: number }) {
  const long = r * 0.92;
  const short = r * 0.2;
  // Four long points, each split into a dark and a light half, like an engraved rose
  const halves = [0, 90, 180, 270].flatMap((deg) => [
    { deg, d: `M 0 0 L ${-short} ${-short} L 0 ${-long} Z`, fill: ink("ink") },
    { deg, d: `M 0 0 L ${short} ${-short} L 0 ${-long} Z`, fill: ink("paper") },
  ]);
  const minor = [45, 135, 225, 315].map((deg) => ({ deg, d: `M ${-short * 0.7} 0 L 0 ${-r * 0.55} L ${short * 0.7} 0 Z` }));
  return (
    <g transform={`translate(${at.x} ${at.y})`} aria-hidden="true">
      <circle r={r} fill="none" stroke={ink("ink-soft")} strokeWidth={1} />
      <circle r={r * 0.8} fill="none" stroke={ink("ink-soft")} strokeWidth={0.6} strokeDasharray="2 3" />
      {minor.map(({ deg, d }) => (
        <path key={deg} d={d} transform={`rotate(${deg})`} fill={ink("ink-soft")} opacity={0.7} />
      ))}
      {halves.map(({ deg, d, fill }, i) => (
        <path key={i} d={d} transform={`rotate(${deg})`} fill={fill} stroke={ink("ink")} strokeWidth={0.8} strokeLinejoin="round" />
      ))}
      <circle r={2.5} fill={ink("ink")} />
      <text y={-r - 6} textAnchor="middle" fontSize={13} fontWeight={700} fill={ink("ink")} style={{ fontFamily: SERIF }}>
        N
      </text>
    </g>
  );
}

/** Pennant for the capstones, open book for the review hall */
function KindGlyph({ kind }: { kind: MapModule["kind"] }) {
  if (kind === "capstone")
    return (
      <g transform="translate(15 -40)" aria-hidden="true">
        <path d="M 0 18 L 0 0" stroke={ink("ink")} strokeWidth={1.4} />
        <path d="M 0 0 L 13 4 L 0 9 Z" fill={ink("accent")} stroke={ink("ink")} strokeWidth={1} strokeLinejoin="round" />
      </g>
    );
  if (kind === "review")
    return (
      <g transform="translate(14 -36)" aria-hidden="true" fill={ink("paper")} stroke={ink("ink")} strokeWidth={1} strokeLinejoin="round">
        <path d="M 0 2 Q 5 0 10 2 L 10 12 Q 5 10 0 12 Z" />
        <path d="M 10 2 Q 15 0 20 2 L 20 12 Q 15 10 10 12 Z" />
      </g>
    );
  return null;
}

/** Footprints and a tag, beside the landmark of the last page opened */
function YouAreHere({ at, flip }: { at: Point; flip: boolean }) {
  const foot = (x: number, y: number, rot: number) => (
    <g transform={`translate(${x} ${y}) rotate(${rot})`}>
      <ellipse rx={2.6} ry={4.2} />
      <ellipse cy={6.2} rx={1.9} ry={2} />
    </g>
  );
  return (
    // Near the right edge the tag points left instead, so it stays on the paper
    <g transform={`translate(${at.x + (flip ? -26 : 26)} ${at.y - 34}) scale(${flip ? -1 : 1} 1)`} aria-hidden="true">
      <g fill={ink("ink")}>
        {foot(0, 10, 20)}
        {foot(8, 2, 20)}
      </g>
      <rect x={14} y={-10} width={82} height={20} rx={10} fill={ink("accent")} stroke={ink("ink")} strokeWidth={0.8} />
      <text x={55} y={4.5} transform={flip ? "scale(-1 1) translate(-110 0)" : undefined} textAnchor="middle" fontSize={12.5} fontStyle="italic" fill={ink("on-accent")} style={{ fontFamily: SERIF }}>
        You are here
      </text>
    </g>
  );
}

function MapSvg({
  layout,
  modules,
  selected,
  here,
  id,
  className,
}: {
  layout: MapLayout;
  modules: Map<string, MapModule>;
  selected: string;
  here: string | null;
  id: string;
  className?: string;
}) {
  const { width, height, regions, landmarks, route, compass, folds } = layout;
  return (
    <svg viewBox={`0 0 ${width} ${height}`} className={className} role="group" aria-label="Course map: tracks as regions, modules as numbered landmarks along the learning route">
      <defs>
        <filter id={`${id}-grain`} x="0" y="0" width="100%" height="100%">
          <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves={3} stitchTiles="stitch" />
          <feColorMatrix type="saturate" values="0" />
        </filter>
      </defs>

      {/* Paper grain and fold creases; clicking bare paper closes an open note */}
      <rect width={width} height={height} fill="transparent" onClick={() => selected && closeSelection()} />
      <rect width={width} height={height} filter={`url(#${id}-grain)`} opacity={0.06} pointerEvents="none" />
      {folds.map(([x1, y1, x2, y2], i) => (
        <g key={i} pointerEvents="none">
          <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={ink("ink-soft")} strokeWidth={1} opacity={0.14} />
          <line x1={x1 + 1.5} y1={y1 + 1.5} x2={x2 + 1.5} y2={y2 + 1.5} stroke={ink("paper-edge")} strokeWidth={1} opacity={0.5} />
        </g>
      ))}

      {/* Regions: double-ruled panels with the track name on a ribbon */}
      {regions.map((r) => {
        const label = r.track.toUpperCase();
        // ~9.4px per uppercase glyph at 11.5px with 0.18em tracking; too small and long track names spill past the ribbon
        const labelW = label.length * 9.4 + 24;
        const labelX = r.labelAt === "start" ? r.x + 16 : r.x + r.w - 16 - labelW;
        return (
          <g key={r.track} pointerEvents="none">
            <rect x={r.x} y={r.y} width={r.w} height={r.h} rx={6} fill="none" stroke={ink("ink-soft")} strokeWidth={1.2} />
            <rect x={r.x + 4} y={r.y + 4} width={r.w - 8} height={r.h - 8} rx={4} fill="none" stroke={ink("ink-soft")} strokeWidth={0.6} opacity={0.7} />
            <rect x={labelX} y={r.y - 10} width={labelW} height={20} fill={ink("paper")} />
            <text x={labelX + labelW / 2} y={r.y + 4} textAnchor="middle" fontSize={11.5} fontWeight={600} letterSpacing="0.18em" fill={ink("ink-soft")}>
              {label}
            </text>
          </g>
        );
      })}

      {/* The learning route, in dotted ink */}
      <path d={route} fill="none" stroke={ink("route")} strokeWidth={2.4} strokeDasharray="0.5 8" strokeLinecap="round" pointerEvents="none" />

      {landmarks.map((lm) => {
        const mod = modules.get(lm.slug);
        const isSelected = lm.slug === selected;
        return (
          <a
            key={lm.slug}
            href={`#${lm.slug}`}
            className="map-landmark"
            aria-label={`Module ${lm.number}: ${mod?.title} - ${lm.subtitle}`}
            aria-current={isSelected ? "true" : undefined}
          >
            <g transform={`translate(${lm.x} ${lm.y})`}>
              <circle className="lm-focus" r={28} fill="none" strokeWidth={3} />
              <circle className="lm-body" r={21} stroke={ink("ink")} strokeWidth={1.6} />
              <circle r={17} fill="none" stroke={isSelected ? ink("on-accent") : ink("ink-soft")} strokeWidth={0.7} strokeDasharray="2 2.5" />
              <text y={5.5} textAnchor="middle" fontSize={16} fontWeight={700} fill={isSelected ? ink("on-accent") : ink("ink")} style={{ fontFamily: SERIF }}>
                {String(lm.number).padStart(2, "0")}
              </text>
              <KindGlyph kind={lm.kind} />
              <text y={46} textAnchor="middle" fontSize={19} fontStyle="italic" fill={ink("ink")} style={{ fontFamily: SERIF }}>
                {lm.subtitle}
              </text>
              {lm.titleLines.map((line, i) => (
                <text key={i} y={63 + i * 13} textAnchor="middle" fontSize={10.5} fontWeight={600} letterSpacing="0.08em" fill={ink("ink-soft")}>
                  {line.toUpperCase()}
                </text>
              ))}
            </g>
          </a>
        );
      })}

      {here && landmarks.filter((lm) => lm.slug === here).map((lm) => <YouAreHere key={lm.slug} at={lm} flip={lm.x > width - 150} />)}

      <Compass at={compass} r={id === "wide" ? 52 : 34} />
    </svg>
  );
}

// ── Module details ───────────────────────────────────────────────────────────

function Details({ mod, hereHref }: { mod: MapModule; hereHref?: string }) {
  const counts = [
    [mod.stats.concepts, "note", "notes"],
    [mod.stats.labs, "lab", "labs"],
    [mod.stats.questions, "review question", "review questions"],
  ].filter(([n]) => (n as number) > 0) as [number, string, string][];

  return (
    <div className="space-y-4 text-map-ink">
      <div className="pr-8">
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-map-ink-soft">
          Module {String(mod.number).padStart(2, "0")} · {mod.title}
        </p>
        <p className="text-2xl italic leading-tight mt-1" style={{ fontFamily: SERIF }}>
          {mod.subtitle}
        </p>
      </div>
      {mod.description && <p className="text-sm leading-relaxed">{mod.description}</p>}
      {counts.length > 0 && (
        <p className="text-xs text-map-ink-soft">{counts.map(([n, one, many]) => `${n} ${n === 1 ? one : many}`).join(" · ")}</p>
      )}
      <Link
        href={mod.href}
        className="inline-flex items-center rounded-md bg-map-accent text-map-on-accent text-xs font-semibold px-3 py-1.5 hover:opacity-90 transition-opacity"
      >
        Start at the overview
      </Link>
      {mod.sections.map((section) => (
        <div key={section.title}>
          {section.title && (
            <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-map-ink-soft border-b border-map-paper-edge pb-1 mb-1.5">
              {section.title}
            </p>
          )}
          <ul className="space-y-0.5">
            {section.pages.map((page) => (
              <li key={page.href}>
                <Link
                  href={page.href}
                  className="flex items-baseline gap-2 text-sm py-0.5 hover:underline underline-offset-2 decoration-map-ink-soft"
                >
                  <span aria-hidden="true" className="text-map-ink-soft">
                    ·
                  </span>
                  <span>{page.title}</span>
                  {page.href === hereHref && <span className="text-[10px] italic text-map-ink-soft">(last visited)</span>}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}

/** Desktop: a note card pinned beside the landmark, opening away from the nearest edges */
function NoteCard({ mod, at, layout, hereHref }: { mod: MapModule; at: Point; layout: MapLayout; hereHref?: string }) {
  const px = (at.x / layout.width) * 100;
  const py = (at.y / layout.height) * 100;
  const style: React.CSSProperties = {
    ...(px < 50 ? { left: `calc(${px}% + 40px)` } : { right: `calc(${100 - px}% + 40px)` }),
    ...(py < 50 ? { top: `max(0px, calc(${py}% - 48px))` } : { bottom: `max(0px, calc(${100 - py}% - 48px))` }),
  };
  return (
    <div
      role="dialog"
      aria-label={`${mod.title} - ${mod.subtitle}`}
      style={style}
      className="hidden md:block absolute z-10 w-[22rem] max-h-[28rem] overflow-y-auto rounded-lg border border-map-ink-soft bg-map-paper p-5 shadow-glass-lg"
    >
      <button
        type="button"
        onClick={closeSelection}
        aria-label="Close"
        className="absolute right-3 top-3 p-1 rounded text-map-ink-soft hover:text-map-ink hover:bg-map-paper-edge transition-colors"
      >
        <X className="h-4 w-4" />
      </button>
      <Details mod={mod} hereHref={hereHref} />
    </div>
  );
}

// ── The map ──────────────────────────────────────────────────────────────────

export function CourseMap({ regions, wide, tall }: { regions: MapRegion[]; wide: MapLayout; tall: MapLayout }) {
  const modules = useMemo(() => new Map(regions.flatMap((r) => r.modules).map((m) => [m.slug, m])), [regions]);
  const selectedSlug = useSyncExternalStore(subscribeSelection, getSelection, () => "");
  const isMobile = useSyncExternalStore(subscribeViewport, getIsMobile, () => false);
  const lastVisitRaw = useSyncExternalStore(subscribeStorage, getLastVisitRaw, () => null);

  const selected = modules.get(selectedSlug);
  const lastVisit = useMemo<LastVisit | null>(() => {
    if (!lastVisitRaw) return null;
    try {
      const v = JSON.parse(lastVisitRaw) as LastVisit;
      return v && typeof v.href === "string" && modules.has(v.module) ? v : null;
    } catch {
      return null;
    }
  }, [lastVisitRaw, modules]);
  const here = lastVisit?.module ?? null;

  // Escape closes the desktop note card (the mobile sheet handles its own)
  useEffect(() => {
    if (!selected) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && closeSelection();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [selected]);

  const wideAt = selected && wide.landmarks.find((lm) => lm.slug === selected.slug);

  return (
    <div className="relative rounded-xl border border-map-paper-edge bg-map-paper text-map-ink shadow-[inset_0_0_80px_var(--map-paper-edge)] px-3 py-6 sm:px-6">
      {/* Title cartouche */}
      <header className="mx-auto max-w-xl text-center border-4 border-double border-map-ink-soft rounded-md px-5 py-4 mb-6">
        <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-map-ink-soft">Learn GenAI</p>
        <h1 className="text-3xl sm:text-4xl italic leading-tight mt-1" style={{ fontFamily: SERIF }}>
          The Course Atlas
        </h1>
        <p className="text-sm text-map-ink-soft mt-2 leading-relaxed">
          Every track and module, from first tokens to production agents. Follow the dotted route in order, or select a landmark to see its pages.
        </p>
        {lastVisit && (
          <p className="text-sm mt-3">
            <span className="italic text-map-ink-soft" style={{ fontFamily: SERIF }}>
              Continue:{" "}
            </span>
            <Link href={lastVisit.href} className="font-semibold underline underline-offset-2 decoration-map-accent decoration-2 hover:decoration-map-ink">
              {lastVisit.title}
            </Link>
          </p>
        )}
      </header>

      <div className="relative">
        <MapSvg layout={wide} modules={modules} selected={selectedSlug} here={here} id="wide" className="hidden md:block w-full h-auto" />
        <MapSvg layout={tall} modules={modules} selected={selectedSlug} here={here} id="tall" className="md:hidden w-full h-auto" />
        {selected && wideAt && <NoteCard mod={selected} at={wideAt} layout={wide} hereHref={lastVisit?.href} />}
      </div>

      {/* Legend */}
      <ul className="mt-4 flex flex-wrap justify-center gap-x-6 gap-y-2 text-xs text-map-ink-soft" aria-label="Legend">
        <li className="flex items-center gap-2">
          <svg width="18" height="18" viewBox="-10 -10 20 20" aria-hidden="true">
            <circle r={8} fill={ink("paper")} stroke={ink("ink")} strokeWidth={1.4} />
          </svg>
          Module landmark
        </li>
        <li className="flex items-center gap-2">
          <svg width="34" height="8" viewBox="0 0 34 8" aria-hidden="true">
            <path d="M 2 4 L 32 4" stroke={ink("route")} strokeWidth={2.4} strokeDasharray="0.5 7" strokeLinecap="round" />
          </svg>
          Learning route
        </li>
        <li className="flex items-center gap-2">
          <svg width="16" height="18" viewBox="0 0 16 18" aria-hidden="true">
            <path d="M 3 17 L 3 1" stroke={ink("ink")} strokeWidth={1.4} />
            <path d="M 3 1 L 15 5 L 3 9 Z" fill={ink("accent")} stroke={ink("ink")} strokeWidth={1} />
          </svg>
          Capstone projects
        </li>
        <li className="flex items-center gap-2">
          <span className="rounded-full bg-map-accent text-map-on-accent px-2 py-px italic" style={{ fontFamily: SERIF }}>
            You are here
          </span>
          Your last page
        </li>
      </ul>

      {/* Mobile: module details in a bottom sheet */}
      <Sheet open={Boolean(selected) && isMobile} onOpenChange={(open) => !open && closeSelection()}>
        <SheetContent side="bottom" aria-describedby={undefined} className="bg-map-paper max-h-[80vh] overflow-y-auto rounded-t-xl">
          {selected && (
            <>
              <SheetTitle className="sr-only">{`${selected.title} - ${selected.subtitle}`}</SheetTitle>
              <Details mod={selected} hereHref={lastVisit?.href} />
            </>
          )}
        </SheetContent>
      </Sheet>
    </div>
  );
}
