import { getSearchIndex } from "@/lib/content/searchIndex";

// Rendered once at build time into out/search-index.json (static export);
// SearchDialog fetches it on first open
export const dynamic = "force-static";

export function GET() {
  return Response.json(getSearchIndex());
}
