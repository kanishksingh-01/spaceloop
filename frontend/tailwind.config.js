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
        },
        ocean: {
          primary: '#0B3D91',
          secondary: '#3BA7F2',
          aqua: '#7FE7D6',
          bg: '#E8F6FF',
          surface: '#FFFFFF',
          nested: '#F0F8FF',
          text: '#0B2545',
          body: '#1E293B',
          muted: '#475569',
          border: '#D0E6F7',
        }
      },
      boxShadow: {
        'sm': '1px 2px 5px 0 rgba(0, 0, 0, 0.35)',
        'DEFAULT': '2px 4px 12px -1px rgba(0, 0, 0, 0.42), 1px 2px 4px -1px rgba(0, 0, 0, 0.26)',
        'md': '3px 6px 16px -2px rgba(0, 0, 0, 0.48), 1.5px 3px 6px -1px rgba(0, 0, 0, 0.30)',
        'lg': '4px 10px 24px -3px rgba(0, 0, 0, 0.55), 2px 4px 10px -2px rgba(0, 0, 0, 0.35)',
        'xl': '6px 16px 36px -4px rgba(0, 0, 0, 0.62), 2.5px 6px 14px -3px rgba(0, 0, 0, 0.38)',
        '2xl': '8px 24px 54px -6px rgba(0, 0, 0, 0.74), 3px 9px 20px -3px rgba(0, 0, 0, 0.45)',
        'card': '2.5px 5px 16px -2px rgba(0, 0, 0, 0.42), 1px 2px 6px -1px rgba(0, 0, 0, 0.28)',
        'card-hover': '4px 14px 30px -4px rgba(0, 0, 0, 0.58), 2px 5px 12px -2px rgba(0, 0, 0, 0.35)',
        'panel': '5px 12px 32px -4px rgba(0, 0, 0, 0.54), 2px 5px 12px -2px rgba(0, 0, 0, 0.36)',
        'modal': '8px 24px 56px -8px rgba(0, 0, 0, 0.75), 3px 10px 22px -3px rgba(0, 0, 0, 0.48)',
        'dropdown': '4px 12px 28px -3px rgba(0, 0, 0, 0.68), 2px 4px 10px -2px rgba(0, 0, 0, 0.42)',
      }
    },

  },
  plugins: [],
}
