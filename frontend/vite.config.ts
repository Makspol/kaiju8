import { defineConfig } from "vite";
import solidPlugin from "vite-plugin-solid";

export default defineConfig({
  plugins: [solidPlugin()],
  server: {
    port: 5173,
    headers: {
      // Vite 6 + solid-refresh HMR uses eval internally in dev mode
      "Content-Security-Policy":
        "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; connect-src 'self' ws: wss:; img-src 'self' data:;",
    },
    proxy: {
      "/auth": "http://localhost:8000",
      "/workflows": "http://localhost:8000",
      "/workflow-templates": "http://localhost:8000",
      "/executions": "http://localhost:8000",
      "/credentials": "http://localhost:8000",
      "/node-types": "http://localhost:8000",
      "/knowledge": "http://localhost:8000",
      "/scheduler": "http://localhost:8000",
      "/users": "http://localhost:8000",
      "/http-triggers": "http://localhost:8000",
      "/health": "http://localhost:8000",
    },
  },
  build: {
    target: "esnext",
  },
});
