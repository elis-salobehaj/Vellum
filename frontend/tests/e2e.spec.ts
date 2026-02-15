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
        getRandomValues: (arr: Uint8Array) => {
          for (let i = 0; i < arr.length; i++) {
            arr[i] = Math.floor(Math.random() * 256);
          }
          return arr;
        },
        randomUUID: () => '00000000-0000-0000-0000-000000000000',
        subtle: {
          digest: async () => new Uint8Array(32),
          importKey: async () => ({ type: 'secret', extractable: true, algorithm: { name: 'HMAC' } as const, usages: ['sign'] as const }),
          sign: async () => new Uint8Array(32),
          generateKey: async () => ({ type: 'secret', extractable: true, algorithm: { name: 'HMAC' } as const, usages: ['sign'] as const }),
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
          // @ts-expect-error - polyfilling missing crypto method
          window.crypto.randomUUID = mockCrypto.randomUUID;
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
    await page.waitForLoadState('networkidle');

    // Verify title
    await expect(page.getByText(/Admin Configuration/i)).toBeVisible();

    // Check if models loaded
    await expect(page.locator('select')).toContainText(/GPT-4/i);
  });

  test('should send message and receive response', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Type and send
    await page.getByPlaceholder('Ask anything...').fill('Hello Real Backend');
    await page.getByRole('button', { name: 'Send message' }).click();

    // Wait for the 'Thinking...' indicator to disappear
    await expect(page.getByText('Thinking...')).not.toBeVisible({ timeout: 20000 });

    // Count only finalized message bubbles (avoid counting the 'Thinking...' indicator)
    const bubbles = page.getByTestId('message-bubble');

    // We expect 3 bubbles: The initial greeting, the user message, and the assistant response.
    await expect(bubbles).toHaveCount(3, { timeout: 20000 });
  });
});
