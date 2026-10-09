import type { NavItem } from "@/types/content";
import { getNavigationTree } from "./nav";
import { getModuleStats, type ModuleStats } from "./stats";
import { MODULE_META, type ModuleMeta } from "./moduleMeta";

// Data + layout for the course map (/map). Everything is derived from nav.yml,
// so new modules and tracks appear on the map without touching this file.

export interface MapPage {
  title: string;
  href: string;
}

export interface MapSection {
  /** Nav group label ("Concepts", "Core Pipeline", "Code Labs"); "" for top-level pages */
  title: string;
  pages: MapPage[];
}

export interface MapModule {
  slug: string;
  number: number;
  title: string;
  subtitle: string;
  description: string;
  /** First page of the module (its Overview) */
  href: string;
  kind: "module" | "capstone" | "review";
  stats: ModuleStats;
  sections: MapSection[];
}

export interface MapRegion {
  track: string;
  modules: MapModule[];
}

// The review hub has no home page tile, so it has no MODULE_META entry
const EXTRA_META: Record<string, ModuleMeta> = {
  "review": {
    subtitle: "The Review Hall",
    description: "Every module's Q&A review bank and quiz in one place - recall the key ideas without the notes open and find weak spots fast.",
  },
};

function sections(items: NavItem[], prefix = ""): MapSection[] {
  const out: MapSection[] = [];
  const direct = items.filter((item) => !item.children).map(({ title, href }) => ({ title, href }));
  if (direct.length) out.push({ title: prefix, pages: direct });
  for (const item of items) {
    if (item.children) out.push(...sections(item.children, prefix ? `${prefix} · ${item.title}` : item.title));
  }
  return out;
}

export function getCourseMap(): MapRegion[] {
  const regions: MapRegion[] = [];
  for (const mod of getNavigationTree().modules) {
    const meta = MODULE_META[mod.slug] ?? EXTRA_META[mod.slug] ?? { subtitle: mod.title, description: "" };
    const track = mod.track ?? "";
    let region = regions.at(-1);
    if (!region || region.track !== track) regions.push((region = { track, modules: [] }));
    const secs = sections(mod.items);
    region.modules.push({
      slug: mod.slug,
      number: mod.number,
      title: mod.title,
      subtitle: meta.subtitle,
      description: meta.description,
      href: secs[0]?.pages[0]?.href ?? "/",
      kind: mod.slug === "capstones" ? "capstone" : mod.slug === "review" ? "review" : "module",
      stats: getModuleStats(mod),
      sections: secs,
    });
  }
  return regions;
}

// ── Layout ───────────────────────────────────────────────────────────────────

export interface Point {
  x: number;
  y: number;
}

export interface LaidOutRegion {
  track: string;
  x: number;
  y: number;
  w: number;
  h: number;
  /** Which end of the top border carries the track ribbon - the end the route doesn't enter by */
  labelAt: "start" | "end";
}

export interface LaidOutLandmark extends Point {
  slug: string;
  number: number;
  subtitle: string;
  /** Module title wrapped to fit under the landmark */
  titleLines: string[];
  kind: MapModule["kind"];
}

export interface MapLayout {
  width: number;
  height: number;
  regions: LaidOutRegion[];
  landmarks: LaidOutLandmark[];
  /** SVG path through every landmark in module order, kept clear of the labels */
  route: string;
  compass: Point;
  /** Fold creases, as [x1, y1, x2, y2] */
  folds: [number, number, number, number][];
}

function wrap(text: string, maxChars: number): string[] {
  const lines: string[] = [];
  for (const word of text.split(" ")) {
    const last = lines.at(-1);
    if (last && (last + " " + word).length <= maxChars) lines[lines.length - 1] = last + " " + word;
    else lines.push(word);
  }
  return lines;
}

/** Smooth curve through the points (Catmull-Rom converted to cubic Béziers) */
export function smoothPath(points: Point[]): string {
  if (!points.length) return "";
  const r = (n: number) => Math.round(n * 10) / 10;
  let d = `M ${r(points[0].x)} ${r(points[0].y)}`;
  for (let i = 0; i < points.length - 1; i++) {
    const p0 = points[i - 1] ?? points[i];
    const p1 = points[i];
    const p2 = points[i + 1];
    const p3 = points[i + 2] ?? p2;
    const c1 = { x: p1.x + (p2.x - p0.x) / 6, y: p1.y + (p2.y - p0.y) / 6 };
    const c2 = { x: p2.x - (p3.x - p1.x) / 6, y: p2.y - (p3.y - p1.y) / 6 };
    d += ` C ${r(c1.x)} ${r(c1.y)}, ${r(c2.x)} ${r(c2.y)}, ${r(p2.x)} ${r(p2.y)}`;
  }
  return d;
}

const landmark = (mod: MapModule, p: Point, maxChars: number): LaidOutLandmark => ({
  ...p,
  slug: mod.slug,
  number: mod.number,
  subtitle: mod.subtitle,
  titleLines: wrap(mod.title, maxChars),
  kind: mod.kind,
});

/**
 * Wide (desktop) layout: regions are packed into rows of up to ROW_SLOTS landmarks and
 * the rows alternate direction (left-to-right, then right-to-left), so the route snakes
 * down the map like a path across folded panels. Leftover space in the last row holds
 * the compass rose.
 */
export function layoutWide(regions: MapRegion[]): MapLayout {
  const WIDTH = 1200;
  const PAD = 24;
  const GAP = 16;
  const ROW_SLOTS = 6;
  const MIN_SLOTS = 4; // a short row doesn't stretch its few landmarks across the whole map
  const ROW_H = 224;
  const inner = WIDTH - PAD * 2;

  const rows: MapRegion[][] = [];
  for (const region of regions) {
    const row = rows.at(-1);
    const used = row?.reduce((n, r) => n + r.modules.length, 0) ?? Infinity;
    if (row && used + region.modules.length <= ROW_SLOTS) row.push(region);
    else rows.push([region]);
  }

  const outRegions: LaidOutRegion[] = [];
  const landmarks: LaidOutLandmark[] = [];
  const route: Point[] = [];
  let compass: Point = { x: WIDTH - 90, y: PAD + ROW_H * rows.length - 90 };

  rows.forEach((row, ri) => {
    const slots = row.reduce((n, r) => n + r.modules.length, 0);
    const slotW = inner / Math.max(slots, MIN_SLOTS);
    const rtl = ri % 2 === 1;
    const y = PAD + ri * ROW_H;
    let cursor = 0; // slots used so far, from the row's starting edge
    for (const region of row) {
      const n = region.modules.length;
      const w = n * slotW - GAP;
      const x = rtl ? PAD + inner - cursor * slotW - n * slotW + GAP / 2 : PAD + cursor * slotW + GAP / 2;
      // The first region of a row is entered from the row's starting edge
      const entered = cursor === 0 && ri > 0;
      outRegions.push({ track: region.track, x, y, w, h: ROW_H - GAP, labelAt: entered && !rtl ? "end" : "start" });
      region.modules.forEach((mod, i) => {
        const slot = cursor + i;
        const cx = rtl ? PAD + inner - (slot + 0.5) * slotW : PAD + (slot + 0.5) * slotW;
        const cy = y + (slot % 2 === 0 ? 78 : 104);
        landmarks.push(landmark(mod, { x: cx, y: cy }, 18));
      });
      cursor += n;
    }
    // Route: along the row at landmark height, and at a row change around the outer
    // edge of the panel, so it never drops through the labels under the landmarks
    const rowMarks = landmarks.slice(landmarks.length - slots);
    const prev = route.at(-1);
    if (prev) {
      const first = rowMarks[0];
      const edge = rtl ? Math.max(prev.x, first.x) + slotW * 0.36 : Math.min(prev.x, first.x) - slotW * 0.36;
      route.push({ x: edge, y: prev.y }, { x: edge, y: first.y });
    }
    route.push(...rowMarks);

    if (ri === rows.length - 1 && slots < Math.max(slots, MIN_SLOTS)) {
      // Centre the compass in the free end of the last row
      const freeCentre = (Math.max(slots, MIN_SLOTS) - slots) / 2 * slotW;
      compass = { x: rtl ? PAD + freeCentre : PAD + inner - freeCentre, y: y + (ROW_H - GAP) / 2 };
    }
  });

  const height = PAD * 2 + ROW_H * rows.length - GAP;
  return {
    width: WIDTH,
    height,
    regions: outRegions,
    landmarks,
    route: smoothPath(route),
    compass,
    folds: [
      [WIDTH / 3, 0, WIDTH / 3, height],
      [(WIDTH * 2) / 3, 0, (WIDTH * 2) / 3, height],
      [0, height / 2, WIDTH, height / 2],
    ],
  };
}

/** Tall (mobile) layout: regions stacked, landmarks zig-zag down a single strip */
export function layoutTall(regions: MapRegion[]): MapLayout {
  const WIDTH = 360;
  const PAD = 12;
  const HEAD = 48;
  const STEP = 124;
  const outRegions: LaidOutRegion[] = [];
  const landmarks: LaidOutLandmark[] = [];
  let y = PAD;
  let i = 0;
  for (const region of regions) {
    const h = HEAD + region.modules.length * STEP;
    // The route enters from above at the first landmark's x, so the ribbon sits at the other end
    outRegions.push({ track: region.track, x: PAD, y, w: WIDTH - PAD * 2, h, labelAt: i % 2 === 0 ? "end" : "start" });
    region.modules.forEach((mod, j) => {
      landmarks.push(landmark(mod, { x: i % 2 === 0 ? 112 : 248, y: y + HEAD + 26 + j * STEP }, 18));
      i++;
    });
    y += h + 12;
  }
  const compass = { x: WIDTH / 2, y: y + 44 };
  const height = y + 100;
  // Leave each landmark sideways at circle height, then come down into the next from above
  const route = landmarks.flatMap((lm, k) => (k === 0 ? [lm] : [{ x: lm.x, y: landmarks[k - 1].y }, lm]));
  return {
    width: WIDTH,
    height,
    regions: outRegions,
    landmarks,
    route: smoothPath(route),
    compass,
    folds: [
      [WIDTH / 2, 0, WIDTH / 2, height],
      [0, height / 3, WIDTH, height / 3],
      [0, (height * 2) / 3, WIDTH, (height * 2) / 3],
    ],
  };
}
