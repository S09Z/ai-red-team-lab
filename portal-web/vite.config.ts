/// <reference types="vitest/config" />
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Dev server proxies the portal API paths so the SPA can call them same-origin.
const apiProxy = { target: "http://localhost:8000", changeOrigin: true };

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/auth": apiProxy,
      "/me": apiProxy,
      "/health": apiProxy,
      "/api": apiProxy,
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/setupTests.ts",
  },
});
