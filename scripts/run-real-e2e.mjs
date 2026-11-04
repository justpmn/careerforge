
import { spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const FRONTEND = path.resolve(HERE, '..');
const ROOT = path.resolve(FRONTEND, '../..');

const python = process.env.CAREERFORGE_PYTHON ||
  path.join(
    ROOT,
    '.venv',
    process.platform === 'win32'
      ? 'Scripts/python.exe'
      : 'bin/python'
  );

const playwright = path.join(
  FRONTEND,
  'node_modules',
  'playwright',
  'cli.js'
);

const cleanupModule = 'scripts.cleanup_e2e_test_accounts';
const args = process.argv.slice(2);

if (!process.env.CAREERFORGE_TEST_DATABASE_URL) {
  console.error(
    'CAREERFORGE_TEST_DATABASE_URL is required.'
  );
  process.exit(1);
}

if (!existsSync(python) || !existsSync(playwright)) {
  console.error(
    'Python virtual environment or local Playwright CLI not found.'
  );
  process.exit(1);
}

if (args.some((arg) =>
  arg === '--config' ||
  arg.startsWith('--config=') ||
  arg === '--list' ||
  arg === '--pass-with-no-tests' ||
  arg === '--ui'
)) {
  console.error(
    'This runner requires its fixed test configuration ' +
    'and an executable test run.'
  );
  process.exit(1);
}

// Record the baseline before creating any test users.
const baseline = spawnSync(
  python,
  ['-m', cleanupModule, '--watermark'],
  {
    cwd: ROOT,
    env: process.env,
    encoding: 'utf8',
  }
);

if (
  baseline.error ||
  baseline.status !== 0 ||
  !/^\d+$/.test(baseline.stdout.trim())
) {
  console.error(
    baseline.stderr ||
    baseline.error?.message ||
    'Could not establish the test-account baseline.'
  );
  process.exit(1);
}

const lastUserId = baseline.stdout.trim();

console.log(
  `E2E baseline recorded: user ID ${lastUserId}`
);
console.log('Starting CareerForge browser tests...\n');

// Execute the existing Playwright configuration.
const result = spawnSync(
  process.execPath,
  [
    playwright,
    'test',
    '--config=playwright.real.config.ts',
    ...args,
  ],
  {
    cwd: FRONTEND,
    env: process.env,
    stdio: 'inherit',
  }
);

if (result.error || result.status !== 0) {
  console.error(
    '\nBrowser tests did not complete successfully.'
  );
  console.error(
    'Test accounts have been preserved for debugging.'
  );

  process.exit(result.status || 1);
}

// Only successful runs reach this point.
console.log('\nAll browser tests passed.');
console.log('Cleaning accounts created by this run...\n');

const cleanup = spawnSync(
  python,
  [
    '-m',
    cleanupModule,
    '--apply',
    '--after-id',
    lastUserId,
  ],
  {
    cwd: ROOT,
    env: process.env,
    stdio: 'inherit',
  }
);

if (cleanup.error || cleanup.status !== 0) {
  console.error(
    '\nAutomatic cleanup failed. Review the test database.'
  );
  process.exit(1);
}

console.log('\nE2E test run and cleanup completed.');
