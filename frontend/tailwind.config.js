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
        // --- SOURCE Design Token Colors (CSS Variable mapped) ---
        background: 'var(--color-bg)',
        surface: {
          DEFAULT: 'var(--color-surface)',
          elevated: 'var(--color-surface-elevated)',
          nested: 'var(--color-surface-elevated)',
        },
        border: {
          DEFAULT: 'var(--color-border)',
          subtle: 'var(--color-border-subtle)',
        },
        text: {
          primary: 'var(--color-text-primary)',
          secondary: 'var(--color-text-secondary)',
          muted: 'var(--color-text-muted)',
        },
        primary: {
          DEFAULT: 'var(--color-primary)',
          hover: 'var(--color-primary-hover)',
          light: 'var(--color-primary-light)',
          dark: 'var(--color-primary-dark)',
        },
        accent: {
          DEFAULT: 'var(--color-accent)',
          hover: 'var(--color-accent-hover)',
          emerald: '#10b981',
          amber: '#f59e0b',
          violet: '#8b5cf6',
        },

        // --- Backward Compatibility Color Aliases ---
        canvas: 'var(--color-bg)',
        seeker: {
          DEFAULT: 'var(--color-primary)',
          glow: 'var(--color-accent)',
          pill: 'var(--color-primary-hover)',
        },
        host: {
          DEFAULT: 'var(--color-accent)',
          gold: '#fbbf24',
        },
        status: {
          success: '#10B981',
          warning: '#F59E0B',
          danger: '#F43F5E',
          ai: 'var(--color-primary)',
        },
        brand: {
          50: '#fef4ec',
          100: '#fde5d2',
          500: 'var(--color-accent)',
          600: 'var(--color-primary)',
          700: 'var(--color-primary-hover)',
          800: 'var(--color-primary-dark)',
          900: '#5c2805',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        display: ['Outfit', 'Plus Jakarta Sans', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
      },
      boxShadow: {
        'sm': 'var(--shadow-sm)',
        'DEFAULT': 'var(--shadow-md)',
        'md': 'var(--shadow-md)',
        'lg': 'var(--shadow-lg)',
        'xl': 'var(--shadow-hover)',
        '2xl': 'var(--shadow-hover)',
        'card': 'var(--shadow-md)',
        'card-hover': 'var(--shadow-hover)',
        'panel': 'var(--shadow-lg)',
        'modal': 'var(--shadow-lg)',
        'dropdown': 'var(--shadow-md)',
        'card-light': '0 4px 20px -2px rgba(180, 83, 9, 0.08), 0 2px 6px -1px rgba(0, 0, 0, 0.04)',
        'card-dark': '0 4px 25px -2px rgba(0, 0, 0, 0.45), 0 0 15px 1px rgba(245, 158, 11, 0.05)',
        'lift-light': '0 12px 30px -4px rgba(180, 83, 9, 0.12), 0 4px 12px -2px rgba(0, 0, 0, 0.06)',
        'lift-dark': '0 14px 35px -4px rgba(0, 0, 0, 0.6), 0 0 20px 2px rgba(245, 158, 11, 0.1)',
      },
      transitionTimingFunction: {
        'natural': 'cubic-bezier(0.16, 1, 0.3, 1)',
        'smooth': 'cubic-bezier(0.4, 0, 0.2, 1)',
        'bounce-soft': 'cubic-bezier(0.34, 1.56, 0.64, 1)',
      },
      transitionDuration: {
        'instant': '100ms',
        'fast': '180ms',
        'normal': '260ms',
        'slow': '420ms',
      },
    },
  },
  plugins: [],
};
