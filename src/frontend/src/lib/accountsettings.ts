
import { csrfHeader } from './auth';

export type AccountSettings = {
  full_name: string;
  email: string;
  has_password: boolean;
  created_at: string;
};

const BASE_URL = '/api/account/settings';

async function readError(response: Response): Promise<string> {
  const body: unknown = await response.json().catch(() => null);

  if (
    body &&
    typeof body === 'object' &&
    'detail' in body
  ) {
    const detail = (body as { detail?: unknown }).detail;

    if (typeof detail === 'string') {
      return detail;
    }
  }

  return `Account request failed (HTTP ${response.status}).`;
}


export async function getAccountSettings(): Promise<AccountSettings> {
  const response = await fetch(BASE_URL, {
    credentials: 'include',
    cache: 'no-store',
  });

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return (await response.json()) as AccountSettings;
}


export async function updateAccountSettings(
  fullName: string
): Promise<AccountSettings> {
  const response = await fetch(BASE_URL, {
    method: 'PATCH',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...csrfHeader(),
    },
    body: JSON.stringify({
      full_name: fullName.trim(),
    }),
  });

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return (await response.json()) as AccountSettings;
}