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
  return (
    <main className="min-h-screen bg-sun-bg flex items-center justify-center px-4">
      <div className="text-center max-w-sm">
        <div className="text-4xl mb-4">🃏</div>
        <h1 className="text-2xl font-bold text-sun-dark mb-2 capitalize">
          {module.replace(/-/g, " ")} Quiz
        </h1>
        <p className="text-sun-muted text-sm">
          Module quizzes are coming in Phase 3.
        </p>
      </div>
    </main>
  );
}
