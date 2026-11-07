
import { useState, useEffect } from 'react';
import type { FormEvent } from 'react';
import { useAuth } from '../context/AuthContext';
import { csrfHeader } from '../lib/auth';

export default function AccountDangerZone() {
  const { user } = useAuth();
  const [expanded, setExpanded] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [hasPassword, setHasPassword] = useState<boolean | null>(null);
  const [methodError, setMethodError] = useState('');
  const [emailRequested, setEmailRequested] = useState(false);

  async function handleDelete(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!user || busy) return;

    setBusy(true);
    setError('');

    try {
      const response = await fetch('/api/account/me', {
        method: 'DELETE',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          ...csrfHeader(),
        },
        body: JSON.stringify({
          email,
          password,
          confirmation,
        }),
      });

      if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(
          typeof body?.detail === 'string'
            ? body.detail
            : 'Could not delete your account.'
        );
      }

      window.location.replace('/signup');
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Account deletion failed.'
      );
    } finally {
      setBusy(false);
    }
  }
  
    useEffect(() => {
    if (!user) return;

    let active = true;
    setHasPassword(null);
    setMethodError('');
    setEmailRequested(false);

    fetch('/api/account/me/deletion-method', {
        credentials: 'include',
        cache: 'no-store',
    })
        .then(async (response) => {
        if (!response.ok) {
            throw new Error('Could not load account deletion options.');
        }

        return response.json() as Promise<{ has_password: boolean }>;
        })
        .then((result) => {
        if (active) setHasPassword(result.has_password);
        })
        .catch((err: unknown) => {
        if (active) {
            setMethodError(
            err instanceof Error ? err.message : 'Unable to load account.'
            );
        }
        });

    return () => {
        active = false;
    };
    }, [user?.id]);

    async function requestEmailDeletion() {
    if (busy) return;

    setBusy(true);
    setError('');

    try {
        const response = await fetch('/api/account/me/deletion-request', {
        method: 'POST',
        credentials: 'include',
        headers: csrfHeader(),
        });

        if (!response.ok) {
        const result = await response.json().catch(() => null);
        throw new Error(
            typeof result?.detail === 'string'
            ? result.detail
            : 'Could not send confirmation email.'
        );
        }

        setEmailRequested(true);
    } catch (err) {
        setError(
        err instanceof Error ? err.message : 'Could not request deletion.'
        );
    } finally {
        setBusy(false);
    }
    }

    if (hasPassword === null || hasPassword === false) {
    return (
        <section className="cf-account-danger">
        <span className="cf-eyebrow">ACCOUNT MANAGEMENT</span>
        <h2>Danger Zone</h2>

        {methodError ? (
            <p role="alert" className="cf-danger-error">
            {methodError}
            </p>
        ) : hasPassword === null ? (
            <p>Loading account security options...</p>
        ) : (
            <>
            <p>
                Permanently delete your CareerForge account and
                its associated personal data.
            </p>

            <p>
                This account has no local password. We'll send a
                deletion confirmation link to <strong>{user?.email}</strong>.
            </p>

            {emailRequested ? (
                <p role="status">
                Check your inbox. Your deletion confirmation link
                expires in 10 minutes.
                </p>
            ) : (
                <button
                type="button"
                className="cf-danger-button"
                disabled={busy}
                onClick={() => void requestEmailDeletion()}
                >
                {busy ? 'Sending...' : 'Email me a deletion link'}
                </button>
            )}

            {error && (
                <p role="alert" className="cf-danger-error">
                {error}
                </p>
            )}
            </>
        )}
        </section>
    );
    }


  return (
    <section className="cf-account-danger">
      <span className="cf-eyebrow">ACCOUNT MANAGEMENT</span>
      <h2>Danger Zone</h2>
      <p>
        Permanently delete your CareerForge account and its associated
        career profile, assessments, learning progress and conversations.
      </p>

      {!expanded ? (
        <button
          type="button"
          className="cf-danger-button"
          onClick={() => setExpanded(true)}
        >
          Delete account
        </button>
      ) : (
        <form onSubmit={handleDelete} className="cf-danger-form">
          <h3>Confirm account deletion</h3>
          <p>
            This action cannot be undone. Enter your email address,
            account password, and the word DELETE.
          </p>

          <label>
            Email address
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              autoComplete="email"
              required
            />
          </label>

          <label>
            Account password
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="current-password"
              required
            />
          </label>

          <label>
            Type DELETE
            <input
              value={confirmation}
              onChange={(event) => setConfirmation(event.target.value)}
              autoComplete="off"
              required
            />
          </label>

          {error && <p role="alert" className="cf-danger-error">{error}</p>}

          <div className="cf-danger-actions">
            <button
              type="button"
              onClick={() => setExpanded(false)}
              disabled={busy}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="cf-danger-button"
              disabled={
                busy ||
                email.trim().toLowerCase() !== user?.email.toLowerCase() ||
                confirmation !== 'DELETE' ||
                !password
              }
            >
              {busy ? 'Deleting account...' : 'Permanently delete account'}
            </button>
          </div>
        </form>
      )}
    </section>
  );
}
