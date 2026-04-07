import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "lain.bgm.tv" },
      { protocol: "https", hostname: "*.bgm.tv" },
    ],
  },
};

export default nextConfig;
