"use client";

import type { TocItem } from "@/types/content";

export function TableOfContents({ toc }: { toc: TocItem[] }) {
  return (
    <div className="sticky top-20">
      <p className="text-xs font-bold uppercase tracking-widest text-sun-muted mb-3">
        On this page
      </p>
      <ul className="space-y-1">
        {toc.map((item) => (
          <li key={item.id} style={{ paddingLeft: `${(item.level - 1) * 12}px` }}>
            <a
              href={`#${item.id}`}
              className="text-xs text-sun-muted hover:text-sun-dark transition-colors line-clamp-2"
            >
              {item.text}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}
