"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, Home } from "lucide-react";

interface UnderDevelopmentProps {
  title?: string;
  description?: string;
}

export function UnderDevelopment({
  title = "Under Development",
  description = "This page is being built. Check back soon.",
}: UnderDevelopmentProps) {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-sun-bg flex items-center justify-center px-4">
      <div className="text-center max-w-md">
        {/* Animated blocks */}
        <div className="flex items-end justify-center gap-2 mb-10 h-16">
          <div
            className="w-4 bg-sun-yellow rounded-sm animate-bounce"
            style={{ height: "2.5rem", animationDelay: "0ms" }}
          />
          <div
            className="w-4 bg-sun-yellow rounded-sm animate-bounce"
            style={{ height: "3.5rem", animationDelay: "150ms" }}
          />
          <div
            className="w-4 bg-sun-yellow rounded-sm animate-bounce"
            style={{ height: "2rem", animationDelay: "300ms" }}
          />
          <div
            className="w-4 bg-sun-yellow rounded-sm animate-bounce"
            style={{ height: "4rem", animationDelay: "100ms" }}
          />
          <div
            className="w-4 bg-sun-yellow rounded-sm animate-bounce"
            style={{ height: "2.5rem", animationDelay: "250ms" }}
          />
        </div>

        <h1 className="text-2xl font-bold text-sun-dark mb-3">{title}</h1>
        <p className="text-sun-muted text-sm mb-8 leading-relaxed">{description}</p>

        <div className="flex items-center justify-center gap-3">
          <button
            onClick={() => router.back()}
            className="inline-flex items-center gap-1.5 text-sm font-medium text-sun-muted hover:text-sun-dark border border-sun-yellow-bdr hover:border-sun-yellow hover:bg-sun-yellow-dim rounded-md px-4 py-2 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            Go Back
          </button>
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 text-sm font-semibold bg-sun-yellow text-sun-dark hover:bg-sun-yellow-dk rounded-md px-4 py-2 transition-colors"
          >
            <Home className="h-4 w-4" />
            Go Home
          </Link>
        </div>
      </div>
    </div>
  );
}
