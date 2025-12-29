
import { test, expect } from '@playwright/test';

test.describe('Admin Page', () => {

  test.beforeEach(async ({ page }) => {
    // Mock Models API
    await page.route('**/admin/models', async route => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            { id: 'model-a', name: 'Model A', provider: 'Provider A', is_active: true },
            { id: 'model-b', name: 'Model B', provider: 'Provider B', is_active: false }
          ])
        });
      } else {
        await route.continue();
      }
    });

    // Mock Update Model API
    await page.route('**/admin/models/*', async route => {
      if (route.request().method() === 'PUT') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true })
        });
      } else {
        // Fallback for default GETs to specific model if any (none in code)
        await route.continue();
      }
    });

    // Navigate to admin
    await page.goto('/admin');
  });

  test('should load models and display active model', async ({ page }) => {
    await expect(page.getByText('Admin Configuration')).toBeVisible();

    // Check if select has the correct value
    // The select likely has the value of the active model ID
    const select = page.getByRole('combobox');
    await expect(select).toHaveValue('model-a');

    // Check options text
    await expect(page.locator('option').filter({ hasText: 'Model A' })).toBeAttached();
    await expect(page.locator('option').filter({ hasText: 'Model B' })).toBeAttached();
  });

  test('should switch model and show success message', async ({ page }) => {
    // Switch to Model B
    await page.getByRole('combobox').selectOption('model-b');

    // Check for success message
    await expect(page.getByText('Switched to Model B')).toBeVisible();
  });

  test('should navigate back to chat', async ({ page }) => {
    await page.click('button:has-text("Back to Chat")');
    await expect(page).toHaveURL('/');
  });

});
