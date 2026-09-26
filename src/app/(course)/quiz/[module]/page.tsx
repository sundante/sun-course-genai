import { UnderDevelopment } from "@/components/course/UnderDevelopment";
import { getNavigationTree } from "@/lib/content/nav";

export async function generateStaticParams() {
  return getNavigationTree().modules.map((mod) => ({ module: mod.slug }));
}

export default function QuizModulePage() {
  return (
    <UnderDevelopment
      title="Module Quiz - Coming Soon"
      description="Module-specific quizzes are under development. Check back soon."
    />
  );
}
