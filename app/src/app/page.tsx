import Link from "next/link";
import { buttonVariants } from "@/components/ui/button";
import { getNavigationTree } from "@/lib/content/nav";
import { cn } from "@/lib/utils";

export default function HomePage() {
  const nav = getNavigationTree();

  return (
    <main className="min-h-screen bg-sun-bg">
      {/* Header */}
      <header className="bg-white border-b-2 border-sun-yellow px-6 h-14 flex items-center justify-between">
        <span className="font-bold text-sun-dark tracking-tight">Learn GenAI</span>
        <div className="flex gap-2">
          <Link
            href="/quiz/all"
            className={cn(buttonVariants({ variant: "ghost", size: "sm" }), "text-xs")}
          >
            Quiz Mode
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
        </div>
      </header>

      {/* Hero */}
      <section className="px-6 py-20 max-w-3xl mx-auto text-center">
        <h1 className="text-4xl font-bold text-sun-dark mb-4 tracking-tight">
          Generative AI to Agentic AI
        </h1>
        <p className="text-sun-muted text-lg mb-8 leading-relaxed">
          A structured curriculum covering the full AI stack — LLMs, Prompts, RAG, MCP, Agents,
          and Agentic Systems.
        </p>
        <div className="flex gap-3 justify-center flex-wrap">
          <Link
            href="/learn/llm-models/index"
            className={cn(
              buttonVariants(),
              "bg-sun-yellow text-sun-dark hover:bg-sun-yellow-dk border-0 font-semibold"
            )}
          >
            Start Learning
          </Link>
          <Link
            href="/quiz/all"
            className={cn(buttonVariants({ variant: "outline" }), "border-sun-yellow-bdr")}
          >
            Practice Quiz
          </Link>
        </div>
      </section>

      {/* Module grid */}
      <section className="px-6 pb-20 max-w-4xl mx-auto">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {nav.modules.map((mod) => {
            const firstLeaf = mod.items.find((i) => i.filePath);
            const firstSlug = firstLeaf?.filePath
              ?.split("/")
              .pop()
              ?.replace(".md", "")
              .toLowerCase()
              .replace(/_/g, "-");
            const href = firstSlug ? `/learn/${mod.slug}/${firstSlug}` : "#";
            return (
              <Link
                key={mod.slug}
                href={href}
                className="group block p-5 rounded-xl border border-sun-yellow-bdr bg-white hover:border-sun-yellow hover:shadow-md transition-all"
              >
                <h3 className="font-semibold text-sun-dark mb-1 group-hover:text-sun-amber transition-colors">
                  {mod.title}
                </h3>
                <p className="text-xs text-sun-muted">
                  {mod.items.reduce((acc, item) => acc + (item.children?.length ?? 1), 0)} topics
                </p>
              </Link>
            );
          })}
        </div>
      </section>
    </main>
  );
}
