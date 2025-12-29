import { test, expect } from '@playwright/test';

test.describe('E2E Full Stack Tests', () => {

  test.beforeEach(async ({ page }) => {
    // Listen for console logs
    page.on('console', msg => console.log(`BROWSER LOG: ${msg.text()}`));
    page.on('pageerror', err => console.log(`BROWSER ERROR: ${err.message}`));

    // Polyfill crypto for HTTP context (Fixes "crypto_nonexistent" error in unsecure contexts)
    await page.addInitScript(() => {
      // Define a mock crypto object
      const mockCrypto = {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        getRandomValues: (arr: any) => {
          for (let i = 0; i < arr.length; i++) {
            arr[i] = Math.floor(Math.random() * 256);
          }
          return arr;
        },
        randomUUID: () => '00000000-0000-0000-0000-000000000000',
        subtle: {
          digest: async () => new Uint8Array(32),
          importKey: async () => ({ type: 'secret', extractable: true, algorithm: { name: 'HMAC' }, usages: ['sign'] }),
          sign: async () => new Uint8Array(32),
          generateKey: async () => ({ type: 'secret', extractable: true, algorithm: { name: 'HMAC' }, usages: ['sign'] }),
          exportKey: async () => new Uint8Array(32),
        }
      };

      if (!window.crypto) {
        Object.defineProperty(window, 'crypto', {
          configurable: true,
          writable: true,
          value: mockCrypto
        });
      } else {
        if (!window.crypto.randomUUID) {
          // eslint-disable-next-line @typescript-eslint/ban-ts-comment
          // @ts-ignore
          window.crypto.randomUUID = mockCrypto.randomUUID;
        }
        if (!window.crypto.getRandomValues) {
          // eslint-disable-next-line @typescript-eslint/ban-ts-comment
          // @ts-ignore
          window.crypto.getRandomValues = mockCrypto.getRandomValues;
        }
        if (!window.crypto.subtle) {
          Object.defineProperty(window.crypto, 'subtle', {
            configurable: true,
            writable: true,
            value: mockCrypto.subtle
          });
        }
      }
    });

  });

  test('should load admin page and fetch models from backend', async ({ page }) => {
    // Navigate to admin
    await page.goto('/admin');

    // Debug info
    console.log(`Current URL: ${page.url()}`);
    console.log(`Page Title: ${await page.title()}`);
    const isCryptoAvailable = await page.evaluate(() => !!window.crypto && !!window.crypto.randomUUID);
    console.log(`Crypto Available: ${isCryptoAvailable}`);

    // Verify title
    await expect(page.getByText('Admin Configuration')).toBeVisible();

    // Check if models loaded (Real backend returns default models in MODEL_CONFIGS)
    // "GPT-4 (OpenAI)" is typically in the list
    await expect(page.locator('select')).toContainText('GPT-4 (openai)');
  });

  test('should send message and receive response', async ({ page }) => {
    await page.goto('/');
    console.log(`Chat Test - Current URL: ${page.url()}`);
    console.log(`Chat Test - Page Title: ${await page.title()}`);

    // Type and send
    await page.getByPlaceholder('Ask anything...').fill('Hello Real Backend');
    await page.getByRole('button', { name: 'Send message' }).click();

    // Verify we get *some* response from the assistant.
    // In a test environment without API keys, this will likely be an error message from the backend,
    // which proves the full integration is working (Frontend -> Backend -> Service -> Frontend).

    // Wait for the 'Thinking...' indicator to disappear, implying a response arrived.
    await expect(page.getByText('Thinking...')).not.toBeVisible({ timeout: 15000 });

    // Check that we have at least 2 messages (User + Assistant)
    // The assistant response might be an error or a real response.
    const messages = page.locator('.space-y-6 > div');
    // Expect 3 messages: Welcome, User, Response
    await expect(messages).toHaveCount(3, { timeout: 10000 });
  });
});
