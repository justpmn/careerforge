
import { useEffect, useState, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import {uploadResume, getLatestResumeAnalysis, refreshResumeRecommendations} from '../lib/resume';
import type { ResumeAnalysis, CareerRecommendation } from '../lib/resume';
import CvUploadModal from '../components/cvuploadmodal';
import { useCareerPreferences } from '../hooks/useCareerPreferences';
import {getCoreSkillCoverage,type CoreCoverageResults,} from '../lib/corecoverage';

function careerName(key: string): string {
  return key
    .replace(/[_-]/g, ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}
type SortMode =
  | 'personalized'
  | 'model_desc'
  | 'model_asc'
  | 'coverage_desc'
  | 'coverage_asc';

export default function CvPage() {
  const { user } = useAuth();
  const {
    loading: preferencesLoading,
    savingKey,
    error: preferencesError,
    preferenceFor,
    choose,
  } = useCareerPreferences(
  user?.id != null ? Number(user.id) : undefined
);

  const [analysis, setAnalysis] = useState<ResumeAnalysis | null>(null);
  const [analyzedFilename, setAnalyzedFilename] = useState('');

  const [loadingSaved, setLoadingSaved] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [cvUploadOpen, setCvUploadOpen] = useState(false);
  const [savedError, setSavedError] = useState('');

  // Load the latest saved CV analysis.
  useEffect(() => {
    let active = true;

    async function loadSavedAnalysis() {
      try {
        const saved = await getLatestResumeAnalysis();

        if (!active) return;

        if (saved) {
          const { filename, ...result } = saved;

          setAnalysis(result);
          setAnalyzedFilename(filename);
        }
      } catch (err) {
        if (!active) return;

        setSavedError(
          err instanceof Error
            ? err.message
            : 'Could not load your saved CV analysis.'
        );
      } finally {
        if (active) setLoadingSaved(false);
      }
    }

    void loadSavedAnalysis();

    return () => {
      active = false;
    };
  }, []);

  async function handleCvAnalysis(selectedFile: File): Promise<void> {
    if (!user?.id) {
      throw new Error('Please sign in to analyze your CV.');
    }

    setUploading(true);

    try {
      const result = await uploadResume(
        selectedFile,
        String(user.id)
      );

      setAnalysis(result);
      setAnalyzedFilename(selectedFile.name);
      setSavedError('');
    } finally {
      setUploading(false);
    }
  }

  return (
    <section className="cf-cv">
      <header className="cf-cv-header">
        <h1>Your experience, understood.</h1>

        <p>
          Upload your CV to identify your technical skills
          and discover relevant career paths.
        </p>
      </header>

      {/* Saved analysis loading state */}

      {loadingSaved && (
        <p className="cf-cv-muted" role="status">
          Loading your saved CV analysis...
        </p>
      )}

      {savedError && (
        <p className="cf-cv-error" role="alert">
          {savedError}
        </p>
      )}

      {/* Upload section */}

      <article className="cf-cv-upload-compact">
        <div>
          <h2>Upload CV</h2>

          <p>
            Add or update your CV to refresh your technical
            skills and career recommendations.
          </p>

          <small>PDF or DOCX · Maximum 5 MB</small>
        </div>

        <button
          type="button"
          className="cf-cv-primary cf-cv-upload-action"
          disabled={uploading || loadingSaved}
          onClick={() => setCvUploadOpen(true)}
        >
          + Upload CV
        </button>
      </article>

      {/* CV upload modal */}

      <CvUploadModal
        open={cvUploadOpen}
        onClose={() => setCvUploadOpen(false)}
        onAnalyze={handleCvAnalysis}
      />

      {/* Saved or newly generated analysis */}

      {analysis && (
        <div className="cf-cv-results" aria-live="polite">
          <div className="cf-cv-results-heading">
            <div>
              <span className="cf-cv-eyebrow cf-neon-cv-label">
                CV ANALYSIS
              </span>

              <h2>Your CV analysis</h2>

              <p>{analyzedFilename}</p>
            </div>
          </div>

          {/* Extracted skills */}

          <article className="cf-cv-panel">
            <div className="cf-cv-panel-heading">
              <h3>Extracted skills</h3>

              <span>
                {analysis.extracted_skills.length} identified
              </span>
            </div>

            {analysis.extracted_skills.length > 0 ? (
              <div className="cf-cv-skills">
                {analysis.extracted_skills.map((skill) => (
                  <span
                    key={skill}
                    className="cf-cv-skill"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            ) : (
              <p className="cf-cv-muted">
                No technical skills were identified.
              </p>
            )}

            <p className="cf-cv-note">
              Skills are identified from your document.
              This does not independently verify proficiency.
            </p>
          </article>

          {/* Random Forest recommendations */}

          <article className="cf-cv-panel">
            <div className="cf-cv-panel-heading">
              <h3>Career recommendations</h3>
              <span>Random Forest</span>
            </div>

            {analysis.recommendations.length > 0 ? (
              <div className="cf-cv-recommendations">
                {[...analysis.recommendations]
                  .sort((a, b) => a.rank - b.rank)
                  .map((recommendation) => (
                    <div
                      className="cf-cv-recommendation"
                      key={recommendation.career_key}
                    >
                      <span className="cf-cv-rank cf-cv-recommendation-rank">
                        {String(recommendation.rank).padStart(2, '0')}
                      </span>

                      <strong>
                        {careerName(recommendation.career_key)}
                      </strong>

                      <span className="cf-cv-score">
                        RF score: {recommendation.score.toFixed(3)}
                      </span>
                    </div>
                  ))}
              </div>
            ) : (
              <p className="cf-cv-muted">
                No career recommendations were returned.
              </p>
            )}

            <p className="cf-cv-note">
              Model scores are ranking signals, not verified
              measures of career readiness.
            </p>
          </article>

          {/* Model vocabulary coverage */}

          <article className="cf-cv-panel">
            <div className="cf-cv-panel-heading">
              <h3>Model skill coverage</h3>
            </div>

            <div className="cf-cv-coverage">
              <div>
                <strong>
                  {analysis.model_skills.length}
                </strong>

                <span>
                  Skills used by the classifier
                </span>
              </div>

              <div>
                <strong>
                  {analysis.ignored_skills.length}
                </strong>

                <span>
                  Extracted skills outside its vocabulary
                </span>
              </div>
            </div>

            {analysis.ignored_skills.length > 0 && (
              <p className="cf-cv-note">
                Not used by the classifier:{' '}
                {analysis.ignored_skills.join(', ')}.
                These may still be relevant to your career.
              </p>
            )}
          </article>
        </div>
      )}
    </section>
  );
}
