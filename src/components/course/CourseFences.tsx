import { Children, isValidElement, type ComponentPropsWithoutRef, type ReactNode } from "react";
import { Clock } from "lucide-react";
import { QuizBlock, QuizOption, QuizPrompt, QuizQuestion, QuizReveal } from "./Quiz";

// Renders the cf-* <div> trees produced by remarkCourseFences.ts. Anything else is a
// plain <div> (e.g. the raw-HTML audience-biz/audience-tech blocks).

type DivProps = ComponentPropsWithoutRef<"div"> & {
  "data-answer"?: string;
  "data-index"?: string;
  "data-scope"?: string;
  "data-time"?: string;
  "data-title"?: string;
};

const sectionLabel = "not-prose block text-[10px] font-bold uppercase tracking-widest text-sun-muted mb-1.5";

export function CourseDiv(props: DivProps) {
  const { className = "", children, ...rest } = props;
  const kind = className.split(/\s+/).find((c) => c.startsWith("cf-"));

  switch (kind) {
    // ```objectives
    case "cf-objectives":
      return (
        <div className="my-6 rounded-xl border border-sun-yellow-bdr bg-glass-card-bg shadow-glass-sm px-4 py-3">
          <div className="not-prose flex items-center justify-between gap-3 mb-2">
            <span className="text-xs font-bold uppercase tracking-widest text-sun-amber">Learning objectives</span>
            {props["data-time"] && (
              <span className="inline-flex items-center gap-1 text-xs text-sun-muted">
                <Clock className="h-3 w-3" aria-hidden="true" /> {props["data-time"]}
              </span>
            )}
          </div>
          <span className="not-prose block text-sm text-sun-muted mb-1">
            By the end of this {props["data-scope"] === "module" ? "module" : "page"} you will be able to:
          </span>
          {children}
        </div>
      );
    case "cf-outcomes":
      return <ul className="mt-0 mb-2">{children}</ul>;
    case "cf-prereqs":
      return (
        <div className="border-t border-glass-card-border pt-2">
          <span className={sectionLabel}>Prerequisites</span>
          <ul className="mt-0 mb-0">{children}</ul>
        </div>
      );
    case "cf-item":
      return <li className="my-0.5">{children}</li>;

    // ```quiz
    case "cf-quiz":
      return <QuizBlock total={Children.toArray(children).filter(isValidElement).length}>{children}</QuizBlock>;
    case "cf-question":
      return <QuizQuestion answer={props["data-answer"]}>{children}</QuizQuestion>;
    case "cf-prompt":
      return <QuizPrompt>{children}</QuizPrompt>;
    case "cf-option":
      return <QuizOption index={props["data-index"] ?? "0"}>{children}</QuizOption>;
    case "cf-model-answer":
      return <QuizReveal label="Answer">{children}</QuizReveal>;
    case "cf-explain":
      return <QuizReveal label="Why">{children}</QuizReveal>;

    // ```exercise
    case "cf-exercises":
      return <div className="cf-exercises my-6 space-y-4">{children}</div>;
    case "cf-exercise":
      return (
        <div className="cf-exercise rounded-xl border border-glass-card-border bg-glass-card-bg shadow-glass-sm px-4 py-3">
          <span className="not-prose block text-xs font-bold uppercase tracking-widest text-sun-amber mb-1">
            Exercise{props["data-title"] ? ` - ${props["data-title"]}` : ""}
          </span>
          {children}
        </div>
      );
    case "cf-task":
      return <div className="[&>*:first-child]:mt-0">{children}</div>;
    case "cf-hint":
      return <Reveal summary="Hint">{children}</Reveal>;
    case "cf-solution":
      return <Reveal summary="Solution">{children}</Reveal>;

    case "cf-error":
      return (
        <div role="alert" className="my-4 rounded-lg border border-sun-coral-bdr bg-sun-coral-dim px-3 py-2 text-sm text-sun-coral-text [&_p]:m-0">
          {children}
        </div>
      );

    default:
      return <div className={className || undefined} {...rest}>{children}</div>;
  }
}

function Reveal({ summary, children }: { summary: string; children: ReactNode }) {
  return (
    <details className="group mt-2 rounded-lg border border-glass-card-border bg-glass-panel-bg px-3 py-1.5">
      <summary className="cursor-pointer select-none text-xs font-semibold text-sun-amber py-0.5">{summary}</summary>
      <div className="pt-1 [&>*:first-child]:mt-1 [&>*:last-child]:mb-1">{children}</div>
    </details>
  );
}
