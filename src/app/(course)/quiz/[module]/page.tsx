import { UnderDevelopment } from "@/components/course/UnderDevelopment";

export async function generateStaticParams() {
  return [
    { module: "llm-models" },
    { module: "prompt-engineering" },
    { module: "rag" },
    { module: "mcp" },
    { module: "agents" },
    { module: "agentic-ai" },
    { module: "knowledge-check" },
  ];
}

export default function QuizModulePage() {
  return (
    <UnderDevelopment
      title="Module Quiz — Coming Soon"
      description="Module-specific quizzes are under development. Check back soon."
    />
  );
}
