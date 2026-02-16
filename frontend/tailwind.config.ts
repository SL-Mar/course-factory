import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        sidebar: {
          DEFAULT: "#0f0f0f",
          hover: "#1a1a1a",
          active: "#1e1e1e",
          border: "#1e1e1e",
          muted: "#717171",
        },
        accent: {
          DEFAULT: "#ff6d00",
          hover: "#e66200",
          light: "#ff8c33",
          faint: "rgba(255, 109, 0, 0.08)",
        },
        content: {
          DEFAULT: "#0f0f0f",
          secondary: "#141414",
          tertiary: "#1a1a1a",
          border: "#222222",
          text: "#e0e0e0",
          muted: "#717171",
          faint: "#4a4a4a",
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
