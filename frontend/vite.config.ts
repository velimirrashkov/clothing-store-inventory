import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Proxying /api through the Vite dev server keeps requests same-origin from the browser's
// point of view, matching the same-origin deploy design in the architecture spec (session
// cookies, not tokens — see the auth notes in src/api/client.ts) even in local dev.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: false,
      },
    },
  },
});
