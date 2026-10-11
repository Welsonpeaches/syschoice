import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  timeout: 90_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  workers: 1,
  reporter: [['list']],
  use: {
    // Override to run the same suite against the Flask-served production build:
    //   E2E_BASE_URL=http://127.0.0.1:5000 npx playwright test
    baseURL: process.env.E2E_BASE_URL ?? 'http://127.0.0.1:5173',
    trace: 'off',
  },
  projects: [
    {
      name: 'desktop',
      use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 960 } },
    },
    {
      name: 'mobile',
      // Pixel uses Chromium, so no extra browser download is needed.
      use: { ...devices['Pixel 7'] },
    },
  ],
  webServer: [
    {
      command: 'cd ../backend && .venv/bin/python run.py',
      url: 'http://127.0.0.1:5000/api/health',
      reuseExistingServer: true,
      timeout: 60_000,
    },
    {
      command: 'npm run dev',
      url: 'http://127.0.0.1:5173/',
      reuseExistingServer: true,
      timeout: 60_000,
    },
  ],
})
