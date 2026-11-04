
import { test, expect } from '@playwright/test';

test.describe('CareerForge frontend authentication routing', () => {

  test('unauthenticated users can access login', async ({ page }) => {
    await page.goto('/login');

    await expect(page).toHaveURL(/\/login$/);

    await expect(page.locator('body')).not.toBeEmpty();
  });

  test('unauthenticated users can access signup', async ({ page }) => {
    await page.goto('/signup');

    await expect(page).toHaveURL(/\/signup$/);

    await expect(page.locator('body')).not.toBeEmpty();
  });

  test('dashboard requires authentication', async ({ page }) => {
    await page.goto('/dashboard');

    await expect(page).toHaveURL(/\/login$/);
  });

  test('CV page requires authentication', async ({ page }) => {
    await page.goto('/cv');

    await expect(page).toHaveURL(/\/login$/);
  });

  test('roadmap requires authentication', async ({ page }) => {
    await page.goto('/roadmap');

    await expect(page).toHaveURL(/\/login$/);
  });

  test('AI Mentor requires authentication', async ({ page }) => {
    await page.goto('/mentor');

    await expect(page).toHaveURL(/\/login$/);
  });

  test('admin page requires authentication', async ({ page }) => {
    await page.goto('/admin');

    await expect(page).toHaveURL(/\/login$/);
  });

  test('theme preference is restored', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('careerforge-theme', 'dark');
    });

    await page.goto('/login');

    await expect.poll(async () => {
      return page.evaluate(
        () => document.documentElement.dataset.theme
      );
    }).toBe('dark');

    await page.reload();

    await expect.poll(async () => {
      return page.evaluate(
        () => document.documentElement.dataset.theme
      );
    }).toBe('dark');
  });

});
