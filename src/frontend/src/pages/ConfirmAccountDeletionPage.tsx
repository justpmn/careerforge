
import { useState } from 'react';
import type { FormEvent } from 'react';
import { Link } from 'react-router-dom';
import '../account-deletion.css';

export default function ConfirmAccountDeletionPage() {
  const [token] = useState(() => {
    const params = new URLSearchParams(window.location.hash.slice(1));
    return params.get('token') || '';
  });

  const [email, setEmail] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [busy, setBusy] = useState(false);
  const [deleted, setDeleted] = useState(false);
  const [error, setError] = useState('');

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy || confirmation !== 'DELETE' || !token) return;

    setBusy(true);
    setError('');

    try {
      const response = await fetch('/api/account/deletion/confirm', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token,
          email: email.trim(),
          confirmation,
        }),
      });

      if (!response.ok) {
        const result = await response.json().catch(() => null);
        throw new Error(
          typeof result?.detail === 'string'
            ? result.detail
            : 'Account deletion failed.'
        );
      }

      window.history.replaceState(null, '', '/delete-account');
      setDeleted(true);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Account deletion failed.'
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="auth-card cf-delete-confirm">
      <div className="form-brow">ACCOUNT / DELETION</div>

      {deleted ? (
        <>
          <h2>Account deleted.</h2>
          <p className="auth-subtitle">
            Your CareerForge account has been deleted successfully.
          </p>
          <button
            type="button"
            className="cf-delete-return"
            onClick={() => window.location.replace('/signup')}
          >
            Create a new account
          </button>
        </>
      ) : !token ? (
        <>
          <h2>Invalid deletion link.</h2>
          <p className="auth-subtitle">
            Open the confirmation link sent to your email address.
          </p>
          <Link to="/login">Return to login</Link>
        </>
      ) : (
        <>
          <h2>Delete your account?</h2>
          <p className="auth-subtitle">
            This permanently deletes your CareerForge account and
            associated personal data. This cannot be undone.
          </p>

          <form className="auth-form" onSubmit={submit}>
            <div className="field-group">
              <label htmlFor="delete-email">Account email</label>
              <input
                id="delete-email"
                type="email"
                required
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                autoComplete="email"
              />
            </div>

            <div className="field-group">
              <label htmlFor="delete-confirmation">
                Type DELETE to confirm
              </label>
              <input
                id="delete-confirmation"
                value={confirmation}
                onChange={(event) =>
                  setConfirmation(event.target.value)
                }
                autoComplete="off"
                required
              />
            </div>

            {error && <p role="alert" className="cf-delete-error">{error}</p>}

            <button
              type="submit"
              className="cf-delete-return"
              disabled={busy || !email.trim() || confirmation !== 'DELETE'}
            >
              {busy ? 'Deleting account...' : 'Permanently delete account'}
            </button>
          </form>

          <Link to="/settings" className="cf-delete-cancel">
            Cancel and return to settings
          </Link>
        </>
      )}
    </section>
  );
}
