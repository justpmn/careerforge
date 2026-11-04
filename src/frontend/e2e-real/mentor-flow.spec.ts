
import { test, expect } from '@playwright/test';
import type { Page } from '@playwright/test';
import { randomUUID } from 'node:crypto';

const PASSWORD = 'CareerForge-E2E-2026!';
const LIVE_LLM = process.env.CAREERFORGE_RUN_LIVE_LLM === '1';

async function createAuthenticatedUser(page: Page) {
  const email = `cf-mentor-e2e-${randomUUID()}@example.com`;

  const registration = await page.request.post(
    '/api/auth/register',
    {
      data: {
        full_name: 'CareerForge Mentor Tester',
        email,
        password: PASSWORD,
      },
    }
  );

  expect(registration.status()).toBe(201);

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

test.describe('CareerForge AI Mentor E2E', () => {

  test('mentor interface, career selection and composer', async ({
    page,
  }) => {
    await createAuthenticatedUser(page);

    await page.goto('/mentor');

    await expect(
      page.getByRole('heading', {
        name: 'Your career mentor.',
      })
    ).toBeVisible();

    await expect(
      page.getByRole('heading', {
        name: 'What can I help you with?',
      })
    ).toBeVisible();

    const careerSelect = page.getByLabel('Career context');

    await expect(careerSelect).toBeEnabled();

    await careerSelect.selectOption('data_engineer');

    await expect(careerSelect).toHaveValue('data_engineer');

    await expect(
      page.locator('.cf-mentor-chat-header').getByRole(
        'heading',
        { name: 'Data Engineer' }
      )
    ).toBeVisible();

    const composer = page.getByLabel('Your message');

    const sendButton = page.getByRole('button', {
      name: 'Send',
      exact: true,
    });

    // Empty and whitespace-only messages must not send.
    await expect(sendButton).toBeDisabled();

    await composer.fill('   ');

    await expect(sendButton).toBeDisabled();

    // A valid message enables sending.
    await composer.fill(
      'What should I learn next for data engineering?'
    );

    await expect(sendButton).toBeEnabled();

    // Shift+Enter inserts a newline without sending.
    await composer.press('Shift+Enter');

    await expect(composer).toHaveValue(
      /What should I learn next for data engineering\?\s/
    );

    await expect(
      page.locator('.cf-mentor-assistant')
    ).toHaveCount(0);

    // Starting a new conversation clears the draft.
    await page.getByRole('button', {
      name: /New conversation/,
    }).click();

    await expect(composer).toHaveValue('');

    await expect(
      page.getByRole('heading', {
        name: 'What can I help you with?',
      })
    ).toBeVisible();

    console.log('MENTOR INTERFACE: PASS');
    console.log('CAREER CONTEXT: PASS');
    console.log('COMPOSER VALIDATION: PASS');
    console.log('NEW CONVERSATION: PASS');
  });

  test('live Qwen reply and conversation persistence', async ({
    page,
  }) => {
    test.skip(
      !LIVE_LLM,
      'Live inference requires CAREERFORGE_RUN_LIVE_LLM=1.'
    );

    test.setTimeout(360_000);

    const email = await createAuthenticatedUser(page);

    await page.goto('/mentor');

    await expect(
      page.getByRole('heading', {
        name: 'Your career mentor.',
      })
    ).toBeVisible();

    await page.getByLabel(
      'Career context'
    ).selectOption('data_engineer');

    const question =
      'Suggest one practical beginner data engineering ' +
      'project using Python and SQL. Keep it brief.';

    await page.getByLabel('Your message').fill(
      question
    );

    await page.getByRole('button', {
      name: 'Send',
      exact: true,
    }).click();

    // Verify the user's message appears.
    await expect(
      page.locator('.cf-mentor-user').last()
    ).toContainText(question);

    // Wait for a real response from the local LLM.
    const mentorAnswer = page.locator(
      '.cf-mentor-assistant .cf-mentor-markdown'
    ).last();

    await expect(mentorAnswer).toBeVisible({
      timeout: 300_000,
    });

    const responseText = await mentorAnswer.innerText();

    expect(responseText.trim().length).toBeGreaterThan(20);

    console.log('LIVE QWEN RESPONSE: PASS');

    // Verify the conversation appears in saved history.
    const savedConversations = page.getByRole(
      'navigation',
      { name: 'Saved conversations' }
    );

    const firstConversation =
      savedConversations.locator('button').first();

    await expect(firstConversation).toBeVisible({
      timeout: 20_000,
    });

    await firstConversation.click();

    await expect(page).toHaveURL(
      /\/mentor\?conversation=\d+/
    );

    await expect(
      page.locator('.cf-mentor-user').last()
    ).toContainText(question);

    await expect(
      page.locator(
        '.cf-mentor-assistant .cf-mentor-markdown'
      ).last()
    ).toContainText(responseText.slice(0, 30));

    console.log('CONVERSATION HISTORY: PASS');

    // Verify persistence across a full browser reload.
    await page.reload();

    await expect(page).toHaveURL(
      /\/mentor\?conversation=\d+/
    );

    await expect(
      page.locator('.cf-mentor-user').last()
    ).toContainText(question, {
      timeout: 30_000,
    });

    await expect(
      page.locator(
        '.cf-mentor-assistant .cf-mentor-markdown'
      ).last()
    ).toContainText(responseText.slice(0, 30));

    console.log('CONVERSATION PERSISTENCE: PASS');
    console.log(`Test account: ${email}`);
  });

});
