
import { test, expect } from '@playwright/test';

test.describe('Chat Page', () => {

  test.beforeEach(async ({ page }) => {
    // Listen for console logs for easier debugging in CI
    page.on('console', msg => console.log(`BROWSER LOG: ${msg.text()}`));

    // Mock the History API
    await page.route('**/api/v1/history/**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([])
      });
    });

    // Mock the Models API
    await page.route('**/api/v1/admin/models', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([{ id: 'test-model', name: 'Test Model', provider: 'openai' }])
      });
    });

    // Mock the Chat API with a flexible glob
    await page.route('**/api/v1/chat*', async route => {
      const json = {
        response: "I am a mock response from Vellum.",
        citations: [
          { source: "doc1.pdf", page: 1, text: "Reference text here." }
        ],
        session_id: "mock-session-id"
      };
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(json)
      });
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('should display initial greeting', async ({ page }) => {
    await expect(page.getByText('Hello! I am Vellum')).toBeVisible();
  });

  test('should send message and display response', async ({ page }) => {
    const message = 'Hello Vellum';

    // Type in chat input
    await page.getByPlaceholder('Ask anything...').fill(message);
    await page.getByRole('button', { name: 'Send message' }).click();

    // Wait for the UI to update to show processing
    await page.waitForTimeout(500);

    // Wait for user message to appear
    await expect(page.getByText(message)).toBeVisible();

    // Wait for response (regex for flexibility)
    await expect(page.getByText(/I am a mock response from Vellum/i)).toBeVisible({ timeout: 15000 });
  });

  test('should show citation panel when clicking citation', async ({ page }) => {
    await page.getByPlaceholder('Ask anything...').fill('test');
    await page.getByRole('button', { name: 'Send message' }).click();

    // Wait for response to appear fully
    await expect(page.getByText(/I am a mock response from Vellum/i)).toBeVisible({ timeout: 15000 });

    // Verify citation exists
    const citationTag = page.getByText('doc1.pdf');
    await expect(citationTag).toBeVisible();

    // Click the preview button (the circle info icon)
    const previewBtn = page.getByTitle('View Preview').first();
    await previewBtn.click();

    // Verify side panel opens and shows the source text
    await expect(page.getByText('Source Panel')).toBeVisible();
    await expect(page.getByText('Reference text here.')).toBeVisible();
  });
});
