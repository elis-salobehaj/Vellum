import { test, expect } from '@playwright/test';

test.describe('Login Page', () => {
  // We need to disable bypass auth for this specific test
  // However, the docker container sets ENV VITE_BYPASS_AUTH=true globally.
  // We can't easily change the build-time/runtime env of the Vite server from here 
  // without restarting it or having a way to toggle it.
  // 
  // If VITE_BYPASS_AUTH is true, RequireAuth component renders children immediately.
  // So /login might redirect to / if authenticated (or treated as such).
  //
  // Let's check how LoginPage.tsx behaves.
  // effectively if isAuthenticated is true (which it might not be if we just use bypass in RequireAuth but not actual msal), 
  // LoginPage checks `useIsAuthenticated()`. 
  // RequireAuth checks `import.meta.env.VITE_BYPASS_AUTH === 'true'`.
  //
  // If we browse to /login directly:
  // - LoginPage renders.
  // - useIsAuthenticated() is likely false because we haven't actually logged in with MSAL.
  // - The effect `if (isAuthenticated) navigate('/')` won't trigger.
  // - So we SHOULD see the login page content even if bypass is enabled, UNLESS we are "authenticated".

  test('should display login button', async ({ page }) => {
    await page.goto('/login');
    await expect(page.getByText('Welcome to kbase-ai')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Sign in with Entra ID' })).toBeVisible();
  });
});
