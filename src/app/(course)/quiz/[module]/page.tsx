import Link from "next/link";
import { notFound } from "next/navigation";
import { MDXRemote } from "next-mdx-remote/rsc";
import remarkGfm from "remark-gfm";
import rehypeSlug from "rehype-slug";
import rehypeRaw from "rehype-raw";
import rehypeHighlight from "rehype-highlight";
import { getNavigationTree } from "@/lib/content/nav";
import { getModuleQuiz } from "@/lib/content/quizzes";
import { remarkRewriteMdLinks } from "@/lib/content/remarkRewriteMdLinks";
import { remarkCourseFences } from "@/lib/content/remarkCourseFences";
import { mdxComponents } from "@/components/course/MdxComponents";

interface Props {
  params: Promise<{ module: string }>;
}

export async function generateStaticParams() {
  return getNavigationTree().modules.map((mod) => ({ module: mod.slug }));
}

export async function generateMetadata({ params }: Props) {
  const { module: moduleSlug } = await params;
  const quiz = getModuleQuiz(moduleSlug);
  return quiz ? { title: `Quiz: ${quiz.module.title} | Learn GenAI` } : {};
}

export default async function QuizModulePage({ params }: Props) {
  const { module: moduleSlug } = await params;
  const quiz = getModuleQuiz(moduleSlug);
  if (!quiz) notFound();

  const { flatPages } = getNavigationTree();
  const { module: mod } = quiz;
  const label = `${String(mod.number).padStart(2, "0")} · ${mod.title}`;

  const mdxOptions = {
    parseFrontmatter: false,
    mdxOptions: {
      format: "md" as const,
      remarkPlugins: [
        remarkGfm,
        remarkCourseFences() as never,
        remarkRewriteMdLinks(quiz.basePath, flatPages) as never,
      ],
      rehypePlugins: [rehypeRaw, rehypeSlug, rehypeHighlight] as never[],
    },
  };

  return (
    <div className="flex flex-col min-h-full">
      <div className="bg-sun-bg border-b border-sun-yellow px-6 lg:px-8 py-3">
        <p className="text-xs font-bold uppercase tracking-widest text-sun-amber mb-0.5">Quiz · {label}</p>
        <h1 className="text-base font-bold text-sun-dark tracking-tight leading-tight">
          {quiz.questions > 0
            ? `${quiz.questions} questions from ${quiz.pages.length} ${quiz.pages.length === 1 ? "page" : "pages"}`
            : "No quiz questions yet"}
        </h1>
      </div>

      <div className="flex-1 px-6 lg:px-8 py-6 max-w-5xl">
        <p className="text-sm text-sun-muted mb-2">
          These are the <em>Check Yourself</em> questions from each page of the module, collected in course order.
          Each heading links back to the page the questions test.{" "}
          <Link href="/quiz/all" className="text-sun-amber font-semibold hover:underline">
            All module quizzes →
          </Link>
        </p>
        {quiz.questions > 0 ? (
          <div className="prose max-w-none">
            <MDXRemote source={quiz.markdown} options={mdxOptions} components={mdxComponents} />
          </div>
        ) : (
          <p className="text-sm text-sun-muted">
            This module has no quiz questions yet. Its review pages are in the sidebar.
          </p>
        )}
      </div>
    </div>
  );
}
