
import { test, expect } from '@playwright/test';
import type { Page } from '@playwright/test';
import { randomUUID } from 'node:crypto';

const PASSWORD = 'CareerForge-E2E-2026!';

async function createAuthenticatedUser(page: Page) {
  const email =
    `cf-roadmap-e2e-${randomUUID()}@example.com`;

  // Register in the isolated careerforge_test database.
  const response = await page.request.post(
    '/api/auth/register',
    {
      data: {
        full_name: 'CareerForge Roadmap Tester',
        email,
        password: PASSWORD,
      },
    }
  );

  expect(response.status()).toBe(201);

  // Establish a real authenticated browser session.
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

test.describe('CareerForge competency and roadmap E2E', () => {

  test('new users must select a career before viewing the roadmap', async ({
    page,
  }) => {
    await createAuthenticatedUser(page);

    await page.goto('/roadmap');

    await expect(
      page.getByText(
        'Select a target career before viewing your roadmap.'
      )
    ).toBeVisible({
      timeout: 20_000,
    });

    console.log('MISSING CAREER HANDLING: PASS');
  });

  test('career selection, skill tree and learning progress persist', async ({
    page,
  }) => {
    test.setTimeout(90_000);

    const email = await createAuthenticatedUser(page);

    // 1. Open Skills Assessment.
    await page.goto('/skills-assessment');

    await expect(
      page.getByRole('heading', {
        name: 'Choose your target career',
      })
    ).toBeVisible();

    // 2. Find the actual Data Engineer career.
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

    // 3. Persist the target career.
    await page.getByRole('button', {
      name: 'Save target career',
    }).click();

    await expect(
      page.getByText(
        'Your target career has been saved.'
      )
    ).toBeVisible({
      timeout: 20_000,
    });

    // 4. Verify that competency analysis loads.
    await expect(
      page.getByRole('heading', {
        name: 'Your competency analysis',
      })
    ).toBeVisible();

    await page.getByRole('button', {
      name: 'All',
      exact: true,
    }).click();

    await expect(
      page.locator('.cf-assessment-gap-row').first()
    ).toBeVisible({
      timeout: 30_000,
    });

    console.log('CAREER SELECTION: PASS');
    console.log('COMPETENCY ANALYSIS: PASS');

    // 5. Navigate to the actual RPG-style skill tree.
    await page.goto('/roadmap');

    await expect(
      page.getByRole('heading', {
        name: 'Data Engineer',
        exact: true,
      })
    ).toBeVisible({
      timeout: 30_000,
    });

    // 6. Verify that React Flow rendered skill nodes.
    const firstNode = page.locator(
      '.react-flow__node'
    ).first();

    await expect(firstNode).toBeVisible({
      timeout: 20_000,
    });

    const nodeId = await firstNode.getAttribute(
      'data-id'
    );

    expect(nodeId).toBeTruthy();

    // 7. Select the node and open its inspector.
    await firstNode.click();

    const inspector = page.getByRole(
      'complementary',
      { name: 'Selected skill details' }
    );

    await expect(inspector).toBeVisible();

    const selectedSkillTitle = await inspector
      .locator('h2')
      .innerText();

    await expect(
      inspector.getByRole('heading', {
        name: 'Your learning progress',
      })
    ).toBeVisible();

    // 8. Save the skill's learned status.
    const learnedButton = inspector.locator(
      '.cf-learning-toggle'
    );

    await expect(learnedButton).toHaveAttribute(
      'aria-pressed',
      'false'
    );

    await learnedButton.click();

    await expect(learnedButton).toHaveAttribute(
      'aria-pressed',
      'true',
      { timeout: 20_000 }
    );

    console.log('SKILL TREE INTERACTION: PASS');
    console.log('LEARNING PROGRESS SAVE: PASS');

    // 9. Reload to verify backend persistence.
    await page.reload();

    await expect(
      page.getByRole('heading', {
        name: 'Data Engineer',
        exact: true,
      })
    ).toBeVisible({
      timeout: 30_000,
    });

    // The ID was obtained from the actual graph,
    // rather than hardcoding a competency name.
    const sameNode = page.locator(
      `.react-flow__node[data-id="${nodeId}"]`
    );

    await expect(sameNode).toBeVisible({
      timeout: 20_000,
    });

    await sameNode.click();

    const restoredInspector = page.getByRole(
      'complementary',
      { name: 'Selected skill details' }
    );

    await expect(restoredInspector).toBeVisible();

    await expect(
      restoredInspector.locator('h2')
    ).toHaveText(selectedSkillTitle);

    await expect(
      restoredInspector.locator(
        '.cf-learning-toggle'
      )
    ).toHaveAttribute(
      'aria-pressed',
      'true',
      { timeout: 20_000 }
    );

    console.log('POSTGRESQL PROGRESS RESTORATION: PASS');
    console.log(`Test account: ${email}`);
    console.log(`Test competency: ${selectedSkillTitle}`);
  });

});
