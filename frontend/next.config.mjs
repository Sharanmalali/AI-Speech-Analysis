/** @type {import('next').NextConfig} */
const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

const nextConfig = {
  reactStrictMode: true,
  output: "standalone", // optimised container image
  poweredByHeader: false,
  transpilePackages: ["three"],
  eslint: {
    // Lint is run as a separate CI step; don't block production builds on it.
    ignoreDuringBuilds: true,
  },
  async rewrites() {
    // Proxy API calls in development to avoid CORS friction.
    return [
      {
        source: "/api/:path*",
        destination: `${apiBase}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
