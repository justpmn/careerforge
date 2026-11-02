import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { onboardingApi } from '../lib/onboarding';
import {getCareerRoadmap, getRecordedSkills,} from '../lib/roadmap';
import { getCompetencyAssessments } from '../lib/competencyassessments';
import { getLearningProgress } from '../lib/learningprogress';
import type { RecordedSkill } from '../lib/roadmap';
import AdminAccessLink from '../components/adminaccesslink';
import '../profile.css';


type ProfileSkill = {
  name: string;
  source: string;
};

type ProfileSummary = {
  careerKey: string | null;
  careerName: string | null;
  skills: ProfileSkill[];
  competencyCount: number | null;
  assessmentCount: number | null;
  learnedCount: number | null;
};


function readable(value: string): string {
  return value
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}


function normalizeSkills(
  records: RecordedSkill[]
): ProfileSkill[] {
  const skills: ProfileSkill[] = [];

  for (const record of records) {
    const item = record as unknown as Record<string, unknown>;

    const name =
      typeof item.name === 'string'
        ? item.name
        : typeof item.skill_name === 'string'
          ? item.skill_name
          : null;

    if (!name) continue;

    skills.push({
      name,
      source:
        typeof item.source === 'string'
          ? item.source
          : 'recorded',
    });
  }

  return skills.sort((a, b) =>
    a.name.localeCompare(b.name)
  );
}


function sourceLabel(source: string): string {
  if (source === 'resume') return 'CV';
  if (source === 'manual') return 'Self-reported';
  return readable(source);
}


export default function ProfilePage() {
  const { user } = useAuth();
  const userId = user?.id;

  const [summary, setSummary] =
    useState<ProfileSummary | null>(null);

  const [loading, setLoading] = useState(true);
  const [warning, setWarning] = useState('');

  useEffect(() => {
    if (userId == null) {
      setLoading(false);
      return;
    }

    let active = true;

    async function loadProfile() {
      setLoading(true);
      setWarning('');

      const warnings: string[] = [];

      try {
        const [selectionResult, careersResult, skillsResult] =
          await Promise.allSettled([
            onboardingApi.selectedCareer(),
            onboardingApi.careers(),
            getRecordedSkills(),
          ]);

        let careerKey: string | null = null;
        let careerName: string | null = null;

        if (selectionResult.status === 'fulfilled') {
          careerKey = selectionResult.value.career_key ?? null;
        } else {
          warnings.push('Could not load your selected career.');
        }

        if (
          careersResult.status === 'fulfilled' &&
          careerKey
        ) {
          const career = careersResult.value.find(
            (item) => item.career_key === careerKey
          );

          careerName = career?.name ?? readable(careerKey);
        } else if (careerKey) {
          careerName = readable(careerKey);
        }

        const skills =
          skillsResult.status === 'fulfilled'
            ? normalizeSkills(skillsResult.value)
            : [];

        if (skillsResult.status === 'rejected') {
          warnings.push('Could not load your recorded skills.');
        }

        let competencyCount: number | null = null;
        let assessmentCount: number | null = null;
        let learnedCount: number | null = null;

        if (careerKey) {
          const [roadmapResult, assessmentsResult, progressResult] =
            await Promise.allSettled([
              getCareerRoadmap(userId!, careerKey),
              getCompetencyAssessments(careerKey),
              getLearningProgress(careerKey),
            ]);

          if (roadmapResult.status === 'fulfilled') {
            competencyCount =
              roadmapResult.value.steps.length;
          } else {
            warnings.push('Could not load roadmap statistics.');
          }

          if (assessmentsResult.status === 'fulfilled') {
            assessmentCount =
              assessmentsResult.value.length;
          } else {
            warnings.push('Could not load proficiency assessments.');
          }

          if (progressResult.status === 'fulfilled') {
            learnedCount = progressResult.value.filter(
              (item) => item.learned
            ).length;
          } else {
            warnings.push('Could not load learning progress.');
          }
        }

        if (!active) return;

        setSummary({
          careerKey,
          careerName,
          skills,
          competencyCount,
          assessmentCount,
          learnedCount,
        });

        setWarning(warnings.join(' '));
      } catch {
        if (!active) return;

        setWarning('Could not retrieve your profile summary.');
      } finally {
        if (active) setLoading(false);
      }
    }

    void loadProfile();

    return () => {
      active = false;
    };
  }, [userId]);


  const name = user?.name?.trim() || 'CareerForge Member';
  const email = user?.email || 'Email unavailable';

  const initials = name
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part.charAt(0).toUpperCase())
    .join('');

  return (
    <section className="cf-dashboard cf-profile">
      <header className="cf-dashboard-header">
        <div>
          <span className="stage-marker">MY PROFILE</span>
          <h1>Your career profile.</h1>
          <p>
            View your account details, career direction
            and development progress.
          </p>
        </div>
      </header>

      {/* Account identity */}
      <article className="cf-dashboard-card cf-profile-identity">
        <div className="cf-profile-avatar" aria-hidden="true">
          {initials}
        </div>

        <div className="cf-profile-identity-details">
          <h2>{name}</h2>
          <p>{email}</p>

          <span className="cf-profile-subtle">
            CareerForge account
          </span>
        </div>

        <div className="cf-profile-actions">
        <AdminAccessLink />

        <Link
            to="/settings"
            className="cf-profile-action"
        >
            Account settings
        </Link>
        </div>
      </article>

      {warning && (
        <p className="cf-error" role="alert">
          {warning}
        </p>
      )}

      <div className="cf-profile-grid">
        {/* Personal information */}
        <article className="cf-dashboard-card">
          <span className="cf-eyebrow">
            01 / PERSONAL INFORMATION
          </span>

          <h2>Account details</h2>

          <dl className="cf-profile-details">
            <div>
              <dt>Full name</dt>
              <dd>{name}</dd>
            </div>

            <div>
              <dt>Email address</dt>
              <dd>{email}</dd>
            </div>

          </dl>

          <p className="cf-profile-subtle">
            Profile changes and account security will
            be managed from Settings.
          </p>
        </article>

        {/* Career direction */}
        <article className="cf-dashboard-card">
          <span className="cf-eyebrow">
            02 / CAREER DIRECTION
          </span>

          <h2>Target career</h2>

          {loading ? (
            <p className="cf-profile-subtle">
              Loading your career...
            </p>
          ) : summary?.careerKey ? (
            <>
              <p className="cf-profile-career">
                {summary.careerName}
              </p>

              <p className="cf-profile-subtle">
                Your roadmap and competency analysis
                are based on this career.
              </p>

              <Link
                to="/roadmap"
                className="cf-profile-action"
              >
                View learning roadmap
              </Link>
            </>
          ) : (
            <>
              <p className="cf-profile-subtle">
                No target career is currently selected.
              </p>

              <Link
                to="/skills-assessment"
                className="cf-profile-action"
              >
                Choose a target career
              </Link>
            </>
          )}
        </article>

        {/* Development summary */}
        <article className="cf-dashboard-card cf-profile-wide">
          <span className="cf-eyebrow">
            03 / DEVELOPMENT SUMMARY
          </span>

          <h2>Your progress</h2>

          <p>
            A snapshot of your recorded skills,
            self-assessments and learning activity.
          </p>

          <div className="cf-profile-stats">
            <div>
              <strong>
                {loading
                  ? '—'
                  : summary?.skills.length ?? '—'}
              </strong>
              <span>Recorded skills</span>
            </div>

            <div>
              <strong>
                {loading
                  ? '—'
                  : summary?.competencyCount ?? '—'}
              </strong>
              <span>Roadmap competencies</span>
            </div>

            <div>
              <strong>
                {loading
                  ? '—'
                  : summary?.assessmentCount ?? '—'}
              </strong>
              <span>Self-assessments</span>
            </div>

            <div>
              <strong>
                {loading
                  ? '—'
                  : summary?.learnedCount ?? '—'}
              </strong>
              <span>Marked as learned</span>
            </div>
          </div>

          <p className="cf-profile-subtle">
            These figures describe recorded activity,
            not independently verified proficiency.
          </p>

          <Link
            to="/skills-assessment"
            className="cf-profile-action"
          >
            View competency analysis
          </Link>
        </article>

        {/* Skills */}
        <article className="cf-dashboard-card cf-profile-wide">
          <span className="cf-eyebrow">
            04 / RECORDED SKILLS
          </span>

          <h2>Your technical skills</h2>

          {loading ? (
            <p className="cf-profile-subtle">
              Loading your skills...
            </p>
          ) : summary && summary.skills.length > 0 ? (
            <div className="cf-profile-skills">
              {summary.skills.map((skill, index) => (
                <div
                  key={`${skill.name}-${index}`}
                  className="cf-profile-skill"
                >
                  <strong>{skill.name}</strong>
                  <small>{sourceLabel(skill.source)}</small>
                </div>
              ))}
            </div>
          ) : (
            <p className="cf-profile-subtle">
              No recorded skills are available.
            </p>
          )}

          <p className="cf-profile-subtle">
            A recorded skill indicates profile evidence or
            self-reporting, not verified mastery.
          </p>
        </article>

        {/* CV */}
        <article className="cf-dashboard-card cf-profile-wide">
          <span className="cf-eyebrow">
            05 / RESUME
          </span>

          <h2>Resume and experience</h2>

          <p>
            Your CV provides information CareerForge
            can use to identify skills and generate
            personalized career recommendations.
          </p>

          <p className="cf-profile-subtle">
            Resume file information is managed in
            the CV workspace.
          </p>

          <Link to="/cv" className="cf-profile-action">
            Open CV workspace
          </Link>
        </article>
      </div>
    </section>
  );
}
