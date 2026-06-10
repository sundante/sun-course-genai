import Link from "next/link";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function Header() {
  return (
    <header className="sticky top-0 z-40 bg-white border-b-2 border-sun-yellow shadow-sm">
      <div className="flex items-center h-14 px-4 gap-4">
        <Link href="/" className="font-bold text-sun-dark text-sm tracking-tight shrink-0">
          Learn GenAI
        </Link>
        <div className="flex-1" />
        <nav className="flex items-center gap-2">
          <Link
            href="/quiz/all"
            className={cn(buttonVariants({ variant: "ghost", size: "sm" }), "text-xs")}
          >
            Quiz Mode
          </Link>
          <Link
            href="/dashboard"
            className={cn(buttonVariants({ variant: "ghost", size: "sm" }), "text-xs")}
          >
            Dashboard
          </Link>
          <Link
            href="/login"
            className={cn(
              buttonVariants({ size: "sm" }),
              "text-xs bg-sun-yellow text-sun-dark hover:bg-sun-yellow-dk border-0"
            )}
          >
            Sign in
          </Link>
        </nav>
      </div>
    </header>
  );
}
