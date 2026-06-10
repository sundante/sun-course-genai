import { notFound } from "next/navigation";
import { MDXRemote } from "next-mdx-remote/rsc";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import rehypeSlug from "rehype-slug";
import rehypeAutolinkHeadings from "rehype-autolink-headings";
import { getAllPages, getPageWithNavigation } from "@/lib/content/loader";
import { PageNav } from "@/components/course/PageNav";
import { TableOfContents } from "@/components/course/TableOfContents";
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
    title: `${result.page.title} — Learn GenAI`,
    description: `${result.page.title} — part of the ${module} module`,
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

  return (
    <div className="flex gap-8 max-w-none">
      <article className="flex-1 min-w-0">
        <div className="prose prose-base max-w-none">
          <MDXRemote source={page.rawContent} options={mdxOptions as any} />
        </div>
        <PageNav prev={prev} next={next} />
      </article>
      {page.toc.length > 0 && (
        <aside className="hidden lg:block w-64 shrink-0">
          <TableOfContents toc={page.toc} />
        </aside>
      )}
    </div>
  );
}
