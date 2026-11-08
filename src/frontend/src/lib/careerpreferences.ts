import { csrfHeader } from './auth';

export type CareerPreference = 'preferred' | 'avoid';

export type CareerPreferences = {
  preferred: string[];
  avoid: string[];
};

const API_ROOT = '/api/preferences';

async function request<T>(
  path: string,
  method = 'GET'
): Promise<T> {
  const response = await fetch(`${API_ROOT}${path}`, {
    method,
    credentials: 'include',
    headers: csrfHeader(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => null);

    throw new Error(
      typeof error?.detail === 'string'
        ? error.detail
        : `Preference request failed (HTTP ${response.status}).`
    );
  }

  return (await response.json()) as T;
}

export const careerPreferencesApi = {
  get: (userId: number) =>
    request<CareerPreferences>(`/careers/${userId}`),

  set: (
    userId: number,
    careerKey: string,
    preference: CareerPreference
  ) => {
    const params = new URLSearchParams({
      user_id: String(userId),
      preference,
    });

    return request(
      `/careers/${encodeURIComponent(careerKey)}?${params}`,
      'PUT'
    );
  },

  remove: (userId: number, careerKey: string) => {
    const params = new URLSearchParams({
      user_id: String(userId),
    });

    return request(
      `/careers/${encodeURIComponent(careerKey)}?${params}`,
      'DELETE'
    );
  },
};