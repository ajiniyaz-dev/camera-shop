import type { MetadataRoute } from "next";

import { publicOrigin } from "@/lib/seo";

export const dynamic = "force-dynamic";

export default function robots(): MetadataRoute.Robots {
  const origin = publicOrigin();
  return {
    rules: {
      userAgent: "*",
      allow: ["/ru", "/uz", "/en"],
      disallow: ["/admin", "/api/", "/media/imports", "/media/private-uploads"],
    },
    ...(origin ? { sitemap: `${origin}/sitemap.xml` } : {}),
  };
}
