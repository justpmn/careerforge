
import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { csrfHeader } from '../lib/auth';

type LinkStatus = {
  linked: boolean;
};

const messages: Record<string, string> = {
  linked: 'Google was connected successfully.',
  session_expired: 'Your linking session expired. Please try again.',
  account_unavailable: 'This account is unavailable.',
  email_unverified: 'Verify your CareerForge email first.',
  email_mismatch: 'Choose the Google account that uses your CareerForge email.',
  already_linked: 'This Google account is already linked.',
};

export default function GoogleAccountLink() {
  const [linked, setLinked] = useState<boolean | null>(null);
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const result = new URLSearchParams(window.location.search)
    .get('google');

  useEffect(() => {
    let active = true;

    fetch('/api/auth/oauth/google/link/status', {
      credentials: 'include',
      cache: 'no-store',
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error('Could not load connected accounts.');
        }

        return response.json() as Promise<LinkStatus>;
      })
      .then((data) => {
        if (active) setLinked(data.linked);
      })
      .catch((cause: unknown) => {
        if (active) {
          setError(
            cause instanceof Error
              ? cause.message
              : 'Could not check Google connection.'
          );
        }
      });

    return () => {
      active = false;
    };
  }, []);

  async function connectGoogle(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy || !password) return;

    setBusy(true);
    setError('');

    try {
      const response = await fetch(
        '/api/auth/oauth/google/link/prepare',
        {
          method: 'POST',
          credentials: 'include',
          cache: 'no-store',
          headers: {
            'Content-Type': 'application/json',
            ...csrfHeader(),
          },
          body: JSON.stringify({ password }),
        }
      );

      const body = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(
          typeof body?.detail === 'string'
            ? body.detail
            : 'Could not start Google account linking.'
        );
      }

      setPassword('');

      window.location.assign(
        '/api/auth/oauth/google/link/start'
      );
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : 'Could not connect Google.'
      );
      setBusy(false);
    }
  }

  return (
    <section className="cf-google-link">
      <h3>Google account</h3>

      {linked === null ? (
        <p>Checking connection...</p>
      ) : linked ? (
        <p role="status">
          Google is connected to your CareerForge account.
        </p>
      ) : (
        <>
          <p>
            Connect your existing Google account to sign in
            without creating a separate CareerForge profile.
          </p>

          <form onSubmit={connectGoogle}>
            <label htmlFor="cf-google-link-password">
              Confirm your CareerForge password
            </label>

            <input
              id="cf-google-link-password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) =>
                setPassword(event.target.value)
              }
              disabled={busy}
              required
            />

            <button
              type="submit"
              disabled={busy || !password}
            >
              {busy ? 'Connecting...' : 'Connect Google'}
            </button>
          </form>
        </>
      )}

      {result && messages[result] && (
        <p role="status">{messages[result]}</p>
      )}

      {error && (
        <p role="alert">{error}</p>
      )}
    </section>
  );
}
