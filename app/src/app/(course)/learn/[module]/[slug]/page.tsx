import { notFound } from "next/navigation";
import { MDXRemote } from "next-mdx-remote/rsc";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import rehypeSlug from "rehype-slug";
import rehypeAutolinkHeadings from "rehype-autolink-headings";
import { getAllPages, getPageWithNavigation } from "@/lib/content/loader";
import { PageNav } from "@/components/course/PageNav";
import { TableOfContents } from "@/components/course/TableOfContents";
import { AudienceToggle } from "@/components/course/AudienceToggle";
import type { Metadata } from "next";

interface Props {
  params: Promise<{ module: string; slug: string }>;
}

export async function generateStaticParams() {
  const pages = getAllPages();
  return pages.map((p) => ({ module: p.module, slug: p.slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { module, slug } = await params;
  const result = getPageWithNavigation(module, slug);
  if (!result) return {};
  return {
    title: `${result.page.title} - Learn GenAI`,
    description: `${result.page.title} - part of the ${module} module`,
  };
}

const mdxOptions = {
  parseFrontmatter: false,
  mdxOptions: {
    format: "md" as const,
    remarkPlugins: [remarkGfm] as any[],
    rehypePlugins: [
      rehypeSlug,
      [rehypeAutolinkHeadings, { behavior: "wrap" }],
      rehypeHighlight,
    ] as any[],
  },
};

export default async function CoursePage({ params }: Props) {
  const { module, slug } = await params;
  const result = getPageWithNavigation(module, slug);
  if (!result) notFound();

  const { page, prev, next } = result;

  const moduleLabel = module
    .split("-")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");

  return (
    <div className="flex flex-col min-h-full">

      {/* Dark title banner - full width */}
      <div className="bg-sun-dark border-b-2 border-sun-yellow px-6 lg:px-8 py-3">
        <p className="text-xs font-bold uppercase tracking-widest text-sun-yellow mb-0.5">
          {moduleLabel}
        </p>
        <h1 className="text-base font-bold text-white tracking-tight leading-tight">{page.title}</h1>
      </div>

      {/* Content row */}
      <div className="flex gap-8 flex-1 px-6 lg:px-8 py-6">
        <div className="flex-1 min-w-0">
          <AudienceToggle />
          <article>
            <div className="prose prose-base max-w-none">
              <MDXRemote source={page.rawContent} options={mdxOptions as any} />
            </div>
          </article>
        </div>
        {page.toc.length > 0 && (
          <aside className="hidden lg:block w-64 shrink-0">
            <TableOfContents toc={page.toc} />
          </aside>
        )}
      </div>

      {/* Sticky prev/next footer */}
      <div className="sticky bottom-0 z-10 bg-sun-bg border-t-2 border-sun-yellow px-6 lg:px-8 py-3">
        <PageNav prev={prev} next={next} className="flex justify-between" />
      </div>

    </div>
  );
}
