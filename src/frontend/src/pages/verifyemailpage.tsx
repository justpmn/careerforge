import { useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { Link } from 'react-router-dom';
import '../verify-email.css';
import { emailVerificationApi } from '../lib/emailVerification';

type Status = 'checking' | 'verified' | 'invalid';

export default function VerifyEmailPage() {
  const token = useRef(
    new URLSearchParams(window.location.search).get('token')
  );
  const started = useRef(false);

  const [status, setStatus] = useState<Status>('checking');
  const [error, setError] = useState('');
  const [email, setEmail] = useState('');
  const [resending, setResending] = useState(false);
  const [resendMessage, setResendMessage] = useState('');

  useEffect(() => {
    if (started.current) return;
    started.current = true;

    // Remove the secret token from the address bar.
    window.history.replaceState(
      window.history.state,
      '',
      window.location.pathname
    );

    if (!token.current) {
      setStatus('invalid');
      setError('No verification token was provided.');
      return;
    }

    void emailVerificationApi.verify(token.current)
      .then(() => {
        setStatus('verified');
      })
      .catch((cause: unknown) => {
        setStatus('invalid');
        setError(
          cause instanceof Error
            ? cause.message
            : 'Could not verify your email address.'
        );
      });
  }, []);

  async function resend(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (resending || !email.trim()) return;

    setResending(true);
    setResendMessage('');

    try {
      const result = await emailVerificationApi.resend(email);
      setResendMessage(result.message);
    } catch {
      setResendMessage(
        'Could not process your request. Please try again.'
      );
    } finally {
      setResending(false);
    }
  }

  return (
    <main className="cf-verify-page">
      <div className="cf-verify-card">
        <span className="stage-marker">
          CAREERFORGE / ACCOUNT VERIFICATION
        </span>

        {status === 'checking' && (
          <section role="status">
            <h1>Verifying your email.</h1>
            <p>Please wait while we confirm your address.</p>
          </section>
        )}

        {status === 'verified' && (
          <section role="status">
            <h1>Email verified.</h1>
            <p>
              Your email address has been confirmed.
              You can now sign in to CareerForge.
            </p>
            <Link to="/login" className="cf-verify-link">
              Continue to login
            </Link>
          </section>
        )}

        {status === 'invalid' && (
          <section>
            <h1>Verification unsuccessful.</h1>
            <p role="alert">{error}</p>

            <p>
              Your verification link may have expired
              or already been used. You can request another.
            </p>

            <form onSubmit={resend}>
              <label htmlFor="verification-email">
                Email address
              </label>

              <input
                id="verification-email"
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="you@example.com"
              />

              <button
                type="submit"
                disabled={resending || !email.trim()}
              >
                {resending
                  ? 'Sending...'
                  : 'Resend verification email'}
              </button>
            </form>

            {resendMessage && (
              <p role="status">{resendMessage}</p>
            )}

            <Link to="/login" className="cf-verify-back">
              Back to login
            </Link>
          </section>
        )}
      </div>
    </main>
  );
}
