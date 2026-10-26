import { oauthStartPath } from '../lib/auth';

type Provider = 'github' | 'google';

export default function OAuthButtons({ onError }: { onError: (message: string) => void }) {
  function start(provider: Provider) {
    const path = oauthStartPath(provider);
    if (!path) {
      onError(`${provider === 'github' ? 'GitHub' : 'Google'} sign-in is ready in the interface, but its FastAPI OAuth endpoint has not been configured yet.`);
      return;
    }
    window.location.assign(path);
  }

  return (
    <div className="social-buttons">
      <button type="button" className="social-button" onClick={() => start('github')}>
        <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 .8a11.2 11.2 0 0 0-3.54 21.83c.56.1.77-.24.77-.54v-2.1c-3.13.68-3.8-1.33-3.8-1.33-.5-1.28-1.24-1.62-1.24-1.62-1.02-.69.08-.68.08-.68 1.14.08 1.73 1.17 1.73 1.17 1.02 1.72 2.66 1.22 3.3.93.1-.74.4-1.23.72-1.52-2.5-.29-5.13-1.25-5.13-5.55 0-1.23.44-2.23 1.16-3.02-.12-.29-.5-1.43.11-2.98 0 0 .95-.3 3.09 1.15a10.8 10.8 0 0 1 5.62 0c2.14-1.45 3.08-1.15 3.08-1.15.62 1.55.23 2.69.12 2.98.72.79 1.15 1.8 1.15 3.02 0 4.31-2.63 5.26-5.14 5.54.42.37.79 1.08.79 2.18v3.24c0 .3.2.65.78.54A11.2 11.2 0 0 0 12 .8Z" /></svg>
        GitHub
      </button>
      <button type="button" className="social-button" onClick={() => start('google')}>
        <svg viewBox="0 0 24 24" aria-hidden="true"><path fill="#4285F4" d="M21.6 12.23c0-.71-.06-1.39-.18-2.05H12v3.88h5.38a4.6 4.6 0 0 1-2 3.02v2.52h3.24c1.89-1.74 2.98-4.31 2.98-7.37z"/><path fill="#34A853" d="M12 22c2.7 0 4.96-.9 6.62-2.4l-3.24-2.52c-.9.6-2.05.97-3.38.97-2.6 0-4.82-1.76-5.61-4.13H3.05v2.59A10 10 0 0 0 12 22z"/><path fill="#FBBC05" d="M6.39 13.92a6.01 6.01 0 0 1 0-3.84V7.49H3.05a10 10 0 0 0 0 9.02l3.34-2.59z"/><path fill="#EA4335" d="M12 5.95c1.43 0 2.72.49 3.73 1.46l2.8-2.8A9.56 9.56 0 0 0 12 2a10 10 0 0 0-8.95 5.49l3.34 2.59c.79-2.37 3.01-4.13 5.61-4.13z"/></svg>
        Google
      </button>
    </div>
  );
}
