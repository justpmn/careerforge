import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getAccountSettings,  updateAccountSettings} from '../lib/accountsettings';
import type { AccountSettings} from '../lib/accountsettings';
import '../settings.css';
import AppearanceSettings from '../components/AppearanceSettings';
import AccountDangerZone from '../components/AccountDangerZone';
import GoogleAccountLink from '../components/GoogleAccountLink';


export default function SettingsPage() {
  const { user, refresh, logout } = useAuth();
  const navigate = useNavigate();

  const [account, setAccount] =
    useState<AccountSettings | null>(null);

  const [fullName, setFullName] = useState('');

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [signingOut, setSigningOut] = useState(false);

  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');


  useEffect(() => {
    let active = true;

    setLoading(true);
    setError('');

    void getAccountSettings()
      .then((result) => {
        if (!active) return;

        setAccount(result);
        setFullName(result.full_name);
      })
      .catch((cause: unknown) => {
        if (!active) return;

        setError(
          cause instanceof Error
            ? cause.message
            : 'Could not load your account settings.'
        );
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [user?.id]);


  const cleanName = fullName.trim();

  const hasChanges =
    account !== null &&
    cleanName !== account.full_name;

  const validName =
    cleanName.length >= 2 &&
    cleanName.length <= 150;


  async function handleSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (saving || !hasChanges) return;

    setError('');
    setSuccess('');

    if (!validName) {
      setError('Name must contain 2 to 150 characters.');
      return;
    }

    setSaving(true);

    try {
      const updated = await updateAccountSettings(cleanName);

      setAccount(updated);
      setFullName(updated.full_name);

      setSuccess('Your account information has been updated.');

      // Refresh the global session user so My Profile
      // and the dashboard display the new name.
      try {
        await refresh();
      } catch {
        setError(
          'Your changes were saved, but the account header ' +
          'could not refresh. Reload the page to see your new name.'
        );
      }
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : 'Could not update your account.'
      );
    } finally {
      setSaving(false);
    }
  }


  async function handleSignOut() {
    if (signingOut) return;

    setSigningOut(true);
    setError('');
    setSuccess('');

    try {
      await logout();
      navigate('/login', { replace: true });
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : 'Could not sign out.'
      );

      setSigningOut(false);
    }
  }


  return (
    <section className="cf-dashboard cf-settings">
      <header className="cf-dashboard-header">
        <div>
          <span className="stage-marker">
            ACCOUNT SETTINGS
          </span>

          <h1>Your settings.</h1>
          <AppearanceSettings />

          <p>
            Manage your personal information,
            appearance and account session.
          </p>
        </div>
      </header>

      <Link to="/profile" className="cf-settings-back">
        ← Back to My Profile
      </Link>

      {error && (
        <p className="cf-settings-error" role="alert">
          {error}
        </p>
      )}

      {success && (
        <p className="cf-settings-success" role="status">
          {success}
        </p>
      )}

      <div className="cf-settings-sections">

        {/* PERSONAL INFORMATION */}
        <article className="cf-dashboard-card">
          <span className="cf-eyebrow">
          </span>
          <h2>Account information</h2>
          <p>
            Update the name displayed on your
            CareerForge account.
          </p>
          {loading ? (
            <p className="cf-settings-helper">
              Loading your account...
            </p>
          ) : account ? (
            <form
              className="cf-settings-form"
              onSubmit={(event) => void handleSave(event)}
            >
              <label htmlFor="cf-settings-name">
                Full name
              </label>

              <input
                id="cf-settings-name"
                type="text"
                autoComplete="name"
                maxLength={150}
                value={fullName}
                disabled={saving}
                onChange={(event) => {
                  setFullName(event.target.value);
                  setSuccess('');
                }}
                required
              />
              <label htmlFor="cf-settings-email">
                Email address
              </label>
              <input
                id="cf-settings-email"
                type="email"
                autoComplete="email"
                value={account.email}
                disabled
              />
              <p className="cf-settings-helper">
                Your email is associated with your
                sign-in identity. Email changes are
                not available in this version.
              </p>
              <div className="cf-settings-form-actions">
                <button
                  type="submit"
                  className="cf-settings-primary"
                  disabled={
                    saving ||
                    !validName ||
                    !hasChanges
                  }
                >
                  {saving
                    ? 'Saving...'
                    : 'Save changes'}
                </button>
                <button
                  type="button"
                  className="cf-settings-secondary"
                  disabled={saving || !hasChanges}
                  onClick={() => {
                    setFullName(account.full_name);
                    setError('');
                    setSuccess('');
                  }}
                >
                  Discard changes
                </button>
              </div>
            </form>
          ) : (
            <p className="cf-settings-helper">
              Account information is unavailable.
            </p>
          )}

        </article>
        {/* ACCOUNT SECURITY */}
        <article className="cf-dashboard-card">
          <span className="cf-eyebrow">
            ACCOUNT SECURITY
          </span>

          <h2>Sign-in information</h2>
          <p>
            Review how password authentication is configured
            for your CareerForge account.
          </p>

          <div className="cf-settings-info-row">
            <div>
              <strong>Password sign-in</strong>

              <span>
                {loading
                  ? 'Checking account...'
                  : account?.has_password
                    ? 'A local password is configured.'
                    : 'No local password is configured.'}
              </span>
            </div>
            <span className="cf-settings-status">
              {loading
                ? 'Checking'
                : account?.has_password
                  ? 'Configured'
                  : 'Not configured'}
            </span>
          </div>

              <section className="cf-settings-connected">
                <h2>Connected accounts</h2>
                <GoogleAccountLink />
              </section>

        </article>


        {/* SESSION */}
        <article className="cf-dashboard-card">
          <span className="cf-eyebrow">
          </span>

          <h2>Your current session</h2>
          <AccountDangerZone />

          <p>
            Sign out of CareerForge on this browser.
          </p>

          {account && (
            <div className="cf-settings-info-row">
              <div>
                <strong>Signed-in account</strong>
                <span>{account.email}</span>
              </div>

              <span className="cf-settings-status">
                Active
              </span>
            </div>
          )}

          <button
            type="button"
            className="cf-settings-signout"
            disabled={signingOut}
            onClick={() => void handleSignOut()}
          >
            {signingOut
              ? 'Signing out...'
              : 'Sign out'}
          </button>
        </article>

      </div>
    </section>
  );
}
