
import { defineConfig, devices } from '@playwright/test';
import { fileURLToPath } from 'node:url';

const ROOT = fileURLToPath(
  new URL('../../', import.meta.url)
);

const FRONTEND = fileURLToPath(
  new URL('.', import.meta.url)
);

const databaseUrl =
  process.env.CAREERFORGE_TEST_DATABASE_URL;

if (!databaseUrl) {
  throw new Error(
    'Set CAREERFORGE_TEST_DATABASE_URL before running real E2E tests.'
  );
}

const parsed = new URL(databaseUrl);

if (
  parsed.protocol !== 'postgresql+psycopg:' ||
  parsed.pathname !== '/careerforge_test' ||
  !['localhost', '127.0.0.1', '::1'].includes(
    parsed.hostname
  ) ||
  !['', '5432'].includes(parsed.port)
) {
  throw new Error(
    'Real browser tests must use local careerforge_test.'
  );
}

export default defineConfig({
  testDir: './e2e-real',
  timeout: 45_000,

  expect: {
    timeout: 15_000,
  },

  workers: 1,
  retries: 0,
  reporter: 'list',

  use: {
    baseURL: 'http://127.0.0.1:15173',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
      },
    },
  ],

  webServer: [
    {
      command:
        'python -m uvicorn src.backend.app.main:app ' +
        '--host 127.0.0.1 --port 18080',
      cwd: ROOT,
      env: {
        ...process.env,
        DATABASE_URL: databaseUrl,
      },
      url: 'http://127.0.0.1:18080/openapi.json',
      reuseExistingServer: false,
      timeout: 60_000,
    },
    {
      command:
        'npm run dev -- --host 127.0.0.1 ' +
        '--port 15173 --strictPort',
      cwd: FRONTEND,
      env: {
        ...process.env,
        BACKEND_PROXY_TARGET:
          'http://127.0.0.1:18080',
      },
      url: 'http://127.0.0.1:15173/login',
      reuseExistingServer: false,
      timeout: 60_000,
    },
  ],
});
