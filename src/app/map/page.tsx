import type { Metadata } from "next";
import Link from "next/link";
import { EB_Garamond } from "next/font/google";
import { Header } from "@/components/course/Header";
import { CourseMap } from "@/components/course/CourseMap";
import { getCourseMap, layoutTall, layoutWide } from "@/lib/content/courseMap";

// Serif for map labels only - loaded on this page, Inter stays the site face
const garamond = EB_Garamond({
  subsets: ["latin"],
  style: ["normal", "italic"],
  variable: "--font-map",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Course Map | Learn GenAI",
  description: "An illustrated map of every track, module and page in the Learn GenAI course.",
};

export default function MapPage() {
  const regions = getCourseMap();

  return (
    <div className={`${garamond.variable} min-h-screen bg-sun-bg`}>
      <Header />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
        <CourseMap regions={regions} wide={layoutWide(regions)} tall={layoutTall(regions)} />

        {/* The whole map as plain links: accessible, works without JavaScript, crawlable */}
        <details open className="mt-8 rounded-xl border border-sun-yellow-bdr bg-sun-surface px-4 sm:px-6 py-4">
          <summary className="cursor-pointer text-sm font-semibold text-sun-dark">Map index - every page</summary>
          <div className="mt-4 columns-1 sm:columns-2 lg:columns-3 gap-8">
            {regions.map((region) => (
              <section key={region.track} className="break-inside-avoid mb-6">
                <h2 className="text-[11px] font-bold uppercase tracking-[0.18em] text-sun-amber mb-2">{region.track}</h2>
                {region.modules.map((mod) => (
                  <div key={mod.slug} className="break-inside-avoid mb-3">
                    <h3 className="text-sm font-semibold text-sun-dark">
                      {String(mod.number).padStart(2, "0")}. {mod.title}
                    </h3>
                    <ul className="mt-1 space-y-0.5">
                      {mod.sections.flatMap((section) => section.pages).map((page) => (
                        <li key={page.href}>
                          <Link href={page.href} className="text-xs text-sun-muted hover:text-sun-dark hover:underline underline-offset-2">
                            {page.title}
                          </Link>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </section>
            ))}
          </div>
        </details>
      </main>
    </div>
  );
}
