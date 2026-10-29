/// <reference types="vitest/config" />
import { defineConfig } from 'vite';

// `testhooks` mode builds a production bundle that additionally exposes the
// deterministic test API (window.__meridian) used by the e2e journey tests.
// The normal `build` output (dist/) never contains it.
export default defineConfig(({ mode }) => ({
  base: './',
  define: {
    __TEST_HOOKS__: JSON.stringify(mode === 'development' || mode === 'testhooks'),
  },
  build: {
    target: 'es2022',
    sourcemap: false,
    chunkSizeWarningLimit: 6000,
    assetsInlineLimit: 0,
  },
  worker: {
    format: 'es',
  },
  server: {
    port: 5173,
    strictPort: true,
  },
  preview: {
    port: 4173,
    strictPort: true,
  },
  test: {
    include: ['tests/**/*.test.ts'],
    environment: 'node',
    testTimeout: 60000,
  },
}));
