
import { useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { FiLock, FiX } from 'react-icons/fi';

type Props = {
  open: boolean;
  title: string;
  description: string;
  busy: boolean;
  error: string;
  onClose: () => void;
  onConfirm: (code: string) => Promise<void>;
};

export default function AdminTotpModal({
  open,
  title,
  description,
  busy,
  error,
  onClose,
  onConfirm,
}: Props) {
  const [code, setCode] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!open) {
      setCode('');
      return;
    }

    inputRef.current?.focus();

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape' && !busy) {
        onClose();
      }

      if (event.key === 'Tab') {
        const dialog = inputRef.current?.closest('[role="dialog"]');
        const controls = dialog?.querySelectorAll<HTMLElement>(
          'button:not(:disabled), input:not(:disabled)'
        );

        if (!controls?.length) return;

        const first = controls[0];
        const last = controls[controls.length - 1];

        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first.focus();
        }
      }
    }

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [open, busy, onClose]);

  if (!open) return null;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!/^\d{6}$/.test(code) || busy) return;

    try {
      await onConfirm(code);
    } finally {
      setCode('');
    }
  }

  return (
    <div className="cf-totp-overlay">
      <section
        className="cf-totp-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="cf-totp-title"
        aria-describedby="cf-totp-description"
      >
        <div className="cf-totp-top">
          <span className="cf-totp-icon">
            <FiLock size={19} />
          </span>

          <button
            type="button"
            className="cf-totp-close"
            aria-label="Close confirmation"
            onClick={onClose}
            disabled={busy}
          >
            <FiX />
          </button>
        </div>

        <h2 id="cf-totp-title">{title}</h2>
        <p id="cf-totp-description">{description}</p>

        <form onSubmit={submit}>
          <label htmlFor="cf-totp-code">
            Authenticator code
          </label>

          <input
            id="cf-totp-code"
            ref={inputRef}
            type="text"
            inputMode="numeric"
            autoComplete="one-time-code"
            pattern="[0-9]{6}"
            maxLength={6}
            required
            value={code}
            disabled={busy}
            placeholder="000000"
            onChange={(event) =>
              setCode(
                event.target.value.replace(/\D/g, '').slice(0, 6)
              )
            }
          />

          <small>
            Enter the current code from your authenticator app.
            Each code can only be used once.
          </small>

          {error && (
            <p className="cf-totp-error" role="alert">
              {error}
            </p>
          )}

          <div className="cf-totp-actions">
            <button
              type="button"
              className="cf-totp-cancel"
              onClick={onClose}
              disabled={busy}
            >
              Cancel
            </button>

            <button
              type="submit"
              className="cf-totp-confirm"
              disabled={busy || code.length !== 6}
            >
              {busy ? 'Verifying...' : 'Verify & confirm'}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}
