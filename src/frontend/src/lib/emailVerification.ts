
const API = '/api/auth';

async function post(
  path: string,
  data: object
): Promise<{ message: string }> {
  const response = await fetch(`${API}${path}`, {
    method: 'POST',
    credentials: 'omit',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  const result = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(
      typeof result?.detail === 'string'
        ? result.detail
        : 'Something went wrong. Please try again.'
    );
  }

  return result;
}

export const emailVerificationApi = {
  verify(token: string) {
    return post('/verify-email', { token });
  },

  resend(email: string) {
    return post('/resend-verification', {
      email: email.trim().toLowerCase(),
    });
  },
};
