import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/ws': {
        target: 'ws://localhost:4002',
        ws: true,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/ws/, ''),
      },
      // Evennia's webclient uses /websocket on the same origin as the
      // page. Proxy it through so the Django session cookie (set on the
      // vite :3000 origin) rides along with the WS upgrade request.
      // Evennia's WS listener is at root on :4002, so strip the path.
      '/websocket': {
        target: 'ws://localhost:4002',
        ws: true,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/websocket/, ''),
      },
      // Proxy Django-served endpoints (REST APIs, allauth OAuth, admin,
      // static) to Evennia's HTTP port so fetch() calls from the React
      // app reach Django with session cookies intact. Without this, vite
      // returns index.html for /api/account/characters/ and similar,
      // which trips the "Unexpected token '<'" JSON parse error on the
      // character-select screen.
      '/api':      { target: 'http://localhost:4001', changeOrigin: true },
      '/accounts': { target: 'http://localhost:4001', changeOrigin: true },
      '/admin':    { target: 'http://localhost:4001', changeOrigin: true },
    },
  },
})
