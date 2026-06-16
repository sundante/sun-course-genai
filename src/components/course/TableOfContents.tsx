"use client";

import { useEffect, useState } from "react";
import type { TocItem } from "@/types/content";

interface Props {
  toc: TocItem[];
}

export function TableOfContents({ toc }: Props) {
  const [activeId, setActiveId] = useState<string>("");

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries.filter((e) => e.isIntersecting);
        if (visible.length) setActiveId(visible[0].target.id);
      },
      { rootMargin: "0px 0px -60% 0px", threshold: 0 }
    );

    toc.forEach(({ id }) => {
      const el = document.getElementById(id);
      if (el) observer.observe(el);
    });

    return () => observer.disconnect();
  }, [toc]);

  return (
    <div className="sticky top-20 py-2 overflow-y-auto max-h-[calc(100vh-6rem)]">
      <p className="text-xs font-bold uppercase tracking-widest text-sun-muted mb-4 px-1">
        On this page
      </p>
      <ul className="space-y-0.5">
        {toc.map((item) => {
          const active = activeId === item.id;
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
