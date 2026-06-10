"use client";

import { useEffect, useState } from "react";
import type { TocItem } from "@/types/content";

export function TableOfContents({ toc }: { toc: TocItem[] }) {
  const [activeId, setActiveId] = useState<string>("");

  useEffect(() => {
    const headings = toc.map((t) => document.getElementById(t.id)).filter(Boolean) as HTMLElement[];
    if (!headings.length) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries.filter((e) => e.isIntersecting);
        if (visible.length) setActiveId(visible[0].target.id);
      },
      { rootMargin: "0px 0px -60% 0px", threshold: 0 }
    );

    headings.forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, [toc]);

  return (
    <div className="sticky top-20 py-2">
      <p className="text-xs font-bold uppercase tracking-widest text-sun-muted mb-4 px-1">
        On this page
      </p>
      <ul className="space-y-0.5">
        {toc.map((item) => {
          const active = item.id === activeId;
          return (
            <li key={item.id} style={{ paddingLeft: `${(item.level - 1) * 10}px` }}>
              <a
                href={`#${item.id}`}
                className={`block text-sm py-1 px-2 rounded-md transition-colors leading-snug line-clamp-2 ${
                  active
                    ? "text-sun-amber font-semibold bg-sun-yellow-dim"
                    : "text-sun-muted hover:text-sun-dark hover:bg-sun-yellow-dim"
                }`}
              >
                {item.text}
              </a>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
