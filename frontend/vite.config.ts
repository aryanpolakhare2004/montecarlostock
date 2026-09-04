import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// mcstock's FastAPI server mounts /static and serves web/static/index.html at "/",
// so the production build must emit assets under /static/ and land in that directory.
export default defineConfig({
  plugins: [vue()],
  base: '/static/',
  build: {
    outDir: '../mcstock/web/static',
    emptyOutDir: true,
  },
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
})
