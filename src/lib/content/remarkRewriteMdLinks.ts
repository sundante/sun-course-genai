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
      if (/^[a-z]+:/i.test(node.url)) return;
      // Split off a trailing #anchor so `Foo.mdx#bar` links resolve too
      const hashIndex = node.url.indexOf("#");
      const target = hashIndex === -1 ? node.url : node.url.slice(0, hashIndex);
      const hash = hashIndex === -1 ? "" : node.url.slice(hashIndex);
      if (!target.endsWith(".md") && !target.endsWith(".mdx")) return;
      const dir = path.dirname(currentFilePath);
      const resolved = path.normalize(path.join(dir, target)).replace(/\\/g, "/");
      // Legacy `.md` links point at files that now live on disk as `.mdx`
      const candidates = resolved.endsWith(".md") ? [resolved, `${resolved}x`] : [resolved];
      const match = flatPages.find((p) => candidates.includes(p.filePath));
      if (match) node.url = match.href + hash;
    });
  };
}
