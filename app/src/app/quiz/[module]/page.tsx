import { UnderDevelopment } from "@/components/course/UnderDevelopment";
import { getNavigationTree } from "@/lib/content/nav";

interface Props {
  params: Promise<{ module: string }>;
}

export function generateStaticParams() {
  const { modules } = getNavigationTree();
  return modules.map((m) => ({ module: m.slug }));
}

export default async function QuizModulePage({ params }: Props) {
  const { module } = await params;
  const title = module.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  return (
    <UnderDevelopment
      title={`${title} Quiz - Coming Soon`}
      description="Module quizzes are being built in Phase 3."
    />
  );
}
