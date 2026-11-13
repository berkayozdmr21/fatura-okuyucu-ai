import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// base './' : aynı derleme hem web sunucusunda hem masaüstü (Electron, file://) uygulamasında çalışsın
export default defineConfig({
  base: "./",
  plugins: [react()],
  server: { port: 5173 },
  test: { environment: "node", include: ["src/**/*.test.ts"] },
});
