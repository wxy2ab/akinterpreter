/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'export',
  distDir: '../static/.next',
  images: {
    unoptimized: true
  },
  reactStrictMode: true,
  transpilePackages: ['@/components/ui'],
}

  

export default nextConfig;
