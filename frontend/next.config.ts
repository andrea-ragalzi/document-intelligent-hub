import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // An optional local-only variable permits HMR from a developer's LAN host.
  allowedDevOrigins: ["127.0.0.1", process.env.NEXT_DEV_ALLOWED_ORIGIN].filter(
    (origin): origin is string => Boolean(origin)
  ),
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
