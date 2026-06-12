import Link from "next/link";
import { ChevronLeft, ChevronRight } from "lucide-react";
import type { PageRef } from "@/types/content";

interface Props {
  prev?: PageRef;
  next?: PageRef;
  className?: string;
}

export function PageNav({ prev, next, className }: Props) {
  return (
    <nav className={className ?? "flex justify-between mt-12 pt-6 border-t border-sun-yellow-bdr"}>
      {prev ? (
        <Link
          href={prev.href}
          className="group flex items-center gap-2 text-sm text-sun-muted hover:text-sun-dark transition-colors max-w-[45%]"
        >
          <ChevronLeft className="h-4 w-4 shrink-0 text-sun-yellow group-hover:text-sun-yellow-dk" />
          <div>
            <div className="text-xs uppercase tracking-wider mb-0.5">Previous</div>
            <div className="font-medium line-clamp-2">{prev.title}</div>
          </div>
        </Link>
      ) : (
        <div />
      )}
      {next && (
        <Link
          href={next.href}
          className="group flex items-center gap-2 text-sm text-sun-muted hover:text-sun-dark transition-colors text-right max-w-[45%]"
        >
          <div>
            <div className="text-xs uppercase tracking-wider mb-0.5">Next</div>
            <div className="font-medium line-clamp-2">{next.title}</div>
          </div>
          <ChevronRight className="h-4 w-4 shrink-0 text-sun-yellow group-hover:text-sun-yellow-dk" />
        </Link>
      )}
    </nav>
  );
}
