import { defineConfig } from '@playwright/test';

// Two static servers: dist/ (the shipped production build, no test hooks) and
// dist-test/ (same code built with the test API for the automated journeys).
// `npm run test:e2e` builds both first (see the pretest:e2e script).
// Software WebGL (SwiftShader) by default so the tests run on GPU-less machines;
// set PW_GPU=1 to use the machine's own GPU instead (e.g. for the profile route).
const swiftshader = process.env.PW_GPU ? [] : ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'];

export default defineConfig({
  testDir: 'e2e',
  timeout: 30 * 60 * 1000,
  expect: { timeout: 60_000 },
  fullyParallel: false,
  workers: 1,
  reporter: [['list']],
  // Overridable so a second run (e.g. against another local build) never wipes a running one's output.
  outputDir: process.env.PW_OUTPUT ?? 'test-results',
  use: {
    browserName: 'chromium',
    viewport: { width: 960, height: 540 },
    launchOptions: { args: swiftshader },
    actionTimeout: 120_000,
    navigationTimeout: 120_000,
  },
  webServer: [
    { command: 'npx vite preview --port 4173 --strictPort', port: 4173, reuseExistingServer: true, timeout: 60_000 },
    { command: 'npx vite preview --outDir dist-test --port 4174 --strictPort', port: 4174, reuseExistingServer: true, timeout: 60_000 },
  ],
  projects: [
    { name: 'prod', testMatch: /prod\/.*\.spec\.ts/, use: { baseURL: 'http://localhost:4173/' } },
    { name: 'journey', testMatch: /journey\/.*\.spec\.ts/, use: { baseURL: process.env.JOURNEY_URL ?? 'http://localhost:4174/' } },
  ],
});
