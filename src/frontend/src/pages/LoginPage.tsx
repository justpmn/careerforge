
import { useState } from 'react';
import type { FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import OAuthButtons from '../components/OAuthButtons';
import PasswordField from '../components/PasswordField';
import { useAuth } from '../context/AuthContext';
import { AuthApiError, postAuthRoute } from '../lib/auth';
import { emailVerificationApi } from '../lib/emailVerification';

export default function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const [verificationRequired, setVerificationRequired] = useState(false);
  const [resendBusy, setResendBusy] = useState(false);
  const [resendMessage, setResendMessage] = useState('');

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError('');
    setVerificationRequired(false);
    setResendMessage('');
    setBusy(true);

    try {
      const user = await login({
        email: email.trim(),
        password,
      });

      navigate(postAuthRoute(user), { replace: true });
    } catch (err) {
      if (
        err instanceof AuthApiError &&
        err.code === 'EMAIL_NOT_VERIFIED'
      ) {
        setVerificationRequired(true);
      }

      setError(
        err instanceof Error
          ? err.message
          : 'Sign in failed. Please try again.'
      );
    } finally {
      setBusy(false);
    }
  }

  async function resendVerification() {
    if (resendBusy || !email.trim()) return;

    setResendBusy(true);
    setResendMessage('');

    try {
      const result = await emailVerificationApi.resend(email);
      setResendMessage(result.message);
    } catch {
      setResendMessage(
        'Could not request a verification email. Please try again.'
      );
    } finally {
      setResendBusy(false);
    }
  }

  return (
    <section className="auth-card" aria-labelledby="login-heading">
      <div className="form-brow">
        WELCOME BACK <span>↗</span>
      </div>

      <h2 id="login-heading">Log in to your account</h2>

      <p className="auth-subtitle">
        Pick up where you left off. Your next milestone is waiting.
      </p>

      <OAuthButtons onError={setError} />

      <div className="form-divider">
        <span>or with email</span>
      </div>

      <form onSubmit={submit} className="auth-form">
        <div className="field-group">
          <label htmlFor="email">Email address</label>
          <input
            id="email"
            name="email"
            type="email"
            required
            autoComplete="email"
            placeholder="you@example.com"
            value={email}
            onChange={(event) => {
              setEmail(event.target.value);
              setVerificationRequired(false);
              setResendMessage('');
            }}
          />
        </div>

        <PasswordField
          id="password"
          label="Password"
          autoComplete="current-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
        <p className="form-bottom">
          <Link to="/forgot-password">Forgot password?</Link>
        </p>

        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}

        {verificationRequired && (
          <div className="field-group">
            <p className="auth-subtitle">
              Check your inbox for the verification link,
              or request a new one below.
            </p>

            <button
              type="button"
              className="primary-button"
              disabled={resendBusy}
              onClick={resendVerification}
            >
              {resendBusy ? 'Requesting...' : 'Resend verification email'}
            </button>

            {resendMessage && (
              <p className="auth-subtitle" role="status">
                {resendMessage}
              </p>
            )}
          </div>
        )}

        <button className="primary-button" disabled={busy} type="submit">
          {busy ? 'Signing in...' : 'Log in'}
          <span aria-hidden="true"> →</span>
        </button>
      </form>

      <p className="form-bottom">
        New to CareerForge? <Link to="/signup">Create an account</Link>
      </p>
    </section>
  );
}
