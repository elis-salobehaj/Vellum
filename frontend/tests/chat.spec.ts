
import { test, expect } from '@playwright/test';

test.describe('Chat Page', () => {

  test.beforeEach(async ({ page }) => {
    let mockSessionMessages: Array<{ role: 'user' | 'assistant'; content: string; citations?: Array<{ source: string; page?: number; text: string }> }> = [];

    // Listen for console logs for easier debugging in CI
    page.on('console', msg => console.log(`BROWSER LOG: ${msg.text()}`));

    // Mock the History API
    await page.route('**/api/v1/history**', async route => {
      const url = route.request().url();
      const body = url.endsWith('/history/mock-session-id') ? mockSessionMessages : [];
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(body)
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
      const request = route.request().postDataJSON() as { message: string };
      mockSessionMessages = [
        { role: 'user', content: request.message, citations: [] },
        { role: 'assistant', content: json.response, citations: json.citations },
      ];
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
    await expect(page.getByRole('heading', { name: 'Welcome to Vellum' })).toBeVisible();
    await expect(page.getByText('Your intelligent knowledge assistant. Ask me anything about your documents.')).toBeVisible();
    await expect(page.getByPlaceholder('How can I help you today?')).toBeVisible();
  });

  test('should send message and display response', async ({ page }) => {
    const message = 'Hello Vellum';

    // Type in chat input
    await page.getByPlaceholder('How can I help you today?').fill(message);
    await page.getByPlaceholder('How can I help you today?').press('Enter');

    // Wait for the UI to update to show processing
    await page.waitForTimeout(500);

    await expect(page).toHaveURL(/\/chat\/mock-session-id$/);

    // Wait for user message to appear
    await expect(page.getByText(message)).toBeVisible();

    // Wait for response (regex for flexibility)
    await expect(page.getByText(/I am a mock response from Vellum/i)).toBeVisible({ timeout: 15000 });
  });

  test('should render citation download link', async ({ page }) => {
    await page.getByPlaceholder('How can I help you today?').fill('test');
    await page.getByPlaceholder('How can I help you today?').press('Enter');

    // Wait for response to appear fully
    await expect(page.getByText(/I am a mock response from Vellum/i)).toBeVisible({ timeout: 15000 });

    const citationLink = page.locator('a[href$="/files/doc1.pdf"]');
    await expect(citationLink).toBeVisible();
    await expect(citationLink).toContainText('doc1.pdf');
  });
});
