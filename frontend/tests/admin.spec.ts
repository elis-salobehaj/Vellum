
import { test, expect } from '@playwright/test';

test.describe('Admin Page', () => {

  test.beforeEach(async ({ page }) => {
    // Navigate to admin
    await page.goto('/admin');
  });

  test('should render ingestion dashboard controls', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Admin Dashboard' })).toBeVisible();
    await expect(page.getByText('Manage system configuration and data ingestion')).toBeVisible();
    await expect(page.getByText('Knowledge Base Ingestion')).toBeVisible();
    await expect(page.getByText('Upload Knowledge Base (PDF)')).toBeVisible();
    await expect(page.getByText('Click to upload or drag and drop')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Start Ingestion' })).toBeVisible();
    await expect(page.getByText('Ingestion Logs (0)')).toBeVisible();
  });

  test('should navigate back to chat', async ({ page }) => {
    // Navigate to root first to establish history
    await page.goto('/');
    await page.goto('/admin');

    // Find the back button (first button in header with arrow icon or clean selector)
    // We can use the locator for the button that navigates back.
    // Assuming it's the first button on the page might be fragile but works for now as it's the header back button.
    const backButton = page.getByRole('button', { name: 'Back to previous page' });
    await backButton.click();

    await expect(page).toHaveURL('/');
  });



});
