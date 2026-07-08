import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  // Not VITE_-prefixed, so loadEnv's 3rd arg ('') exposes it here without
  // Vite ever bundling it into client code — only this dev-server proxy sees it.
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [react()],
    base: '/baseball',
    server: {
      port: 3000,
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
          // Backend routes have no /api prefix (e.g. POST /chat), so strip it
          // before forwarding — matches Nginx's proxy_pass behavior in prod.
          rewrite: (path) => path.replace(/^\/api/, ''),
          // Production's Nginx injects this same header server-side (see
          // frontend/nginx.conf.template) so the backend's API_KEY check
          // never has to be satisfied by browser JS. Mirror that here.
          headers: env.API_KEY ? { 'X-API-Key': env.API_KEY } : {},
        },
      },
    },
  }
})
