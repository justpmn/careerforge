
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const ROOT = fileURLToPath(new URL('../../../', import.meta.url));
const HELPER = fileURLToPath(
  new URL('../../../tests/e2e_account_support.py', import.meta.url)
);

export function activateTestAccount(email: string): void {
  execFileSync('python', [HELPER, 'activate', email], {
    cwd: ROOT,
    env: process.env,
    stdio: 'pipe',
  });
}
export function takeVerificationToken(email: string): string {
  const python = fileURLToPath(
    new URL('../../../.venv-new/Scripts/python.exe', import.meta.url)
  );

  return execFileSync(
    python,
    [HELPER, 'take-token', email],
    {
      cwd: ROOT,
      env: process.env,
      encoding: 'utf8',
    }
  ).trim();
}
export function updateVerificationToken(
  action: 'expire-token' | 'age-token',
  email: string
): void {
  const python = fileURLToPath(
    new URL('../../../.venv-new/Scripts/python.exe', import.meta.url)
  );

  execFileSync(
    python,
    [HELPER, action, email],
    {
      cwd: ROOT,
      env: process.env,
      encoding: 'utf8',
    }
  );
}
export function promoteTestAdmin(email: string): void {
  const python = fileURLToPath(
    new URL('../../../.venv-new/Scripts/python.exe', import.meta.url)
  );

  execFileSync(
    python,
    [HELPER, 'promote-admin', email],
    {
      cwd: ROOT,
      env: process.env,
      encoding: 'utf8',
    }
  );
}
export function getExpiredAdminMfaChallenge(email: string): string {
  const python = fileURLToPath(
    new URL('../../../.venv-new/Scripts/python.exe', import.meta.url)
  );

  return execFileSync(
    python,
    [HELPER, 'expired-mfa-challenge', email],
    {
      cwd: ROOT,
      env: process.env,
      encoding: 'utf8',
    }
  ).trim();
}