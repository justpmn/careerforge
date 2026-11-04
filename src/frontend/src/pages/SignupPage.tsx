
import { useState } from 'react';
import type { FormEvent } from 'react';
import { Link } from 'react-router-dom';
import OAuthButtons from '../components/OAuthButtons';
import PasswordField from '../components/PasswordField';
import { useAuth } from '../context/AuthContext';
import { emailVerificationApi } from '../lib/emailVerification';

export default function SignupPage() {
  const { register } = useAuth();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const [registeredEmail, setRegisteredEmail] = useState<string | null>(null);
  const [resendBusy, setResendBusy] = useState(false);
  const [resendMessage, setResendMessage] = useState('');

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError('');

    if (name.trim().length < 2) {
      setError('Please enter your name (at least 2 characters).');
      return;
    }

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
      const normalizedEmail = email.trim().toLowerCase();

      await register({
        name: name.trim(),
        email: normalizedEmail,
        password,
      });

      setRegisteredEmail(normalizedEmail);
      setPassword('');
      setConfirm('');
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Registration failed. Please try again.'
      );
    } finally {
      setBusy(false);
    }
  }

  async function resendVerification() {
    if (!registeredEmail || resendBusy) return;

    setResendBusy(true);
    setResendMessage('');

    try {
      const result = await emailVerificationApi.resend(registeredEmail);
      setResendMessage(result.message);
    } catch (err) {
      setResendMessage(
        err instanceof Error
          ? err.message
          : 'Could not request another verification email.'
      );
    } finally {
      setResendBusy(false);
    }
  }

  if (registeredEmail) {
    return (
      <section className="auth-card" aria-labelledby="verify-heading">
        <div className="form-brow">ONE MORE STEP</div>

        <h2 id="verify-heading">Check your email</h2>

        <p className="auth-subtitle">
          Your CareerForge account has been created.
          Verify your email address before signing in.
        </p>

        <div className="field-group">
          <label>Email address</label>
          <p>{registeredEmail}</p>
        </div>

        <p className="auth-subtitle">
          Open the verification link sent to your email.
          The link expires after 24 hours.
        </p>

        {import.meta.env.DEV && (
          <p className="auth-subtitle">
            Development mode: if console email delivery is enabled,
            find the verification link in your FastAPI terminal.
          </p>
        )}

        <button
          className="primary-button"
          type="button"
          disabled={resendBusy}
          onClick={resendVerification}
        >
          {resendBusy ? 'Requesting...' : 'Resend verification email'}
        </button>

        {resendMessage && (
          <p role="status" className="auth-subtitle">
            {resendMessage}
          </p>
        )}

        <p className="form-bottom">
          Already verified? <Link to="/login">Log in</Link>
        </p>
      </section>
    );
  }

  return (
    <section className="auth-card" aria-labelledby="signup-heading">
      <div className="form-brow">
        THE FIRST STEP <span>→</span>
      </div>

      <h2 id="signup-heading">Create your account</h2>

      <p className="auth-subtitle">
        A clear direction for your career starts with knowing where you stand.
      </p>

      <OAuthButtons onError={setError} />

      <div className="form-divider">
        <span>or with email</span>
      </div>

      <form onSubmit={submit} className="auth-form">
        <div className="field-group">
          <label htmlFor="name">Full name</label>
          <input
            id="name"
            name="name"
            type="text"
            autoComplete="name"
            minLength={2}
            maxLength={100}
            required
            placeholder="Your name"
            value={name}
            onChange={(event) => setName(event.target.value)}
          />
        </div>

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
            onChange={(event) => setEmail(event.target.value)}
          />
        </div>

        <PasswordField
          id="password"
          label="Password"
          autoComplete="new-password"
          minLength={12}
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          placeholder="At least 12 characters"
        />

        <PasswordField
          id="confirm"
          label="Confirm password"
          autoComplete="new-password"
          minLength={12}
          value={confirm}
          onChange={(event) => setConfirm(event.target.value)}
          placeholder="Repeat your password"
        />

        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}

        <button className="primary-button" disabled={busy} type="submit">
          {busy ? 'Creating account...' : 'Create account'}
          <span aria-hidden="true"> →</span>
        </button>
      </form>

      <p className="form-bottom">
        Already have an account? <Link to="/login">Log in</Link>
      </p>
    </section>
  );
}
