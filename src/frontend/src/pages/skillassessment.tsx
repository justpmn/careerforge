import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { onboardingApi } from '../lib/onboarding';
import type { Career } from '../lib/onboarding';
import {getCareerRoadmap, getRecordedSkills} from '../lib/roadmap';
import type {CareerRoadmap,  RecordedSkill} from '../lib/roadmap';
import {getCompetencyAssessments} from '../lib/competencyassessments';
import type {CompetencyAssessment} from '../lib/competencyassessments';
import {getLearningProgress} from '../lib/learningprogress';
import type {LearningSkill} from '../lib/learningprogress';
import ManualSkillManager from '../components/manualskillmanager';
import '../skill-assessment.css';


type StepInfo = {
  key: string;
  name: string;
  level: string;
  status: string;
  nextAction: string;
  matchedSkills: string[];
};
type GapFilter = 'attention' | 'all' | 'evidenced' | 'assessed';

const STATUS_LABELS: Record<string, string> = {
  evidenced: 'Skill recorded',
  evidence_found: 'CV evidence to review',
  not_evidenced: 'No matching skill recorded',
  not_assessed: 'Not assessed',
};
const ACTION_LABELS: Record<string, string> = {
  no_immediate_action: 'Review or develop further',
  review_submitted_evidence: 'Review submitted evidence',
  review_resume_evidence: 'Review CV evidence',
  assess_competency: 'Assess this competency',
  confirm_skill_experience: 'Confirm your experience',
};


function readable(value: string): string {
  return value.replace(/_/g, ' ');
}

function stringValue(value: unknown): string | null {
  return typeof value === 'string' && value.trim()
    ? value.trim()
    : null;
}

function normalizeStep(input: unknown): StepInfo {
  const raw = input as Record<string, unknown>;

  const key = stringValue(raw.competency_key) ?? '';
  const matchedSkills = Array.isArray(raw.matched_skills)
    ? raw.matched_skills.filter(
        (item): item is string => typeof item === 'string'
      )
    : [];

  return {
    key,
    name:
      stringValue(raw.competency) ??
      stringValue(raw.title) ??
      readable(key),
    level: stringValue(raw.level) ?? 'supporting',
    status: stringValue(raw.status) ?? 'not_assessed',
    nextAction:
      stringValue(raw.next_action) ?? 'assess_competency',
    matchedSkills,
  };
}

function recordedSkillName(input: RecordedSkill): string | null {
  const raw = input as unknown as Record<string, unknown>;

  const nested =
    raw.skill && typeof raw.skill === 'object'
      ? raw.skill as Record<string, unknown>
      : null;

  return (
    stringValue(raw.skill_name) ??
    stringValue(raw.name) ??
    stringValue(raw.label) ??
    stringValue(raw.skill) ??
    stringValue(nested?.name) ??
    null
  );
}

export default function SkillsAssessmentPage() {
  const { user } = useAuth();
  const userId = user?.id;

  const [careers, setCareers] = useState<Career[]>([]);
  const [selectedCareer, setSelectedCareer] = useState('');
  const [savedCareer, setSavedCareer] = useState('');
  const [search, setSearch] = useState('');

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState('');
  const [roadmap, setRoadmap] = useState<CareerRoadmap | null>(null);
  const [recordedSkills, setRecordedSkills] =
    useState<RecordedSkill[]>([]);
  const [assessments, setAssessments] =
    useState<CompetencyAssessment[]>([]);
  const [progress, setProgress] = useState<LearningSkill[]>([]);

  const [profileLoading, setProfileLoading] = useState(false);
  const [profileError, setProfileError] = useState('');
  const [gapFilter, setGapFilter] = useState<GapFilter>('attention');
  const [careerExpanded, setCareerExpanded] = useState(true);
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
        setCareerExpanded(!selection.career_key);
      })
      .catch((err: unknown) => {
        if (!active) return;

        setError(
          err instanceof Error
            ? err.message
            : 'Could not load careers.'
        );
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);


  // 2. Load actual user data whenever the saved career changes.
  useEffect(() => {
    let active = true;

    setRoadmap(null);
    setRecordedSkills([]);
    setAssessments([]);
    setProgress([]);
    setProfileError('');
    setGapFilter('attention');

    if (!savedCareer || userId == null) {
      setProfileLoading(false);
      return;
    }

    setProfileLoading(true);

    async function loadProfile() {
      try {
        const [careerRoadmap, skills, ratings, learning] =
          await Promise.all([
            getCareerRoadmap(userId!, savedCareer),
            getRecordedSkills(),
            getCompetencyAssessments(savedCareer),
            getLearningProgress(savedCareer),
          ]);

        if (!active) return;

        setRoadmap(careerRoadmap);
        setRecordedSkills(skills);
        setAssessments(ratings);
        setProgress(learning);
      } catch (cause) {
        if (!active) return;

        setProfileError(
          cause instanceof Error
            ? cause.message
            : 'Could not load your assessment information.'
        );
      } finally {
        if (active) setProfileLoading(false);
      }
    }

    void loadProfile();

    return () => {
      active = false;
    };
  }, [userId, savedCareer]);


  const filteredCareers = careers.filter((career) => {
    const query = search.toLowerCase().trim();

    return (
      career.name.toLowerCase().includes(query) ||
      career.career_key.toLowerCase().includes(query)
    );
  });

  const selected = careers.find(
    (career) => career.career_key === selectedCareer
  );


  const steps = useMemo(() => {
    return (roadmap?.steps ?? [])
      .map((step) => normalizeStep(step))
      .filter((step) => Boolean(step.key));
  }, [roadmap]);


  const assessmentByKey = useMemo(() => {
    return new Map(
      assessments.map((item) => [item.competency_key, item])
    );
  }, [assessments]);


  const learnedKeys = useMemo(() => {
    return new Set(
      progress
        .filter((item) => item.learned)
        .map((item) => item.skill_key)
    );
  }, [progress]);


  // Combine recorded skill names with skills already matched by
  // the existing competency-gap analysis.
  const knownSkills = useMemo(() => {
    const names = new Set<string>();

    for (const item of recordedSkills) {
      // Manually declared skills have their own section.
      if (
        (item as { source?: string }).source === 'manual'
      ) {
        continue;
      }
      const name = recordedSkillName(item);
      if (name) names.add(name);
    }

    for (const step of steps) {
      for (const name of step.matchedSkills) {
        names.add(name);
      }
    }

    return Array.from(names).sort((a, b) =>
      a.localeCompare(b)
    );
  }, [recordedSkills, steps]);


  const recordedCount = steps.filter(
    (step) => step.status === 'evidenced'
  ).length;

  const reviewCount = steps.filter(
    (step) => step.status === 'evidence_found'
  ).length;

  const attentionCount = steps.filter(
    (step) => step.status !== 'evidenced'
  ).length;

  const selfAssessedCount = steps.filter(
    (step) => assessmentByKey.has(step.key)
  ).length;

  const learnedCount = steps.filter(
    (step) => learnedKeys.has(step.key)
  ).length;


  const visibleSteps = steps.filter((step) => {
    switch (gapFilter) {
      case 'attention':
        return step.status !== 'evidenced';

      case 'evidenced':
        return step.status === 'evidenced';

      case 'assessed':
        return assessmentByKey.has(step.key);

      default:
        return true;
    }
  });


  async function saveCareer() {
    if (!selectedCareer || saving) return;

    setSaving(true);
    setError(null);
    setMessage('');

    try {
      const result = await onboardingApi.saveCareer(
        selectedCareer
      );

      setSavedCareer(result.career_key ?? '');
      setCareerExpanded(!result.career_key);
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
async function refreshSkillProfile() {
  if (userId == null || !savedCareer) return;

  const [skills, updatedRoadmap] = await Promise.all([
    getRecordedSkills(),
    getCareerRoadmap(userId, savedCareer),
  ]);

  setRecordedSkills(skills);
  setRoadmap(updatedRoadmap);
}

  return (
    <section className="cf-dashboard">
      <header className="cf-dashboard-header">
        <div>
          {/* <span className="stage-marker">
            SKILLS ASSESSMENT
          </span> */}

          <h1>Understand your abilities.</h1>

          <p>
            Review your recorded skills, assess your experience
            and identify competencies to develop.
          </p>
        </div>
      </header>

      <div className="cf-assessment-sections">

        {/* SECTION 01: CAREER DIRECTION */}
        <article className="cf-dashboard-card">
          <div className="cf-career-collapse-header">
          <div>
            <span className="cf-eyebrow">
              CAREER DIRECTION
            </span>

            <h2>
              {savedCareer
                ? careers.find(
                    (career) => career.career_key === savedCareer
                  )?.name ?? savedCareer
                : 'Choose your target career'}
            </h2>
          </div>

          {savedCareer && (
            <button
              type="button"
              className="cf-career-toggle"
              aria-expanded={careerExpanded}
              aria-controls="career-direction-options"
              disabled={saving}
              onClick={() => {
                if (careerExpanded) {
                  setSelectedCareer(savedCareer);
                  setSearch('');
                }

                setCareerExpanded((current) => !current);
                setError(null);
                setMessage('');
              }}
            >
              {careerExpanded ? 'Cancel' : 'Change career'}
            </button>
          )}
        </div>

          {!careerExpanded && savedCareer && (
            <p className="cf-assessment-hint">
              Your competency analysis and learning roadmap
              are based on this career.
            </p>
          )}

          <div
            id="career-direction-options"
            hidden={!careerExpanded}
          >
            <p>
              Select the career you want to work toward.
              Your competency analysis will use this selection.
            </p>

            <label
              className="cf-input-label"
              htmlFor="career-search"
            >
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
                onboarding API and database.
              </p>
            ) : (
              <div className="cf-career-options">
                {filteredCareers.map((career) => (
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

                {filteredCareers.length === 0 && (
                  <p>No matching careers found.</p>
                )}
              </div>
            )}

            {selected && (
              <p className="cf-selected-career">
                Selected: <strong>{selected.name}</strong>
              </p>
            )}

            {selectedCareer !== savedCareer && savedCareer && (
              <p className="cf-assessment-hint">
                Save your new career selection to refresh
                the competency analysis below.
              </p>
            )}

            {error && (
              <p role="alert" className="cf-error">
                {error}
              </p>
            )}

            {message && (
              <p role="status" className="cf-success">
                {message}
              </p>
            )}

            <div className="cf-card-footer">
              <span className="cf-muted">
                {savedCareer
                  ? 'You can change your target career later.'
                  : 'Select a target career to begin.'}
              </span>

              <button
                type="button"
                className="cf-button cf-button-primary"
                onClick={() => void saveCareer()}
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
          </div>

          {!careerExpanded && error && (
            <p role="alert" className="cf-error">
              {error}
            </p>
          )}
        </article>

        {/* SECTION 02: CURRENT SKILLS */}
        <article className="cf-dashboard-card">
          <span className="cf-eyebrow">
            CURRENT SKILLS
          </span>

          <h2>Your recorded skills</h2>

          <p>
            These are skills recorded in your profile
            or matched through CareerForge's competency analysis.
            A recorded skill does not independently prove proficiency.
          </p>

          {!savedCareer ? (
            <p className="cf-assessment-hint">
              Choose and save a target career to begin.
            </p>
          ) : profileLoading ? (
            <p className="cf-assessment-hint">
              Loading your skills...
            </p>
          ) : profileError ? (
            <p className="cf-error" role="alert">
              {profileError}
            </p>
          ) : (
            <>
              <div className="cf-assessment-metrics">
                <div>
                  <strong>{knownSkills.length}</strong>
                  <span>Recorded skills</span>
                </div>

                <div>
                  <strong>{selfAssessedCount}</strong>
                  <span>Self-assessed competencies</span>
                </div>

                <div>
                  <strong>{learnedCount}</strong>
                  <span>Marked as learned</span>
                </div>
              </div>

              {knownSkills.length > 0 ? (
                <div className="cf-assessment-skill-list">
                  {knownSkills.map((skill) => (
                    <span
                      key={skill}
                      className="cf-assessment-skill"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="cf-assessment-hint">
                  No recorded skills were found. Upload a CV
                  or add competency evidence through your roadmap.
                </p>
              )}

              <p className="cf-assessment-hint">
                Self-assessments and learning progress
                are tracked separately from CV evidence.
              </p>

              <Link
                to="/roadmap"
                className="cf-assessment-link"
              >
                Review skills and submit evidence
              </Link>
            </>
          )}
        </article>


        {/* SECTION 03: COMPETENCY GAPS */}
        <article className="cf-dashboard-card">
          <span className="cf-eyebrow">
            COMPETENCY GAPS
          </span>

          <h2>Your competency analysis</h2>

          <p>
            Compare your recorded skills against the
            requirements of your target career.
          </p>

          {!savedCareer ? (
            <p className="cf-assessment-hint">
              Save a target career to view competency gaps.
            </p>
          ) : profileLoading ? (
            <p className="cf-assessment-hint">
              Analysing your competencies...
            </p>
          ) : profileError ? (
            <p className="cf-error" role="alert">
              {profileError}
            </p>
          ) : (
            <>
              <div className="cf-assessment-metrics">
                <div>
                  <strong>{steps.length}</strong>
                  <span>Total competencies</span>
                </div>

                <div>
                  <strong>{recordedCount}</strong>
                  <span>With recorded skill matches</span>
                </div>

                <div>
                  <strong>{attentionCount}</strong>
                  <span>Need attention</span>
                </div>

                <div>
                  <strong>{reviewCount}</strong>
                  <span>CV evidence to review</span>
                </div>
              </div>

              <p className="cf-assessment-hint">
                These counts indicate available evidence, not
                verified proficiency or a career-readiness score.
                Missing evidence does not necessarily mean
                you lack the skill.
              </p>

              <div className="cf-assessment-filters">
                {([
                  ['attention', 'Needs attention'],
                  ['all', 'All'],
                  ['evidenced', 'Recorded'],
                  ['assessed', 'Self-assessed'],
                ] as const).map(([value, label]) => (
                  <button
                    key={value}
                    type="button"
                    aria-pressed={gapFilter === value}
                    className={
                      gapFilter === value ? 'is-active' : ''
                    }
                    onClick={() => setGapFilter(value)}
                  >
                    {label}
                  </button>
                ))}
              </div>

              <div className="cf-assessment-gap-list">
                {visibleSteps.map((step) => {
                  const assessment =
                    assessmentByKey.get(step.key);

                  const learned = learnedKeys.has(step.key);

                  return (
                    <div
                      key={step.key}
                      className="cf-assessment-gap-row"
                    >
                      <div className="cf-assessment-gap-heading">
                        <strong>{step.name}</strong>

                        <span>
                          {readable(step.level)}
                        </span>
                      </div>

                      <p>
                        {STATUS_LABELS[step.status] ??
                          readable(step.status)}
                      </p>

                      <small>
                        {ACTION_LABELS[step.nextAction] ??
                          readable(step.nextAction)}
                      </small>

                      <div className="cf-assessment-gap-tags">
                        {assessment && (
                          <span>
                            Self-assessed:{' '}
                            {readable(
                              assessment.proficiency_level
                            )}
                          </span>
                        )}

                        {learned && (
                          <span>Marked as learned</span>
                        )}
                      </div>
                    </div>
                  );
                })}

                {visibleSteps.length === 0 && (
                  <p className="cf-assessment-hint">
                    No competencies match this filter.
                  </p>
                )}
              </div>

              <Link
                to="/roadmap"
                className="cf-assessment-link"
              >
                Open learning roadmap
              </Link>
            </>
          )}
        </article>
      </div>
    </section>
  );
}
