import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Static files in web/out: the site has no server code, so it can be hosted anywhere or served offline.
  output: "export",
};

export default nextConfig;
