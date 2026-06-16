"use client";

import { useState } from "react";
import { Menu } from "lucide-react";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Sidebar } from "./Sidebar";
import type { NavigationTree } from "@/types/content";

interface Props {
  nav: NavigationTree;
}

export function MobileNav({ nav }: Props) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <div className="lg:hidden flex items-center justify-between px-5 py-3 border-b border-sun-yellow-bdr bg-white">
        <span className="text-sm font-medium text-sun-muted">Contents</span>
        <button
          onClick={() => setOpen(true)}
          className="flex items-center gap-2 text-sm font-semibold text-sun-dark hover:text-sun-amber transition-colors"
        >
          <Menu className="h-4 w-4" />
          Menu
        </button>
      </div>

      <Sheet open={open} onOpenChange={setOpen}>
        <SheetContent side="left" className="p-0 w-96">
          <SheetHeader className="px-5 py-4 border-b border-sun-yellow-bdr">
            <SheetTitle className="text-base font-bold text-sun-dark">Navigation</SheetTitle>
          </SheetHeader>
          <div className="overflow-y-auto h-full pb-12">
            <Sidebar nav={nav} mobile />
          </div>
        </SheetContent>
      </Sheet>
    </>
  );
}
