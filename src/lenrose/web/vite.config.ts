/// <reference types="vitest" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Build into dist/ which FastAPI serves. During dev, proxy /api to the backend.
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: "dist",
  },
  server: {
    proxy: {
      "/api": "http://localhost:8001",
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/test/setup.ts",
  },
});
