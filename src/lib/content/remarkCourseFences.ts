import type { Plugin, Processor } from "unified";
import type { Code, Root, RootContent } from "mdast";
import { visit } from "unist-util-visit";
import yaml from "js-yaml";

// Turns ```objectives, ```quiz and ```exercise fences (YAML bodies) into marked
// <div class="cf-..."> trees. String fields are parsed as Markdown with the page's
// own parser, so GFM, code highlighting and .mdx link rewriting all apply to them.
// `CourseDiv` (CourseFences.tsx, mapped as `div` in MdxComponents.tsx) dispatches on the cf-* class names.
//
// Schemas (see CLAUDE.md "Note template"):
//   objectives: { time?: string, scope?: "page" | "module", outcomes: string[], prerequisites?: string[] }
//   quiz:       [{ q: string, options?: string[], answer: number (1-based) | string, explain?: string }]
//   exercise:   { title?: string, task: string, hints?: string[], solution?: string } | list of those

export const FENCE_LANGS = ["objectives", "quiz", "exercise"] as const;

type Block = RootContent & { data?: { hName?: string; hProperties?: Record<string, unknown> } };

function block(className: string, children: RootContent[], props: Record<string, unknown> = {}): Block {
  // An mdast node type with no to-hast handler falls back to an element named by data.hName
  return {
    type: "courseBlock",
    children,
    data: { hName: "div", hProperties: { className: [className], ...props } },
  } as unknown as Block;
}

export function remarkCourseFences(): Plugin<[], Root> {
  return function (this: Processor) {
    // Parse fragments with this processor's own parser so GFM and friends apply
    const parse = (doc: string) => this.parse(doc) as Root;
    const markdown = (value: unknown): RootContent[] => parse(String(value ?? "").trim()).children;

    // Single-paragraph fragments (question stems, options) render inline
    const inline = (value: unknown): RootContent[] => {
      const nodes = markdown(value);
      return nodes.length === 1 && nodes[0].type === "paragraph" ? (nodes[0].children as RootContent[]) : nodes;
    };

    const error = (lang: string, message: string) =>
      block("cf-error", [{ type: "paragraph", children: [{ type: "text", value: `Invalid ${lang} block: ${message}` }] }]);

    function objectives(data: Record<string, unknown>): Block {
      const outcomes = Array.isArray(data.outcomes) ? data.outcomes : [];
      if (!outcomes.length) throw new Error("`outcomes` must be a non-empty list");
      const prereqs = Array.isArray(data.prerequisites) ? data.prerequisites : [];
      const list = (items: unknown[], className: string) =>
        block(className, items.map((item) => block("cf-item", inline(item))));
      const children: RootContent[] = [list(outcomes, "cf-outcomes")];
      if (prereqs.length) children.push(list(prereqs, "cf-prereqs"));
      const props: Record<string, unknown> = { "data-scope": data.scope === "module" ? "module" : "page" };
      if (data.time) props["data-time"] = String(data.time);
      return block("cf-objectives", children, props);
    }

    function quiz(data: unknown): Block {
      if (!Array.isArray(data) || !data.length) throw new Error("expected a non-empty list of questions");
      const questions = data.map((raw, i) => {
        const item = raw as Record<string, unknown>;
        if (!item.q) throw new Error(`question ${i + 1} has no \`q\``);
        const children: RootContent[] = [block("cf-prompt", inline(item.q))];
        const props: Record<string, unknown> = {};
        if (Array.isArray(item.options)) {
          const answer = Number(item.answer);
          if (!Number.isInteger(answer) || answer < 1 || answer > item.options.length) {
            throw new Error(`question ${i + 1}: \`answer\` must be the 1-based number of the correct option`);
          }
          props["data-answer"] = String(answer);
          item.options.forEach((option, j) => children.push(block("cf-option", inline(option), { "data-index": String(j + 1) })));
        } else if (item.answer === undefined) {
          throw new Error(`question ${i + 1} needs \`options\` + \`answer\`, or a free-text \`answer\``);
        } else {
          children.push(block("cf-model-answer", markdown(item.answer)));
        }
        if (item.explain) children.push(block("cf-explain", markdown(item.explain)));
        return block("cf-question", children, props);
      });
      return block("cf-quiz", questions);
    }

    function exercise(data: unknown): Block {
      const items = (Array.isArray(data) ? data : [data]) as Record<string, unknown>[];
      return block(
        "cf-exercises",
        items.map((item, i) => {
          if (!item?.task) throw new Error(`exercise ${i + 1} has no \`task\``);
          const children: RootContent[] = [block("cf-task", markdown(item.task))];
          const hints = Array.isArray(item.hints) ? item.hints : [];
          hints.forEach((hint) => children.push(block("cf-hint", markdown(hint))));
          if (item.solution) children.push(block("cf-solution", markdown(item.solution)));
          return block("cf-exercise", children, item.title ? { "data-title": String(item.title) } : {});
        })
      );
    }

    return (tree) => {
      visit(tree, "code", (node: Code, index, parent) => {
        if (!parent || index === undefined) return;
        const lang = node.lang ?? "";
        if (!(FENCE_LANGS as readonly string[]).includes(lang)) return;
        let replacement: Block;
        try {
          const data = yaml.load(node.value);
          if (lang === "objectives") replacement = objectives((data ?? {}) as Record<string, unknown>);
          else if (lang === "quiz") replacement = quiz(data);
          else replacement = exercise(data);
        } catch (e) {
          replacement = error(lang, e instanceof Error ? e.message.split("\n")[0] : String(e));
        }
        parent.children[index] = replacement;
      });
    };
  };
}
