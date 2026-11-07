
import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { useAuth } from '../context/AuthContext';
import { postAuthRoute } from '../lib/auth';

const errorMessages: Record<string, string> = {
  authorization_failed: 'Authorization was cancelled or could not be completed.',
  verified_email_required: 'A verified email address is required.',
  account_exists: 'An account with this email already exists. Sign in using your existing method.',
  account_unavailable: 'This account is no longer available.',
  provider_error: 'Could not retrieve your account details. Please try again.',
};

export default function AuthCallbackPage() {
  const navigate = useNavigate();
  const { refresh } = useAuth();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get('error');

    if (code) {
      setError(errorMessages[code] ?? 'Authentication failed.');
      return;
    }

    let active = true;

    refresh()
      .then((user) => {
        if (!active) return;

        if (user) {
          navigate(postAuthRoute(user), { replace: true });
        } else {
          setError('No authenticated session was found.');
        }
      })
      .catch(() => {
        if (active) setError('Could not verify your session.');
      });

    return () => {
      active = false;
    };
  }, [refresh, navigate]);

  return (
    <section className="workspace-panel">
      <h1>{error ? 'Sign-in unsuccessful' : 'Signing you in...'}</h1>
      <p>{error ?? 'Verifying your CareerForge account.'}</p>

      {error && <Link to="/login">Return to login</Link>}
    </section>
  );
}
