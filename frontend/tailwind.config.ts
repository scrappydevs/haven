import type { Config } from "tailwindcss"

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // PRIMARY PALETTE - Tropical Green Medical
        primary: {
          950: '#1e293b',  // Deep slate - darkest text
          900: '#334155',  // Darker slate
          700: '#6b9080',  // Soft teal green - main accent
          400: '#a4c3b2',  // Light teal
          100: '#eaf4f4',  // Very light teal
        },
        // ACCENT PALETTE - Terracotta & Earth
        accent: {
          terra: '#c97064',  // Terracotta red - warnings, CTAs
          sand: '#f4e8d8',   // Warm sand
          clay: '#e8cebf',   // Warm clay
        },
        // NEUTRAL PALETTE - Sophisticated Grays
        neutral: {
          950: '#0f172a',  // Almost black
          700: '#475569',  // Dark gray
          500: '#94a3b8',  // Medium gray
          400: '#cbd5e1',  // Light medium gray
          300: '#cbd5e1',  // Border gray
          200: '#e2e8f0',  // Light gray - borders
          100: '#f1f5f9',  // Very light gray
          50: '#fafafa',   // Off-white background
        },
        // SEMANTIC COLORS
        background: '#fafafa',  // Main background
        surface: '#ffffff',     // Cards, panels
        border: '#e2e8f0',      // All borders
      },
      fontFamily: {
        playfair: ['var(--font-playfair)'],
        inter: ['var(--font-inter)'],
      },
      fontWeight: {
        extralight: '200',
        light: '300',
        normal: '400',
        medium: '500',
        black: '900',
      },
      letterSpacing: {
        tighter: '-0.05em',
        tight: '-0.025em',
        wide: '0.025em',
        wider: '0.05em',
        widest: '0.1em',
      },
      borderRadius: {
        none: '0',
        sm: '0.125rem',  // 2px
        DEFAULT: '0.25rem',  // 4px
        lg: '0.5rem',  // 8px
        xl: '0.75rem',  // 12px
      },
    },
  },
  plugins: [],
}
export default config

