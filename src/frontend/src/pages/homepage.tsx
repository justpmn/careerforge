import { useEffect, useState } from 'react';
import type { CSSProperties, TransitionEvent } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { postAuthRoute } from '../lib/auth';
import Brand from '../components/Brand';
import '../homepage.css';

type Props = {
  theme: 'light' | 'dark';
  toggleTheme: () => void;
};

const features = [
  {
    title: 'Understand your experience',
    description:
      'Upload your CV to identify technical skills and explore career recommendations.',
  },
  {
    title: 'Find your skill gaps',
    description:
      'Compare your recorded skills and assessments with the competencies of your target career.',
  },
  {
    title: 'Build your learning path',
    description:
      'Explore connected competencies, learning resources and your progress through an interactive roadmap.',
  },
  {
    title: 'Get AI-powered guidance',
    description:
      'Ask the AI mentor questions about careers, technical skills and your next steps.',
  },
];

const steps = [
  {
    title: 'Bring your skills',
    description:
      'Upload a CV or build your skill profile through CareerForge.',
  },
  {
    title: 'Choose a direction',
    description:
      'Explore technology careers and select the path you want to work toward.',
  },
  {
    title: 'Keep building',
    description:
      'Follow your roadmap, discover resources and track what you learn.',
  },
];

const totalFeatures = features.length;
const loopOffset = 2;

const slides = [
  ...features.slice(-loopOffset),
  ...features,
  ...features.slice(0, loopOffset),
];

export default function HomePage({ theme, toggleTheme }: Props) {
  const { user } = useAuth();
  const workspace = user ? postAuthRoute(user) : '/signup';

  const [slideIndex, setSlideIndex] = useState(loopOffset);
  const [carouselCycle, setCarouselCycle] = useState(0);
  const [transitionEnabled, setTransitionEnabled] = useState(true);
  const [moving, setMoving] = useState(false);
  const [carouselHovered, setCarouselHovered] = useState(false);
  const [carouselFocused, setCarouselFocused] = useState(false);

  const [tabVisible, setTabVisible] = useState(
    () => document.visibilityState === 'visible'
  );

  const [reducedMotion, setReducedMotion] = useState(
    () => window.matchMedia('(prefers-reduced-motion: reduce)').matches
  );

  const carouselPaused =
    carouselHovered ||
    carouselFocused ||
    !tabVisible ||
    moving ||
    reducedMotion;

  const currentFeature =
    ((slideIndex - loopOffset + totalFeatures) % totalFeatures) + 1;

  useEffect(() => {
    function updateVisibility() {
      setTabVisible(document.visibilityState === 'visible');
    }

    document.addEventListener('visibilitychange', updateVisibility);

    return () => {
      document.removeEventListener('visibilitychange', updateVisibility);
    };
  }, []);

  useEffect(() => {
    const preference = window.matchMedia(
      '(prefers-reduced-motion: reduce)'
    );

    function updatePreference() {
      setReducedMotion(preference.matches);

      if (preference.matches) {
        setMoving(false);
        setTransitionEnabled(false);
        setSlideIndex((current) =>
          ((current - loopOffset + totalFeatures) % totalFeatures) +
          loopOffset
        );
      }
    }

    preference.addEventListener('change', updatePreference);

    return () => {
      preference.removeEventListener('change', updatePreference);
    };
  }, []);

  function moveFeature(direction: -1 | 1) {
    if (moving) return;

    if (reducedMotion) {
      setTransitionEnabled(false);
      setSlideIndex((current) => {
        const next =
          (current - loopOffset + direction + totalFeatures) %
          totalFeatures;

        return loopOffset + next;
      });
    } else {
      setTransitionEnabled(true);
      setMoving(true);
      setSlideIndex((current) => current + direction);
    }

    setCarouselCycle((current) => current + 1);
  }

  function handleSlideEnd(event: TransitionEvent<HTMLDivElement>) {
    if (
      event.target !== event.currentTarget ||
      event.propertyName !== 'transform'
    ) {
      return;
    }

    if (slideIndex >= totalFeatures + loopOffset) {
      setTransitionEnabled(false);
      setSlideIndex(loopOffset);
    } else if (slideIndex < loopOffset) {
      setTransitionEnabled(false);
      setSlideIndex(totalFeatures + slideIndex);
    }

    setMoving(false);
  }

  return (
    <div className="cf-landing">
      <a className="cf-landing-skip" href="#main-content">
        Skip to content
      </a>

      <header className="cf-landing-header">
        <div className="cf-landing-nav-container">
          <Brand />

          <nav
            className="cf-landing-navigation"
            aria-label="Main navigation"
          >
            <a href="#features">Features</a>
            <a href="#how-it-works">How it works</a>
          </nav>

          <div className="cf-landing-nav-actions">
            <button
              type="button"
              className="cf-landing-theme"
              onClick={toggleTheme}
              aria-label={`Switch to ${
                theme === 'dark' ? 'light' : 'dark'
              } mode`}
              title={`Switch to ${
                theme === 'dark' ? 'light' : 'dark'
              } mode`}
            >
              {theme === 'dark' ? '☀' : '☾'}
            </button>

            <Link
              to={user ? workspace : '/login'}
              className="cf-landing-login"
            >
              {user ? 'Workspace' : 'Log in'}
            </Link>

            <Link to={workspace} className="cf-landing-button">
              {user ? 'Open app' : 'Get started'}
            </Link>
          </div>
        </div>
      </header>

      <main id="main-content">
        {/* Hero */}

        <section className="cf-landing-hero">
          <div className="cf-landing-hero-copy">
            <h1>
              Your next move,
              <br />
              <span>made clearer.</span>
            </h1>

            <p className="cf-landing-intro">
              Understand your skills. Explore career directions.
              Build a learning path you can actually follow.
            </p>

            <div className="cf-landing-hero-actions">
              <Link
                to={workspace}
                className="cf-landing-button cf-landing-button-large"
              >
                {user ? 'Continue your journey' : 'Start your journey'}
                <span aria-hidden="true">↗</span>
              </Link>

              <a
                href="#features"
                className="cf-landing-button-outline"
              >
                Explore CareerForge
              </a>
            </div>

            <p className="cf-landing-hero-note">
              Built for people navigating careers in technology.
            </p>
          </div>

          {/* Example pathway */}

          <div className="cf-landing-preview">
            <div className="cf-landing-preview-top">
              <div>
                <h2>Software Engineer</h2>
              </div>
            </div>

            <div className="cf-landing-path">
              <div className="cf-landing-path-item">
                <span className="cf-landing-path-marker">01</span>
                <div>
                  <strong>Programming</strong>
                  <small>Foundation</small>
                </div>
              </div>

              <div className="cf-landing-path-item">
                <span className="cf-landing-path-marker">02</span>
                <div>
                  <strong>API Development</strong>
                  <small>Build</small>
                </div>
              </div>

              <div className="cf-landing-path-item">
                <span className="cf-landing-path-marker">03</span>
                <div>
                  <strong>Testing</strong>
                  <small>Practice</small>
                </div>
              </div>

              <div className="cf-landing-path-item">
                <span className="cf-landing-path-marker">04</span>
                <div>
                  <strong>CI/CD</strong>
                  <small>Deliver</small>
                </div>
              </div>
            </div>

            <div className="cf-landing-preview-bottom">
              <span>Learn skills. Build evidence. Track progress.</span>
              <span aria-hidden="true">↗</span>
            </div>
          </div>
        </section>

        {/* Features */}

        <section id="features" className="cf-landing-section">
          <div className="cf-landing-section-heading">
            <h2>More direction</h2>

            <p>
              From understanding what you already know to
              planning what comes next.
            </p>
          </div>

          <div
            className="cf-landing-feature-carousel"
            role="region"
            aria-roledescription="carousel"
            aria-label="CareerForge features"
            onMouseEnter={() => setCarouselHovered(true)}
            onMouseLeave={() => setCarouselHovered(false)}
            onFocusCapture={() => setCarouselFocused(true)}
            onBlurCapture={(event) => {
              if (!event.currentTarget.contains(event.relatedTarget)) {
                setCarouselFocused(false);
              }
            }}
          >
            <div className="cf-landing-feature-viewport">
              <div
                className={`cf-landing-feature-track ${
                  transitionEnabled ? 'is-animated' : ''
                }`}
                style={{
                  '--shift-desktop':
                    `calc(-${slideIndex * 50}% - ${slideIndex * 8}px)`,
                  '--shift-mobile':
                    `calc(-${slideIndex * 100}% - ${slideIndex * 16}px)`,
                } as CSSProperties}
                onTransitionEnd={handleSlideEnd}
              >
                {slides.map((feature, index) => (
                  <article
                    className="cf-landing-feature"
                    key={`${feature.title}-${index}`}
                    aria-hidden={
                      index < slideIndex || index > slideIndex + 1
                    }
                  >
                    <div className="cf-landing-feature-top">
                      <span aria-hidden="true">↗</span>
                    </div>

                    <h3>{feature.title}</h3>
                    <p>{feature.description}</p>
                  </article>
                ))}
              </div>
            </div>

            {/* Autoplay countdown */}

            <div
              className="cf-landing-carousel-progress"
              aria-hidden="true"
            >
              <div
                key={carouselCycle}
                className="cf-landing-carousel-progress-fill"
                style={{
                  animationPlayState: carouselPaused
                    ? 'paused'
                    : 'running',
                }}
                onAnimationEnd={() => {
                  if (!carouselPaused) moveFeature(1);
                }}
              />
            </div>

            {/* Carousel navigation */}

            <div className="cf-landing-carousel-footer">
              <span className="cf-landing-carousel-count">
                {String(currentFeature).padStart(2, '0')}
                {' / '}
                {String(totalFeatures).padStart(2, '0')}
              </span>

              <div className="cf-landing-carousel-actions">
                <button
                  type="button"
                  aria-label="Previous feature"
                  disabled={moving}
                  onClick={() => moveFeature(-1)}
                >
                  ←
                </button>

                <button
                  type="button"
                  aria-label="Next feature"
                  disabled={moving}
                  onClick={() => moveFeature(1)}
                >
                  →
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* How it works */}

        <section
          id="how-it-works"
          className="cf-landing-section cf-landing-process-section"
        >
          <div className="cf-landing-section-heading">
            <h2>
              Start where you are.
              <br />
              Build from there.
            </h2>
          </div>

          <div className="cf-landing-process">
            {steps.map((step) => (
              <div
                className="cf-landing-process-step"
                key={step.title}
              >
                <div>
                  <h3>{step.title}</h3>
                  <p>{step.description}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Final call to action */}

        <section className="cf-landing-final">
          <h2>
            A career doesn't happen
            <br />
            all at once.
          </h2>

          <p>
            Take the next step with a clearer understanding
            of where you are and what you can build.
          </p>

          <Link
            to={workspace}
            className="cf-landing-button cf-landing-button-large"
          >
            {user
              ? 'Return to your workspace'
              : 'Get started with CareerForge'}
            <span aria-hidden="true">↗</span>
          </Link>
        </section>
      </main>

      <footer className="cf-landing-footer">
        <Brand />
        <p>Make your next move count.</p>
        <span>© {new Date().getFullYear()} CareerForge</span>
      </footer>
    </div>
  );
}
