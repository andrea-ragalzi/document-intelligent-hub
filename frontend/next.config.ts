import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Permit the loopback and current LAN host used to access the same local
  // development server. This keeps Turbopack's HMR connection available when
  // testing from another device on the local network.
  allowedDevOrigins: ["127.0.0.1", "192.168.1.220"],
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
