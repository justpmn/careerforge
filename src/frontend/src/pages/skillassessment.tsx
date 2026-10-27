
import { useEffect, useState } from 'react';

import { onboardingApi } from '../lib/onboarding';
import type { Career } from '../lib/onboarding';

export default function SkillsAssessmentPage() {
  const [careers, setCareers] = useState<Career[]>([]);
  const [selectedCareer, setSelectedCareer] = useState('');
  const [savedCareer, setSavedCareer] = useState('');
  const [search, setSearch] = useState('');

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState('');

  useEffect(() => {
    let active = true;

    Promise.all([
      onboardingApi.careers(),
      onboardingApi.selectedCareer(),
    ])
      .then(([available, selection]) => {
        if (!active) return;

        setCareers(available);
        setSelectedCareer(selection.career_key ?? '');
        setSavedCareer(selection.career_key ?? '');
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

  const filtered = careers.filter((career) => {
    const query = search.toLowerCase().trim();

    return (
      career.name.toLowerCase().includes(query) ||
      career.career_key.toLowerCase().includes(query)
    );
  });

  const selected = careers.find(
    (career) => career.career_key === selectedCareer
  );

  async function saveCareer() {
    if (!selectedCareer || saving) return;

    setSaving(true);
    setError(null);
    setMessage('');

    try {
      const result = await onboardingApi.saveCareer(selectedCareer);
      setSavedCareer(result.career_key ?? '');
      setMessage('Your target career has been saved.');
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

  return (
    <section className="cf-dashboard">
      <header className="cf-dashboard-header">
        <div>
          <span className="stage-marker">SKILLS ASSESSMENT</span>
          <h1>Understand your abilities.</h1>
          <p>
            Choose a career, build your skill profile,
            and identify the competencies you need to develop.
          </p>
        </div>
      </header>

      <div className="cf-assessment-sections">
        <article className="cf-dashboard-card">
          <span className="cf-eyebrow">01 / CAREER DIRECTION</span>
          <h2>Choose your target career</h2>
          <p>
            Select the career you'd like to work toward.
            Your choice will guide future assessments.
          </p>

          <label className="cf-input-label" htmlFor="career-search">
            Search careers
          </label>

          <input
            id="career-search"
            type="search"
            className="cf-career-search"
            placeholder="e.g. Backend Developer"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />

          {loading ? (
            <p>Loading careers...</p>
          ) : careers.length === 0 ? (
            <p>
              No careers are available. Check the
              onboarding careers API and database records.
            </p>
          ) : (
            <div className="cf-career-options">
              {filtered.map((career) => (
                <button
                  key={career.career_key}
                  type="button"
                  aria-pressed={
                    selectedCareer === career.career_key
                  }
                  className={`cf-career-option ${
                    selectedCareer === career.career_key
                      ? 'cf-career-selected'
                      : ''
                  }`}
                  onClick={() => {
                    setSelectedCareer(career.career_key);
                    setMessage('');
                    setError(null);
                  }}
                >
                  <strong>{career.name}</strong>

                  {career.description && (
                    <span>{career.description}</span>
                  )}
                </button>
              ))}

              {filtered.length === 0 && (
                <p>No matching careers found.</p>
              )}
            </div>
          )}

          {selected && (
            <p className="cf-selected-career">
              Selected: <strong>{selected.name}</strong>
            </p>
          )}

          {error && (
            <p role="alert" className="cf-error">{error}</p>
          )}

          {message && (
            <p role="status" className="cf-success">{message}</p>
          )}

          <div className="cf-card-footer">
            <span className="cf-muted">
              {savedCareer
                ? 'You can change your career later.'
                : 'Select a target career to begin.'}
            </span>

            <button
              type="button"
              className="cf-button cf-button-primary"
              onClick={saveCareer}
              disabled={
                !selectedCareer ||
                loading ||
                saving ||
                selectedCareer === savedCareer
              }
            >
              {saving ? 'Saving...' : 'Save target career'}
            </button>
          </div>
        </article>

        <article className="cf-dashboard-card">
          <span className="cf-eyebrow">02 / CURRENT SKILLS</span>
          <h2>Build your skill profile</h2>
          <p>
            Here you'll select the skills you already know
            and provide information about your experience.
          </p>
          <span className="cf-feature-status">
            Skill selection will be connected next.
          </span>
        </article>

        <article className="cf-dashboard-card">
          <span className="cf-eyebrow">03 / COMPETENCY GAPS</span>
          <h2>Assess your career readiness</h2>
          <p>
            Compare your existing skills against the
            requirements of your selected career and
            discover which competencies need attention.
          </p>
          <span className="cf-feature-status">
            Competency analysis will be connected next.
          </span>
        </article>
      </div>
    </section>
  );
}
