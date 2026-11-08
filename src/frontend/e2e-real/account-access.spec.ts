import { test, expect, request as apiRequest } from '@playwright/test';
import type { Page } from '@playwright/test';
import { randomUUID } from 'node:crypto';
import { activateTestAccount } from './test-accounts';

const PASSWORD = 'CareerForge-E2E-2026!';

async function createAuthenticatedUser(page: Page) {
  const email =
    `cf-account-e2e-${randomUUID()}@example.com`;

  const name = 'CareerForge Account Tester';

  const registration = await page.request.post(
    '/api/auth/register',
    {
      data: {
        full_name: name,
        email,
        password: PASSWORD,
      },
    }
  );

  expect(registration.status()).toBe(201);

  activateTestAccount(email);

  await page.goto('/login');

  await page.getByLabel('Email address').fill(email);

  await page.getByLabel('Password', {
    exact: true,
  }).fill(PASSWORD);

  await page.getByRole('button', {
    name: 'Log in',
  }).click();

  await expect(page).toHaveURL(/\/dashboard$/);

  return { name, email };
}

test.describe('CareerForge account and administration', () => {

  test('regular users cannot access the administrator workspace', async ({
    page,
  }) => {
    await createAuthenticatedUser(page);
      const protectedEndpoints = [
    '/api/admin/me',
    '/api/admin/overview',
    '/api/admin/users?page=1&page_size=20',
    '/api/admin/logs?page=1&page_size=25',
    '/api/admin/health',
  ];

  for (const endpoint of protectedEndpoints) {
    const response = await page.request.get(endpoint);

    expect(
      response.status(),
      `Regular user accessed ${endpoint}`
    ).toBe(403);
  }

  console.log('ADMIN API AUTHORIZATION: PASS');

    await page.goto('/admin');

    await expect(
      page.getByRole('heading', {
        name: 'Access restricted',
      })
    ).toBeVisible({
      timeout: 20_000,
    });

    await expect(
      page.getByRole('heading', {
        name: 'System Administration',
      })
    ).toHaveCount(0);

    await expect(
      page.getByRole('navigation', {
        name: 'Administration sections',
      })
    ).toHaveCount(0);

    await page.getByRole('link', {
      name: 'Return to your workspace',
    }).click();

    await expect(page).toHaveURL(/\/dashboard$/);

    console.log('ADMIN ACCESS RESTRICTION: PASS');
  });

  test('profile information and settings navigation', async ({
    page,
  }) => {
    const { name, email } =
      await createAuthenticatedUser(page);

    await page.goto('/profile');

    await expect(
      page.getByRole('heading', {
        name: 'Your career profile.',
      })
    ).toBeVisible();

    const identity = page.locator(
      '.cf-profile-identity-details'
    );

    await expect(
      identity.getByRole('heading', {
        name,
        exact: true,
      })
    ).toBeVisible();

    await expect(
      identity.getByText(email, {
        exact: true,
      })
    ).toBeVisible();

    await expect(
      page.getByRole('heading', {
        name: 'Your progress',
      })
    ).toBeVisible();

    await page.getByRole('link', {
      name: 'Account settings',
    }).click();

    await expect(page).toHaveURL(/\/settings$/);

    await expect(
      page.getByRole('heading', {
        name: 'Your settings.',
      })
    ).toBeVisible();

    console.log('PROFILE IDENTITY: PASS');
    console.log('SETTINGS NAVIGATION: PASS');
  });
  
  test('account updates, profile synchronization and logout', async ({
    page,
  }) => {
    const { name, email } = await createAuthenticatedUser(page);

    const updatedName = 'CareerForge Updated Tester';

    // 1. Open account settings.
    await page.goto('/settings');

    await expect(
      page.getByRole('heading', {
        name: 'Your settings.',
      })
    ).toBeVisible();

    // 2. Locate the account information form.
    const settingsForm = page.locator('form').filter({
      has: page.getByRole('button', {
        name: 'Save changes',
      }),
    });

    await expect(settingsForm).toHaveCount(1);

    const nameInput = settingsForm.locator(
      'input:not([readonly]):not([type="hidden"])'
    ).first();

    await expect(nameInput).toHaveValue(name);

    // 3. Update the account name.
    await nameInput.fill(updatedName);

    await settingsForm.getByRole('button', {
      name: 'Save changes',
    }).click();

    await expect(
      page.getByText(
        'Your account information has been updated.'
      )
    ).toBeVisible({
      timeout: 20_000,
    });

    console.log('ACCOUNT UPDATE: PASS');

    // 4. Verify the backend persisted the change.
    const response = await page.request.get(
      '/api/account/settings'
    );

    expect(response.status()).toBe(200);

    const account = await response.json();

    expect(account.full_name).toBe(updatedName);
    expect(account.email).toBe(email);

    console.log('ACCOUNT PERSISTENCE: PASS');

    // 5. Verify the profile reflects the new name.
    await page.goto('/profile');

    const identity = page.locator(
      '.cf-profile-identity-details'
    );

    await expect(
      identity.getByRole('heading', {
        name: updatedName,
        exact: true,
      })
    ).toBeVisible();

    // 6. Reload to verify session and profile restoration.
    await page.reload();

    await expect(
      identity.getByRole('heading', {
        name: updatedName,
        exact: true,
      })
    ).toBeVisible();

    console.log('PROFILE SYNCHRONIZATION: PASS');

    // 7. Sign out using the Settings interface.
    await page.goto('/settings');

    await page.getByRole('button', {
      name: 'Sign out',
      exact: true,
    }).click();

    await expect(page).toHaveURL(/\/login$/);

    console.log('LOGOUT: PASS');

    // 8. The old session must no longer be authenticated.
    const session = await page.request.get(
      '/api/auth/me'
    );

    expect(session.status()).toBe(401);

    // 9. Protected routes must redirect to login.
    await page.goto('/profile');
    await expect(page).toHaveURL(/\/login$/);

    await page.goto('/roadmap');
    await expect(page).toHaveURL(/\/login$/);

    console.log('SESSION INVALIDATION: PASS');
    console.log('ACCOUNT MANAGEMENT E2E: PASS');
  });

  
test('cookie CSRF protection and bearer authentication', async ({
  page,
}) => {
  const { name, email } = await createAuthenticatedUser(page);

  // 1. Reject cookie-authenticated writes without CSRF.
  const rejected = await page.request.patch(
    '/api/account/settings',
    {
      data: {
        full_name: 'Unauthorized Account Change',
      },
    }
  );

  expect(rejected.status()).toBe(403);

  const error = await rejected.json();
  expect(error.detail).toMatch(/csrf/i);

  console.log('CSRF PROTECTION: PASS');

  // 2. Confirm the rejected update was not persisted.
  const accountResponse = await page.request.get(
    '/api/account/settings'
  );

  expect(accountResponse.status()).toBe(200);

  const account = await accountResponse.json();
  expect(account.full_name).toBe(name);

  console.log('CSRF DATA INTEGRITY: PASS');

  // 3. Authenticate using the existing login API.
  const loginResponse = await page.request.post(
    '/api/auth/login',
    {
      data: {
        email,
        password: PASSWORD,
      },
    }
  );

  expect(loginResponse.status()).toBe(200);

  const login = await loginResponse.json();

  expect(typeof login.access_token).toBe('string');
  expect(login.access_token.length).toBeGreaterThan(20);

  // 4. Verify the browser session cookie is HttpOnly.
  const cookies = loginResponse.headersArray()
    .filter((header) =>
      header.name.toLowerCase() === 'set-cookie'
    )
    .map((header) => header.value);

  expect(
    cookies.some(
      (cookie) =>
        cookie.startsWith('careerforge_session=') &&
        /httponly/i.test(cookie)
    )
  ).toBe(true);

  console.log('HTTPONLY SESSION COOKIE: PASS');

  // 5. Create a completely separate API client.
  // It does not share the browser's session cookies.
  const bearerClient = await apiRequest.newContext({
    baseURL: 'http://127.0.0.1:15173',
  });

  try {
    // Without cookies or a bearer token, access is denied.
    const unauthenticated = await bearerClient.get(
      '/api/auth/me'
    );

    expect(unauthenticated.status()).toBe(401);

    // Authenticate using only the Authorization header.
    const authenticated = await bearerClient.get(
      '/api/auth/me',
      {
        headers: {
          Authorization: `Bearer ${login.access_token}`,
        },
      }
    );

    expect(authenticated.status()).toBe(200);

    const user = await authenticated.json();
    expect(user.email).toBe(email);

    console.log('BEARER AUTHENTICATION: PASS');
    console.log('COOKIELESS API ACCESS: PASS');
  } finally {
    await bearerClient.dispose();
  }
});



});
