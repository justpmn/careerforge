import { activateTestAccount } from './test-accounts';
import { test, expect } from '@playwright/test';
import { randomUUID } from 'node:crypto';

const PASSWORD = 'CareerForge-E2E-2026!';

test('competency assessment and evidence persist after reload', async ({
  page,
}) => {
  test.setTimeout(120_000);

  const email =
    `cf-competency-e2e-${randomUUID()}@example.com`;

  const initialNotes =
    'I have used this competency in academic projects.';

  const updatedNotes =
    'I have implemented this competency independently in several projects.';

  const evidenceDescription =
    `CareerForge E2E project ${randomUUID()}: ` +
    'implemented a Python and SQL data pipeline, ' +
    'with PostgreSQL storage and automated validation.';

  // =====================================================
  // 1. REGISTER A TEST USER
  // =====================================================

  const registration = await page.request.post(
    '/api/auth/register',
    {
      data: {
        full_name: 'CareerForge Competency Tester',
        email,
        password: PASSWORD,
      },
    }
  );

  expect(registration.status()).toBe(201);
  activateTestAccount(email);

  // =====================================================
  // 2. LOGIN THROUGH THE REAL FRONTEND
  // =====================================================

  await page.goto('/login');

  await page.getByLabel('Email address').fill(email);

  await page.getByLabel('Password', {
    exact: true,
  }).fill(PASSWORD);

  await page.getByRole('button', {
    name: 'Log in',
  }).click();

  await expect(page).toHaveURL(/\/dashboard$/);

  console.log('AUTHENTICATION: PASS');

  // =====================================================
  // 3. SELECT A TARGET CAREER
  // =====================================================

  await page.goto('/skills-assessment');

  await expect(
    page.getByRole('heading', {
      name: 'Choose your target career',
    })
  ).toBeVisible();

  await page.getByLabel('Search careers').fill(
    'Data Engineer'
  );

  const careerOption = page
    .locator('.cf-career-option')
    .filter({
      has: page.getByText('Data Engineer', {
        exact: true,
      }),
    });

  await expect(careerOption).toBeVisible();

  await careerOption.click();

  await expect(careerOption).toHaveAttribute(
    'aria-pressed',
    'true'
  );

  await page.getByRole('button', {
    name: 'Save target career',
  }).click();

    // Verify the saved career appears in the collapsed header.
  const savedCareerHeading = page
    .locator('.cf-career-collapse-header')
    .getByRole('heading', {
      name: 'Data Engineer',
      exact: true,
    });

  await expect(savedCareerHeading).toBeVisible({
    timeout: 20_000,
  });

  // Reload to verify the selection persisted in PostgreSQL.
  await page.reload();

  await expect(savedCareerHeading).toBeVisible({
    timeout: 20_000,
  });

  console.log('CAREER SELECTION: PASS');

  // =====================================================
  // 4. OPEN THE ROADMAP
  // =====================================================

  await page.goto('/roadmap');

  await expect(
    page.getByRole('heading', {
      name: 'Data Engineer',
      exact: true,
    })
  ).toBeVisible({
    timeout: 30_000,
  });

  const nodes = page.locator('.react-flow__node');

  await expect(nodes.first()).toBeVisible({
    timeout: 20_000,
  });

  const inspector = page.getByRole(
    'complementary',
    {
      name: 'Selected skill details',
    }
  );

  let selectedNodeId: string | null = null;

  // Find a skill linked to a real competency.
  for (let i = 0; i < await nodes.count(); i++) {
    const candidate = nodes.nth(i);

    await candidate.click();

    await expect(inspector).toBeVisible();

    const assessmentHeading = inspector.locator(
      '.cf-assessment-panel h3'
    ).filter({
      hasText: 'Assess your proficiency',
    });

    if (await assessmentHeading.count() > 0) {
      selectedNodeId = await candidate.getAttribute(
        'data-id'
      );

      break;
    }

    await inspector.getByRole('button', {
      name: 'Close skill details',
    }).click();
  }

  if (!selectedNodeId) {
    throw new Error(
      'No roadmap node with a linked competency was found.'
    );
  }

  console.log(
    'Selected roadmap node:',
    selectedNodeId
  );

  // =====================================================
  // 5. IDENTIFY THE ACTUAL ASSESSMENT FORM
  // =====================================================

  const assessmentForm = inspector.locator(
    'form.cf-assessment-form'
  );

  // There should be exactly one assessment form
  // for the selected competency.
  await expect(assessmentForm).toHaveCount(1, {
    timeout: 20_000,
  });

  const assessment = assessmentForm.locator('..');

  const evidence = inspector.locator(
    '.cf-evidence-panel'
  );

  await expect(evidence).toHaveCount(1);

  await expect(
    assessment.locator('h3', {
      hasText: 'Assess your proficiency',
    })
  ).toBeVisible();

  console.log(
    'Assessment containers:',
    await inspector.locator(
      '.cf-assessment-panel'
    ).count()
  );

  console.log(
    'Assessment forms:',
    await inspector.locator(
      'form.cf-assessment-form'
    ).count()
  );

  console.log(
    'Evidence panels:',
    await inspector.locator(
      '.cf-evidence-panel'
    ).count()
  );

  // =====================================================
  // 6. SAVE INTERMEDIATE PROFICIENCY
  // =====================================================

  const intermediateInput = assessmentForm.locator(
    'input[type="radio"][value="intermediate"]'
  );

  const intermediateLabel = assessmentForm.locator(
    'label.cf-assessment-option:has(input[value="intermediate"])'
  );

  await expect(intermediateInput).toHaveCount(1);

  // Click the visible label, not the potentially
  // visually hidden radio input.
  await intermediateLabel.click();

  await expect(intermediateInput).toBeChecked();

  await assessmentForm.getByLabel(
    'Additional notes (optional)'
  ).fill(initialNotes);

  await assessmentForm.getByRole('button', {
    name: 'Save assessment',
  }).click();

  await expect(
    assessment.locator('.cf-assessment-success')
  ).toContainText(
    'Your assessment has been saved.',
    {
      timeout: 20_000,
    }
  );

  await expect(
    assessment.locator('.cf-assessment-saved')
  ).toContainText('intermediate');

  console.log('ASSESSMENT CREATION: PASS');

  // =====================================================
  // 7. UPDATE PROFICIENCY TO ADVANCED
  // =====================================================

  const advancedInput = assessmentForm.locator(
    'input[type="radio"][value="advanced"]'
  );

  const advancedLabel = assessmentForm.locator(
    'label.cf-assessment-option:has(input[value="advanced"])'
  );

  await expect(advancedInput).toHaveCount(1);

  await advancedLabel.click();

  await expect(advancedInput).toBeChecked();

  await assessmentForm.getByLabel(
    'Additional notes (optional)'
  ).fill(updatedNotes);

  await assessmentForm.getByRole('button', {
    name: 'Update assessment',
  }).click();

  await expect(
    assessment.locator('.cf-assessment-success')
  ).toContainText(
    'Your assessment has been updated.',
    {
      timeout: 20_000,
    }
  );

  await expect(
    assessment.locator('.cf-assessment-saved')
  ).toContainText('advanced');

  console.log('ASSESSMENT UPDATE: PASS');

  // =====================================================
  // 8. SUBMIT PROJECT EVIDENCE
  // =====================================================

  await expect(
    evidence.getByRole('heading', {
      name: 'Competency evidence',
    })
  ).toBeVisible();

  await expect(
    evidence.locator('form.cf-evidence-form')
  ).toBeVisible({
    timeout: 20_000,
  });

  await evidence.getByLabel(
    'Evidence type'
  ).selectOption('project');

  await evidence.getByLabel('Description', {
    exact: true,
  }).fill(evidenceDescription);

  await evidence.getByRole('button', {
    name: 'Submit evidence',
  }).click();

  await expect(
    evidence.locator('.cf-evidence-success')
  ).toContainText(
    'Evidence saved as self-reported.',
    {
      timeout: 20_000,
    }
  );

  const submittedEvidence = evidence
    .locator('.cf-evidence-entry')
    .filter({
      hasText: evidenceDescription,
    });

  await expect(submittedEvidence).toBeVisible();

  await expect(submittedEvidence).toContainText(
    'Self-reported'
  );

  console.log('PROJECT EVIDENCE SUBMISSION: PASS');

  // =====================================================
  // 9. RELOAD AND RESELECT THE SAME SKILL
  // =====================================================

  await page.reload();

  await expect(
    page.getByRole('heading', {
      name: 'Data Engineer',
      exact: true,
    })
  ).toBeVisible({
    timeout: 30_000,
  });

  const restoredNode = page.locator(
    `.react-flow__node[data-id="${selectedNodeId}"]`
  );

  await expect(restoredNode).toBeVisible({
    timeout: 20_000,
  });

  await restoredNode.click();

  const restoredInspector = page.getByRole(
    'complementary',
    {
      name: 'Selected skill details',
    }
  );

  await expect(restoredInspector).toBeVisible();

  const restoredAssessmentForm =
    restoredInspector.locator(
      'form.cf-assessment-form'
    );

  await expect(restoredAssessmentForm).toHaveCount(
    1,
    {
      timeout: 20_000,
    }
  );

  const restoredAssessment =
    restoredAssessmentForm.locator('..');

  const restoredEvidence =
    restoredInspector.locator(
      '.cf-evidence-panel'
    );

  await expect(restoredEvidence).toHaveCount(1);

  // =====================================================
  // 10. VERIFY SAVED PROFICIENCY
  // =====================================================

  await expect(
    restoredAssessmentForm.locator(
      'input[type="radio"][value="advanced"]'
    )
  ).toBeChecked();

  await expect(
    restoredAssessmentForm.getByLabel(
      'Additional notes (optional)'
    )
  ).toHaveValue(updatedNotes);

  await expect(
    restoredAssessment.locator(
      '.cf-assessment-saved'
    )
  ).toContainText('advanced');

  console.log('ASSESSMENT PERSISTENCE: PASS');

  // =====================================================
  // 11. VERIFY SAVED EVIDENCE
  // =====================================================

  const restoredEntry = restoredEvidence
    .locator('.cf-evidence-entry')
    .filter({
      hasText: evidenceDescription,
    });

  await expect(restoredEntry).toBeVisible({
    timeout: 20_000,
  });

  await expect(restoredEntry).toContainText(
    'Self-reported'
  );

  console.log('EVIDENCE PERSISTENCE: PASS');

  // =====================================================
  // 12. VERIFY SKILLS ASSESSMENT SUMMARY
  // =====================================================

  await page.goto('/skills-assessment');

  await expect(
    page.getByRole('heading', {
      name: 'Your competency analysis',
    })
  ).toBeVisible();

  await expect(
    page.getByRole('button', {
      name: 'Self-assessed',
      exact: true,
    })
  ).toBeVisible({
    timeout: 30_000,
  });

  await page.getByRole('button', {
    name: 'Self-assessed',
    exact: true,
  }).click();

  await expect(
    page.locator('.cf-assessment-gap-row').first()
  ).toBeVisible({
    timeout: 30_000,
  });

  console.log('ASSESSMENT SUMMARY SYNC: PASS');
  console.log('COMPETENCY E2E: PASS');
  console.log(`Test account: ${email}`);
});
