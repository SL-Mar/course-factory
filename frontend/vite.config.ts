import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3006,
    proxy: {
      "/api": {
        target: "http://localhost:8006",
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: path.resolve(__dirname, "../course_factory/api/static"),
    emptyOutDir: true,
  },
});
