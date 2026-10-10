import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  poweredByHeader: false,
  async rewrites() {
    const api = process.env.API_INTERNAL_URL?.trim().replace(/\/+$/, "");
    if (!api) {
      return [];
    }
    return [{ source: "/api/:path*", destination: `${api}/api/:path*` }];
  },
};

export default nextConfig;
