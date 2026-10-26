
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { useAuth } from '../context/AuthContext';
import { authApi } from '../lib/auth';

export default function OnboardingPage() {
  const navigate = useNavigate();
  const { refresh } = useAuth();

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const completeOnboarding = async () => {
    setSaving(true);
    setError(null);

    try {
      await authApi.completeOnboarding();

      const user = await refresh();

      if (!user?.onboarding_completed) {
        throw new Error(
          'Could not verify onboarding completion.'
        );
      }

      navigate('/dashboard', { replace: true });
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Something went wrong. Please try again.'
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="workspace-panel">
      <span className="stage-marker">
        01 / GETTING STARTED
      </span>

      <h1>Let's find your direction.</h1>

      <p>
        Welcome to CareerForge! Your account is ready.
        Soon, you'll be able to choose your target career,
        identify your existing skills, and create a
        personalized learning roadmap.
      </p>

      <div className="placeholder-list">
        <span>Target career</span>
        <span>Skills & experience</span>
        <span>Learning goals</span>
      </div>

      <p className="small-note">
        This is a temporary onboarding completion step.
        The full questionnaire will be implemented later.
      </p>

      {error && (
        <p role="alert" className="mt-4 text-red-500">
          {error}
        </p>
      )}

      <button
        type="button"
        onClick={completeOnboarding}
        disabled={saving}
        className="mt-6 rounded-lg bg-amber-700 px-5 py-3
          text-sm font-semibold text-white transition
          hover:bg-amber-800 disabled:cursor-not-allowed
          disabled:opacity-60"
      >
        {saving ? 'Saving...' : 'Finish setup'}
      </button>
    </section>
  );
}
