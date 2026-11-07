
import { useState } from 'react';
import type { FormEvent } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';

import { useAuth } from '../context/AuthContext';
import { csrfHeader } from '../lib/auth';
import MfaQrEnrollment from '../components/MfaQrEnrollment';
import '../adminmfa.css';

type VerificationMode = 'authenticator' | 'recovery';

export default function AdminMfaPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { refresh } = useAuth();

  const enrollmentMode = searchParams.get('enroll') === '1';
  const providerParam = searchParams.get('oauth');

  const oauthProvider =
    providerParam === 'google' ||
    providerParam === 'github' ||
    providerParam === 'both'
      ? providerParam
      : undefined;

  const [mode, setMode] = useState<VerificationMode>('authenticator');
  const [code, setCode] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const isRecovery = mode === 'recovery';
  const validCode = isRecovery
    ? /^[0-9a-f]{32}$/.test(code)
    : /^[0-9]{6}$/.test(code);
  const [recoveringAuthenticator, setRecoveringAuthenticator] =
    useState(false);

  function changeMode(next: VerificationMode) {
    if (busy) return;
    setMode(next);
    setCode('');
    setError('');
  }

  function updateCode(value: string) {
    setCode(
      isRecovery
        ? value.replace(/[^0-9a-f]/gi, '').toLowerCase().slice(0, 32)
        : value.replace(/\D/g, '').slice(0, 6)
    );
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy || !validCode) return;

    setBusy(true);
    setError('');

    try {
      const endpoint = isRecovery
        ? '/api/auth/admin-mfa/challenge/recovery'
        : '/api/auth/admin-mfa/challenge/verify';

      const payload = isRecovery
        ? { recovery_code: code }
        : { code };

      const response = await fetch(endpoint, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          ...csrfHeader(),
        },
        body: JSON.stringify(payload),
      });

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
              : 'Could not verify your credentials.'
        );
      }

      const user = await refresh();

    if (!user) {
      throw new Error('Could not establish your admin session.');
    }

    setCode('');

    if (isRecovery) {
      setRecoveringAuthenticator(true);
      return;
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
            <h2 id="mfa-heading">
              Secure your administrator account.
            </h2>

            <p className="auth-subtitle">
              Set up an authenticator app to protect your
              CareerForge administrator account.
            </p>

            <MfaQrEnrollment
              oauthOnly={oauthProvider !== undefined}
              oauthProvider={oauthProvider}
              onComplete={() =>
                navigate('/login', { replace: true })
              }
            />

            <p className="form-bottom">
              Already enrolled?{' '}
              <Link to="/auth/mfa">
                Enter your authenticator code
              </Link>
            </p>
          </>
                ) : recoveringAuthenticator ? (
          <>
            <h2 id="mfa-heading">
              Replace your lost authenticator
            </h2>

            <p className="auth-subtitle">
              Recovery verification succeeded. You can now connect
              a new authenticator. Complete the replacement within
              five minutes.
            </p>

            <MfaQrEnrollment
              mode="recover"
              onComplete={() => {
                window.location.replace('/login');
              }}
            />
          </>
        ) : (
          <>
            <h2 id="mfa-heading">Verify it's you</h2>

            <p className="auth-subtitle">
              {isRecovery
                ? 'Enter one of the recovery codes you saved during authenticator setup.'
                : 'Open your authenticator app and enter the six-digit code for CareerForge.'}
            </p>

            <div
              className="cf-mfa-methods"
              role="group"
              aria-label="Verification method"
            >
              <button
                type="button"
                className={`cf-mfa-method ${
                  !isRecovery ? 'is-active' : ''
                }`}
                aria-pressed={!isRecovery}
                disabled={busy}
                onClick={() => changeMode('authenticator')}
              >
                Authenticator
              </button>

              <button
                type="button"
                className={`cf-mfa-method ${
                  isRecovery ? 'is-active' : ''
                }`}
                aria-pressed={isRecovery}
                disabled={busy}
                onClick={() => changeMode('recovery')}
              >
                Recovery code
              </button>
            </div>

            <form onSubmit={submit} className="auth-form">
              <div className="field-group">
                <label htmlFor="mfa-code">
                  {isRecovery
                    ? 'Recovery code'
                    : 'Authenticator code'}
                </label>

                <input
                  id="mfa-code"
                  type="text"
                  inputMode={isRecovery ? 'text' : 'numeric'}
                  autoComplete={
                    isRecovery ? 'off' : 'one-time-code'
                  }
                  autoCapitalize="off"
                  spellCheck={false}
                  pattern={
                    isRecovery
                      ? '[0-9a-fA-F]{32}'
                      : '[0-9]{6}'
                  }
                  maxLength={isRecovery ? 32 : 6}
                  required
                  autoFocus
                  value={code}
                  onChange={(event) =>
                    updateCode(event.target.value)
                  }
                  placeholder={
                    isRecovery
                      ? 'Enter your recovery code'
                      : '000000'
                  }
                  aria-describedby="mfa-help"
                />

                <p id="mfa-help" className="auth-subtitle">
                  {isRecovery
                    ? 'Each recovery code can only be used once. Keep your remaining codes somewhere safe.'
                    : 'Codes change approximately every 30 seconds.'}
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
                disabled={busy || !validCode}
              >
                {busy
                  ? 'Verifying...'
                  : 'Verify and continue'}
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
