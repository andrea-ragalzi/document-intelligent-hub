import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Vercel supplies its own build adapter and does not use standalone output.
  // Keep standalone enabled for the existing self-hosted/Docker build only.
  output: process.env.VERCEL ? undefined : "standalone",
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "lh3.googleusercontent.com",
        pathname: "**",
      },
    ],
  },
  experimental: {
    // Optimize for production
  },
};

export default nextConfig;
