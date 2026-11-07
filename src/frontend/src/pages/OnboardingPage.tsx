import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { useAuth } from '../context/AuthContext';
import { authApi } from '../lib/auth';
import { onboardingApi } from '../lib/onboarding';
import type { Career } from '../lib/onboarding';


export default function OnboardingPage() {
  const navigate = useNavigate();
  const {user, refresh } = useAuth();

  const [careers, setCareers] = useState<Career[]>([]);
  const [search, setSearch] = useState('');
  const [selectedCareer, setSelectedCareer] = useState('');
  const [persistedCareer, setPersistedCareer] = useState('');

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [finishing, setFinishing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const tourDismissalKey = (userId: number | string) =>
  `careerforge:tour-dismissed:${userId}`;
  

  useEffect(() => {
    let active = true;

    Promise.all([
      onboardingApi.careers(),
      onboardingApi.selectedCareer(),
    ])
      .then(([available, selection]) => {
        if (!active) return;

        setCareers(available);

        const current = selection.career_key ?? '';
        setSelectedCareer(current);
        setPersistedCareer(current);
      })
      .catch((err) => {
        if (active) {
          setError(
            err instanceof Error
              ? err.message
              : 'Could not load careers.'
          );
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  const filteredCareers = careers.filter((career) =>
    career.name.toLowerCase().includes(search.toLowerCase()) ||
    career.career_key.toLowerCase().includes(search.toLowerCase())
  );

  const careerSaved =
    selectedCareer !== '' &&
    selectedCareer === persistedCareer;

  async function saveCareer() {
    if (!selectedCareer || saving) return;

    setSaving(true);
    setError(null);

    try {
      const result = await onboardingApi.saveCareer(
        selectedCareer
      );

      setPersistedCareer(result.career_key ?? '');
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Could not save your career.'
      );
    } finally {
      setSaving(false);
    }
  }

  function skipSetup() {
  if (user) {
    localStorage.setItem(
      tourDismissalKey(user.id),
      '1'
    );
  }

  navigate('/dashboard', { replace: true });
}
  async function finishSetup() {
    if (!careerSaved || finishing) return;

    setFinishing(true);
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
          : 'Could not complete setup.'
      );
    } finally {
      setFinishing(false);
    }
  }

  return (
    <section className="workspace-panel">
      <span className="stage-marker">
        CAREER DIRECTION
      </span>

      <h1>Where do you want to go?</h1>

      <p>
        Choose the tech career you want to pursue.
        We'll use this to personalize your competency
        assessment and learning roadmap.
      </p>

      <div className="mt-6">
        <label
          htmlFor="career-search"
          className="mb-2 block text-sm font-medium"
        >
          Find a career
        </label>

        <input
          id="career-search"
          type="search"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search careers..."
          className="w-full rounded-xl border border-current/20
            bg-transparent p-3 outline-offset-2"
        />
      </div>

      {loading ? (
        <p className="mt-6">Loading careers...</p>
      ) : careers.length === 0 ? (
        <p className="mt-6">
          No careers are available.
          Check the database career records.
        </p>
      ) : (
        <div className="mt-5 grid gap-3 sm:grid-cols-2">
          {filteredCareers.map((career) => {
            const selected =
              selectedCareer === career.career_key;

            return (
              <button
                key={career.career_key}
                type="button"
                aria-pressed={selected}
                onClick={() => {
                  setSelectedCareer(career.career_key);
                  setError(null);
                }}
                className={
                  `rounded-xl border p-4 text-left transition ` +
                  (selected
                    ? 'border-amber-600 bg-amber-500/10'
                    : 'border-current/20 bg-transparent hover:border-amber-600/60')
                }
              >
                <span className="block font-semibold">
                  {career.name}
                </span>

                {career.description && (
                  <span className="mt-2 block text-sm opacity-70">
                    {career.description}
                  </span>
                )}
              </button>
            );
          })}

          {filteredCareers.length === 0 && (
            <p>No careers match your search.</p>
          )}
        </div>
      )}

      {error && (
        <p role="alert" className="mt-4 text-red-500">
          {error}
        </p>
      )}

      {careerSaved && (
        <p role="status" className="mt-4 text-sm">
          Your career direction has been saved.
        </p>
      )}

      <div className="mt-6 flex flex-wrap gap-3">
        <button
          type="button"
          onClick={saveCareer}
          disabled={
            !selectedCareer ||
            loading ||
            saving ||
            careerSaved
          }
          className="rounded-lg bg-amber-700 px-5 py-3
            text-sm font-semibold text-white
            hover:bg-amber-800 disabled:opacity-50"
        >
          {saving ? 'Saving...' : 'Save career'}
        </button>
        <button
        type="button"
        onClick={skipSetup}
        disabled={finishing}
        className="rounded-lg border border-current/20
          px-5 py-3 text-sm font-medium
          hover:border-amber-600/60"
      >
        Skip for now
      </button>

        <button
          type="button"
          onClick={finishSetup}
          disabled={!careerSaved || finishing}
          className="rounded-lg border border-current/30
            px-5 py-3 text-sm font-semibold
            disabled:opacity-50"
        >
          {finishing
            ? 'Finishing...'
            : 'Continue to dashboard'}
        </button>
      </div>

      <p className="small-note mt-5">
        Temporary setup: skills and learning preferences
        will be added in the next stages.
      </p>
    </section>
  );
}
