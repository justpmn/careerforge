
import { useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { csrfHeader } from '../lib/auth';
import '../mfa-qr.css';

type EnrollmentStart = {
  provisioning_uri: string;
  qr_code_data_url: string;
  expires_at?: string;
};

type EnrollmentResult = {
  message?: string;
  recovery_codes?: string[];
};

type Props = {
  mode?: 'enroll' | 'replace';
  onComplete?: () => void;
};

async function postMfa<T>(path: string, body?: object): Promise<T> {
  const response = await fetch(
    `/api/auth/admin-mfa/${path}`,
    {
      method: 'POST',
      credentials: 'include',
      cache: 'no-store',
      headers: {
        'Content-Type': 'application/json',
        ...csrfHeader(),
      },
      ...(body ? { body: JSON.stringify(body) } : {}),
    },
  );

  if (!response.ok) {
    const result = await response.json().catch(() => null);
    const detail = result?.detail;

    throw new Error(
      typeof detail === 'string'
        ? detail
        : typeof detail?.message === 'string'
          ? detail.message
          : `MFA request failed (HTTP ${response.status}).`
    );
  }

  return response.json() as Promise<T>;
}


export default function MfaQrEnrollment({
  mode = 'enroll',
  onComplete,
}: Props) {
  const [open, setOpen] = useState(false);
  const [setup, setSetup] = useState<EnrollmentStart | null>(null);
  const [code, setCode] = useState('');
  const [password, setPassword] = useState('');
  const [currentCode, setCurrentCode] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [completed, setCompleted] = useState(false);
  const [recoveryCodes, setRecoveryCodes] = useState<string[]>([]);
  const dialogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;

    dialogRef.current?.focus();

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape' && !busy) {
        closeModal();
      }
    }

    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [open, busy]);


function beginEnrollment() {
  if (busy) return;

  setOpen(true);
  setSetup(null);
  setCode('');
  setPassword('');
  setCurrentCode('');
  setError('');
  setCompleted(false);
  setRecoveryCodes([]);
}


async function prepareEnrollment() {
  if (busy) return;

  if (mode === 'replace' && !/^\d{6}$/.test(currentCode)) {
    setError('Enter a fresh six-digit code from your current authenticator.');
    return;
  }

  setBusy(true);
  setError('');

  try {
    const result = await postMfa<EnrollmentStart>(
      mode === 'replace' ? 'replace/start' : 'enroll/start',
      mode === 'replace'
        ? { current_code: currentCode }
        : { password: password || null },
    );

    if (!result.provisioning_uri || !result.qr_code_data_url) {
      throw new Error('Authenticator setup information is unavailable.');
    }

    setSetup(result);
    setPassword('');
    setCurrentCode('');
  } catch (err) {
    setError(
      err instanceof Error
        ? err.message
        : 'Could not prepare the authenticator.'
    );
  } finally {
    setBusy(false);
  }
}



  async function confirmEnrollment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!setup || busy || !/^\d{6}$/.test(code)) return;

    setBusy(true);
    setError('');

    try {
      const result = await postMfa<EnrollmentResult>(
        mode === 'replace' ? 'replace/confirm' : 'enroll/confirm',
        { code },
        );

      setRecoveryCodes(result.recovery_codes ?? []);
      setCode('');
      setCompleted(true);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Could not verify the authenticator code.'
      );
    } finally {
      setBusy(false);
    }
  }

  function closeModal() {
    if (busy) return;

    const wasCompleted = completed;

    setOpen(false);
    setSetup(null);
    setCode('');
    setPassword('');
    setCurrentCode('');
    setError('');
    setRecoveryCodes([]);
    setCompleted(false);

    if (wasCompleted) {
      if (onComplete) {
        onComplete();
      } else {
        window.location.assign('/login');
      }
    }
  }

  async function copyText(value: string) {
    try {
      await navigator.clipboard.writeText(value);
    } catch {
      setError('Copy failed. Select and copy the text manually.');
    }
  }

  const manualSecret = setup
    ? new URL(setup.provisioning_uri).searchParams.get('secret') ?? ''
    : '';


return (
  <>
    <button
      type="button"
      className="cf-mfa-setup-trigger"
      onClick={() => void beginEnrollment()}
      disabled={busy}
    >
      {mode === 'replace'
        ? 'Replace authenticator'
        : 'Set up authenticator app'}
    </button>

    {open && (
      <div className="cf-mfa-qr-overlay">
        <div
          className="cf-mfa-qr-dialog"
          role="dialog"
          aria-modal="true"
          aria-labelledby="cf-mfa-qr-title"
          tabIndex={-1}
          ref={dialogRef}
        >
          <div className="cf-mfa-qr-header">
            <span>CAREERFORGE / ACCOUNT SECURITY</span>
            <button
              type="button"
              aria-label="Close setup"
              disabled={busy}
              onClick={closeModal}
            >
              ×
            </button>
          </div>

          {completed ? (
            <div className="cf-mfa-qr-body">
              <h2 id="cf-mfa-qr-title">
                {mode === 'replace'
                  ? 'Authenticator replaced.'
                  : 'Authenticator connected.'}
              </h2>

              <p>
                {mode === 'replace'
                  ? 'Your new authenticator is now registered with CareerForge. Your previous authenticator can no longer be used.'
                  : 'Your authenticator app is now registered with CareerForge.'}
              </p>

              {recoveryCodes.length > 0 && (
                <section className="cf-mfa-recovery">
                  <h3>Save your recovery codes</h3>

                  <p>
                    Store these codes somewhere secure. Each recovery
                    code is intended for emergency account access.
                    They may not be shown again.
                  </p>

                  <div className="cf-mfa-recovery-list">
                    {recoveryCodes.map((item, index) => (
                      <code key={index}>{item}</code>
                    ))}
                  </div>

                  <button
                    type="button"
                    onClick={() =>
                      void copyText(recoveryCodes.join('\n'))
                    }
                  >
                    Copy recovery codes
                  </button>
                </section>
              )}

              <button
                type="button"
                className="cf-mfa-qr-primary"
                onClick={closeModal}
              >
                {recoveryCodes.length > 0
                  ? "I've saved my recovery codes"
                  : mode === 'replace'
                    ? 'Finish replacement'
                    : 'Finish setup'}
              </button>
            </div>
          ) : (
            <div className="cf-mfa-qr-body">
              <h2 id="cf-mfa-qr-title">
                {mode === 'replace'
                  ? 'Replace your authenticator.'
                  : 'Connect your authenticator.'}
              </h2>

              <p>
                {mode === 'replace'
                  ? 'Connect a new authenticator app to replace your current one.'
                  : 'Connect an authenticator app to secure your CareerForge account.'}
              </p>

              {!setup && (
                <div className="cf-mfa-confirm-form">
                  {mode === 'replace' ? (
                    <>
                      <label htmlFor="cf-mfa-current-code">
                        Current authenticator code
                      </label>

                      <input
                        id="cf-mfa-current-code"
                        type="text"
                        inputMode="numeric"
                        autoComplete="one-time-code"
                        pattern="[0-9]{6}"
                        maxLength={6}
                        placeholder="000000"
                        value={currentCode}
                        disabled={busy}
                        onChange={(event) =>
                          setCurrentCode(
                            event.target.value
                              .replace(/\D/g, '')
                              .slice(0, 6)
                          )
                        }
                      />

                      <p>
                        Enter a fresh code from your currently connected
                        authenticator. Your existing authenticator will
                        remain active until replacement is completed.
                      </p>
                    </>
                  ) : (
                    <>
                      <label htmlFor="cf-mfa-setup-password">
                        Confirm your account password
                      </label>

                      <input
                        id="cf-mfa-setup-password"
                        type="password"
                        autoComplete="current-password"
                        value={password}
                        onChange={(event) =>
                          setPassword(event.target.value)
                        }
                        placeholder="Account password"
                        disabled={busy}
                      />

                      <p>
                        Google-only administrator accounts require the
                        existing Google reauthentication process.
                      </p>
                    </>
                  )}

                  {error && <p role="alert">{error}</p>}

                  <button
                    type="button"
                    className="cf-mfa-qr-primary"
                    onClick={() => void prepareEnrollment()}
                    disabled={
                      busy ||
                      (mode === 'replace' && currentCode.length !== 6)
                    }
                  >
                    {busy
                      ? 'Preparing...'
                      : mode === 'replace'
                        ? 'Generate replacement QR code'
                        : 'Generate setup QR code'}
                  </button>
                </div>
              )}

              {setup && (
                <>
                  <p>
                    Scan the QR code using Google Authenticator,
                    Microsoft Authenticator, or another compatible app.
                  </p>

                  <div className="cf-mfa-qr-image">
                    <img
                      src={setup.qr_code_data_url}
                      alt="CareerForge authenticator setup QR code"
                      width="224"
                      height="224"
                    />
                  </div>

                  <details className="cf-mfa-manual">
                    <summary>
                      Can't scan? Enter the key manually
                    </summary>

                    <div className="cf-mfa-manual-value">
                      <code>{manualSecret}</code>

                      <button
                        type="button"
                        onClick={() => void copyText(manualSecret)}
                      >
                        Copy
                      </button>
                    </div>

                    <p>
                      Account type: Time-based (TOTP)
                      <br />
                      Issuer: CareerForge
                    </p>
                  </details>

                  <form
                    className="cf-mfa-confirm-form"
                    onSubmit={confirmEnrollment}
                  >
                    <label htmlFor="cf-enrollment-code">
                      {mode === 'replace'
                        ? 'Enter the code from your new authenticator'
                        : 'Enter the six-digit code to finish setup'}
                    </label>

                    <input
                      id="cf-enrollment-code"
                      type="text"
                      inputMode="numeric"
                      pattern="[0-9]{6}"
                      autoComplete="one-time-code"
                      maxLength={6}
                      placeholder="000000"
                      value={code}
                      onChange={(event) =>
                        setCode(
                          event.target.value
                            .replace(/\D/g, '')
                            .slice(0, 6)
                        )
                      }
                      required
                    />

                    {error && <p role="alert">{error}</p>}

                    <button
                      type="submit"
                      className="cf-mfa-qr-primary"
                      disabled={busy || code.length !== 6}
                    >
                      {busy
                        ? 'Verifying...'
                        : mode === 'replace'
                          ? 'Verify and replace'
                          : 'Verify and enable'}
                    </button>
                  </form>
                </>
              )}
            </div>
          )}

          {completed && error && (
            <p className="cf-mfa-qr-error" role="alert">
              {error}
            </p>
          )}

          {!completed && !busy && (
            <button
              type="button"
              className="cf-mfa-qr-cancel"
              onClick={closeModal}
            >
              {mode === 'replace'
                ? 'Cancel replacement'
                : 'Cancel setup'}
            </button>
          )}
        </div>
      </div>
    )}
  </>
);

}
