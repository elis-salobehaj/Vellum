import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for Vellum E2E tests.
 * Supports:
 * 1. Hybrid Mode: Local frontend (using port 5174 to avoid dev.sh clash)
 * 2. Kubernetes: Running against a deployed cluster (using BASE_URL)
 * 3. CI Mode: GitHub Workflows (internal Docker networking on port 80)
 */
export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  // Detailed feedback in CLI, HTML report for debugging
  reporter: process.env.CI ? [['github'], ['list']] : [['html', { open: 'never' }], ['list']],
  testIgnore: process.env.SKIP_E2E ? '**/e2e.spec.ts' : undefined,
  use: {
    // We use port 5174 for local tests to avoid clashing with dev.sh (port 5173)
    baseURL: process.env.BASE_URL || (process.env.CI ? 'http://frontend:80' : 'http://localhost:5174'),
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  // Webserver handles local development (Hybrid Mode)
  // We explicitly use 5174 here so developers can keep dev.sh running on 5173 simultaneously
  webServer: (!process.env.CI && !process.env.BASE_URL && process.env.RUN_WEB_SERVER !== 'false') ? {
    command: 'pnpm dev --port 5174 --host',
    url: 'http://localhost:5174',
    reuseExistingServer: true,
    timeout: 60 * 1000,
    env: {
      VITE_BYPASS_AUTH: 'true',
    }
  } : undefined,
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        launchOptions: {
          args: [
            '--unsafely-treat-insecure-origin-as-secure=http://localhost:5174,http://frontend,http://frontend:80',
            '--disable-web-security',
            '--ignore-certificate-errors',
            '--allow-running-insecure-content'
          ]
        }
      },
    },
  ],
});
