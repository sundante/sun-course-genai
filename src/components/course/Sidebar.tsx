"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { ChevronRight, ChevronDown, ChevronLeft, PanelLeftClose, PanelLeftOpen } from "lucide-react";
import type { NavigationTree, NavItem, NavModule } from "@/types/content";

function containsPath(items: NavItem[], path: string): boolean {
  return items.some(
    (item) => item.href === path || (item.children ? containsPath(item.children, path) : false)
  );
}

function NavLeaf({ item, pathname }: { item: NavItem; pathname: string }) {
  const active = pathname === item.href;
  return (
    <Link
      href={item.href}
      className={`block text-sm py-1 px-3 rounded-md transition-colors leading-snug ${
        active
          ? "bg-sun-yellow-dim text-sun-amber font-semibold"
          : "text-sun-muted hover:text-sun-dark hover:bg-sun-yellow-dim"
      }`}
    >
      {item.title}
    </Link>
  );
}

function NavSection({
  item,
  depth = 0,
  pathname,
}: {
  item: NavItem;
  depth?: number;
  pathname: string;
}) {
  const [open, setOpen] = useState(() =>
    item.children ? containsPath(item.children, pathname) : false
  );
  if (!item.children) return <NavLeaf item={item} pathname={pathname} />;
  return (
    <div>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 w-full text-left text-xs font-semibold uppercase tracking-wider text-sun-muted py-1.5 px-1 hover:text-sun-dark transition-colors"
      >
        {open ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
        {item.title}
      </button>
      {open && (
        <div className="pl-2 border-l border-sun-yellow-bdr space-y-0.5">
          {item.children.map((child, i) => (
            <NavSection key={i} item={child} depth={depth + 1} pathname={pathname} />
          ))}
        </div>
      )}
    </div>
  );
}

function ModuleSection({
  mod,
  pathname,
}: {
  mod: NavModule;
  pathname: string;
}) {
  const [open, setOpen] = useState(() => containsPath(mod.items, pathname));
  return (
    <div className="mb-5">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 w-full text-left text-xs font-bold uppercase tracking-widest text-sun-dark py-2 px-1 hover:text-sun-amber transition-colors"
      >
        {open ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
        {mod.title}
      </button>
      {open && (
        <div className="space-y-0.5">
          {mod.items.map((item, i) => (
            <NavSection key={i} item={item} pathname={pathname} />
          ))}
        </div>
      )}
    </div>
  );
}

/** Abbreviation shown in the collapsed rail — up to 3 chars */
function moduleAbbr(title: string): string {
  const words = title.split(" ");
  if (words.length === 1) return title.slice(0, 3).toUpperCase();
  return words
    .slice(0, 2)
    .map((w) => w[0])
    .join("")
    .toUpperCase();
}

function CollapsedRail({
  nav,
  pathname,
  onExpand,
}: {
  nav: NavigationTree;
  pathname: string;
  onExpand: (slug?: string) => void;
}) {
  return (
    <div className="flex flex-col items-center py-3 gap-1">
      <button
        onClick={() => onExpand()}
        title="Expand sidebar"
        className="p-1.5 mb-2 text-sun-muted hover:text-sun-dark hover:bg-sun-yellow-dim rounded transition-colors"
      >
        <PanelLeftOpen className="h-4 w-4" />
      </button>
      {nav.modules.map((mod) => {
        const active = containsPath(mod.items, pathname);
        return (
          <button
            key={mod.slug}
            title={mod.title}
            onClick={() => onExpand(mod.slug)}
            className={`w-9 h-9 rounded-md text-[10px] font-bold transition-colors ${
              active
                ? "bg-sun-yellow text-sun-dark"
                : "text-sun-muted hover:text-sun-dark hover:bg-sun-yellow-dim"
            }`}
          >
            {moduleAbbr(mod.title)}
          </button>
        );
      })}
    </div>
  );
}

export function Sidebar({ nav, mobile = false }: { nav: NavigationTree; mobile?: boolean }) {
  const pathname = usePathname();
  const [expanded, setExpanded] = useState(true);
  const [focusSlug, setFocusSlug] = useState<string | undefined>();

  function handleExpand(slug?: string) {
    setFocusSlug(slug);
    setExpanded(true);
  }

  const inner = expanded ? (
    <div className="flex flex-col h-full">
      {/* Collapse toggle */}
      <div className="flex justify-end px-3 pt-3 pb-1 shrink-0">
        <button
          onClick={() => setExpanded(false)}
          title="Collapse sidebar"
          className="p-1.5 text-sun-muted hover:text-sun-dark hover:bg-sun-yellow-dim rounded transition-colors"
        >
          <PanelLeftClose className="h-4 w-4" />
        </button>
      </div>
      {/* Scrollable nav */}
      <div className="flex-1 overflow-y-auto px-4 pb-5">
        {nav.modules.map((mod) => (
          <ModuleSection
            key={mod.slug}
            mod={mod}
            pathname={pathname}
          />
        ))}
      </div>
    </div>
  ) : (
    <CollapsedRail nav={nav} pathname={pathname} onExpand={handleExpand} />
  );

  if (mobile) {
    return (
      <div className="py-5 px-4">
        {nav.modules.map((mod) => (
          <ModuleSection key={mod.slug} mod={mod} pathname={pathname} />
        ))}
      </div>
    );
  }

  return (
    <aside
      className={`hidden lg:block shrink-0 border-r border-sun-yellow-bdr h-[calc(100vh-3.5rem)] sticky top-14 overflow-hidden transition-all duration-200 ${
        expanded ? "w-64" : "w-12"
      }`}
    >
      {inner}
    </aside>
  );
}
