/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable standalone output for production deployment
  output: 'standalone',
  
  // Environment variables
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
  
  // Image optimization
  images: {
    domains: [],
    unoptimized: true, // For Vercel deployment
  },
  
  // Disable X-Powered-By header
  poweredByHeader: false,
  
  // Compression
  compress: true,
}

module.exports = nextConfig

