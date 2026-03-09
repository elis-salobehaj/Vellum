import { test, expect } from '@playwright/test';

test.describe('Login Page', () => {
  // If VITE_BYPASS_AUTH is true, RequireAuth component renders children immediately.
  // So /login might redirect to / if authenticated (or treated as such).
  //
  //LoginPage.tsx: useEffect redirects to / if config.auth.bypassAuth is true.

  test('should verify login access or bypass redirect', async ({ page }) => {
    await page.goto('/login');

    const bypassHeading = page.getByRole('heading', { name: 'Welcome to Vellum' });
    const loginButton = page.getByRole('button', { name: /Sign in with Entra ID/i });
    const loginHeading = page.getByRole('heading', { name: 'Vellum' });

    await expect(bypassHeading.or(loginButton)).toBeVisible({ timeout: 10000 });
    await expect(bypassHeading.or(loginHeading)).toBeVisible();
  });
});
