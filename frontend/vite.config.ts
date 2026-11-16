import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    clearMocks: true,
    coverage: {
      provider: "v8",
      include: ["src/**/*.{ts,tsx}"],
      exclude: ["src/test/**", "src/main.tsx", "src/**/*.d.ts"],
      reporter: ["text", "html", "lcov", "json-summary"],
      reportsDirectory: "./coverage",
      thresholds: {
        lines: 80,
        statements: 80,
        functions: 75,
        branches: 70,
      },
    },
  },
});
