/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // 根据环境变量决定是否使用自定义 distDir
  distDir: process.env.BUILD_OUTPUT ? '../static/.next' : '.next',
  // 只在构建时设置 output 为 'export'
  ...(process.env.BUILD_OUTPUT && { output: 'export' }),
  images: {
    unoptimized: true
  },
  transpilePackages: ['@/components/ui'],
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8181/api/:path*' // Proxy to Backend
      }
    ]
  }
}

module.exports = nextConfig;