import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';

import {
  getCompetencyEvidence,
  submitCompetencyEvidence,
} from '../lib/competencyevidence';

import type {
  CompetencyEvidence,
  CompetencyEvidenceType,
} from '../lib/competencyevidence';

import '../competency-evidence.css';

type Props = {
  userId: string | number;
  careerKey: string;
  competencyKey: string;
  onSaved?: () => Promise<void>;
};

const evidenceLabels: Record<CompetencyEvidenceType, string> = {
  project: 'Project',
  experience: 'Work experience',
  certification: 'Certification',
};

export default function CompetencyEvidencePanel({
  userId,
  careerKey,
  competencyKey,
  onSaved,
}: Props) {
  const [records, setRecords] = useState<CompetencyEvidence[]>([]);
  const [evidenceType, setEvidenceType] =
    useState<CompetencyEvidenceType>('project');

  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [refreshWarning, setRefreshWarning] = useState('');

  useEffect(() => {
    let active = true;

    setLoading(true);
    setError('');
    setSuccess('');
    setRefreshWarning('');
    setRecords([]);
    setEvidenceType('project');
    setDescription('');

    void getCompetencyEvidence(userId, careerKey)
      .then((items) => {
        if (!active) return;

        setRecords(
          items.filter(
            (item) => item.competency_key === competencyKey
          )
        );
      })
      .catch((cause: unknown) => {
        if (!active) return;

        setError(
          cause instanceof Error
            ? cause.message
            : 'Could not load competency evidence.'
        );
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [userId, careerKey, competencyKey]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const cleanDescription = description.trim();

    if (!cleanDescription || submitting) return;

    setSubmitting(true);
    setError('');
    setSuccess('');
    setRefreshWarning('');

    try {
      const saved = await submitCompetencyEvidence(
        userId,
        careerKey,
        {
          competency_key: competencyKey,
          evidence_type: evidenceType,
          description: cleanDescription,
        }
      );

      setRecords((previous) => [saved, ...previous]);
      setDescription('');
      setSuccess('Evidence saved as self-reported.');

      // Refresh the roadmap so its next action reflects
      // the newly submitted evidence.
      if (onSaved) {
        try {
          await onSaved();
        } catch {
          setRefreshWarning(
            'Evidence was saved, but the roadmap could not refresh. ' +
            'Reload the page to see the updated next action.'
          );
        }
      }
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : 'Could not submit competency evidence.'
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="cf-skill-inspector-section cf-evidence-panel">
      <h3>Competency evidence</h3>

      <p className="cf-evidence-helper">
        Describe a project, practical experience or certification
        that demonstrates this competency. Submissions are
        self-reported and are not independently verified.
      </p>

      {loading ? (
        <p className="cf-evidence-helper">
          Loading submitted evidence...
        </p>
      ) : (
        <>
          {records.length > 0 && (
            <div className="cf-evidence-list">
              <h4>
                Submitted evidence ({records.length})
              </h4>

              {records.map((record) => (
                <div
                  key={record.id}
                  className="cf-evidence-entry"
                >
                  <div className="cf-evidence-entry-meta">
                    <strong>
                      {evidenceLabels[record.evidence_type] ??
                        record.evidence_type}
                    </strong>

                    <span>
                      {record.verification_status === 'self_reported'
                        ? 'Self-reported'
                        : record.verification_status}
                    </span>
                  </div>

                  <p>{record.description}</p>

                  {record.created_at && (
                    <small>
                      Submitted{' '}
                      {new Date(record.created_at).toLocaleDateString()}
                    </small>
                  )}
                </div>
              ))}
            </div>
          )}

          <form
            className="cf-evidence-form"
            onSubmit={(event) => void handleSubmit(event)}
          >
            <h4>Add evidence</h4>

            <label htmlFor="cf-evidence-type">
              Evidence type
            </label>

            <select
              id="cf-evidence-type"
              value={evidenceType}
              disabled={submitting}
              onChange={(event) =>
                setEvidenceType(
                  event.target.value as CompetencyEvidenceType
                )
              }
            >
              <option value="project">Project</option>
              <option value="experience">Work experience</option>
              <option value="certification">Certification</option>
            </select>

            <label htmlFor="cf-evidence-description">
              Description
            </label>

            <textarea
              id="cf-evidence-description"
              value={description}
              onChange={(event) =>
                setDescription(event.target.value)
              }
              placeholder="Describe what you built, completed, or worked on..."
              rows={4}
              maxLength={5000}
              required
              disabled={submitting}
            />

            <button
              type="submit"
              className="cf-evidence-submit"
              disabled={!description.trim() || submitting}
            >
              {submitting ? 'Saving...' : 'Submit evidence'}
            </button>
          </form>
        </>
      )}

      {error && (
        <p className="cf-evidence-error" role="alert">
          {error}
        </p>
      )}

      {success && (
        <p className="cf-evidence-success" role="status">
          {success}
        </p>
      )}

      {refreshWarning && (
        <p className="cf-evidence-error" role="alert">
          {refreshWarning}
        </p>
      )}
    </div>
  );
}
