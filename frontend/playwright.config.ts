import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: 2,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  testIgnore: process.env.SKIP_E2E ? '**/e2e.spec.ts' : undefined,
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:3000',
    trace: 'on-first-retry',
  },
  // Only start webServer if NOT in Docker Compose mode (where app is already running)
  webServer: process.env.RUN_WEB_SERVER !== 'false' ? {
    command: 'npm run dev -- --port 3000 --host',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
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
            '--unsafely-treat-insecure-origin-as-secure=http://frontend,http://frontend:80',
            '--disable-web-security',
            '--ignore-certificate-errors',
            '--allow-running-insecure-content'
          ]
        }
      },
    },
  ],
});
