import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  basePath: "/learngenai",
  // Trailing slash so /learn/llm-models/01-llm-fundamentals/index.html resolves correctly
  trailingSlash: true,
  images: {
    unoptimized: true, // required for static export
  },
};

export default nextConfig;
