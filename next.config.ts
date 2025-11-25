import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  images: {
    // Add all external domains you want Next.js <Image> to accept
    domains: ["hidden-backend-1.onrender.com"],
  },
};

export default nextConfig;
