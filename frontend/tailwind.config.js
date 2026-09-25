/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: '#020617',
        surface: {
          DEFAULT: '#0F172A',
          elevated: '#0F172A',
          nested: '#1E293B',
        },
        seeker: {
          DEFAULT: '#4F46E5',
          glow: '#6366F1',
          pill: '#818CF8',
        },
        host: {
          DEFAULT: '#F59E0B',
          gold: '#FBBF24',
        },
        status: {
          success: '#10B981',
          warning: '#F59E0B',
          danger: '#F43F5E',
          ai: '#7C3AED',
        },
        brand: {
          50: '#eef2ff',
          100: '#e0e7ff',
          500: '#6366f1',
          600: '#4f46e5',
          700: '#4338ca',
          800: '#3730a3',
          900: '#312e81',
        },
        accent: {
          emerald: '#10b981',
          amber: '#f59e0b',
          violet: '#8b5cf6'
        }
      }
    },

  },
  plugins: [],
}
