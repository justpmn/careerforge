/** API contract to implement or adapt in the existing FastAPI backend.
 * Requests are same-origin (/api) and include cookies, so auth tokens never
 * need to be stored in localStorage.
 */
export type User = {
  id: string;
  name: string;
  email: string;
  onboarding_completed: boolean;
};

export type Credentials = { email: string; password: string };
export type Registration = Credentials & { name: string };

const API_ROOT = '/api/auth';

function csrfHeader(): Record<string, string> {
  const item = document.cookie.split('; ').find((part) => part.startsWith('csrf_token='));
  if (!item) return {};
  return { 'X-CSRF-Token': decodeURIComponent(item.slice('csrf_token='.length)) };
}

async function request(path: string, init?: RequestInit): Promise<Response> {
  try {
    return await fetch(`${API_ROOT}${path}`, {
      credentials: 'include',
      ...init,
      headers: {
        ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
        ...csrfHeader(),
        ...init?.headers,
      },
    });
  } catch {
    throw new Error('Cannot reach the authentication API. Start FastAPI and check the Vite proxy settings.');
  }
}

async function messageFrom(response: Response): Promise<string> {
  try {
    const body: unknown = await response.json();
    if (typeof body === 'object' && body !== null) {
      const error = body as { detail?: unknown; message?: unknown };
      if (typeof error.detail === 'string') return error.detail;
      if (typeof error.message === 'string') return error.message;
    }
  } catch { /* Not every error response is JSON */ }
  if (response.status === 404) return 'This authentication endpoint is not available yet. It needs to be connected to FastAPI.';
  return `Authentication failed (HTTP ${response.status}). Please try again.`;
}

async function post(path: string, body?: object): Promise<void> {
  const response = await request(path, {
    method: 'POST',
    ...(body ? { body: JSON.stringify(body) } : {}),
  });
  if (!response.ok) throw new Error(await messageFrom(response));
}

export const authApi = {
  login: (data: Credentials) => post('/login', data),
  register: (data: Registration) =>
  post('/register', {
    full_name: data.name,
    email: data.email.trim().toLowerCase(),
    password: data.password,
  }),
  logout: () => post('/logout'),
  completeOnboarding: () => post('/onboarding/complete'),
  async me(): Promise<User | null> {
    const response = await request('/me');
    if (response.status === 401) return null;
    if (!response.ok) throw new Error(await messageFrom(response));
    const user: User = await response.json();
    if (!user || typeof user.id !== 'string' || typeof user.onboarding_completed !== 'boolean') {
      throw new Error('Invalid user response from the API. Check the /api/auth/me contract.');
    }
    return user;
  },
};

export function postAuthRoute(user: User): string {
  return user.onboarding_completed ? '/dashboard' : '/onboarding';
}

export function oauthStartPath(provider: 'google' | 'github'): string | null {
  const path = provider === 'google'
    ? import.meta.env.VITE_GOOGLE_OAUTH_START_PATH
    : import.meta.env.VITE_GITHUB_OAUTH_START_PATH;
  return typeof path === 'string' && /^\/api\/[a-zA-Z0-9/_-]+$/.test(path) ? path : null;
}
