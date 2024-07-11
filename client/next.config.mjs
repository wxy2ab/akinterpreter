/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'export',
  distDir: '../static/.next',
  images: {
    unoptimized: true
  }
}

  

export default nextConfig;
