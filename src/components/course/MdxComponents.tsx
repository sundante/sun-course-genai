import { MermaidDiagram } from "./MermaidDiagram";
import { ComponentPropsWithoutRef, ReactElement } from "react";

function CustomPre(props: ComponentPropsWithoutRef<"pre">) {
  const child = props.children as ReactElement<ComponentPropsWithoutRef<"code">>;

  if (
    child &&
    typeof child === "object" &&
    "props" in child &&
    typeof child.props.className === "string" &&
    child.props.className.includes("language-mermaid")
  ) {
    const value =
      typeof child.props.children === "string"
        ? child.props.children.trim()
        : "";
    return <MermaidDiagram value={value} />;
  }

  return <pre {...props} />;
}

export const mdxComponents = {
  pre: CustomPre,
};
