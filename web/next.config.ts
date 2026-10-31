import type { NextConfig } from "next";

// GitHub Pages serves the site under /<repo>; the deploy workflow sets this. Local builds leave it empty.
const basePath = process.env.NEXT_BASE_PATH ?? "";

const nextConfig: NextConfig = {
  // Static files in web/out: the site has no server code, so it can be hosted anywhere or served offline.
  output: "export",
  basePath,
  assetPrefix: basePath || undefined,
};

export default nextConfig;
