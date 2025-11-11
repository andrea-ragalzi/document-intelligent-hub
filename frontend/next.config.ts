import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone", // For Docker deployment
  experimental: {
    // Optimize for production
  },
};

export default nextConfig;
