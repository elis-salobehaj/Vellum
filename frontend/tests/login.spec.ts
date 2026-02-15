import { test, expect } from '@playwright/test';

test.describe('Login Page', () => {
  // If VITE_BYPASS_AUTH is true, RequireAuth component renders children immediately.
  // So /login might redirect to / if authenticated (or treated as such).
  //
  //LoginPage.tsx: useEffect redirects to / if config.auth.bypassAuth is true.

  test('should verify login access or bypass redirect', async ({ page }) => {
    // Navigate to login
    await page.goto('/login');

    // Wait for the URL to stabilize (either stays /login or redirects to /)
    // We use a regex to match either path
    await page.waitForURL(url => url.pathname === '/' || url.pathname === '/login', { timeout: 10000 });

    if (page.url().endsWith('/login')) {
      // Standard flow (Bypass OFF)
      // Use regex/case-insensitive for robustness
      await expect(page.getByText(/Welcome to kbase-ai/i)).toBeVisible();
      await expect(page.getByRole('button', { name: /Sign in with Entra ID/i })).toBeVisible();
    } else {
      // Bypass flow (Bypass ON) - verify we successfully landed in the app
      await expect(page.getByText(/Hello! I am Vellum/i)).toBeVisible();
    }
  });
});
