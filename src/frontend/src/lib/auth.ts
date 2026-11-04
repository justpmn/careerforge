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

export function csrfHeader(): Record<string, string> {
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

export class AuthApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly code?: string,
  ) {
    super(message);
    this.name = 'AuthApiError';
  }
}

async function errorFrom(response: Response): Promise<AuthApiError> {
  let message = response.status === 404
    ? 'This authentication endpoint is not available yet.'
    : `Authentication failed (HTTP ${response.status}). Please try again.`;

  let code: string | undefined;

  try {
    const body: unknown = await response.json();

    if (body && typeof body === 'object') {
      const data = body as { detail?: unknown; message?: unknown };

      if (typeof data.detail === 'string') {
        message = data.detail;
      } else if (data.detail && typeof data.detail === 'object') {
        const detail = data.detail as {
          code?: unknown;
          message?: unknown;
        };

        if (typeof detail.message === 'string') {
          message = detail.message;
        }

        if (typeof detail.code === 'string') {
          code = detail.code;
        }
      } else if (typeof data.message === 'string') {
        message = data.message;
      }
    }
  } catch {
    // Preserve the fallback message for non-JSON responses.
  }

  return new AuthApiError(message, response.status, code);
}
async function post(path: string, body?: object): Promise<void> {
  const response = await request(path, {
    method: 'POST',
    ...(body ? { body: JSON.stringify(body) } : {}),
  });
 if (!response.ok) throw await errorFrom(response);
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
    const controller = new AbortController();

    // Give the authentication request 10 seconds.
    const timeout = setTimeout(() => {
      controller.abort();
    }, 10000);

    try {
      const response = await request('/me', {
        signal: controller.signal,
      });

      if (response.status === 401) {
        return null;
      }

      if (!response.ok) {
        throw await errorFrom(response);
      }

      const user: User = await response.json();

      if (
        !user ||
        typeof user.id !== 'string' ||
        typeof user.onboarding_completed !== 'boolean'
      ) {
        throw new Error(
          'Invalid user response from the API.'
        );
      }

      return user;
    } finally {
      clearTimeout(timeout);
    }
  },
};

export function postAuthRoute(_user: User): string {
  return '/dashboard';
}
export function oauthStartPath(provider: 'google' | 'github'): string {
  if (provider === 'google') {
    return '/api/auth/oauth/google/start';
  }

  return '/api/auth/oauth/github/start';
}
