
import { test, expect } from '@playwright/test';
import { randomUUID } from 'node:crypto';
import { activateTestAccount } from './test-accounts';

const PASSWORD = 'CareerForge-E2E-2026!';

test.describe('CareerForge real authentication', () => {

  test('signup, login and session restoration', async ({
    page,
  }) => {
    const email =
      `cf-browser-e2e-${randomUUID()}@example.com`;

    // 1. Register through the actual React form.
    await page.goto('/signup');

    await expect(
      page.getByRole('heading', {
        name: 'Create your account',
      })
    ).toBeVisible();

    await page.getByLabel('Full name').fill(
      'CareerForge E2E Tester'
    );

    await page.getByLabel('Email address').fill(email);

    await page.getByLabel('Password', {
      exact: true,
    }).fill(PASSWORD);

    await page.getByLabel('Confirm password', {
      exact: true,
    }).fill(PASSWORD);

    await page.getByRole('button', {
      name: 'Create account',
    }).click();

    // Registration intentionally redirects to login.
    // Registration requires email verification.
await expect(
  page.getByText(/verification email has been sent to/i)
).toBeVisible();

    // Registration requires email verification.
    await expect(
      page.getByText(/verification email has been sent to/i)
    ).toBeVisible();

    // Check that unverified users cannot log in.
    const unverified = await page.request.post('/api/auth/login', {
      data: { email, password: PASSWORD },
    });

    expect(unverified.status()).toBe(403);

    // Activate only this disposable test account.
    activateTestAccount(email);

    // 2. Login with the newly verified account.
    await page.goto('/login');

    await page.getByLabel('Email address').fill(email);

    await page.getByLabel('Password', {
      exact: true,
    }).fill(PASSWORD);

    await page.getByRole('button', {
      name: 'Log in',
    }).click();

    // Login and /api/auth/me must succeed.
    await expect(page).toHaveURL(/\/dashboard$/, {
      timeout: 20_000,
    });

    // 3. Verify the actual backend session.
    const identity = await page.request.get(
      '/api/auth/me'
    );

    expect(identity.status()).toBe(200);

    const user = await identity.json();

    expect(user.email).toBe(email);

    expect(user.onboarding_completed).toEqual(
      expect.any(Boolean)
    );

    // 4. Refresh and verify session restoration.
    await page.reload();

    await expect(page).toHaveURL(/\/dashboard$/);

    // 5. Verify protected application routes.
    await page.goto('/cv');
    await expect(page).toHaveURL(/\/cv$/);

    await page.goto('/roadmap');
    await expect(page).toHaveURL(/\/roadmap$/);

    await page.goto('/mentor');
    await expect(page).toHaveURL(/\/mentor$/);

    // 6. Authenticated users should not see
    // the guest-only login page.
    await page.goto('/login');

    await expect(page).toHaveURL(/\/dashboard$/);

    console.log('REAL AUTHENTICATION E2E: PASS');
    console.log(`Account: ${email}`);
    console.log(`Backend user ID: ${user.id}`);
  });

  test('signup rejects mismatched passwords', async ({
    page,
  }) => {
    await page.goto('/signup');

    await page.getByLabel('Full name').fill(
      'Test Account'
    );

    await page.getByLabel('Email address').fill(
      `cf-browser-e2e-${randomUUID()}@example.com`
    );

    // Enter two DIFFERENT passwords.
    await page.getByLabel('Password', {
      exact: true,
    }).fill(PASSWORD);

    await page.getByLabel('Confirm password', {
      exact: true,
    }).fill('DifferentPassword123!');

    await page.getByRole('button', {
      name: 'Create account',
    }).click();

    // Client-side validation should reject submission.
    await expect(
      page.getByRole('alert')
    ).toContainText(
      'Your passwords do not match.'
    );

    // User must remain on the signup page.
    await expect(page).toHaveURL(/\/signup$/);
  });

});
