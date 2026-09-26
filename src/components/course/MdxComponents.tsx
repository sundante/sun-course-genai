import { MermaidDiagram } from "./MermaidDiagram";
import { AgentUseCaseMindmap } from "./AgentUseCaseMindmap";
import { CourseDiv } from "./CourseFences";
import { ComponentPropsWithoutRef, ReactElement } from "react";

function CustomPre(props: ComponentPropsWithoutRef<"pre">) {
  const child = props.children as ReactElement<ComponentPropsWithoutRef<"code">>;

  if (
    child &&
    typeof child === "object" &&
    "props" in child &&
    typeof child.props.className === "string"
  ) {
    const className = child.props.className;

    if (className.includes("language-mermaid")) {
      const value =
        typeof child.props.children === "string"
          ? child.props.children.trim()
          : "";
      return <MermaidDiagram value={value} />;
    }

    if (className.includes("language-agent-navigator")) {
      return <AgentUseCaseMindmap />;
    }
  }

  return <pre {...props} />;
}

export const mdxComponents = {
  pre: CustomPre,
  // ```objectives / ```quiz / ```exercise fences arrive as cf-* divs (remarkCourseFences.ts)
  div: CourseDiv,
};
