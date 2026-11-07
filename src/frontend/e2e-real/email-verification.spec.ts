
import { test, expect } from '@playwright/test';
import { randomUUID } from 'node:crypto';
import { takeVerificationToken, updateVerificationToken } from './test-accounts';

const PASSWORD = 'CareerForge-E2E-2026!';

test.describe('CareerForge email verification', () => {
  test('registration, verification, token reuse and login', async ({
    page,
  }) => {
    const email = `cf-verify-e2e-${randomUUID()}@example.com`;

    const registration = await page.request.post(
      '/api/auth/register',
      {
        data: {
          full_name: 'CareerForge Verification Tester',
          email,
          password: PASSWORD,
        },
      }
    );

    expect(registration.status()).toBe(201);

    const token = takeVerificationToken(email);
    expect(token.length).toBeGreaterThan(20);

    // Unverified accounts cannot sign in.
    const blockedLogin = await page.request.post(
      '/api/auth/login',
      {
        data: { email, password: PASSWORD },
      }
    );

    expect(blockedLogin.status()).toBe(403);

    // Redeem the actual token through the React page.
    await page.goto(
      `/verify-email?token=${encodeURIComponent(token)}`
    );

    await expect(
      page.getByRole('heading', {
        name: 'Email verified.',
      })
    ).toBeVisible();

    // The page removes the token from the address bar.
    await expect(page).toHaveURL(/\/verify-email$/);

    // Verification tokens must not work twice.
    await page.goto(
      `/verify-email?token=${encodeURIComponent(token)}`
    );

    await expect(
      page.getByRole('heading', {
        name: 'Verification unsuccessful.',
      })
    ).toBeVisible();

    // The verified user must now be able to log in.
    await page.getByRole('link', {
      name: 'Back to login',
    }).click();

    await page.getByLabel('Email address').fill(email);

    await page.getByLabel('Password', {
      exact: true,
    }).fill(PASSWORD);

    await page.getByRole('button', {
      name: 'Log in',
    }).click();

    await expect(page).toHaveURL(/\/dashboard$/);

    const identity = await page.request.get('/api/auth/me');

    expect(identity.status()).toBe(200);
    expect((await identity.json()).email).toBe(email);

    console.log('EMAIL VERIFICATION: PASS');
    console.log('SINGLE-USE TOKEN: PASS');
    console.log('VERIFIED LOGIN: PASS');
  });

  test('invalid verification tokens are rejected', async ({ page }) => {
    await page.goto('/verify-email?token=invalid-token');

    await expect(
      page.getByRole('heading', {
        name: 'Verification unsuccessful.',
      })
    ).toBeVisible();

    await expect(page.getByRole('alert')).toBeVisible();

    await expect(
      page.getByRole('button', {
        name: 'Resend verification email',
      })
    ).toBeVisible();

    console.log('INVALID TOKEN REJECTION: PASS');
  });

  test('verification page rejects a missing token', async ({ page }) => {
    await page.goto('/verify-email');

    await expect(
      page.getByRole('heading', {
        name: 'Verification unsuccessful.',
      })
    ).toBeVisible();

    await expect(page.getByRole('alert')).toHaveText(
      'No verification token was provided.'
    );

    console.log('MISSING TOKEN HANDLING: PASS');
  });

test('expired verification tokens cannot activate accounts', async ({
  page,
}) => {
  const email = `cf-verify-e2e-${randomUUID()}@example.com`;

  const registration = await page.request.post('/api/auth/register', {
    data: {
      full_name: 'CareerForge Expiry Tester',
      email,
      password: PASSWORD,
    },
  });

  expect(registration.status()).toBe(201);

  const token = takeVerificationToken(email);

  // Expire the token in the isolated test database.
  updateVerificationToken('expire-token', email);

  await page.goto(
    `/verify-email?token=${encodeURIComponent(token)}`
  );

  await expect(
    page.getByRole('heading', {
      name: 'Verification unsuccessful.',
    })
  ).toBeVisible();

  await expect(page.getByRole('alert')).toContainText(
    'Invalid or expired verification link.'
  );

  // An expired token must not activate the account.
  const login = await page.request.post('/api/auth/login', {
    data: { email, password: PASSWORD },
  });

  expect(login.status()).toBe(403);

  console.log('EXPIRED TOKEN REJECTION: PASS');
  console.log('UNVERIFIED ACCOUNT PROTECTION: PASS');
});

test('resending verification rotates the token', async ({ page }) => {
  const email = `cf-verify-e2e-${randomUUID()}@example.com`;

  const registration = await page.request.post('/api/auth/register', {
    data: {
      full_name: 'CareerForge Resend Tester',
      email,
      password: PASSWORD,
    },
  });

  expect(registration.status()).toBe(201);

  const originalToken = takeVerificationToken(email);

  // Move outside the existing two-minute resend cooldown.
  updateVerificationToken('age-token', email);

  // Request a replacement through the actual React interface.
  await page.goto('/verify-email');

  await expect(
    page.getByRole('heading', {
      name: 'Verification unsuccessful.',
    })
  ).toBeVisible();

  await page.getByLabel('Email address').fill(email);

  await page.getByRole('button', {
    name: 'Resend verification email',
  }).click();

  await expect(
    page.getByText(
      'If this account requires verification and is eligible, ' +
      'a new verification email will be sent.'
    )
  ).toBeVisible();

  const replacementToken = takeVerificationToken(email);

  expect(replacementToken).toBeTruthy();
  expect(replacementToken).not.toBe(originalToken);

  // The replaced token must no longer work.
  const oldVerification = await page.request.post(
    '/api/auth/verify-email',
    {
      data: { token: originalToken },
    }
  );

  expect(oldVerification.status()).toBe(400);

  // The new token must activate the account.
  await page.goto(
    `/verify-email?token=${encodeURIComponent(replacementToken)}`
  );

  await expect(
    page.getByRole('heading', {
      name: 'Email verified.',
    })
  ).toBeVisible();

  const login = await page.request.post('/api/auth/login', {
    data: { email, password: PASSWORD },
  });

  expect(login.status()).toBe(200);

  console.log('VERIFICATION RESEND: PASS');
  console.log('OLD TOKEN INVALIDATION: PASS');
  console.log('REPLACEMENT TOKEN ACTIVATION: PASS');
});

});
