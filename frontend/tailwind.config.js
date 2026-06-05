/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      colors: {
        bg: "#0B1120",
        surface: "#0F1B2E",
        surface2: "#16243B",
        line: "#22344c",
        ink: "#E6EDF6",
        muted: "#8aa0b8",
        accent: "#22D3EE",
        accent2: "#3B82F6",
        up: "#34D399",
        down: "#FB7185",
        warn: "#FBBF24",
      },
      boxShadow: {
        card: "0 8px 24px rgba(0,0,0,.28)",
        glow: "0 6px 18px rgba(34,211,238,.35)",
      },
    },
  },
  plugins: [],
};
