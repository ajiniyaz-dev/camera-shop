import type { MetadataRoute } from "next";

import { getInternalApiUrl } from "@/lib/config";
import { publicOrigin } from "@/lib/seo";

export const dynamic = "force-dynamic";

type SitemapEntry = {
  path: string;
  last_modified: string | null;
  alternates: Record<string, string>;
};

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const origin = publicOrigin();
  if (!origin) {
    return [];
  }
  const response = await fetch(`${getInternalApiUrl()}/api/public/sitemap`, {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    throw new Error("sitemap request failed");
  }
  const body = (await response.json()) as { entries: SitemapEntry[] };
  return body.entries.map((entry) => {
    const languages: Record<string, string> = {};
    for (const [locale, path] of Object.entries(entry.alternates)) {
      languages[locale] = `${origin}${path}`;
    }
    return {
      url: `${origin}${entry.path}`,
      lastModified: entry.last_modified ?? undefined,
      alternates: { languages },
    };
  });
}
