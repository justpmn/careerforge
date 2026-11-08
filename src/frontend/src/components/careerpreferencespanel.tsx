import { useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useCareerPreferences } from '../hooks/useCareerPreferences';
import type { CareerPreference } from '../lib/careerpreferences';

function careerName(key: string): string {
  return key
    .replace(/[_-]/g, ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export default function CareerPreferencesPanel() {
  const { user } = useAuth();

  const {
    preferences,
    loading,
    savingKey,
    error,
    choose,
    resetAll,
  } = useCareerPreferences(
    user?.id != null ? Number(user.id) : undefined
  );

  const preferredRef = useRef<HTMLDivElement>(null);
  const avoidedRef = useRef<HTMLDivElement>(null);
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [confirmReset, setConfirmReset] = useState(false);
  const preferenceCount = preferences.preferred.length + preferences.avoid.length;

    async function handleResetAll() {
    const success = await resetAll();

    if (success) {
        setConfirmReset(false);
    }
    }

  const groups = [
    {
      title: 'Preferred careers',
      keys: preferences.preferred,
      preference: 'preferred' as CareerPreference,
      ref: preferredRef,
    },
    {
      title: 'Avoided careers',
      keys: preferences.avoid,
      preference: 'avoid' as CareerPreference,
      ref: avoidedRef,
    },
  ];

  function scroll(
    element: HTMLDivElement | null,
    direction: number
  ) {
    if (!element) return;

    element.scrollBy({
      left: element.clientWidth * direction,
      behavior: 'smooth',
    });
  }

  function careerCard(
    key: string,
    preference: CareerPreference
  ) {
    const opposite =
      preference === 'preferred' ? 'avoid' : 'preferred';

    return (
      <div className="cf-pref-carousel-card" key={key}>
        <strong>{careerName(key)}</strong>

        <div className="cf-pref-actions">
          <button
            type="button"
            className="cf-pref-btn"
            disabled={savingKey !== null}
            onClick={() => void choose(key, opposite)}
          >
            {opposite === 'preferred'
              ? 'Prefer instead'
              : 'Avoid instead'}
          </button>

          <button
            type="button"
            className="cf-pref-btn"
            disabled={savingKey !== null}
            onClick={() => void choose(key, preference)}
          >
            {savingKey === key ? 'Saving...' : 'Remove'}
          </button>
        </div>
      </div>
    );
  }

  return (
    <article className="cf-dashboard-card cf-profile-wide">
      <div className="cf-pref-section-heading">
        <h2>Career preferences</h2>

        <button
          type="button"
          className="cf-pref-text-link"
          disabled={loading}
          onClick={() => dialogRef.current?.showModal()}
        >
          View all preferences
        </button>
      </div>

      <p className="cf-profile-subtle">
        Manage which careers CareerForge should prioritize
        or avoid when generating recommendations.
      </p>

      {error && (
        <p className="cf-cv-error" role="alert">
          {error}
        </p>
      )}

      {loading ? (
        <p className="cf-profile-subtle" role="status">
          Loading career preferences...
        </p>
      ) : (
        <div className="cf-pref-carousel-groups">
          {groups.map((group) => (
            <section
              key={group.preference}
              className="cf-pref-carousel-section"
            >
              <div className="cf-pref-section-heading">
                <h3>
                  {group.title}{' '}
                  <span className="cf-profile-pref-count">
                    {group.keys.length}
                  </span>
                </h3>

                <div className="cf-pref-navigation">
                  <button
                    type="button"
                    aria-label={`Scroll ${group.title} left`}
                    disabled={group.keys.length <= 3}
                    onClick={() => scroll(group.ref.current, -1)}
                  >
                    ‹
                  </button>

                  <button
                    type="button"
                    aria-label={`Scroll ${group.title} right`}
                    disabled={group.keys.length <= 3}
                    onClick={() => scroll(group.ref.current, 1)}
                  >
                    ›
                  </button>
                </div>
              </div>

              {group.keys.length === 0 ? (
                <p className="cf-profile-subtle">
                  No careers selected.
                </p>
              ) : (
                <div
                  ref={group.ref}
                  className="cf-pref-carousel-track"
                  tabIndex={0}
                  aria-label={group.title}
                >
                  {group.keys.map((key) =>
                    careerCard(key, group.preference)
                  )}
                </div>
              )}
            </section>
          ))}
        </div>
      )}

      <Link to="/cv" className="cf-profile-action">
        View career recommendations
      </Link>

      <dialog
        ref={dialogRef}
        className="cf-dashboard-card cf-pref-dialog"
      >
        <div className="cf-pref-dialog-header">
            <h2>All career preferences</h2>

            <div className="cf-pref-dialog-actions">
                <button
                type="button"
                className="cf-pref-reset-link"
                disabled={
                    preferenceCount === 0 ||
                    loading ||
                    savingKey !== null
                }
                onClick={() => setConfirmReset(true)}
                >
                Reset all preferences
                </button>

                <button
                type="button"
                className="cf-pref-text-link"
                onClick={() => {
                    setConfirmReset(false);
                    dialogRef.current?.close();
                }}
                >
                Close
                </button>
            </div>
        </div>

        {confirmReset && (
        <div className="cf-pref-reset-confirm">
            <p>
            Remove all {preferenceCount} saved career preferences?
            This will return your preferred and avoided careers
            to neutral.
            </p>

            <div className="cf-pref-actions">
            <button
                type="button"
                className="cf-pref-btn"
                disabled={savingKey !== null}
                onClick={() => void handleResetAll()}
            >
                {savingKey === '__reset__'
                ? 'Resetting...'
                : 'Confirm reset'}
            </button>

            <button
                type="button"
                className="cf-pref-btn"
                disabled={savingKey !== null}
                onClick={() => setConfirmReset(false)}
            >
                Cancel
            </button>
            </div>
        </div>
        )}

        <p className="cf-profile-subtle">
          Change or remove any saved preference.
        </p>

        {groups.map((group) => (
          <section
            key={group.preference}
            className="cf-pref-dialog-group"
          >
            <h3>
              {group.title} ({group.keys.length})
            </h3>

            {group.keys.length === 0 ? (
              <p className="cf-profile-subtle">
                None selected.
              </p>
            ) : (
              <div className="cf-pref-dialog-grid">
                {group.keys.map((key) =>
                  careerCard(key, group.preference)
                )}
              </div>
            )}
          </section>
        ))}
      </dialog>
    </article>
  );
}