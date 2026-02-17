
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
    // Check for Model Configuration heading
    await expect(page.getByText('Model Configuration')).toBeVisible();

    // The component might be loading initially. Skeleton is displayed.
    // Wait for the skeleton to disappear or real content to appear.
    // The select trigger will be present when loaded.
    const selectTrigger = page.locator('button[role="combobox"]');

    // Explicitly wait for it to be visible
    await expect(selectTrigger).toBeVisible({ timeout: 10000 });

    // Check initial value
    await expect(selectTrigger).toContainText('Model A');

    // Open dropdown to check options
    await selectTrigger.click();
    await expect(page.getByRole('option', { name: 'Model A' })).toBeVisible();
    await expect(page.getByRole('option', { name: 'Model B' })).toBeVisible();
  });

  test('should switch model and show success message', async ({ page }) => {
    // Open dropdown
    await expect(page.getByText('Model Configuration')).toBeVisible();
    const selectTrigger = page.locator('button[role="combobox"]');
    await selectTrigger.waitFor();
    await selectTrigger.click();

    // Select Model B
    await page.getByRole('option', { name: 'Model B' }).click();

    // Check for success message
    await expect(page.getByText('Model updated successfully')).toBeVisible();
  });

  test('should navigate back to chat', async ({ page }) => {
    // Navigate to root first to establish history
    await page.goto('/');
    await page.goto('/admin');

    // Find the back button (first button in header with arrow icon or clean selector)
    // We can use the locator for the button that navigates back.
    // Assuming it's the first button on the page might be fragile but works for now as it's the header back button.
    const backButton = page.getByRole('button', { name: /Back/i });
    await backButton.click();

    await expect(page).toHaveURL('/');
  });



});
