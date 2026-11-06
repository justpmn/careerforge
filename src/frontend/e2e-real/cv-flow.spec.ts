import { activateTestAccount } from './test-accounts';
import { test, expect } from '@playwright/test';
import type { Page } from '@playwright/test';
import { randomUUID } from 'node:crypto';
import { fileURLToPath } from 'node:url';

const PASSWORD = 'CareerForge-E2E-2026!';

const DOCX_PATH = fileURLToPath(
  new URL('./fixtures/sample-resume.docx', import.meta.url)
);

const PDF_PATH = fileURLToPath(
  new URL('./fixtures/sample-resume.pdf', import.meta.url)
);

async function createAuthenticatedUser(page: Page) {
  const email =
    `cf-browser-cv-e2e-${randomUUID()}@example.com`;

  // Create a real account in careerforge_test.
  const registration = await page.request.post(
    '/api/auth/register',
    {
      data: {
        full_name: 'CareerForge CV E2E Tester',
        email,
        password: PASSWORD,
      },
    }
  );

  expect(registration.status()).toBe(201);
  activateTestAccount(email);

  // Establish authentication through the React UI.
  await page.goto('/login');

  await page.getByLabel('Email address').fill(email);

  await page.getByLabel('Password', {
    exact: true,
  }).fill(PASSWORD);

  await page.getByRole('button', {
    name: 'Log in',
  }).click();

  await expect(page).toHaveURL(/\/dashboard$/);

  return email;
}

test.describe('CareerForge real CV analysis', () => {

  test('DOCX upload, recommendations and saved analysis', async ({
    page,
  }) => {
    await createAuthenticatedUser(page);

    // 1. Open the real CV page.
    await page.goto('/cv');

    await expect(
      page.getByRole('heading', {
        name: 'Upload CV',
      })
    ).toBeVisible();

    // 2. Upload an actual DOCX document.
    await page.getByRole('button', {
      name: '+ Upload CV',
    }).click();

    await page.locator('input[type="file"]').setInputFiles(
      DOCX_PATH
    );

    const analyzeButton = page.getByRole('button', {
      name: 'Analyze CV',
    });

    await expect(analyzeButton).toBeEnabled();

    await analyzeButton.click();

    // 3. Wait for the actual Random Forest result.
    await expect(
      page.getByRole('heading', {
        name: 'Your CV analysis',
      })
    ).toBeVisible({
      timeout: 40_000,
    });

    // 4. Check the extracted skills.
    const extractedSkills = page.locator(
      '.cf-cv-skills'
    );

    await expect(extractedSkills).toContainText(
      'Python'
    );

    await expect(extractedSkills).toContainText(
      'SQL'
    );

    await expect(extractedSkills).toContainText(
      'Docker'
    );

    // 5. Verify three career recommendations.
    await expect(
      page.getByRole('heading', {
        name: 'Career recommendations',
      })
    ).toBeVisible();

    await expect(
      page.locator('.cf-cv-recommendation')
    ).toHaveCount(3);

    // 6. Confirm that PostgreSQL stored the analysis.
    const savedResponse = await page.request.get(
      '/api/recommendations/resumes/latest'
    );

    expect(savedResponse.status()).toBe(200);

    const saved = await savedResponse.json();

    expect(saved.filename).toBe(
      'sample-resume.docx'
    );

    expect(saved.extracted_skills).toContain(
      'Python'
    );

    expect(saved.recommendations).toHaveLength(3);

    // 7. Reload and verify saved analysis restoration.
    await page.reload();

    await expect(
      page.getByRole('heading', {
        name: 'Your CV analysis',
      })
    ).toBeVisible();

    await expect(
      page.getByText('sample-resume.docx', {
        exact: true,
      })
    ).toBeVisible();

    await expect(
      page.locator('.cf-cv-recommendation')
    ).toHaveCount(3);

    console.log('DOCX EXTRACTION: PASS');
    console.log('REAL RF RECOMMENDATIONS: PASS');
    console.log('POSTGRESQL PERSISTENCE: PASS');
    console.log('SAVED ANALYSIS RESTORATION: PASS');
  });

  test('PDF upload and oversized file rejection', async ({
    page,
  }) => {
    await createAuthenticatedUser(page);

    await page.goto('/cv');

    // 1. Upload a valid PDF.
    await page.getByRole('button', {
      name: '+ Upload CV',
    }).click();

    await page.locator('input[type="file"]').setInputFiles(
      PDF_PATH
    );

    await page.getByRole('button', {
      name: 'Analyze CV',
    }).click();

    await expect(
      page.getByRole('heading', {
        name: 'Your CV analysis',
      })
    ).toBeVisible({
      timeout: 40_000,
    });

    await expect(
      page.getByText('sample-resume.pdf', {
        exact: true,
      })
    ).toBeVisible();

    await expect(
      page.locator('.cf-cv-recommendation')
    ).toHaveCount(3);

    // 2. Attempt to upload a file larger than 5 MB.
    const oversizedBuffer = Buffer.alloc(
      5 * 1024 * 1024 + 1,
      0x20
    );

// Reopen the upload modal for the oversized-file test.
    await page.getByRole('button', {
      name: '+ Upload CV',
    }).click();

    await page.locator('input[type="file"]').setInputFiles({
      name: 'oversized.pdf',
      mimeType: 'application/pdf',
      buffer: oversizedBuffer,
    });

    // The upload modal must reject files larger than 5 MB.
    const uploadDialog = page.getByRole('dialog');

    await expect(
      uploadDialog.getByRole('alert')
    ).toHaveText('Your CV must be between 1 byte and 5 MB.');

// An invalid file must not be submitted for analysis.
    await expect(
      uploadDialog.getByRole('button', {
        name: 'Analyze CV',
      })
    ).toBeDisabled();

    // 3. The UI must communicate the upload failure.
    await expect(
      page.getByRole('alert')
    ).toBeVisible({
      timeout: 15_000,
    });

    // 4. Rejected uploads must not replace the
    // previously successful saved analysis.
    const savedResponse = await page.request.get(
      '/api/recommendations/resumes/latest'
    );

    expect(savedResponse.status()).toBe(200);

    const saved = await savedResponse.json();

    expect(saved.filename).toBe(
      'sample-resume.pdf'
    );

    console.log('PDF UPLOAD: PASS');
    console.log('OVERSIZED FILE REJECTION: PASS');
    console.log('SAVED ANALYSIS PRESERVED: PASS');
  });

});
