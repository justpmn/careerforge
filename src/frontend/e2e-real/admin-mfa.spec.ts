import { test, expect } from '@playwright/test';
import type { Page } from '@playwright/test';
import { randomUUID, createHmac } from 'node:crypto';
import { promoteTestAdmin, getExpiredAdminMfaChallenge, expireAdminRecoveryGrant} from './test-accounts';

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

test('administrator recovery codes are single-use', async ({ page }) => {
  test.setTimeout(120_000);

  const email = `cf-admin-mfa-e2e-${randomUUID()}@example.com`;

  const registration = await page.request.post('/api/auth/register', {
    data: {
      full_name: 'CareerForge Recovery Tester',
      email,
      password: PASSWORD,
    },
  });

  expect(registration.status()).toBe(201);
  promoteTestAdmin(email);

  await login(page, email);

  await expect(
    page.getByRole('heading', {
      name: 'Secure your administrator account.',
    })
  ).toBeVisible();

  const enrollment = await page.request.post(
    '/api/auth/admin-mfa/enroll/start',
    {
      headers: await csrfHeaders(page),
      data: { password: PASSWORD },
    }
  );

  expect(enrollment.status()).toBe(200);

  const { provisioning_uri } = await enrollment.json();

  const confirmation = await page.request.post(
    '/api/auth/admin-mfa/enroll/confirm',
    {
      headers: await csrfHeaders(page),
      data: { code: totpFromUri(provisioning_uri) },
    }
  );

  expect(confirmation.status()).toBe(200);

  const { recovery_codes } = await confirmation.json() as {
    recovery_codes: string[];
  };

  expect(recovery_codes).toHaveLength(8);

  console.log('EIGHT RECOVERY CODES GENERATED: PASS');

  await login(page, email);

  await expect(
    page.getByRole('heading', { name: "Verify it's you" })
  ).toBeVisible();

  const endpoint = '/api/auth/admin-mfa/challenge/recovery';

  // A fabricated code must not establish an administrator session.
  const invalid = await page.request.post(endpoint, {
    headers: await csrfHeaders(page),
    data: { recovery_code: '0'.repeat(32) },
  });

  expect(invalid.status()).toBe(400);

  const beforeRecovery = await page.request.get('/api/auth/me');
  expect(beforeRecovery.status()).not.toBe(200);

  console.log('INVALID RECOVERY CODE REJECTED: PASS');

  // A legitimate saved recovery code must work.
  const valid = await page.request.post(endpoint, {
    headers: await csrfHeaders(page),
    data: { recovery_code: recovery_codes[0] },
  });

  expect(valid.status(), await valid.text()).toBe(200);

  const authenticated = await page.request.get('/api/auth/me');
  expect(authenticated.status()).toBe(200);

  console.log('RECOVERY LOGIN SUCCESSFUL: PASS');

  // Clear the browser session and initiate another MFA challenge.
  await page.context().clearCookies();

  await login(page, email);

  await expect(
    page.getByRole('heading', { name: "Verify it's you" })
  ).toBeVisible();

  // The previously consumed code must no longer work.
  const replay = await page.request.post(endpoint, {
    headers: await csrfHeaders(page),
    data: { recovery_code: recovery_codes[0] },
  });

  expect(replay.status()).toBe(400);

  const afterReplay = await page.request.get('/api/auth/me');
  expect(afterReplay.status()).not.toBe(200);

  console.log('RECOVERY CODE REPLAY REJECTED: PASS');

  // An unused second recovery code must still work.
  const second = await page.request.post(endpoint, {
    headers: await csrfHeaders(page),
    data: { recovery_code: recovery_codes[1] },
  });

  expect(second.status(), await second.text()).toBe(200);

  const finalSession = await page.request.get('/api/auth/me');
  expect(finalSession.status()).toBe(200);

  console.log('SECOND RECOVERY CODE SUCCESSFUL: PASS');
});

test('administrator can sign in using the recovery code UI', async ({
  page,
}) => {
  test.setTimeout(120_000);

  const email = `cf-admin-mfa-e2e-${randomUUID()}@example.com`;

  const registration = await page.request.post('/api/auth/register', {
    data: {
      full_name: 'CareerForge Recovery UI Tester',
      email,
      password: PASSWORD,
    },
  });

  expect(registration.status()).toBe(201);
  promoteTestAdmin(email);

  await login(page, email);

  await expect(
    page.getByRole('heading', {
      name: 'Secure your administrator account.',
    })
  ).toBeVisible();

  const enrollment = await page.request.post(
    '/api/auth/admin-mfa/enroll/start',
    {
      headers: await csrfHeaders(page),
      data: { password: PASSWORD },
    }
  );

  expect(enrollment.status()).toBe(200);

  const { provisioning_uri } = await enrollment.json();

  const confirmation = await page.request.post(
    '/api/auth/admin-mfa/enroll/confirm',
    {
      headers: await csrfHeaders(page),
      data: { code: totpFromUri(provisioning_uri) },
    }
  );

  expect(confirmation.status()).toBe(200);

  const { recovery_codes } = await confirmation.json() as {
    recovery_codes: string[];
  };

  expect(recovery_codes).toHaveLength(8);

  await login(page, email);

  await expect(
    page.getByRole('heading', { name: "Verify it's you" })
  ).toBeVisible();

  // Switch from the default authenticator input.
  await page.getByRole('button', {
    name: 'Recovery code',
    exact: true,
  }).click();

  const recoveryInput = page.getByRole('textbox', {
    name: 'Recovery code',
  });

  await expect(recoveryInput).toBeVisible();

  console.log('RECOVERY MODE SWITCH: PASS');

  // An invalid code should display an error.
  await recoveryInput.fill('0'.repeat(32));

  await page.getByRole('button', {
    name: 'Verify and continue',
  }).click();

  await expect(page.getByRole('alert')).toContainText(
    'Invalid or previously used recovery code.'
  );

  console.log('RECOVERY UI ERROR HANDLING: PASS');

  // A valid recovery code should establish the session.
  await recoveryInput.fill(recovery_codes[0]);

  await page.getByRole('button', {
    name: 'Verify and continue',
  }).click();

  await expect(
  page.getByRole('heading', {
    name: 'Replace your lost authenticator',
  })
).toBeVisible();

await expect(
  page.getByRole('button', {
    name: 'Replace lost authenticator',
  })
).toBeVisible();

  const identity = await page.request.get('/api/auth/me');
  expect(identity.status()).toBe(200);

  console.log('RECOVERY UI LOGIN: PASS');
});

test('lost authenticator replacement requires a single-use recovery grant', async ({
  page,
}) => {
  test.setTimeout(180_000);

  const email = `cf-admin-mfa-e2e-${randomUUID()}@example.com`;

  const registration = await page.request.post('/api/auth/register', {
    data: {
      full_name: 'CareerForge Lost Device Tester',
      email,
      password: PASSWORD,
    },
  });

  expect(registration.status()).toBe(201);
  promoteTestAdmin(email);

  // Enroll the original authenticator.
  // Enroll the original authenticator.
    await login(page, email);

    await expect(
    page.getByRole('heading', {
        name: 'Secure your administrator account.',
    })
    ).toBeVisible();

    const enroll = await page.request.post(
    '/api/auth/admin-mfa/enroll/start',
    {
      headers: await csrfHeaders(page),
      data: { password: PASSWORD },
    }
  );

  expect(enroll.status(), await enroll.text()).toBe(200);

  const { provisioning_uri: oldUri } = await enroll.json();

  const confirm = await page.request.post(
    '/api/auth/admin-mfa/enroll/confirm',
    {
      headers: await csrfHeaders(page),
      data: { code: totpFromUri(oldUri) },
    }
  );

  expect(confirm.status()).toBe(200);

  const { recovery_codes: oldCodes } = await confirm.json();

  expect(oldCodes).toHaveLength(8);

  const recoveryStart =
    '/api/auth/admin-mfa/replace/recovery/start';

  // A regular admin MFA session must not authorize lost-device recovery.
  const enrollmentStep = Math.floor(Date.now() / 30_000);

  await expect.poll(
    () => Math.floor(Date.now() / 30_000),
    { timeout: 40_000, intervals: [500] }
  ).toBeGreaterThan(enrollmentStep);

    await login(page, email);

    await expect(
    page.getByRole('heading', { name: "Verify it's you" })
    ).toBeVisible();

    const regularLogin = await page.request.post(
    '/api/auth/admin-mfa/challenge/verify',
    {
      headers: await csrfHeaders(page),
      data: { code: totpFromUri(oldUri) },
    }
  );

  expect(regularLogin.status(),await regularLogin.text()).toBe(200);

  const withoutGrant = await page.request.post(recoveryStart, {
    headers: await csrfHeaders(page),
    data: {},
  });

  expect(withoutGrant.status()).toBe(403);

  console.log('NORMAL ADMIN SESSION CANNOT RESET MFA: PASS');

  // Simulate losing the authenticator and logging in via recovery.
  await page.context().clearCookies();
  await login(page, email);
  await expect(
    page.getByRole('heading', { name: "Verify it's you" })
    ).toBeVisible();

  const recovered = await page.request.post(
    '/api/auth/admin-mfa/challenge/recovery',
    {
      headers: await csrfHeaders(page),
      data: { recovery_code: oldCodes[0] },
    }
  );

  expect(recovered.status()).toBe(200);

  const recoveredSession = await page.request.get('/api/auth/me');
  expect(recoveredSession.status()).toBe(200);

  console.log('RECOVERY-CODE LOGIN: PASS');

  // The recovery grant must authorize replacement exactly once.
  const headers = await csrfHeaders(page);

const [first, second] = await Promise.all([
  page.request.post(recoveryStart, {
    headers,
    data: {},
  }),
  page.request.post(recoveryStart, {
    headers,
    data: {},
  }),
]);

const statuses = [first.status(), second.status()].sort(
  (a, b) => a - b
);

expect(statuses).toEqual([200, 403]);

const replacementStart = first.status() === 200 ? first : second;

console.log('CONCURRENT RECOVERY GRANT PROTECTION: PASS');

  const { provisioning_uri: newUri } =
    await replacementStart.json();

  const reusedGrant = await page.request.post(recoveryStart, {
    headers: await csrfHeaders(page),
    data: {},
  });

  expect(reusedGrant.status()).toBe(403);

  console.log('SINGLE-USE RECOVERY GRANT: PASS');

  // Activate the replacement authenticator.
  const replacementConfirm = await page.request.post(
    '/api/auth/admin-mfa/replace/confirm',
    {
      headers: await csrfHeaders(page),
      data: { code: totpFromUri(newUri) },
    }
  );

  expect(
    replacementConfirm.status(),
    await replacementConfirm.text()
  ).toBe(200);

  const { recovery_codes: newCodes } =
    await replacementConfirm.json();

  expect(newCodes).toHaveLength(8);
  expect(newCodes).not.toContain(oldCodes[1]);

  console.log('AUTHENTICATOR REPLACEMENT: PASS');
  console.log('RECOVERY CODE ROTATION: PASS');

  // Replacement must invalidate the previous session.
  const oldSession = await page.request.get('/api/auth/me');
  expect(oldSession.status()).not.toBe(200);

  console.log('PREVIOUS ADMIN SESSION REVOKED: PASS');

  // The old authenticator and old recovery codes must no longer work.
  await login(page, email);
  await expect(
    page.getByRole('heading', { name: "Verify it's you" })
    ).toBeVisible();

  const oldAuthenticator = await page.request.post(
    '/api/auth/admin-mfa/challenge/verify',
    {
      headers: await csrfHeaders(page),
      data: { code: totpFromUri(oldUri) },
    }
  );

  expect(oldAuthenticator.status()).toBe(400);

  const oldRecoveryCode = await page.request.post(
    '/api/auth/admin-mfa/challenge/recovery',
    {
      headers: await csrfHeaders(page),
      data: { recovery_code: oldCodes[1] },
    }
  );

  expect(oldRecoveryCode.status()).toBe(400);

  console.log('OLD MFA CREDENTIALS REJECTED: PASS');

  // A recovery code issued with the new authenticator must work.
  const newRecoveryCode = await page.request.post(
    '/api/auth/admin-mfa/challenge/recovery',
    {
      headers: await csrfHeaders(page),
      data: { recovery_code: newCodes[0] },
    }
  );

  expect(newRecoveryCode.status()).toBe(200);

  const finalSession = await page.request.get('/api/auth/me');
  expect(finalSession.status()).toBe(200);

  console.log('NEW RECOVERY CREDENTIALS ACCEPTED: PASS');
});


test('administrator can replace a lost authenticator through the UI', async ({
  page,
}) => {
  test.setTimeout(180_000);

  const email = `cf-admin-mfa-e2e-${randomUUID()}@example.com`;

  const registration = await page.request.post('/api/auth/register', {
    data: {
      full_name: 'CareerForge Recovery Replacement Tester',
      email,
      password: PASSWORD,
    },
  });

  expect(registration.status()).toBe(201);
  promoteTestAdmin(email);

  // 1. Enroll the original authenticator.
  await login(page, email);

  await expect(
    page.getByRole('heading', {
      name: 'Secure your administrator account.',
    })
  ).toBeVisible();

  const enrollment = await page.request.post(
    '/api/auth/admin-mfa/enroll/start',
    {
      headers: await csrfHeaders(page),
      data: { password: PASSWORD },
    }
  );

  expect(enrollment.status(), await enrollment.text()).toBe(200);

  const { provisioning_uri: oldUri } = await enrollment.json();

  const confirmation = await page.request.post(
    '/api/auth/admin-mfa/enroll/confirm',
    {
      headers: await csrfHeaders(page),
      data: { code: totpFromUri(oldUri) },
    }
  );

  expect(confirmation.status(), await confirmation.text()).toBe(200);

  const { recovery_codes: oldCodes } = await confirmation.json() as {
    recovery_codes: string[];
  };

  expect(oldCodes).toHaveLength(8);

  // 2. Sign in with a saved recovery code.
  await login(page, email);

  await expect(
    page.getByRole('heading', { name: "Verify it's you" })
  ).toBeVisible();

  await page.getByRole('button', {
    name: 'Recovery code',
    exact: true,
  }).click();

  await page.getByRole('textbox', {
    name: 'Recovery code',
  }).fill(oldCodes[0]);

  await page.getByRole('button', {
    name: 'Verify and continue',
  }).click();

  await expect(
    page.getByRole('heading', {
      name: 'Replace your lost authenticator',
    })
  ).toBeVisible();

  console.log('RECOVERY LOGIN TO REPLACEMENT: PASS');

  // 3. Open the actual replacement popup.
  await page.getByRole('button', {
    name: 'Replace lost authenticator',
  }).click();

  const dialog = page.getByRole('dialog');

  await expect(dialog).toBeVisible();

  await expect(
    dialog.getByRole('heading', {
      name: 'Replace your authenticator.',
    })
  ).toBeVisible();

  // Lost-device recovery must not request the old TOTP.
  await expect(
    dialog.getByLabel('Current authenticator code')
  ).toHaveCount(0);

  await expect(
    dialog.getByLabel('Confirm your account password')
  ).toHaveCount(0);

  console.log('LOST-DEVICE REPLACEMENT POPUP: PASS');

  // 4. Generate the replacement QR code through the UI.
  const qrResponsePromise = page.waitForResponse(
    (response) =>
      response.url().includes(
        '/api/auth/admin-mfa/replace/recovery/start'
      ) &&
      response.request().method() === 'POST'
  );

  await dialog.getByRole('button', {
    name: 'Generate replacement QR code',
  }).click();

  const qrResponse = await qrResponsePromise;

  expect(qrResponse.status(), await qrResponse.text()).toBe(200);

  const { provisioning_uri: newUri } = await qrResponse.json() as {
    provisioning_uri: string;
  };

  expect(newUri).toMatch(/^otpauth:\/\/totp\//);

  await expect(
    dialog.getByRole('img', {
      name: 'CareerForge authenticator setup QR code',
    })
  ).toBeVisible();

  console.log('REPLACEMENT QR GENERATION: PASS');

  // 5. Confirm the new authenticator through the React form.
  const newAuthenticatorCode = totpFromUri(newUri);

  await dialog.getByLabel(
    'Enter the code from your new authenticator'
  ).fill(newAuthenticatorCode);

  const confirmResponsePromise = page.waitForResponse(
    (response) =>
      response.url().includes(
        '/api/auth/admin-mfa/replace/confirm'
      ) &&
      response.request().method() === 'POST'
  );

  await dialog.getByRole('button', {
    name: 'Verify and replace',
  }).click();

  const confirmResponse = await confirmResponsePromise;

  expect(
    confirmResponse.status(),
    await confirmResponse.text()
  ).toBe(200);

  const confirmedStep = Math.floor(Date.now() / 30_000);

  await expect(
    dialog.getByRole('heading', {
      name: 'Authenticator replaced.',
    })
  ).toBeVisible();

  console.log('NEW AUTHENTICATOR ACTIVATED: PASS');

  // 6. Verify eight replacement recovery codes are displayed.
  const displayedCodes = dialog.locator(
    '.cf-mfa-recovery-list code'
  );

  await expect(displayedCodes).toHaveCount(8);

  const newCodes = await displayedCodes.allTextContents();

  expect(newCodes).toHaveLength(8);

  for (const oldCode of oldCodes) {
    expect(newCodes).not.toContain(oldCode);
  }

  console.log('NEW RECOVERY CODES DISPLAYED: PASS');
  console.log('OLD RECOVERY CODES ROTATED: PASS');

  // 7. The previous administrator session must be invalid.
  const revokedSession = await page.request.get('/api/auth/me');

  expect(revokedSession.status()).not.toBe(200);

  console.log('OLD ADMIN SESSION REVOKED: PASS');

  // 8. Finish the replacement and return to login.
  await dialog.getByRole('button', {
    name: "I've saved my recovery codes",
  }).click();

  await expect(page).toHaveURL(/\/login(?:\?.*)?$/);

  console.log('REPLACEMENT COMPLETION NAVIGATION: PASS');

  // 9. Log in again and reject the old authenticator.
  await login(page, email);

  await expect(
    page.getByRole('heading', {
      name: "Verify it's you",
    })
  ).toBeVisible();

  const oldAuthenticator = await page.request.post(
    '/api/auth/admin-mfa/challenge/verify',
    {
      headers: await csrfHeaders(page),
      data: { code: totpFromUri(oldUri) },
    }
  );

  expect(oldAuthenticator.status()).toBe(400);

  console.log('OLD AUTHENTICATOR REJECTED: PASS');

  // 10. Wait for a fresh TOTP step before using the new authenticator.
  await expect.poll(
    () => Math.floor(Date.now() / 30_000),
    { timeout: 40_000, intervals: [500] }
  ).toBeGreaterThan(confirmedStep);

  await page.getByLabel('Authenticator code').fill(
    totpFromUri(newUri)
  );

  await page.getByRole('button', {
    name: 'Verify and continue',
  }).click();

  await expect(page).toHaveURL(/\/admin(?:\?.*)?$/);

  const session = await page.request.get('/api/auth/me');

  expect(session.status()).toBe(200);

  console.log('NEW AUTHENTICATOR LOGIN: PASS');
  console.log('COMPLETE LOST-DEVICE RECOVERY: PASS');
});

test('expired recovery grant cannot authorize authenticator replacement', async ({
  page,
}) => {
  test.setTimeout(120_000);

  const email = `cf-admin-mfa-e2e-${randomUUID()}@example.com`;

  const registration = await page.request.post('/api/auth/register', {
    data: {
      full_name: 'CareerForge Expired Recovery Tester',
      email,
      password: PASSWORD,
    },
  });

  expect(registration.status()).toBe(201);
  promoteTestAdmin(email);

  // Enroll the original authenticator.
  await login(page, email);

  await expect(
    page.getByRole('heading', {
      name: 'Secure your administrator account.',
    })
  ).toBeVisible();

  const enrollment = await page.request.post(
    '/api/auth/admin-mfa/enroll/start',
    {
      headers: await csrfHeaders(page),
      data: { password: PASSWORD },
    }
  );

  expect(enrollment.status(), await enrollment.text()).toBe(200);

  const { provisioning_uri } = await enrollment.json();

  const confirmation = await page.request.post(
    '/api/auth/admin-mfa/enroll/confirm',
    {
      headers: await csrfHeaders(page),
      data: { code: totpFromUri(provisioning_uri) },
    }
  );

  expect(confirmation.status(), await confirmation.text()).toBe(200);

  const { recovery_codes } = await confirmation.json() as {
    recovery_codes: string[];
  };

  expect(recovery_codes).toHaveLength(8);

  // Obtain a legitimate recovery grant.
  await login(page, email);

  await expect(
    page.getByRole('heading', { name: "Verify it's you" })
  ).toBeVisible();

  const recovered = await page.request.post(
    '/api/auth/admin-mfa/challenge/recovery',
    {
      headers: await csrfHeaders(page),
      data: { recovery_code: recovery_codes[0] },
    }
  );

  expect(recovered.status(), await recovered.text()).toBe(200);

  console.log('RECOVERY GRANT ISSUED: PASS');

  // Simulate the five-minute grant expiring.
  expireAdminRecoveryGrant(email);

  // An expired grant must not generate replacement credentials.
  const denied = await page.request.post(
    '/api/auth/admin-mfa/replace/recovery/start',
    {
      headers: await csrfHeaders(page),
      data: {},
    }
  );

  expect(denied.status(), await denied.text()).toBe(403);

  const body = await denied.json();

  expect(body.detail).toMatch(/expired|already used/i);

  console.log('EXPIRED RECOVERY GRANT REJECTED: PASS');
});

});
