import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        sidebar: {
          DEFAULT: "#1a1a2e",
          hover: "#252540",
          active: "#2c2c4a",
          border: "#2a2a44",
          muted: "#9b9bae",
        },
        accent: {
          DEFAULT: "#2383e2",
          hover: "#1b73c9",
          light: "#529CCA",
          faint: "rgba(35, 131, 226, 0.08)",
        },
        content: {
          DEFAULT: "#1e1e32",
          secondary: "#222238",
          tertiary: "#28283e",
          border: "#2e2e48",
          text: "#d4d4dc",
          muted: "#8b8ba0",
          faint: "#55556a",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
    },
  },
  plugins: [],
} satisfies Config;
