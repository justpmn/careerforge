
import { useState } from 'react';
import type { FormEvent } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';

import { useAuth } from '../context/AuthContext';
import { csrfHeader } from '../lib/auth';
import MfaQrEnrollment from '../components/MfaQrEnrollment';

export default function AdminMfaPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { refresh } = useAuth();

  const enrollmentMode = searchParams.get('enroll') === '1';

  const [code, setCode] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy || code.length !== 6) return;

    setBusy(true);
    setError('');

    try {
      const response = await fetch(
        '/api/auth/admin-mfa/challenge/verify',
        {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
            ...csrfHeader(),
          },
          body: JSON.stringify({ code }),
        }
      );

      if (!response.ok) {
        const result: {
          detail?: string | { message?: string };
        } | null = await response.json().catch(() => null);

        const detail = result?.detail;

        throw new Error(
          typeof detail === 'string'
            ? detail
            : typeof detail?.message === 'string'
              ? detail.message
              : 'Could not verify your authenticator code.'
        );
      }

      const user = await refresh();

      if (!user) {
        throw new Error('Could not establish your admin session.');
      }

      navigate('/admin', { replace: true });
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Authentication failed.'
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="cf-verify-page">
      <section className="auth-card" aria-labelledby="mfa-heading">
        {enrollmentMode ? (
          <>
            <h2 id="mfa-heading">Secure your administrator account.</h2>

            <p className="auth-subtitle">
              Set up an authenticator app to protect your
              CareerForge administrator account.
            </p>

            <MfaQrEnrollment
              onComplete={() => navigate('/login', { replace: true })}
            />

            <p className="form-bottom">
              Already enrolled?{' '}
              <Link to="/auth/mfa">Enter your authenticator code</Link>
            </p>
          </>
        ) : (
          <>
            <h2 id="mfa-heading">Verify it's you</h2>

            <p className="auth-subtitle">
              Open your authenticator app and enter the
              six-digit code for CareerForge.
            </p>

            <form onSubmit={submit} className="auth-form">
              <div className="field-group">
                <label htmlFor="mfa-code">Authenticator code</label>

                <input
                  id="mfa-code"
                  type="text"
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  pattern="[0-9]{6}"
                  maxLength={6}
                  required
                  autoFocus
                  value={code}
                  onChange={(event) => {
                    setCode(
                      event.target.value.replace(/\D/g, '').slice(0, 6)
                    );
                  }}
                  placeholder="000000"
                  aria-describedby="mfa-help"
                />

                <p id="mfa-help" className="auth-subtitle">
                  Codes change approximately every 30 seconds.
                </p>
              </div>

              {error && (
                <p className="form-error" role="alert">
                  {error}
                </p>
              )}

              <button
                className="primary-button"
                type="submit"
                disabled={busy || code.length !== 6}
              >
                {busy ? 'Verifying...' : 'Verify and continue'}
              </button>
            </form>

            <p className="form-bottom">
              Challenge expired?{' '}
              <Link to="/login">Sign in again</Link>
            </p>
          </>
        )}
      </section>
    </main>
  );
}
