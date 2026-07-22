"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronDown, ChevronRight, PanelLeftClose, PanelLeftOpen } from "lucide-react";
import type { NavItem, NavModule, NavigationTree } from "@/types/content";

interface Props {
  nav: NavigationTree;
  mobile?: boolean;
}

function getModuleAbbr(title: string): string {
  const words = title.trim().split(/\s+/);
  if (words.length >= 2) return words.map((w) => w[0]).join("").toUpperCase().slice(0, 2);
  return title.slice(0, 3).toUpperCase();
}

function normalizePath(p: string) {
  return p.replace(/\/$/, "");
}

function containsPath(items: NavItem[], pathname: string): boolean {
  const normalized = normalizePath(pathname);
  for (const item of items) {
    if (normalizePath(item.href) === normalized) return true;
    if (item.children && containsPath(item.children, normalized)) return true;
  }
  return false;
}

function NavLeaf({ item, index }: { item: NavItem; index?: number }) {
  const pathname = usePathname();
  const active = normalizePath(pathname) === normalizePath(item.href);

  if (item.wip) {
    return (
      <span className="flex items-baseline gap-1.5 text-sm py-1 px-3 rounded-md leading-snug cursor-default select-none">
        {index !== undefined && (
          <span className="shrink-0 text-[10px] font-bold tabular-nums opacity-30">
            {String(index + 1).padStart(2, "0")}
          </span>
        )}
        <span className="text-sun-wip italic truncate">{item.title}</span>
        <span className="shrink-0 text-[9px] font-semibold uppercase tracking-wide text-sun-wip/70 border border-sun-wip/40 rounded px-1 py-px ml-auto">
          WIP
        </span>
      </span>
    );
  }

  return (
    <Link
      href={item.href}
      className={`flex items-baseline gap-1.5 text-sm py-1 px-3 rounded-md transition-colors leading-snug ${
        active
          ? "bg-sun-yellow-dim text-sun-amber font-semibold"
          : "text-sun-muted hover:text-sun-dark hover:bg-sun-yellow-dim"
      }`}
    >
      {index !== undefined && (
        <span className="shrink-0 text-[10px] font-bold tabular-nums opacity-50">
          {String(index + 1).padStart(2, "0")}
        </span>
      )}
      {item.title}
    </Link>
  );
}

function NavSection({ item }: { item: NavItem }) {
  const pathname = usePathname();
  const hasChildren = item.children && item.children.length > 0;
  const [open, setOpen] = useState(() => containsPath(item.children ?? [], pathname));

  useEffect(() => {
    const shouldOpen = containsPath(item.children ?? [], pathname);
    setOpen(shouldOpen);
  }, [pathname, item.children]);

  if (!hasChildren) return <NavLeaf item={item} />;

  return (
    <div>
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-1.5 w-full text-left text-xs font-semibold uppercase tracking-wider text-sun-muted py-1.5 px-1 hover:text-sun-dark transition-colors"
      >
        {open ? <ChevronDown className="h-3.5 w-3.5 shrink-0" /> : <ChevronRight className="h-3.5 w-3.5 shrink-0" />}
        {item.title}
      </button>
      {open && (
        <div className="pl-2 border-l border-sun-yellow-bdr space-y-0.5">
          {item.children!.map((child, i) =>
            child.children ? <NavSection key={child.href} item={child} /> : <NavLeaf key={child.href} item={child} index={i} />
          )}
        </div>
      )}
    </div>
  );
}

function ModuleSection({ mod, index }: { mod: NavModule; index: number }) {
  const pathname = usePathname();
  const [open, setOpen] = useState(() => containsPath(mod.items, pathname));

  useEffect(() => {
    const shouldOpen = containsPath(mod.items, pathname);
    setOpen(shouldOpen);
  }, [pathname, mod.items]);

  return (
    <div className="mb-1">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-1.5 w-full text-left text-xs font-bold uppercase tracking-widest text-sun-dark py-2 px-1 hover:text-sun-amber transition-colors"
      >
        {open ? <ChevronDown className="h-3.5 w-3.5 shrink-0" /> : <ChevronRight className="h-3.5 w-3.5 shrink-0" />}
        <span className="text-sun-yellow mr-0.5">{String(index + 1).padStart(2, "0")}.</span>
        {mod.title}
      </button>
      {open && (
        <div className="space-y-0.5">
          {mod.items.map((item) =>
            item.children ? <NavSection key={item.href} item={item} /> : <NavLeaf key={item.href} item={item} />
          )}
        </div>
      )}
    </div>
  );
}

function CollapsedRail({ nav, onExpand }: { nav: NavigationTree; onExpand: () => void }) {
  const pathname = usePathname();
  return (
    <div className="flex flex-col items-center py-3 gap-1">
      <button
        onClick={onExpand}
        className="p-1.5 mb-2 text-sun-muted hover:text-sun-dark hover:bg-sun-yellow-dim rounded transition-colors"
        title="Expand sidebar"
      >
        <PanelLeftOpen className="h-4 w-4" />
      </button>
      {nav.modules.map((mod) => {
        const active = containsPath(mod.items, pathname);
        return (
          <button
            key={mod.slug}
            onClick={onExpand}
            title={mod.title}
            className={`w-9 h-9 rounded-md text-[10px] font-bold transition-colors ${
              active
                ? "bg-sun-yellow text-sun-dark"
                : "text-sun-muted hover:text-sun-dark hover:bg-sun-yellow-dim"
            }`}
          >
            {getModuleAbbr(mod.title)}
          </button>
        );
      })}
    </div>
  );
}

export function Sidebar({ nav, mobile = false }: Props) {
  const [collapsed, setCollapsed] = useState(false);

  if (mobile) {
    return (
      <div className="py-5 px-4">
        {nav.modules.map((mod, i) => (
          <ModuleSection key={mod.slug} mod={mod} index={i} />
        ))}
      </div>
    );
  }

  return (
    <aside
      className={`hidden lg:flex flex-col border-r border-sun-yellow-bdr h-[calc(100vh-3.5rem)] sticky top-14 overflow-hidden transition-all duration-200 bg-glass-nav-bg backdrop-blur-glass-md ${
        collapsed ? "w-12" : "w-64"
      }`}
    >
      {collapsed ? (
        <CollapsedRail nav={nav} onExpand={() => setCollapsed(false)} />
      ) : (
        <>
          <div className="px-3 pt-3 pb-1 flex justify-end">
            <button
              onClick={() => setCollapsed(true)}
              className="p-1.5 text-sun-muted hover:text-sun-dark hover:bg-sun-yellow-dim rounded transition-colors"
              title="Collapse sidebar"
            >
              <PanelLeftClose className="h-4 w-4" />
            </button>
          </div>
          <div className="flex-1 overflow-y-auto px-4 pb-5">
            {nav.modules.map((mod, i) => (
              <ModuleSection key={mod.slug} mod={mod} index={i} />
            ))}
          </div>
          <div className="px-4 py-2.5 border-t border-sun-yellow-bdr bg-glass-panel-bg backdrop-blur-glass-sm">
            <p className="text-[10px] text-sun-wip leading-snug">
              <span className="font-semibold">WIP</span> pages are under active development - content is coming soon.
            </p>
          </div>
        </>
      )}
    </aside>
  );
}
