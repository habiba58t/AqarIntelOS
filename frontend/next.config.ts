import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    domains: ['files.propertyhub.site'], // ✅ allow remote images
  },
};

export default nextConfig;
