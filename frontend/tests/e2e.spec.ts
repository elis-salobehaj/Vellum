import { test, expect } from '@playwright/test';

test.describe('E2E Full Stack Tests', () => {
  test.describe.configure({ mode: 'serial' });

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
    await expect(page.getByRole('heading', { name: 'Admin Dashboard' })).toBeVisible();
    await expect(page.getByText('Knowledge Base Ingestion')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Start Ingestion' })).toBeVisible();
  });

  test('should send message and receive response', async ({ page }) => {
    test.slow();

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Type and send
    await page.getByPlaceholder('How can I help you today?').fill('Hello Real Backend');
    await page.getByPlaceholder('How can I help you today?').press('Enter');

    await expect(page).toHaveURL(/\/chat\//, { timeout: 90000 });
    await expect(page.getByPlaceholder('How can I help you today?')).toHaveValue('');
    await expect(page.locator('.prose').first()).toBeVisible({ timeout: 90000 });
  });
});
