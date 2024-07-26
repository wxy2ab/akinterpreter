/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    unoptimized: true
  },
  transpilePackages: ['@/components/ui'],
};

if (process.env.NODE_ENV === 'development') {
  // 开发环境配置
  nextConfig.rewrites = async () => {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8181/api/:path*' // Proxy to Backend
      }
    ];
  };
} else if (process.env.BUILD_OUTPUT) {
  // 生产环境构建配置
  nextConfig.output = 'export';
  nextConfig.distDir = '../static/.next';
}

module.exports = nextConfig;