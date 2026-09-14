import path from "node:path";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: ["./vitest.setup.ts"],
  },
  resolve: {
    // import.meta.dirname (Node 20.11+), not __dirname — this file runs as
    // native ESM now that package.json declares "type": "module".
    alias: { "@": path.resolve(import.meta.dirname, "./src") },
  },
});
