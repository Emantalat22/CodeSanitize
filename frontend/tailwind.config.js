/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: '#050811',
        card: '#0b1122',
        border: '#162238',
        teal: {
          400: '#2dd4bf',
          500: '#14b8a6',
          DEFAULT: '#06b6d4',
        },
        primary: {
          400: '#38bdf8',
          500: '#0284c7',
          DEFAULT: '#0284c7',
        },
        purple: {
          400: '#a5b4fc',
          500: '#818cf8',
          DEFAULT: '#818cf8',
        },
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Cascadia Code', 'Consolas', 'monospace'],
      },
    },
  },
  plugins: [],
}
