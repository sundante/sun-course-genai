import { notFound } from "next/navigation";
import { MDXRemote } from "next-mdx-remote/rsc";
import remarkGfm from "remark-gfm";
import rehypeSlug from "rehype-slug";
import rehypeAutolinkHeadings from "rehype-autolink-headings";
import rehypeHighlight from "rehype-highlight";
import { getAllPages, getPageWithNavigation } from "@/lib/content/loader";
import { getNavigationTree } from "@/lib/content/nav";
import { remarkRewriteMdLinks } from "@/lib/content/remarkRewriteMdLinks";
import { AudienceToggle } from "@/components/course/AudienceToggle";
import { TableOfContents } from "@/components/course/TableOfContents";
import { PageNav } from "@/components/course/PageNav";

interface Props {
  params: Promise<{ module: string; slug: string }>;
}

export async function generateStaticParams() {
  const pages = getAllPages();
  return pages.map((p) => ({ module: p.module, slug: p.slug }));
}

export async function generateMetadata({ params }: Props) {
  const { module: moduleSlug, slug } = await params;
  const result = getPageWithNavigation(moduleSlug, slug);
  if (!result) return {};
  return { title: `${result.page.title} | Learn GenAI` };
}

export default async function CoursePage({ params }: Props) {
  const { module: moduleSlug, slug } = await params;
  const result = getPageWithNavigation(moduleSlug, slug);
  if (!result) notFound();

  const { page, prev, next } = result;
  const { flatPages } = getNavigationTree();

  const moduleLabel = moduleSlug
    .split("-")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");

  const mdxOptions = {
    parseFrontmatter: false,
    mdxOptions: {
      format: "md" as const,
      remarkPlugins: [
        remarkGfm,
        remarkRewriteMdLinks(page.filePath, flatPages) as never,
      ],
      rehypePlugins: [
        rehypeSlug,
        [rehypeAutolinkHeadings, { behavior: "wrap" }],
        rehypeHighlight,
      ] as never[],
    },
  };

  return (
    <div className="flex flex-col min-h-full">
      {/* Dark title banner */}
      <div className="bg-sun-dark border-b-2 border-sun-yellow px-6 lg:px-8 py-3">
        <p className="text-xs font-bold uppercase tracking-widest text-sun-yellow mb-0.5">
          {moduleLabel}
        </p>
        <h1 className="text-base font-bold text-white tracking-tight leading-tight">
          {page.title}
        </h1>
      </div>

      {/* Content row */}
      <div className="flex gap-8 flex-1 px-6 lg:px-8 py-6">
        <div className="flex-1 min-w-0">
          <AudienceToggle />
          <article>
            <div className="prose prose-base max-w-none">
              <MDXRemote source={page.rawContent} options={mdxOptions} />
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
