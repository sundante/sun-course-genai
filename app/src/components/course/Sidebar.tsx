"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { ChevronRight, ChevronDown } from "lucide-react";
import type { NavigationTree, NavItem, NavModule } from "@/types/content";

function NavLeaf({ item }: { item: NavItem }) {
  const pathname = usePathname();
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

function NavSection({ item, depth = 0 }: { item: NavItem; depth?: number }) {
  const [open, setOpen] = useState(true);
  if (!item.children) return <NavLeaf item={item} />;
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
            <NavSection key={i} item={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  );
}

function ModuleSection({ mod }: { mod: NavModule }) {
  const [open, setOpen] = useState(true);
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
            <NavSection key={i} item={item} />
          ))}
        </div>
      )}
    </div>
  );
}

export function Sidebar({ nav, mobile = false }: { nav: NavigationTree; mobile?: boolean }) {
  const inner = (
    <div className="py-5 px-4">
      {nav.modules.map((mod) => (
        <ModuleSection key={mod.slug} mod={mod} />
      ))}
    </div>
  );

  if (mobile) return inner;

  return (
    <aside className="hidden lg:block w-72 shrink-0 border-r border-sun-yellow-bdr h-[calc(100vh-3.5rem)] sticky top-14 overflow-y-auto">
      {inner}
    </aside>
  );
}
