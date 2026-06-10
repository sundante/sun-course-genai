import Link from "next/link";
import { getNavigationTree } from "@/lib/content/nav";

export default function DashboardPage() {
  const nav = getNavigationTree();
  return (
    <main className="min-h-screen bg-sun-bg px-6 py-12 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-sun-dark mb-2">Your Dashboard</h1>
      <p className="text-sun-muted text-sm mb-8">
        Sign in to track your progress. (Auth coming in Phase 2.)
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {nav.modules.map((mod) => (
          <div
            key={mod.slug}
            className="p-5 rounded-xl border border-sun-yellow-bdr bg-white"
          >
            <h3 className="font-semibold text-sun-dark mb-2">{mod.title}</h3>
            <div className="h-1.5 bg-gray-100 rounded-full">
              <div className="h-1.5 bg-sun-yellow rounded-full" style={{ width: "0%" }} />
            </div>
            <p className="text-xs text-sun-muted mt-1">0% complete</p>
          </div>
        ))}
      </div>
    </main>
  );
}
