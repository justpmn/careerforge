import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { postAuthRoute } from '../lib/auth';

export default function AuthCallbackPage() {
  const { refresh } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    refresh()
      .then((user) => {
        if (!active) return;
        if (user) navigate(postAuthRoute(user), { replace: true });
        else setError('Sign in could not be completed. No active session was found.');
      })
      .catch((err: unknown) => { if (active) setError(err instanceof Error ? err.message : 'OAuth sign in failed.'); });
    return () => { active = false; };
  }, [refresh, navigate]);

  return (
    <section className="auth-card" aria-live="polite">
      <div className="form-brow">AUTHENTICATION</div>
      <h2>{error ? 'Unable to sign in' : 'Finishing your sign in…'}</h2>
      <p className="auth-subtitle">{error || 'Checking your session securely.'}</p>
      {error && <p className="form-bottom"><Link to="/login">Return to login</Link></p>}
    </section>
  );
}
