
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
