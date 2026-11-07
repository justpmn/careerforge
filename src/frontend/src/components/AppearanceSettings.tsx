
import { useAppearance } from '../context/appearancecontext';
import '../appearance-settings.css';

export default function AppearanceSettings() {
  const {
    appearance,
    setAppearance,
    cozyTheme,
    setCozyTheme,
  } = useAppearance();

  return (
    <section className="cf-appearance-settings">
      <div className="cf-appearance-heading">
        <div>
          <span className="cf-appearance-eyebrow">PERSONALIZATION</span>
          <h2>Appearance</h2>
          <p>Make CareerForge feel like your workspace.</p>
        </div>
      </div>

      <div
        className="cf-appearance-options"
        role="group"
        aria-label="Choose appearance"
      >
        <button
          type="button"
          className={`cf-appearance-option ${
            appearance === 'cozy' ? 'is-selected' : ''
          }`}
          aria-pressed={appearance === 'cozy'}
          onClick={() => setAppearance('cozy')}
        >
          <span className="cf-appearance-preview is-cozy" aria-hidden="true">
            <span className="cf-appearance-preview-sidebar" />
            <span className="cf-appearance-preview-content">
              <span />
              <span />
              <span />
            </span>
          </span>

          <span className="cf-appearance-option-info">
            <strong>Cozy</strong>
            <small>Warm, familiar, minimal.</small>
          </span>

          <span className="cf-appearance-check" aria-hidden="true">
            {appearance === 'cozy' ? '✓' : ''}
          </span>
        </button>

        <button
          type="button"
          className={`cf-appearance-option ${
            appearance === 'neon' ? 'is-selected' : ''
          }`}
          aria-pressed={appearance === 'neon'}
          onClick={() => setAppearance('neon')}
        >
          <span className="cf-appearance-preview is-neon" aria-hidden="true">
            <span className="cf-appearance-preview-sidebar" />
            <span className="cf-appearance-preview-content">
              <span />
              <span />
              <span />
            </span>
          </span>

          <span className="cf-appearance-option-info">
            <strong>Neon</strong>
            <small>Always dark.</small>
          </span>

          <span className="cf-appearance-check" aria-hidden="true">
            {appearance === 'neon' ? '✓' : ''}
          </span>
        </button>
      </div>

      {appearance === 'cozy' && (
        <div className="cf-cozy-preferences">
          <div>
            <strong>Colour scheme</strong>
            <p>Choose how Cozy looks.</p>
          </div>

          <div
            className="cf-cozy-mode-switch"
            role="group"
            aria-label="Cozy colour scheme"
          >
            <button
              type="button"
              aria-pressed={cozyTheme === 'light'}
              className={cozyTheme === 'light' ? 'is-active' : ''}
              onClick={() => setCozyTheme('light')}
            >
              ☀ Light
            </button>

            <button
              type="button"
              aria-pressed={cozyTheme === 'dark'}
              className={cozyTheme === 'dark' ? 'is-active' : ''}
              onClick={() => setCozyTheme('dark')}
            >
              ☾ Dark
            </button>
          </div>
        </div>
      )}

      {appearance === 'neon' && (
        <p className="cf-neon-notice">
          Neon uses its own dark colour palette.
        </p>
      )}
    </section>
  );
}
