/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#F7F7F2",
        forest: {
          900: "#0E1712",
          800: "#17231D",
          700: "#1E2E26",
          600: "#2B3D34",
          500: "#3D5247",
        },
        botanical: {
          50: "#F2F6F4",
          100: "#E5ECE8",
          200: "#C9D9D0",
          300: "#A8BDAE",
          400: "#608B73",
          500: "#2F6B4F",
          600: "#25553E",
          700: "#1B3E2D",
        },
        sage: {
          50: "#F8FAF8",
          100: "#EFF4F0",
          200: "#E2E7E2",
          300: "#CAD4CD",
          400: "#A8BDAE",
          500: "#839E8C",
        },
        sand: {
          50: "#FAF9F5",
          100: "#F4F1EA",
          200: "#E8E3D7",
        },
        earth: {
          amber: "#C97A2B",
          rust: "#B85438",
          clay: "#8C4A32",
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Menlo', 'Consolas', 'monospace'],
      },
      boxShadow: {
        'subtle': '0 1px 3px 0 rgba(23, 35, 29, 0.04), 0 1px 2px -1px rgba(23, 35, 29, 0.03)',
        'card': '0 4px 12px -2px rgba(23, 35, 29, 0.06), 0 2px 6px -1px rgba(23, 35, 29, 0.03)',
        'elevated': '0 10px 25px -4px rgba(23, 35, 29, 0.08), 0 6px 10px -3px rgba(23, 35, 29, 0.04)',
      }
    },
  },
  plugins: [],
}
