import { fileURLToPath, URL } from 'node:url'

import tailwindcss from '@tailwindcss/vite'
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    // '::' binds dual-stack on Linux, so both http://127.0.0.1:5173 and
    // http://[::1]:5173 work. Override with VITE_DEV_HOST to restrict it.
    host: process.env.VITE_DEV_HOST ?? '::',
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
      },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    // Playwright owns e2e/; vitest must not try to run those specs.
    exclude: ['node_modules/**', 'dist/**', 'e2e/**'],
  },
})
