
import { useState } from 'react';
import type { FormEvent } from 'react';
import { Link } from 'react-router-dom';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [busy, setBusy] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;

    setBusy(true);
    setError('');

    try {
      const response = await fetch('/api/auth/forgot-password', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim() }),
      });

      if (!response.ok) {
        throw new Error(
          response.status === 429
            ? 'Too many requests. Please try again later.'
            : 'Could not process your request. Please try again.'
        );
      }

      setSubmitted(true);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Something went wrong.'
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="auth-card" aria-labelledby="forgot-heading">
      <div className="form-brow">ACCOUNT / RECOVERY</div>

      {submitted ? (
        <>
          <h2 id="forgot-heading">Check your email.</h2>
          <p className="auth-subtitle" role="status">
            If your address belongs to an eligible CareerForge account,
            we've sent a password reset link.
          </p>
          <p className="auth-subtitle">
            The link expires after 15 minutes. Check your spam
            folder if you don't see it.
          </p>
          <p className="form-bottom">
            <Link to="/login">Back to login</Link>
          </p>
        </>
      ) : (
        <>
          <h2 id="forgot-heading">Forgot your password?</h2>
          <p className="auth-subtitle">
            Enter your account email and we'll send you
            a link to create a new password.
          </p>

          <form className="auth-form" onSubmit={submit}>
            <div className="field-group">
              <label htmlFor="recovery-email">Email address</label>
              <input
                id="recovery-email"
                type="email"
                autoComplete="email"
                placeholder="you@example.com"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
              />
            </div>

            {error && (
              <p role="alert" className="form-error">{error}</p>
            )}

            <button
              className="primary-button"
              type="submit"
              disabled={busy}
            >
              {busy ? 'Sending...' : 'Send reset link'}
            </button>
          </form>

          <p className="form-bottom">
            Remember your password? <Link to="/login">Log in</Link>
          </p>
        </>
      )}
    </section>
  );
}
