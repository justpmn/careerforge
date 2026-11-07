import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { FcGoogle } from 'react-icons/fc';
import { FaGithub } from 'react-icons/fa';
import { FiCheckCircle, FiLink2, FiArrowUpRight, FiRefreshCw, FiAlertTriangle, FiX} from 'react-icons/fi';
import { LuUnlink } from 'react-icons/lu';
import { csrfHeader } from '../lib/auth';
import '../connected-accounts.css';

type Provider = 'google' | 'github';

type LinkStatus = {
  google: boolean;
  github: boolean;
  has_password: boolean;
};

const providers = [
  {
    id: 'google',
    name: 'Google',
    description: 'Sign in using your Google account.',
    Icon: FcGoogle,
  },
  {
    id: 'github',
    name: 'GitHub',
    description: 'Sign in using your GitHub account.',
    Icon: FaGithub,
  },
] as const;

const messages: Record<string, string> = {
  linked: 'Account connected successfully.',
  already_linked: 'This account is already connected elsewhere.',
  email_mismatch: 'The provider email must match your CareerForge email.',
  email_unverified: 'Verify your CareerForge email before linking.',
  account_unavailable: 'This account is unavailable.',
  session_expired: 'Your session expired. Sign in again and retry.',
  authorization_failed: 'Authorization was unsuccessful. Try again.',
};

async function readError(response: Response): Promise<string> {
  const body = await response.json().catch(() => null);
  const detail = body?.detail;

  if (typeof detail === 'string') return detail;
  if (typeof detail?.message === 'string') return detail.message;

  return `Request failed (HTTP ${response.status}).`;
}

export default function ConnectedAccounts() {
  const [status, setStatus] = useState<LinkStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [actionError, setActionError] = useState('');
  const [selected, setSelected] = useState<Provider | null>(null);
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState<Provider | null>(null);
  const [reload, setReload] = useState(0);

  const params = new URLSearchParams(window.location.search);
  const result = params.get('account_link');
  const resultProvider = params.get('provider');

  const providerName =
    resultProvider === 'google' ? 'Google' :
    resultProvider === 'github' ? 'GitHub' : 'Provider';
    const [disconnectTarget, setDisconnectTarget] = useState<Provider | null>(null);
    const [disconnectPassword, setDisconnectPassword] = useState('');
    const [disconnectBusy, setDisconnectBusy] = useState(false);

    const methodCount = status
    ? Number(status.google) +
        Number(status.github) +
        Number(status.has_password)
    : 0;

  useEffect(() => {
    const controller = new AbortController();

    setLoading(true);
    setLoadError('');

    fetch('/api/auth/oauth/link/status', {
      credentials: 'include',
      cache: 'no-store',
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok) throw new Error(await readError(response));
        return response.json() as Promise<LinkStatus>;
      })
      .then((data) => setStatus(data))
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setLoadError(
          err instanceof Error ? err.message : 'Could not load connected accounts.'
        );
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
  }, [reload]);

  async function connect(provider: Provider) {
    if (!status || busy) return;

    setBusy(provider);
    setActionError('');

    try {
      const response = await fetch('/api/auth/oauth/link/prepare', {
        method: 'POST',
        credentials: 'include',
        cache: 'no-store',
        headers: {
          'Content-Type': 'application/json',
          ...csrfHeader(),
        },
        body: JSON.stringify({
          provider,
          ...(status.has_password ? { password } : {}),
        }),
      });

      if (!response.ok) throw new Error(await readError(response));

      setPassword('');
      window.location.assign(`/api/auth/oauth/${provider}/link/start`);
    } catch (err) {
      setActionError(
        err instanceof Error ? err.message : 'Could not connect account.'
      );
      setBusy(null);
    }
  }

  function chooseProvider(provider: Provider) {
    setActionError('');

    if (!status?.has_password) {
      void connect(provider);
      return;
    }

    if (selected === provider) {
      setSelected(null);
      setPassword('');
    } else {
      setSelected(provider);
      setPassword('');
    }
  }

  function submitPassword(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selected && password) void connect(selected);
  }
  
function closeDisconnect() {
  if (disconnectBusy) return;
  setDisconnectTarget(null);
  setDisconnectPassword('');
  setActionError('');
}

async function disconnect(event: FormEvent<HTMLFormElement>) {
  event.preventDefault();

  if (!disconnectTarget || !status || disconnectBusy) return;

  setDisconnectBusy(true);
  setActionError('');

  try {
    const response = await fetch('/api/auth/oauth/link/disconnect', {
      method: 'POST',
      credentials: 'include',
      cache: 'no-store',
      headers: {
        'Content-Type': 'application/json',
        ...csrfHeader(),
      },
      body: JSON.stringify({
        provider: disconnectTarget,
        ...(status.has_password
          ? { password: disconnectPassword }
          : {}),
      }),
    });

    if (!response.ok) throw new Error(await readError(response));

    window.location.replace('/login');
  } catch (err) {
    setActionError(
      err instanceof Error
        ? err.message
        : 'Could not disconnect this account.'
    );
    setDisconnectBusy(false);
  }
}


  return (
    <section className="cf-connected-panel" aria-label="Connected sign-in accounts">
      <div className="cf-connected-intro">
        <span className="cf-connected-intro-icon">
          <FiLink2 size={19} />
        </span>

        <p>
          Connect your accounts to access CareerForge using different sign-in
          methods. Your profile, skills and progress stay in one place.
        </p>
      </div>

      {result && messages[result] && (
        <div
          className={`cf-connected-notice ${result === 'linked' ? 'cf-connected-notice--success' : ''}`}
          role="status"
        >
          {result === 'linked'
            ? `${providerName} connected successfully.`
            : messages[result]}
        </div>
      )}

      {loading ? (
        <div className="cf-connected-placeholder">
          <span className="cf-connected-spinner" />
          Checking connected accounts...
        </div>
      ) : loadError || !status ? (
        <div className="cf-connected-load-error" role="alert">
          <span>{loadError || 'Could not load connected accounts.'}</span>
          <button type="button" onClick={() => setReload((n) => n + 1)}>
            <FiRefreshCw size={15} />
            Retry
          </button>
        </div>
      ) : (
        <div className="cf-connected-list">
          {providers.map(({ id, name, description, Icon }) => {
            const linked = status[id];
            const expanded = selected === id && !linked;

            return (
              <div className="cf-connected-item" key={id}>
                <div className="cf-connected-row">
                  <div className={`cf-connected-logo cf-connected-logo--${id}`}>
                    <Icon size={25} aria-hidden="true" />
                  </div>

                  <div className="cf-connected-details">
                    <strong>{name}</strong>
                    <span>
                      {linked ? 'Available as a sign-in method' : description}
                    </span>
                  </div>

                  <div className="cf-connected-action-area">
                    {linked ? (
                    <div className="cf-connected-linked-actions">
                        <span className="cf-connected-linked">
                        <FiCheckCircle size={15} />
                        Connected
                        </span>

                        {methodCount > 1 ? (
                        <button
                            type="button"
                            className="cf-connected-disconnect"
                            disabled={busy !== null || disconnectBusy}
                            onClick={() => {
                            setSelected(null);
                            setPassword('');
                            setActionError('');
                            setDisconnectTarget(id);
                            }}
                        >
                            <LuUnlink size={14} />
                            Disconnect
                        </button>
                        ) : (
                        <span className="cf-connected-only-method">
                            Only sign-in method
                        </span>
                        )}
                    </div>
                    ) : (
                      <button
                        type="button"
                        className="cf-connected-connect"
                        onClick={() => chooseProvider(id)}
                        disabled={busy !== null}
                        aria-expanded={status.has_password ? expanded : undefined}
                      >
                        {busy === id ? 'Connecting...' : 'Connect'}
                        {busy !== id && <FiArrowUpRight size={15} />}
                      </button>
                    )}
                  </div>
                </div>

                {expanded && (
                  <form className="cf-connected-confirm" onSubmit={submitPassword}>
                    <div className="cf-connected-confirm-heading">
                      <strong>Confirm your password</strong>
                      <p>
                        Enter your CareerForge password to connect {name}.
                      </p>
                    </div>

                    <div className="cf-connected-confirm-fields">
                      <input
                        type="password"
                        autoComplete="current-password"
                        aria-label="CareerForge password"
                        placeholder="Your account password"
                        value={password}
                        onChange={(event) => setPassword(event.target.value)}
                        disabled={busy !== null}
                        required
                      />

                      <button
                        type="submit"
                        className="cf-connected-confirm-button"
                        disabled={!password || busy !== null}
                      >
                        {busy === id ? 'Connecting...' : `Continue with ${name}`}
                      </button>

                      <button
                        type="button"
                        className="cf-connected-cancel"
                        onClick={() => {
                          setSelected(null);
                          setPassword('');
                          setActionError('');
                        }}
                        disabled={busy !== null}
                      >
                        Cancel
                      </button>
                    </div>
                  </form>
                )}
              </div>
            );
          })}
        </div>
      )}

      {actionError && !disconnectTarget && (
    <p className="cf-connected-error" role="alert">{actionError}</p>
    )}
      
    {disconnectTarget && (
    <div className="cf-connected-modal-overlay">
        <div
        className="cf-connected-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="cf-disconnect-title"
        >
        <div className="cf-connected-modal-header">
            <span className="cf-connected-modal-icon">
            <FiAlertTriangle size={22} />
            </span>

            <button
            type="button"
            className="cf-connected-modal-close"
            aria-label="Close confirmation"
            onClick={closeDisconnect}
            disabled={disconnectBusy}
            >
            <FiX size={20} />
            </button>
        </div>

        <h3 id="cf-disconnect-title">
            Disconnect {disconnectTarget === 'google' ? 'Google' : 'GitHub'}?
        </h3>

        <p>
            You will no longer be able to use this provider to
            sign in to CareerForge. Your profile, skills and
            progress will remain unchanged.
        </p>

        <p>
            For security, you'll be signed out of all active
            CareerForge sessions.
        </p>

        <form onSubmit={disconnect}>
            {status?.has_password && (
            <div className="cf-connected-modal-field">
                <label htmlFor="cf-disconnect-password">
                Confirm your CareerForge password
                </label>

                <input
                id="cf-disconnect-password"
                type="password"
                autoComplete="current-password"
                placeholder="Account password"
                value={disconnectPassword}
                onChange={(event) =>
                    setDisconnectPassword(event.target.value)
                }
                disabled={disconnectBusy}
                required
                />
            </div>
            )}

            {actionError && (
            <p className="cf-connected-modal-error" role="alert">
                {actionError}
            </p>
            )}

            <div className="cf-connected-modal-actions">
            <button
                type="button"
                className="cf-connected-modal-cancel"
                onClick={closeDisconnect}
                disabled={disconnectBusy}
            >
                Cancel
            </button>

            <button
                type="submit"
                className="cf-connected-modal-confirm"
                disabled={
                disconnectBusy ||
                (Boolean(status?.has_password) && !disconnectPassword)
                }
            >
                {disconnectBusy ? 'Disconnecting...' : 'Disconnect account'}
            </button>
            </div>
        </form>
        </div>
    </div>
    )}


      {status && !status.has_password && (
        <p className="cf-connected-footnote">
          Connecting another provider requires a recent sign-in.
          If prompted, sign in again and retry.
        </p>
      )}
    </section>
  );
}
