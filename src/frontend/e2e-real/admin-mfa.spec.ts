import { test, expect } from '@playwright/test';
import type { Page } from '@playwright/test';
import { randomUUID, createHmac } from 'node:crypto';
import { promoteTestAdmin, getExpiredAdminMfaChallenge, } from './test-accounts';

const PASSWORD = 'CareerForge-E2E-2026!';

function totpFromUri(uri: string): string {
  const url = new URL(uri);
  const secret = url.searchParams.get('secret');

  if (url.protocol !== 'otpauth:' || !secret) {
    throw new Error('Invalid TOTP provisioning URI.');
  }

  const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
  const bytes: number[] = [];
  let value = 0;
  let bits = 0;

  for (const char of secret.toUpperCase().replace(/=+$/, '')) {
    const index = alphabet.indexOf(char);
    if (index === -1) throw new Error('Invalid Base32 secret.');

    value = (value << 5) | index;
    bits += 5;

    if (bits >= 8) {
      bytes.push((value >>> (bits - 8)) & 255);
      bits -= 8;
    }
  }

  const period = Number(url.searchParams.get('period') || '30');
  const digits = Number(url.searchParams.get('digits') || '6');
  const counter = Buffer.alloc(8);

  counter.writeBigUInt64BE(
    BigInt(Math.floor(Date.now() / (period * 1000)))
  );

  const digest = createHmac('sha1', Buffer.from(bytes))
    .update(counter)
    .digest();

  const offset = digest[digest.length - 1] & 15;
  const number = digest.readUInt32BE(offset) & 0x7fffffff;

  return String(number % (10 ** digits)).padStart(digits, '0');
}

async function csrfHeaders(page: Page) {
  return page.evaluate(async () => {
    const { csrfHeader } = await import('../src/lib/auth.ts');
    return csrfHeader();
  });
}

async function login(page: Page, email: string) {
  await page.goto('/login');
  await page.getByLabel('Email address').fill(email);
  await page.getByLabel('Password', { exact: true }).fill(PASSWORD);
  await page.getByRole('button', { name: 'Log in' }).click();
}

test.describe('CareerForge administrator MFA', () => {
  test('admin enrollment and TOTP-protected login', async ({ page }) => {
    test.setTimeout(150_000);

    const email = `cf-admin-mfa-e2e-${randomUUID()}@example.com`;

    // 1. Create a disposable user through real registration.
    const registration = await page.request.post('/api/auth/register', {
      data: {
        full_name: 'CareerForge MFA Tester',
        email,
        password: PASSWORD,
      },
    });

    expect(registration.status()).toBe(201);
    promoteTestAdmin(email);

    // 2. First login must require authenticator enrollment.
    await login(page, email);

    await expect(
      page.getByRole('heading', {
        name: 'Secure your administrator account.',
      })
    ).toBeVisible({ timeout: 20_000 });

    const beforeEnrollment = await page.request.get('/api/auth/me');
    expect(beforeEnrollment.status()).not.toBe(200);

    // 3. Start real enrollment with password confirmation.
    const start = await page.request.post(
      '/api/auth/admin-mfa/enroll/start',
      {
        headers: await csrfHeaders(page),
        data: { password: PASSWORD },
      }
    );

    expect(start.status()).toBe(200);

    const setup = await start.json() as {
      provisioning_uri: string;
      qr_code_data_url: string;
    };

    expect(setup.provisioning_uri).toMatch(/^otpauth:\/\/totp\//);
    expect(setup.qr_code_data_url).toMatch(/^data:image\//);

    // 4. Confirm enrollment with a genuine authenticator code.
    const enrollmentCode = totpFromUri(setup.provisioning_uri);

    const confirm = await page.request.post(
      '/api/auth/admin-mfa/enroll/confirm',
      {
        headers: await csrfHeaders(page),
        data: { code: enrollmentCode },
      }
    );

    expect(confirm.status()).toBe(200);

    const result = await confirm.json();
    expect(result.recovery_codes).toHaveLength(8);

    const afterEnrollment = await page.request.get('/api/auth/me');
    expect(afterEnrollment.status()).not.toBe(200);

    console.log('ADMIN MFA ENROLLMENT: PASS');
    console.log('SESSION REVOCATION: PASS');

    // Enrollment consumed this TOTP time step.
    // Wait for the next step before attempting login MFA.
    const enrolledStep = Math.floor(Date.now() / 30_000);

    await expect.poll(
      () => Math.floor(Date.now() / 30_000),
      { timeout: 35_000, intervals: [500] }
    ).toBeGreaterThan(enrolledStep);

    // 5. Password login alone must not grant admin access.
    await login(page, email);

    await expect(
      page.getByRole('heading', { name: "Verify it's you" })
    ).toBeVisible({ timeout: 20_000 });

    const beforeChallenge = await page.request.get('/api/auth/me');
    expect(beforeChallenge.status()).not.toBe(200);

    console.log('ADMIN MFA CHALLENGE REQUIRED: PASS');

    // 6. Invalid TOTP must be rejected.
    const validCode = totpFromUri(setup.provisioning_uri);
    const invalidCode = validCode === '000000'
      ? '999999'
      : '000000';

    await page.getByLabel('Authenticator code').fill(invalidCode);
    await page.getByRole('button', {
      name: 'Verify and continue',
    }).click();

    await expect(page.getByRole('alert')).toBeVisible();

    const afterInvalidCode = await page.request.get('/api/auth/me');
    expect(afterInvalidCode.status()).not.toBe(200);

    console.log('INVALID ADMIN TOTP REJECTION: PASS');

    // 7. Fresh valid TOTP must establish an admin session.
    await page.getByLabel('Authenticator code').fill(
      totpFromUri(setup.provisioning_uri)
    );

    await page.getByRole('button', {
      name: 'Verify and continue',
    }).click();

    await expect(page).toHaveURL(/\/admin$/, {
      timeout: 20_000,
    });

    const authenticated = await page.request.get('/api/auth/me');

    expect(authenticated.status()).toBe(200);
    expect((await authenticated.json()).email).toBe(email);

    console.log('VALID ADMIN MFA LOGIN: PASS');
    console.log('ADMINISTRATOR SESSION: PASS');
  });
  
test('rejects TOTP replay and enforces administrator lockout', async ({
  page,
}) => {
  test.setTimeout(120_000);

  const email = `cf-admin-mfa-e2e-${randomUUID()}@example.com`;

  const registration = await page.request.post('/api/auth/register', {
    data: {
      full_name: 'CareerForge MFA Security Tester',
      email,
      password: PASSWORD,
    },
  });

  expect(registration.status()).toBe(201);
  promoteTestAdmin(email);

  // 1. Authenticate as a new administrator.
  await login(page, email);

  await expect(
    page.getByRole('heading', {
      name: 'Secure your administrator account.',
    })
  ).toBeVisible();

  // 2. Enroll an authenticator using the real backend.
  const start = await page.request.post(
    '/api/auth/admin-mfa/enroll/start',
    {
      headers: await csrfHeaders(page),
      data: { password: PASSWORD },
    }
  );

  expect(start.status()).toBe(200);

  const { provisioning_uri } = await start.json();

  const acceptedStep = Math.floor(Date.now() / 30_000);
  const consumedCode = totpFromUri(provisioning_uri);

  const confirmation = await page.request.post(
    '/api/auth/admin-mfa/enroll/confirm',
    {
      headers: await csrfHeaders(page),
      data: { code: consumedCode },
    }
  );

  expect(confirmation.status()).toBe(200);

  // 3. Start a new admin login challenge.
  const loginResponse = await page.request.post(
    '/api/auth/login',
    {
      data: { email, password: PASSWORD },
    }
  );

  expect(loginResponse.status()).toBe(200);

  const loginResult = await loginResponse.json();
  expect(loginResult.mfa_required).toBe(true);

  const headers = await csrfHeaders(page);

  // Keep the replay attempt within the TOTP validity window.
  expect(
    Math.floor(Date.now() / 30_000) - acceptedStep
  ).toBeLessThanOrEqual(1);

  // 4. Previously consumed TOTP codes must be rejected.
  const replay = await page.request.post(
    '/api/auth/admin-mfa/challenge/verify',
    {
      headers,
      data: { code: consumedCode },
    }
  );

  expect(replay.status()).toBe(400);
  expect((await replay.json()).detail).toBe(
    'Invalid or already used authenticator code.'
  );

  console.log('TOTP REPLAY PROTECTION: PASS');

  // 5. Four additional failures reach the five-attempt limit.
  for (let attempt = 2; attempt <= 5; attempt++) {
    const response = await page.request.post(
      '/api/auth/admin-mfa/challenge/verify',
      {
        headers,
        data: { code: consumedCode },
      }
    );

    expect(response.status()).toBe(400);
  }

  // 6. Further attempts must be blocked by lockout.
  const locked = await page.request.post(
    '/api/auth/admin-mfa/challenge/verify',
    {
      headers,
      data: { code: consumedCode },
    }
  );

  expect(locked.status()).toBe(429);
  expect((await locked.json()).detail).toBe(
    'Too many attempts. Try again later.'
  );

  console.log('FIVE-ATTEMPT LOCKOUT: PASS');

  // 7. The lockout must survive a new login challenge.
  const retryLogin = await page.request.post(
    '/api/auth/login',
    {
      data: { email, password: PASSWORD },
    }
  );

  expect(retryLogin.status()).toBe(200);
  expect((await retryLogin.json()).mfa_required).toBe(true);

  const persistentLockout = await page.request.post(
    '/api/auth/admin-mfa/challenge/verify',
    {
      headers: await csrfHeaders(page),
      data: { code: totpFromUri(provisioning_uri) },
    }
  );

  expect(persistentLockout.status()).toBe(429);

  // Lockout must never establish an admin session.
  const identity = await page.request.get('/api/auth/me');
  expect(identity.status()).not.toBe(200);

  console.log('PERSISTENT MFA LOCKOUT: PASS');
  console.log('ADMIN SESSION PROTECTION: PASS');
});

test('expired MFA challenge cannot establish an admin session', async ({
  page,
}) => {
  test.setTimeout(120_000);

  const email = `cf-admin-mfa-e2e-${randomUUID()}@example.com`;

  const registration = await page.request.post('/api/auth/register', {
    data: {
      full_name: 'CareerForge Expired MFA Tester',
      email,
      password: PASSWORD,
    },
  });

  expect(registration.status()).toBe(201);
  promoteTestAdmin(email);

  // Enroll MFA using the actual backend.
  await login(page, email);

  await expect(
    page.getByRole('heading', {
      name: 'Secure your administrator account.',
    })
  ).toBeVisible();

  const start = await page.request.post(
    '/api/auth/admin-mfa/enroll/start',
    {
      headers: await csrfHeaders(page),
      data: { password: PASSWORD },
    }
  );

  expect(start.status()).toBe(200);

  const { provisioning_uri } = await start.json();

  const confirm = await page.request.post(
    '/api/auth/admin-mfa/enroll/confirm',
    {
      headers: await csrfHeaders(page),
      data: { code: totpFromUri(provisioning_uri) },
    }
  );

  expect(confirm.status()).toBe(200);

  // Begin an actual administrator login challenge.
  await login(page, email);

  await expect(
    page.getByRole('heading', {
      name: "Verify it's you",
    })
  ).toBeVisible();

  // Password-only authentication cannot create a session.
  const before = await page.request.get('/api/auth/me');
  expect(before.status()).not.toBe(200);

  // Replace the challenge cookie with a correctly signed,
  // expired token for this same disposable administrator.
  const challengeCookie = (
    await page.context().cookies()
  ).find(
    (cookie) =>
      cookie.name === 'careerforge_admin_mfa_challenge'
  );

  if (!challengeCookie) {
    throw new Error('Admin MFA challenge cookie missing.');
  }

  const expiredToken = getExpiredAdminMfaChallenge(email);

  await page.context().addCookies([
    {
      ...challengeCookie,
      value: expiredToken,
    },
  ]);

  // Wait for a fresh code so that the only intentional
  // authentication failure is the expired challenge.
  const currentStep = Math.floor(Date.now() / 30_000);

  await expect.poll(
    () => Math.floor(Date.now() / 30_000),
    {
      timeout: 35_000,
      intervals: [500],
    }
  ).toBeGreaterThan(currentStep);

  await page.getByLabel('Authenticator code').fill(
    totpFromUri(provisioning_uri)
  );

  await page.getByRole('button', {
    name: 'Verify and continue',
  }).click();

  await expect(
    page.getByRole('alert')
  ).toContainText(
    'Invalid or expired MFA challenge.'
  );

  // The expired challenge must not issue a session.
  const after = await page.request.get('/api/auth/me');
  expect(after.status()).not.toBe(200);

  console.log('EXPIRED MFA CHALLENGE: PASS');
  console.log('ADMIN SESSION PROTECTION: PASS');
});

test('admin resource writes require a fresh TOTP code', async ({ page }) => {
  test.setTimeout(180_000);

  const email = `cf-admin-mfa-e2e-${randomUUID()}@example.com`;
  const resourceTitle = `CareerForge MFA E2E ${randomUUID()}`;

  const registration = await page.request.post('/api/auth/register', {
    data: {
      full_name: 'CareerForge Resource Security Tester',
      email,
      password: PASSWORD,
    },
  });

  expect(registration.status()).toBe(201);
  promoteTestAdmin(email);

  // 1. Enroll this disposable administrator.
  await login(page, email);

  await expect(
    page.getByRole('heading', {
      name: 'Secure your administrator account.',
    })
  ).toBeVisible();

  const start = await page.request.post(
    '/api/auth/admin-mfa/enroll/start',
    {
      headers: await csrfHeaders(page),
      data: { password: PASSWORD },
    }
  );

  expect(start.status()).toBe(200);

  const { provisioning_uri } = await start.json();

  const enrollmentStep = Math.floor(Date.now() / 30_000);
  const enrollmentCode = totpFromUri(provisioning_uri);

  const confirmation = await page.request.post(
    '/api/auth/admin-mfa/enroll/confirm',
    {
      headers: await csrfHeaders(page),
      data: { code: enrollmentCode },
    }
  );

  expect(confirmation.status()).toBe(200);

  // 2. Use a fresh time step for administrator login.
  await expect.poll(
    () => Math.floor(Date.now() / 30_000),
    { timeout: 40_000, intervals: [500] }
  ).toBeGreaterThan(enrollmentStep);

  await login(page, email);

  await expect(
    page.getByRole('heading', { name: "Verify it's you" })
  ).toBeVisible();

  const loginStep = Math.floor(Date.now() / 30_000);
  const loginCode = totpFromUri(provisioning_uri);

  const challenge = await page.request.post(
    '/api/auth/admin-mfa/challenge/verify',
    {
      headers: await csrfHeaders(page),
      data: { code: loginCode },
    }
  );

  expect(challenge.status()).toBe(200);

  const identity = await page.request.get('/api/auth/me');
  expect(identity.status()).toBe(200);

  // Choose an actual career competency from the backend.
const optionsResponse = await page.request.get(
  '/api/admin/resources/options'
);

expect(optionsResponse.status()).toBe(200);

const options = await optionsResponse.json() as {
  careers: {
    key: string;
    competencies: { key: string }[];
  }[];
};

const career = options.careers.find(
  (item) => item.competencies?.length > 0
);

if (!career) {
  throw new Error('No career competency available for testing.');
}

    const resource = {
    title: resourceTitle,
    provider: 'CareerForge E2E Tests',
    resource_type: 'course',
    url: `https://example.com/careerforge-mfa-test/${randomUUID()}`,
    description: 'Disposable administrator MFA test resource.',
    assignments: [
        {
        career_key: career.key,
        competency_key: career.competencies[0].key,
        },
    ],
    skill_ids: [],
    };

  const endpoint = '/api/admin/resources';

  // 4. The resource API must require a TOTP field.
  const missingCode = await page.request.post(endpoint, {
    headers: await csrfHeaders(page),
    data: resource,
  });

  expect(missingCode.status()).toBe(422);

  console.log('MISSING TOTP REJECTION: PASS');

  // 5. The code already used for login cannot authorize a write.
  const replayedLoginCode = await page.request.post(endpoint, {
    headers: await csrfHeaders(page),
    data: {
      ...resource,
      totp_code: loginCode,
    },
  });

  const replayBody = await replayedLoginCode.json();

    console.log('REPLAY STATUS:', replayedLoginCode.status());
    console.log('REPLAY ERROR:', JSON.stringify(replayBody, null, 2));

    expect(
    replayedLoginCode.status(),
    JSON.stringify(replayBody)
    ).toBe(400);

  console.log('REUSED LOGIN TOTP REJECTION: PASS');

  // 6. Wait for a new code before creating the resource.
  await expect.poll(
    () => Math.floor(Date.now() / 30_000),
    { timeout: 40_000, intervals: [500] }
  ).toBeGreaterThan(loginStep);

  const resourceCode = totpFromUri(provisioning_uri);

  const created = await page.request.post(endpoint, {
    headers: await csrfHeaders(page),
    data: {
      ...resource,
      totp_code: resourceCode,
    },
  });

  expect(created.status(), await created.text()).toBe(201);

  const saved = await created.json();
  expect(saved.id).toBeGreaterThan(0);

  console.log('AUTHORIZED RESOURCE CREATION: PASS');

  // 7. Reusing the creation code must not authorize another write.
  const replay = await page.request.post(endpoint, {
    headers: await csrfHeaders(page),
    data: {
        ...resource,
        title: `${resourceTitle} replay`,
        url: `${resource.url}/replay`,
        totp_code: resourceCode,
    },
    });

    expect(replay.status(), await replay.text()).toBe(400);

  console.log('RESOURCE ACTION TOTP REPLAY: PASS');
});

test('resource creation popup enforces administrator TOTP', async ({
  page,
}) => {
  test.setTimeout(180_000);

  const email = `cf-admin-mfa-e2e-${randomUUID()}@example.com`;
  const resourceTitle = `CareerForge UI E2E ${randomUUID()}`;

  // Create and promote a disposable administrator.
  const registration = await page.request.post('/api/auth/register', {
    data: {
      full_name: 'CareerForge MFA UI Tester',
      email,
      password: PASSWORD,
    },
  });

  expect(registration.status()).toBe(201);
  promoteTestAdmin(email);

  // Enroll the authenticator.
  await login(page, email);

  await expect(
    page.getByRole('heading', {
      name: 'Secure your administrator account.',
    })
  ).toBeVisible();

  const start = await page.request.post(
    '/api/auth/admin-mfa/enroll/start',
    {
      headers: await csrfHeaders(page),
      data: { password: PASSWORD },
    }
  );

  expect(start.status()).toBe(200);

  const { provisioning_uri } = await start.json();

  const enrollmentStep = Math.floor(Date.now() / 30_000);

  const confirmation = await page.request.post(
    '/api/auth/admin-mfa/enroll/confirm',
    {
      headers: await csrfHeaders(page),
      data: { code: totpFromUri(provisioning_uri) },
    }
  );

  expect(confirmation.status()).toBe(200);

  // Wait for a fresh code before administrator login.
  await expect.poll(
    () => Math.floor(Date.now() / 30_000),
    { timeout: 40_000, intervals: [500] }
  ).toBeGreaterThan(enrollmentStep);

  await login(page, email);

  await expect(
    page.getByRole('heading', { name: "Verify it's you" })
  ).toBeVisible();

  const loginStep = Math.floor(Date.now() / 30_000);

  const challenge = await page.request.post(
    '/api/auth/admin-mfa/challenge/verify',
    {
      headers: await csrfHeaders(page),
      data: { code: totpFromUri(provisioning_uri) },
    }
  );

  expect(challenge.status()).toBe(200);

  // Open the actual resource-management interface.
  await page.goto('/admin/resources');

  await page.getByRole('button', {
    name: '+ Add resource',
  }).click();

  const panel = page.locator('.cf-resources-panel').filter({
    has: page.getByRole('heading', {
      name: /learning resource|add resource|new resource/i,
    }),
  });

  await expect(panel).toBeVisible();

  // Fill in the resource details.
  await panel.getByLabel('Resource title').fill(resourceTitle);
  await panel.getByLabel('Provider').fill('CareerForge E2E');
  await panel.getByLabel('Resource URL').fill(
    `https://example.com/careerforge-ui/${randomUUID()}`
  );
  await panel.getByLabel('Description').fill(
    'Disposable resource created by the MFA browser test.'
  );

  // Use a valid career competency instead of an arbitrary skill ID.
  const optionsResponse = await page.request.get(
    '/api/admin/resources/options'
  );

  expect(optionsResponse.status()).toBe(200);

  const options = await optionsResponse.json() as {
    careers: {
      key: string;
      competencies: { key: string }[];
    }[];
  };

  const career = options.careers.find(
    (item) => item.competencies?.length > 0
  );

  if (!career) {
    throw new Error('No career competencies available.');
  }
    const mappingRadios = panel.locator(
    'input[type="radio"][name="mapping-mode"]'
    );

    await expect(mappingRadios).toHaveCount(3);

    // Order: Global, Career, Both
    await mappingRadios.nth(1).check();

    await expect(mappingRadios.nth(1)).toBeChecked();

  await panel.getByRole('combobox', {
    name: 'Career',
    exact: true,
  }).selectOption(career.key);

  await panel.getByRole('combobox', {
    name: 'Competency',
    exact: true,
  }).selectOption(career.competencies[0].key);

  // Submitting the form must trigger the authenticator popup.
  await panel.locator('button[type="submit"]').click();

  const dialog = page.getByRole('dialog', {
    name: 'Confirm resource creation',
  });

  await expect(dialog).toBeVisible();

  console.log('AUTHENTICATOR POPUP: PASS');

  // Submit an invalid code and ensure the dialog remains open.
  const validCode = totpFromUri(provisioning_uri);
  const invalidCode = validCode === '000000'
    ? '999999'
    : '000000';

  await dialog.getByLabel('Authenticator code').fill(invalidCode);

  await dialog.getByRole('button', {
    name: 'Verify & confirm',
  }).click();

  await expect(dialog.getByRole('alert')).toContainText(
    'Invalid or already used authenticator code.'
  );

  await expect(dialog).toBeVisible();

  console.log('POPUP INVALID TOTP REJECTION: PASS');

  // The code used during login cannot be reused for the resource.
  await expect.poll(
    () => Math.floor(Date.now() / 30_000),
    { timeout: 40_000, intervals: [500] }
  ).toBeGreaterThan(loginStep);

  // Save using a fresh authenticator code.
  await dialog.getByLabel('Authenticator code').fill(
    totpFromUri(provisioning_uri)
  );

  await dialog.getByRole('button', {
    name: 'Verify & confirm',
  }).click();

  await expect(dialog).toBeHidden({
    timeout: 20_000,
  });

  await expect(
    page.getByText(/Resource #\d+ created successfully\./)
  ).toBeVisible();

  console.log('POPUP VALID TOTP SAVE: PASS');

  // Verify the new resource appears in the catalog.
  await page.getByRole('searchbox', {
    name: 'Search learning resources',
  }).fill(resourceTitle);

  await expect(
    page.getByText(resourceTitle, { exact: true }).first()
  ).toBeVisible({ timeout: 20_000 });

  console.log('RESOURCE CATALOG PERSISTENCE: PASS');
});

});
