/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      colors: {
        bg: "#0A0F1C",
        surface: "#111a2e",
        surface2: "#16223a",
        line: "#1f2c44",
        ink: "#F1F5FB",
        muted: "#8b9bb4",
        accent: "#3B82F6",
        accent2: "#2563EB",
        up: "#22C55E",
        down: "#EF4444",
        warn: "#F59E0B",
      },
      boxShadow: {
        card: "0 8px 24px rgba(0,0,0,.30)",
        glow: "0 8px 22px rgba(59,130,246,.40)",
      },
    },
  },
  plugins: [],
};
