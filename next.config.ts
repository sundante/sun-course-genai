import type { NextConfig } from "next";
import { createHash } from "node:crypto";
import fs from "node:fs";
import path from "node:path";

// Build ID = hash of the app code only (not src/content, not public/). Next stamps the build ID
// into every exported page, so a random ID made all ~260 HTML files differ on every build and the
// FTP deploy re-uploaded the whole site. With this, a content-only change re-uploads just the
// pages it touches; any code or dependency change still gets a new ID.
function appCodeHash(): string {
  const hash = createHash("sha256");
  const walk = (dir: string) => {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        if (full !== path.join("src", "content")) walk(full);
      } else {
        hash.update(full).update(fs.readFileSync(full));
      }
    }
  };
  walk("src");
  for (const file of ["package-lock.json", "next.config.ts"]) {
    if (fs.existsSync(file)) hash.update(file).update(fs.readFileSync(file));
  }
  return hash.digest("hex").slice(0, 16);
}

const nextConfig: NextConfig = {
  output: "export",
  trailingSlash: true,
  images: { unoptimized: true },
  generateBuildId: async () => appCodeHash(),
};

export default nextConfig;
