import type { Plugin } from "unified";
import type { Root } from "mdast";
import { visit } from "unist-util-visit";
import path from "path";
import type { PageRef } from "@/types/content";

export function remarkRewriteMdLinks(
  currentFilePath: string,
  flatPages: PageRef[]
): Plugin<[], Root> {
  return () => (tree) => {
    visit(tree, "link", (node) => {
      if (!node.url.endsWith(".md") && !node.url.endsWith(".mdx")) return;
      const dir = path.dirname(currentFilePath);
      const resolved = path.normalize(path.join(dir, node.url));
      const normalized = resolved.replace(/\\/g, "/");
      const match = flatPages.find((p) => p.filePath === normalized);
      if (match) node.url = match.href;
    });
  };
}
