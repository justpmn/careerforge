
import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';

import {
  getCompetencyAssessments,
  saveCompetencyAssessment,
} from '../lib/competencyassessments';

import type {
  CompetencyAssessment,
  ProficiencyLevel,
} from '../lib/competencyassessments';

import '../competency-assessment.css';

type Props = {
  careerKey: string;
  competencyKey: string;
};

const LEVELS: {
  value: ProficiencyLevel;
  label: string;
  description: string;
}[] = [
  {
    value: 'beginner',
    label: 'Beginner',
    description: 'I understand the fundamentals but still need guidance.',
  },
  {
    value: 'intermediate',
    label: 'Intermediate',
    description: 'I can apply this skill independently.',
  },
  {
    value: 'advanced',
    label: 'Advanced',
    description: 'I can solve complex problems and guide others.',
  },
];

export default function CompetencyAssessmentPanel({
  careerKey,
  competencyKey,
}: Props) {
  const [assessment, setAssessment] =
    useState<CompetencyAssessment | null>(null);

  const [level, setLevel] = useState<ProficiencyLevel | ''>('');
  const [notes, setNotes] = useState('');

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    let active = true;

    setLoading(true);
    setError('');
    setSuccess('');
    setAssessment(null);
    setLevel('');
    setNotes('');

    void getCompetencyAssessments(careerKey)
      .then((items) => {
        if (!active) return;

        const existing =
          items.find(
            (item) => item.competency_key === competencyKey
          ) ?? null;

        setAssessment(existing);
        setLevel(existing?.proficiency_level ?? '');
        setNotes(existing?.notes ?? '');
      })
      .catch((cause: unknown) => {
        if (!active) return;

        setError(
          cause instanceof Error
            ? cause.message
            : 'Could not load your assessment.'
        );
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [careerKey, competencyKey]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!level || loading || saving) return;

    setSaving(true);
    setError('');
    setSuccess('');

    try {
      const saved = await saveCompetencyAssessment(
        careerKey,
        competencyKey,
        {
          proficiency_level: level,
          notes: notes.trim() || null,
        }
      );

      setAssessment(saved);
      setLevel(saved.proficiency_level);
      setNotes(saved.notes ?? '');
      setSuccess(
        assessment
          ? 'Your assessment has been updated.'
          : 'Your assessment has been saved.'
      );
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : 'Could not save your assessment.'
      );
    } finally {
      setSaving(false);
    }
  }

  const hasChanges =
    level !== (assessment?.proficiency_level ?? '') ||
    notes.trim() !== (assessment?.notes ?? '');

  return (
    <div className="cf-skill-inspector-section cf-assessment-panel">
      <h3>Assess your proficiency</h3>

      <p className="cf-assessment-helper">
        How comfortable are you applying this competency?
        Your response is self-reported and does not
        independently verify proficiency.
      </p>

      {loading ? (
        <p className="cf-assessment-helper">
          Loading your assessment...
        </p>
      ) : (
        <form
          className="cf-assessment-form"
          onSubmit={(event) => void handleSubmit(event)}
        >
          <fieldset disabled={saving}>
            <legend>Experience level</legend>

            <div className="cf-assessment-levels">
              {LEVELS.map((option) => (
                <label
                  key={option.value}
                  className={
                    'cf-assessment-option' +
                    (level === option.value ? ' is-selected' : '')
                  }
                >
                  <input
                    type="radio"
                    name={`proficiency-${competencyKey}`}
                    value={option.value}
                    checked={level === option.value}
                    onChange={() => {
                      setLevel(option.value);
                      setSuccess('');
                    }}
                  />

                  <span>
                    <strong>{option.label}</strong>
                    <small>{option.description}</small>
                  </span>
                </label>
              ))}
            </div>

            <label
              className="cf-assessment-notes-label"
              htmlFor="cf-assessment-notes"
            >
              Additional notes (optional)
            </label>

            <textarea
              id="cf-assessment-notes"
              value={notes}
              onChange={(event) => {
                setNotes(event.target.value);
                setSuccess('');
              }}
              placeholder="For example: I have used this skill in two projects..."
              rows={3}
              maxLength={2000}
            />

            <button
              type="submit"
              className="cf-assessment-save"
              disabled={!level || !hasChanges || saving}
            >
              {saving
                ? 'Saving...'
                : assessment
                  ? 'Update assessment'
                  : 'Save assessment'}
            </button>
          </fieldset>
        </form>
      )}

      {assessment && (
        <p className="cf-assessment-saved">
          Saved proficiency: <strong>{assessment.proficiency_level}</strong>
          {' · '}Self-reported
        </p>
      )}

      {success && (
        <p className="cf-assessment-success" role="status">
          {success}
        </p>
      )}

      {error && (
        <p className="cf-assessment-error" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
