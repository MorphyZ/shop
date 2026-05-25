import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

const proxyTarget = process.env.VITE_BACKEND_PROXY || "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [vue()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: {
      "/api": {
        target: proxyTarget,
        changeOrigin: true,
      },
      "/api-auth": {
        target: proxyTarget,
        changeOrigin: true,
      },
      "/admin": {
        target: proxyTarget,
        changeOrigin: true,
      },
    },
  },
});

