/** @type {import('next').NextConfig} */
const nextConfig = {
  // Environment variables
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
  
  // Image optimization
  images: {
    domains: [],
    unoptimized: true,
  },
  
  // Disable X-Powered-By header
  poweredByHeader: false,
  
  // Compression
  compress: true,
}

module.exports = nextConfig

