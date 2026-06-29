"use client";

import { useEffect, useId, useState } from "react";

interface Props {
  value: string;
}

export function MermaidDiagram({ value }: Props) {
  const id = useId().replace(/:/g, "");
  const [svg, setSvg] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function render() {
      const mermaid = (await import("mermaid")).default;
      mermaid.initialize({
        startOnLoad: false,
        theme: "base",
        themeVariables: {
          // Neutral warm base
          primaryColor: "#e8e2d9",
          primaryTextColor: "#3d3730",
          primaryBorderColor: "#ccc4b8",
          lineColor: "#a89e94",
          secondaryColor: "#edeae5",
          tertiaryColor: "#f4f1ec",
          background: "#faf8f5",
          mainBkg: "#f0ece6",
          nodeBorder: "#ccc4b8",
          clusterBkg: "#f4f1ec",
          titleColor: "#3d3730",
          edgeLabelBackground: "#faf8f5",
          fontFamily: "ui-sans-serif, system-ui, sans-serif",
          fontSize: "14px",
          // Mindmap branch palette - soft, low-saturation earth tones
          cScale0: "#dde4dc",  // soft sage
          cScale1: "#d8dfe8",  // soft slate blue
          cScale2: "#e8e0d4",  // soft sand
          cScale3: "#ddd8e4",  // soft lavender
          cScale4: "#e4dbd8",  // soft dusty rose
          cScale5: "#dce4e0",  // soft teal-gray
          cScale6: "#e4e2d8",  // soft warm gray
          cScale7: "#dfe4dc",  // soft moss
          cScaleLabel0: "#3d3730",
          cScaleLabel1: "#3d3730",
          cScaleLabel2: "#3d3730",
          cScaleLabel3: "#3d3730",
          cScaleLabel4: "#3d3730",
        },
      });

      try {
        const { svg: rendered } = await mermaid.render(`mermaid-${id}`, value);
        if (!cancelled) setSvg(rendered);
      } catch {
        if (!cancelled) setSvg(null);
      }
    }

    render();
    return () => { cancelled = true; };
  }, [id, value]);

  if (!svg) {
    return (
      <pre className="text-sm text-sun-muted bg-transparent border border-sun-yellow/30 rounded p-4 overflow-x-auto">
        {value}
      </pre>
    );
  }

  return (
    <div
      className="my-6 flex justify-center overflow-x-auto rounded-lg border border-[#ccc4b8]/60 bg-[#faf8f5] p-4"
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}
