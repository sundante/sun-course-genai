"use client";

import { useEffect, useMemo, useRef, useState, useSyncExternalStore } from "react";
import { useRouter } from "next/navigation";
import * as Dialog from "@radix-ui/react-dialog";
import MiniSearch, { type SearchResult } from "minisearch";
import { Search as SearchIcon, CornerDownLeft } from "lucide-react";
import { cn } from "@/lib/utils";
import type { SearchSection } from "@/lib/content/searchIndex";

const MAX_RESULTS = 30;

// The index is fetched and built once per session, on first open
let indexPromise: Promise<MiniSearch<SearchSection>> | null = null;

function loadIndex(): Promise<MiniSearch<SearchSection>> {
  indexPromise ??= fetch("/search-index.json")
    .then((res) => {
      if (!res.ok) throw new Error(`search-index.json: ${res.status}`);
      return res.json() as Promise<SearchSection[]>;
    })
    .then((sections) => {
      const index = new MiniSearch<SearchSection>({
        fields: ["h", "p", "m", "x", "c"],
        storeFields: ["p", "m", "h", "u", "x"],
        searchOptions: {
          boost: { h: 3, p: 2, m: 1.5, c: 0.5 },
          combineWith: "AND",
          // Only the word being typed is a prefix; typo tolerance for longer words
          prefix: (_term, i, terms) => i === terms.length - 1,
          fuzzy: (term) => (term.length > 4 ? 0.2 : false),
        },
      });
      index.addAll(sections);
      return index;
    })
    .catch((err) => {
      indexPromise = null; // allow a retry on next open
      throw err;
    });
  return indexPromise;
}

type Hit = SearchResult & Pick<SearchSection, "p" | "m" | "h" | "u" | "x">;

function escapeRegExp(s: string) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/** A window of the section text around the first match, with matches marked */
function Snippet({ text, terms }: { text: string; terms: string[] }) {
  if (!text) return null;
  const pattern = new RegExp(`(${terms.map(escapeRegExp).join("|")})`, "gi");
  const first = terms.length ? text.search(pattern) : -1;
  pattern.lastIndex = 0;
  const start = Math.max(0, first - 60);
  let snippet = text.slice(start, start + 180);
  if (start > 0) snippet = "..." + snippet.replace(/^\S*\s/, "");
  if (start + 180 < text.length) snippet = snippet.replace(/\s\S*$/, "") + "...";
  const parts = terms.length ? snippet.split(pattern) : [snippet];
  return (
    <p className="text-xs text-sun-muted leading-relaxed line-clamp-2">
      {parts.map((part, i) =>
        i % 2 === 1 ? (
          <mark key={i} className="bg-sun-yellow-dim text-sun-dark rounded-sm px-0.5">
            {part}
          </mark>
        ) : (
          part
        )
      )}
    </p>
  );
}

const subscribeNoop = () => () => {};

export function Search() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [index, setIndex] = useState<MiniSearch<SearchSection> | null>(null);
  const [error, setError] = useState(false);
  const [active, setActive] = useState(0);
  const listRef = useRef<HTMLUListElement>(null);

  const isMac = useSyncExternalStore(
    subscribeNoop,
    () => /Mac|iPhone|iPad/.test(navigator.platform),
    () => true
  );

  // ⌘K / Ctrl+K toggles; "/" opens unless the user is typing somewhere
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((o) => !o);
        return;
      }
      const el = e.target as HTMLElement;
      const typing = el.isContentEditable || ["INPUT", "TEXTAREA", "SELECT"].includes(el.tagName);
      if (e.key === "/" && !typing && !e.metaKey && !e.ctrlKey && !e.altKey) {
        e.preventDefault();
        setOpen(true);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  function onOpenChange(next: boolean) {
    setOpen(next);
    if (!next) setError(false); // closing clears a load error so reopening retries
  }

  // Load on first open, whether from the button or a shortcut
  useEffect(() => {
    if (open && !index && !error) loadIndex().then(setIndex, () => setError(true));
  }, [open, index, error]);

  const hits = useMemo<Hit[]>(() => {
    const q = query.trim();
    if (!index || q.length < 2) return [];
    return index.search(q).slice(0, MAX_RESULTS) as Hit[];
  }, [index, query]);

  function updateQuery(value: string) {
    setQuery(value);
    setActive(0);
  }

  function go(hit: Hit | undefined) {
    if (!hit) return;
    setOpen(false);
    router.push(hit.u);
  }

  function onInputKey(e: React.KeyboardEvent) {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      if (!hits.length) return;
      const next = (active + (e.key === "ArrowDown" ? 1 : -1) + hits.length) % hits.length;
      setActive(next);
      listRef.current?.children[next]?.scrollIntoView({ block: "nearest" });
    } else if (e.key === "Enter") {
      e.preventDefault();
      go(hits[active]);
    }
  }

  const q = query.trim();

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Trigger asChild>
        <button
          type="button"
          aria-label="Search the course"
          className="inline-flex items-center gap-2 h-8 rounded-md border border-sun-yellow-bdr bg-sun-surface px-2 sm:px-2.5 text-xs text-sun-muted hover:text-sun-dark hover:border-sun-yellow transition-colors shrink-0"
        >
          <SearchIcon className="h-3.5 w-3.5" />
          <span className="hidden sm:inline">Search course</span>
          <kbd className="hidden sm:inline font-mono text-[10px] border border-sun-yellow-bdr rounded px-1 py-px">
            {isMac ? "⌘K" : "Ctrl K"}
          </kbd>
        </button>
      </Dialog.Trigger>

      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-glass-scrim backdrop-blur-glass-sm data-[state=open]:animate-in data-[state=open]:fade-in-0" />
        <Dialog.Content
          className="fixed z-50 left-1/2 top-4 sm:top-[12vh] -translate-x-1/2 w-[calc(100vw-2rem)] max-w-2xl bg-sun-surface border border-glass-modal-border rounded-xl shadow-glass-lg overflow-hidden flex flex-col max-h-[calc(100vh-2rem)] sm:max-h-[70vh] data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:zoom-in-95"
        >
          <Dialog.Title className="sr-only">Search the course</Dialog.Title>
          <Dialog.Description className="sr-only">
            Type to search every page. Use the arrow keys to move through results and Enter to open one.
          </Dialog.Description>

          <div className="flex items-center gap-3 px-4 border-b border-sun-yellow-bdr">
            <SearchIcon className="h-4 w-4 text-sun-muted shrink-0" />
            <input
              autoFocus
              // Reopening keeps the last query, selected so typing replaces it
              onFocus={(e) => e.target.select()}
              value={query}
              onChange={(e) => updateQuery(e.target.value)}
              onKeyDown={onInputKey}
              placeholder="Search notes, labs, Q&A..."
              aria-label="Search query"
              aria-controls="search-results"
              aria-activedescendant={hits[active] ? `search-hit-${hits[active].id}` : undefined}
              className="flex-1 h-12 bg-transparent text-sm text-sun-dark placeholder:text-sun-muted outline-none"
            />
            <kbd className="font-mono text-[10px] text-sun-muted border border-sun-yellow-bdr rounded px-1.5 py-0.5">Esc</kbd>
          </div>

          <div className="overflow-y-auto">
            {error ? (
              <p className="px-4 py-8 text-center text-sm text-sun-muted">Couldn&apos;t load the search index. Close and try again.</p>
            ) : !index ? (
              <p className="px-4 py-8 text-center text-sm text-sun-muted">Loading search index...</p>
            ) : q.length < 2 ? (
              <p className="px-4 py-8 text-center text-sm text-sun-muted">
                Search every note, lab and Q&amp;A bank - try &quot;kv cache&quot;, &quot;lora&quot; or &quot;mcp&quot;.
              </p>
            ) : hits.length === 0 ? (
              <p className="px-4 py-8 text-center text-sm text-sun-muted">No results for &quot;{q}&quot;.</p>
            ) : (
              <ul id="search-results" ref={listRef} role="listbox" className="p-2">
                {hits.map((hit, i) => (
                  <li
                    key={hit.id}
                    id={`search-hit-${hit.id}`}
                    role="option"
                    aria-selected={i === active}
                    onMouseMove={() => setActive(i)}
                    onClick={() => go(hit)}
                    className={cn(
                      "cursor-pointer rounded-lg px-3 py-2.5 border-l-2 flex gap-3 items-start",
                      i === active ? "bg-sun-yellow-dim border-sun-yellow" : "border-transparent"
                    )}
                  >
                    <div className="min-w-0 flex-1 space-y-0.5">
                      <p className="text-[11px] uppercase tracking-wide text-sun-amber truncate">
                        {hit.m} <span aria-hidden="true">›</span> {hit.p}
                      </p>
                      <p className="text-sm font-semibold text-sun-dark truncate">{hit.h || hit.p}</p>
                      <Snippet text={hit.x} terms={hit.terms} />
                    </div>
                    {i === active && <CornerDownLeft className="h-3.5 w-3.5 text-sun-muted mt-1 shrink-0" aria-hidden="true" />}
                  </li>
                ))}
              </ul>
            )}
          </div>

          {hits.length > 0 && (
            <div className="px-4 py-2 border-t border-sun-yellow-bdr text-[11px] text-sun-muted flex gap-4">
              <span>
                {hits.length}
                {hits.length === MAX_RESULTS ? "+" : ""} results
              </span>
              <span className="hidden sm:inline">↑↓ to move · Enter to open</span>
            </div>
          )}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
