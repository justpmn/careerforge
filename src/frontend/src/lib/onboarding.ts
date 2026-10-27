
export type Career = {
  career_key: string;
  name: string;
  description: string | null;
};

type CareerSelection = {
  career_key: string | null;
};

const API_ROOT = '/api/onboarding';

async function apiRequest<T>(
  path: string,
  init?: RequestInit
): Promise<T> {
  const headers = new Headers(init?.headers);

  if (init?.body) {
    headers.set('Content-Type', 'application/json');
  }

  const csrfCookie = document.cookie
    .split('; ')
    .find((part) => part.startsWith('csrf_token='));

  if (csrfCookie) {
    headers.set(
      'X-CSRF-Token',
      decodeURIComponent(csrfCookie.split('=').slice(1).join('='))
    );
  }

  const response = await fetch(`${API_ROOT}${path}`, {
    ...init,
    credentials: 'include',
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => null);

    throw new Error(
      typeof error?.detail === 'string'
        ? error.detail
        : `Request failed (HTTP ${response.status}).`
    );
  }

  return (await response.json()) as T;
}

export const onboardingApi = {
  careers: () =>
    apiRequest<Career[]>('/careers'),

  selectedCareer: () =>
    apiRequest<CareerSelection>('/career'),

  saveCareer: (careerKey: string) =>
    apiRequest<CareerSelection>('/career', {
      method: 'PUT',
      body: JSON.stringify({
        career_key: careerKey,
      }),
    }),
};
