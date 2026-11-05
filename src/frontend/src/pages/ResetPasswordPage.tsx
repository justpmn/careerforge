
import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { Link } from 'react-router-dom';
import PasswordField from '../components/PasswordField';

export default function ResetPasswordPage() {
  const [token] = useState(() => {
    const params = new URLSearchParams(window.location.hash.slice(1));
    return params.get('token') || '';
  });

  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [busy, setBusy] = useState(false);
  const [completed, setCompleted] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (token) {
      window.history.replaceState(null, '', '/reset-password');
    }
  }, [token]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy || !token) return;

    setError('');

    if (password.length < 12) {
      setError('Password must contain at least 12 characters.');
      return;
    }

    if (password !== confirm) {
      setError('Your passwords do not match.');
      return;
    }

    setBusy(true);

    try {
      const response = await fetch('/api/auth/reset-password', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token,
          new_password: password,
        }),
      });

      if (!response.ok) {
        const result = await response.json().catch(() => null);
        throw new Error(
          typeof result?.detail === 'string'
            ? result.detail
            : 'Unable to reset your password.'
        );
      }

      setPassword('');
      setConfirm('');
      setCompleted(true);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Password reset failed.'
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="auth-card" aria-labelledby="reset-heading">
      <div className="form-brow">ACCOUNT / PASSWORD RESET</div>

      {completed ? (
        <>
          <h2 id="reset-heading">Password updated.</h2>
          <p className="auth-subtitle" role="status">
            Your CareerForge password has been changed successfully.
            Sign in with your new password to continue.
          </p>
          <p className="form-bottom">
            <a href="/login">Continue to login</a>
          </p>
        </>
      ) : !token ? (
        <>
          <h2 id="reset-heading">Invalid reset link.</h2>
          <p className="auth-subtitle">
            This page needs a valid password reset link from your email.
          </p>
          <p className="form-bottom">
            <Link to="/forgot-password">Request another link</Link>
          </p>
        </>
      ) : (
        <>
          <h2 id="reset-heading">Choose a new password.</h2>
          <p className="auth-subtitle">
            Create a secure password for your CareerForge account.
          </p>

          <form className="auth-form" onSubmit={submit}>
            <PasswordField
              id="reset-password"
              label="New password"
              autoComplete="new-password"
              minLength={12}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="At least 12 characters"
            />

            <PasswordField
              id="reset-confirm"
              label="Confirm new password"
              autoComplete="new-password"
              minLength={12}
              value={confirm}
              onChange={(event) => setConfirm(event.target.value)}
              placeholder="Repeat your new password"
            />

            {error && (
              <p role="alert" className="form-error">{error}</p>
            )}

            <button
              className="primary-button"
              type="submit"
              disabled={busy || !password || !confirm}
            >
              {busy ? 'Updating...' : 'Reset password'}
            </button>
          </form>
        </>
      )}
    </section>
  );
}
