import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  poweredByHeader: false,
  experimental: {
    // The API accepts a workbook up to 40 MB. Next's default 10 MB proxy buffer
    // truncates the multipart body, Nginx resets the connection, and the
    // rewrite responds with a non-JSON 500.
    middlewareClientMaxBodySize: "40mb",
  },
  async rewrites() {
    const api = process.env.API_INTERNAL_URL?.trim().replace(/\/+$/, "");
    const media = process.env.MEDIA_PROXY_URL?.trim().replace(/\/+$/, "");
    const rules: { source: string; destination: string }[] = [];
    if (api) {
      rules.push({ source: "/api/:path*", destination: `${api}/api/:path*` });
    }
    // Local preview only. Set MEDIA_PROXY_URL to the Nginx origin at build time.
    // Production Nginx already serves /media/objects and does not use this rewrite.
    // The path stops at objects so private import workbooks stay unproxied.
    if (media) {
      rules.push({
        source: "/media/objects/:path*",
        destination: `${media}/media/objects/:path*`,
      });
    }
    return rules;
  },
};

export default nextConfig;
