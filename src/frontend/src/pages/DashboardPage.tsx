
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { useAuth } from '../context/AuthContext';
import { authApi } from '../lib/auth';
import { onboardingApi } from '../lib/onboarding';
import { useAppearance } from '../context/appearancecontext';
import NeonGreeting from '../components/neongreeting';

const tourSteps = [
  {
    target: 'target',
    title: 'Your target career',
    description:
      'Your selected career appears here. You can choose or change it in Skills Assessment.',
  },
  {
    target: 'recommendations',
    title: 'Career recommendations',
    description:
      'CareerForge will recommend suitable roles based on your skills and profile.',
  },
  {
    target: 'gaps',
    title: 'Skill gap analysis',
    description:
      'See which skills you have and which ones your chosen career requires.',
  },
  {
    target: 'roadmap',
    title: 'Learning roadmap',
    description:
      'Follow your learning journey through skills, milestones, and resources.',
  },
  {
    target: 'mentor',
    title: 'Your AI mentor',
    description:
      'Start conversations to get career guidance and discuss your progress.',
  },
] as const;
const tourDismissalKey = (userId: number | string) =>
  `careerforge:tour-dismissed:${userId}`;

export default function DashboardPage() {
  const { user, refresh } = useAuth();

  const [targetRole, setTargetRole] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [roleError, setRoleError] = useState(false);

  const [tourStep, setTourStep] = useState<number | null>(null);
  const [tourSaving, setTourSaving] = useState(false);
  const [tourError, setTourError] = useState('');

  const rawName = user?.name?.trim().split(/\s+/)[0] || 'there';
  const firstName =
    rawName.charAt(0).toUpperCase() + rawName.slice(1);

  useEffect(() => {
    let active = true;

    Promise.all([
      onboardingApi.selectedCareer(),
      onboardingApi.careers(),
    ])
      .then(([selection, careers]) => {
        if (!active) return;

        const match = careers.find(
          (career) => career.career_key === selection.career_key
        );

        setTargetRole(
          match?.name ?? selection.career_key ?? null
        );
      })
      .catch(() => {
        if (active) setRoleError(true);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

    useEffect(() => {
    if (!user || user.onboarding_completed) return;

    const dismissed = localStorage.getItem(
      tourDismissalKey(user.id)
    );

    if (dismissed !== '1') {
      setTourStep(0);
    }
  }, [user?.id, user?.onboarding_completed]);

  useEffect(() => {
    if (tourStep === null) return;

    const target = tourSteps[tourStep].target;

    document
      .querySelector(`[data-tour="${target}"]`)
      ?.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
      });
  }, [tourStep]);

  function skipTour() {
  if (user) {
    localStorage.setItem(
      tourDismissalKey(user.id),
      '1'
    );
  }

  setTourError('');
  setTourStep(null);
}

  async function finishTour() {
    if (tourSaving) return;

    setTourSaving(true);
    setTourError('');

    try {
      if (!user?.onboarding_completed) {
        await authApi.completeOnboarding();

        const updated = await refresh();

        if (!updated?.onboarding_completed) {
          throw new Error('Could not save tutorial completion.');
        }
      }

      setTourStep(null);
    } catch (error) {
      setTourError(
        error instanceof Error
          ? error.message
          : 'Could not finish the tutorial.'
      );
    } finally {
      setTourSaving(false);
    }
  }

  const currentTour =
    tourStep === null ? null : tourSteps[tourStep];
  const { appearance } = useAppearance();
  
    return (
      <section className="cf-home">
        <header className="cf-home-header">
          <div>
            {appearance === 'neon' ? (
              <NeonGreeting />
            ) : (
              <h1 className="cf-home-welcome">
                Welcome back,{' '}
                <span className="cf-home-name">{firstName}.</span>
              </h1>
            )}
          </div>

          <button
            className="cf-home-tour-link"
            type="button"
            onClick={() => {
              setTourError('');
              setTourStep(0);
            }}
          >
            Take a tour
          </button>
        </header>

        <div
          className="cf-home-target"
          data-tour="target"
          data-tour-active={currentTour?.target === 'target'}
        >
          <div>
            <h2>
              {loading
                ? 'Loading...'
                : roleError
                  ? 'Unable to load target role'
                  : targetRole ?? 'Not selected yet'}
            </h2>
            <p>
              {targetRole
                ? 'Your current career direction'
                : 'Choose a career in Skills Assessment'}
            </p>
          </div>

          <Link to="/skills-assessment" className="cf-home-link">
            {targetRole ? 'Manage role' : 'Choose a role'}
            <span aria-hidden="true">→</span>
          </Link>
        </div>

        <div className="cf-home-grid">
          <article
            className="cf-home-card"
            data-tour="recommendations"
            data-tour-active={
              currentTour?.target === 'recommendations'
            }
          >
            <div className="cf-home-card-heading">
              <h2>Career recommendations</h2>
              <span className="cf-home-index"></span>
            </div>

            <p className="cf-home-empty">
              Your career matches will appear after
              your profile has been analyzed.
            </p>

            <Link to="/skills-assessment" className="cf-home-link">
              Explore careers <span aria-hidden="true">→</span>
            </Link>
          </article>

          <article
            className="cf-home-card"
            data-tour="gaps"
            data-tour-active={currentTour?.target === 'gaps'}
          >
            <div className="cf-home-card-heading">
              <h2>Skill gap summary</h2>
              <span className="cf-home-index"></span>
            </div>

            <p className="cf-home-empty">
              No assessment results yet.
              Complete an assessment to view your gaps.
            </p>

            <Link to="/skills-assessment" className="cf-home-link">
              Skills Assessment <span aria-hidden="true">→</span>
            </Link>
          </article>
        </div>

        <div className="cf-home-bottom">
          <article
            className="cf-home-card cf-home-horizontal"
            data-tour="roadmap"
            data-tour-active={currentTour?.target === 'roadmap'}
          >
            <div>
              <h2>Learning roadmap</h2>
              <p>Your learning milestones and next steps.</p>
            </div>

            <Link to="/roadmap" className="cf-home-link">
              View roadmap <span aria-hidden="true">→</span>
            </Link>
          </article>

          <article
            className="cf-home-card cf-home-horizontal"
            data-tour="mentor"
            data-tour-active={currentTour?.target === 'mentor'}
          >
            <div>
              <h2>AI Mentor</h2>
              <p>Ask questions about your career journey.</p>
            </div>

            <Link to="/mentor" className="cf-home-primary">
              Start a conversation
            </Link>
          </article>
        </div>

        {currentTour && (
          <aside
            className="cf-home-tour  cf-tour-popover"
            role="dialog"
            aria-modal="false"
            aria-labelledby="tour-title"
          >
            <span className="cf-home-label">
              QUICK TOUR / {tourStep! + 1} OF {tourSteps.length}
            </span>

            <h3 id="tour-title">{currentTour.title}</h3>
            <p>{currentTour.description}</p>

            {tourError && (
              <p role="alert" className="cf-home-error">
                {tourError}
              </p>
            )}

            <div className="cf-home-tour-actions">
              <button
                type="button"
                onClick={skipTour}
                disabled={tourSaving}
              >
                Skip
              </button>

              {tourStep !== null && tourStep > 0 && (
                <button
                  type="button"
                  onClick={() => setTourStep(tourStep - 1)}
                >
                  Back
                </button>
              )}

              {tourStep !== null &&
              tourStep < tourSteps.length - 1 ? (
                <button
                  type="button"
                  className="cf-home-primary"
                  onClick={() => setTourStep(tourStep + 1)}
                >
                  Next
                </button>
              ) : (
                <button
                  type="button"
                  className="cf-home-primary"
                  onClick={finishTour}
                  disabled={tourSaving}
                >
                  Finish
                </button>
              )}
            </div>
          </aside>
        )}
      </section>
    );

}
