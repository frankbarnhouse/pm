import type { NextConfig } from "next";

const backendOrigin = process.env.BACKEND_ORIGIN ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  output: "export",
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${backendOrigin}/api/:path*`,
      },
      {
        source: "/auth/:path*",
        destination: `${backendOrigin}/auth/:path*`,
      },
      {
        source: "/login",
        destination: `${backendOrigin}/login`,
      },
    ];
  },
};

export default nextConfig;
