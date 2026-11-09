
import { useEffect, useState, useRef } from 'react';
import { useQueryClient, useQuery } from '@tanstack/react-query';
import CvUploadModal from '../components/cvuploadmodal';
import { useAuth } from '../context/AuthContext';
import { useCareerPreferences } from '../hooks/useCareerPreferences';
import {getCoreSkillCoverage,type CoreCoverageResults,} from '../lib/corecoverage';
import {uploadResume, getLatestResumeAnalysis, refreshResumeRecommendations} from '../lib/resume';
import type { ResumeAnalysis, CareerRecommendation, SavedResumeAnalysis } from '../lib/resume';
import { queryKeys } from '../lib/queryclient';



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
  const cache = useQueryClient();
  const {
    loading: preferencesLoading,
    savingKey,
    error: preferencesError,
    preferenceFor,
    choose,
  } = useCareerPreferences(
  user?.id != null ? Number(user.id) : undefined
);

  const userId = user?.id ?? '';

  const savedCvQuery = useQuery({
    queryKey: queryKeys.savedCv(userId),
    queryFn: getLatestResumeAnalysis,
    enabled: Boolean(userId),
    staleTime: 5 * 60 * 1000,
  });

  const analysis = savedCvQuery.data ?? null;
  const analyzedFilename = analysis?.filename ?? '';
  const loadingSaved = savedCvQuery.isPending;

  const savedError = savedCvQuery.isError
    ? savedCvQuery.error.message
    : '';

  const recommendationsQuery = useQuery({
    queryKey: queryKeys.cvRecommendations(userId),
    queryFn: refreshResumeRecommendations,
    enabled: Boolean(userId && analysis),
    staleTime: 5 * 60 * 1000,
    retry: 0,
  });

  const recommendations =
    recommendationsQuery.data ?? analysis?.recommendations ?? [];

  const recommendationsLoading =
    Boolean(analysis) && recommendationsQuery.isPending;

  const coverageQuery = useQuery({
    queryKey: queryKeys.coreCoverage(userId),
    queryFn: getCoreSkillCoverage,
    enabled: Boolean(userId && analysis),
    staleTime: 2 * 60 * 1000,
  });

  const coreCoverage: CoreCoverageResults = coverageQuery.data ?? {};
  const coverageLoading = Boolean(analysis) && coverageQuery.isPending;

  
  const [uploading, setUploading] = useState(false);
  const [cvUploadOpen, setCvUploadOpen] = useState(false);
  
  
  const [processingKey, setProcessingKey] =
    useState<string | null>(null);

  const [exitingKey, setExitingKey] =
    useState<string | null>(null);

  const [recommendationError, setRecommendationError] =
    useState('');
  const [skippedKeys, setSkippedKeys] = useState<string[]>([]);

const rankingsDialogRef = useRef<HTMLDialogElement>(null);

const [sortMode, setSortMode] =
  useState<SortMode>('coverage_desc');

const sortedRecommendations = [...recommendations].sort((a, b) => {
  const originalOrder = a.rank - b.rank;
const cache = useQueryClient();

  if (sortMode === 'personalized') {
    return originalOrder;
  }

  if (sortMode === 'model_desc') {
    return b.score - a.score || originalOrder;
  }

  if (sortMode === 'model_asc') {
    return a.score - b.score || originalOrder;
  }

  const aCoverage = coreCoverage[a.career_key]?.overall_percentage;
  const bCoverage = coreCoverage[b.career_key]?.overall_percentage;

  if (aCoverage == null && bCoverage == null) {
    return originalOrder;
  }

  if (aCoverage == null) return 1;
  if (bCoverage == null) return -1;

  if (sortMode === 'coverage_desc') {
    return bCoverage - aCoverage || originalOrder;
  }

  return aCoverage - bCoverage || originalOrder;
});

const visibleRecommendations = sortedRecommendations
  .filter((item) => !skippedKeys.includes(item.career_key))
  .slice(0, 3);

  // Load the latest saved CV analysis.



  async function handleCvAnalysis(selectedFile: File): Promise<void> {
    if (!user?.id) {
      throw new Error('Please sign in to analyze your CV.');
    }

    setUploading(true);
    setRecommendationError('');

    try {
      const result = await uploadResume(selectedFile, user.id);

      const saved: SavedResumeAnalysis = {
        ...result,
        filename: selectedFile.name,
      };

      cache.setQueryData(queryKeys.savedCv(user.id), saved);
      cache.setQueryData(
        queryKeys.cvRecommendations(user.id),
        result.recommendations
      );

      setSkippedKeys([]);

      await cache.invalidateQueries({
        queryKey: queryKeys.coreCoverage(user.id),
      });

      await cache.invalidateQueries({
        queryKey: queryKeys.recordedSkills(user.id),
        refetchType: 'none',
      });

      await cache.invalidateQueries({
        queryKey: queryKeys.roadmaps(user.id),
        refetchType: 'none',
      });

      try {
        const updated = await refreshResumeRecommendations();

        cache.setQueryData(
          queryKeys.cvRecommendations(user.id),
          updated
        );
      } catch {
        setRecommendationError(
          'Showing initial recommendations. The full ranking could not be loaded.'
        );
      }
    } finally {
      setUploading(false);
    }
  }


  async function handleAvoid(careerKey: string): Promise<void> {
  if (processingKey !== null || savingKey !== null) return;

  setProcessingKey(careerKey);
  setRecommendationError('');

  try {
    const saved = await choose(careerKey, 'avoid');

    if (!saved) return;

    const updated = await refreshResumeRecommendations();

    setExitingKey(careerKey);

    await new Promise<void>((resolve) => {
      window.setTimeout(resolve, 260);
    });

    cache.setQueryData(
      queryKeys.cvRecommendations(userId),
      updated
    );
  } catch (err) {
    setRecommendationError(
      err instanceof Error
        ? err.message
        : 'Could not update recommendations.'
    );
  } finally {
    setExitingKey(null);
    setProcessingKey(null);
  }
}
function handleSkip(careerKey: string): void {
  if (processingKey !== null || savingKey !== null) return;

  setProcessingKey(careerKey);
  setExitingKey(careerKey);

  window.setTimeout(() => {
    setSkippedKeys((previous) =>
      previous.includes(careerKey)
        ? previous
        : [...previous, careerKey]
    );

    setExitingKey(null);
    setProcessingKey(null);
  }, 260);
}

async function handlePrefer(careerKey: string): Promise<void> {
  if (processingKey !== null || savingKey !== null) return;

  setProcessingKey(careerKey);
  setRecommendationError('');

  try {
    const saved = await choose(careerKey, 'preferred');
    if (!saved) return;

    const updated = await refreshResumeRecommendations();
    cache.setQueryData(
      queryKeys.cvRecommendations(userId),
      updated
    );
  } catch (err) {
    setRecommendationError(
      err instanceof Error
        ? err.message
        : 'Could not refresh career rankings.'
    );
  } finally {
    setProcessingKey(null);
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

    <CvUploadModal
      open={cvUploadOpen}
      onClose={() => setCvUploadOpen(false)}
      onAnalyze={handleCvAnalysis}
    />

    {/* CV analysis results */}

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

        {/* Random Forest career recommendations */}

        <article className="cf-cv-panel">
          <div className="cf-cv-panel-heading">
          <h3>Career recommendations</h3>

          <div className="cf-pref-heading-actions">
            <label htmlFor="cf-career-sort" className="cf-sort-label">
              Sort by
            </label>

            <select
              id="cf-career-sort"
              className="cf-career-sort"
              value={sortMode}
              onChange={(event) =>
                setSortMode(event.target.value as SortMode)
              }
              disabled={recommendationsLoading}
            >
              <option value="personalized">Personalized ranking</option>
              <option value="model_desc">Model score: High to Low</option>
              <option value="model_asc">Model score: Low to High</option>
              <option value="coverage_desc">Coverage: High to Low</option>
              <option value="coverage_asc">Coverage: Low to High</option>
            </select>

            <button
              type="button"
              className="cf-pref-text-link"
              disabled={recommendationsLoading || recommendations.length === 0}
              onClick={() => rankingsDialogRef.current?.showModal()}
            >
              View all rankings
            </button>
          </div>
        </div>

          {recommendationsLoading ? (
            <p className="cf-cv-muted" role="status">
              Loading personalized recommendations...
            </p>
          ) : visibleRecommendations.length > 0 ? (
            <div className="cf-cv-match-grid">
              {visibleRecommendations.map((recommendation, index) => {
                  const careerKey = recommendation.career_key;
                  const coverage = coreCoverage[careerKey];
                  const preference = preferenceFor(careerKey);
                  const exiting = exitingKey === careerKey;

                  const disabled =
                    preferencesLoading ||
                    savingKey !== null ||
                    processingKey !== null;

                  return (
                    <div
                      key={careerKey}
                      className={
                        'cf-cv-match-card' +
                        (exiting
                          ? ' cf-cv-match-card--exiting'
                          : '')
                      }
                    >
                      <div className="cf-cv-match-top">
                        <span className="cf-cv-rank">
                          {String(index + 1).padStart(2, '0')}
                        </span>

                        <div className="cf-pref-card-tools">
                          {preference === 'preferred' && (
                            <span className="cf-cv-match-state">
                              Preferred
                            </span>
                          )}

                          <button
                            type="button"
                            className="cf-pref-text-link"
                            disabled={disabled}
                            onClick={() => handleSkip(careerKey)}
                          >
                            Skip
                          </button>
                        </div>
                      </div>

                      <strong className="cf-cv-match-title">
                        {careerName(careerKey)}
                      </strong>

                      <div className="cf-cv-score-display">
                        <div className="cf-cv-score-heading">
                          <span>Documented skill coverage</span>

                          <strong>
                            {coverageLoading
                              ? '...'
                              : coverage?.overall_percentage != null
                                ? `${coverage.overall_percentage.toFixed(1)}%`
                                : 'Not assessed'}
                          </strong>
                        </div>

                        <div className="cf-cv-score-track" aria-hidden="true">
                          <span
                            style={{
                              width: `${coverage?.overall_percentage ?? 0}%`,
                            }}
                          />
                        </div>

                        <small className="cf-cv-coverage-detail">
                          {coverageLoading
                            ? 'Calculating coverage...'
                            : coverage?.overall_percentage != null
                              ? `${coverage.matched_core}/${coverage.total_core} core and ${coverage.matched_supporting}/${coverage.total_supporting} supporting groups documented`
                              : 'Coverage unavailable'}
                        </small>

                        <div className="cf-cv-model-secondary">
                          <span>Random Forest score</span>
                          <span>
                            {(recommendation.score * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>

                      <div className="cf-pref-actions">
                        <button
                          type="button"
                          className="cf-pref-btn"
                          aria-pressed={preference === 'preferred'}
                          disabled={disabled}
                          onClick={() => void handlePrefer(careerKey)}
                        >
                          Prefer
                        </button>

                        <button
                          type="button"
                          className="cf-pref-btn"
                          disabled={disabled}
                          onClick={() =>
                            void handleAvoid(careerKey)
                          }
                        >
                          Avoid
                        </button>
                      </div>
                    </div>
                  );
                })}
            </div>
          ) : (
            <p className="cf-cv-muted">
              No eligible career recommendations are available.
              You can review avoided careers in My Profile.
            </p>
          )}

          {recommendationError && (
            <p className="cf-cv-error" role="alert">
              {recommendationError}
            </p>
          )}

          {preferencesError && (
            <p className="cf-cv-error" role="alert">
              {preferencesError}
            </p>
          )}

          <p className="cf-cv-note">
            Coverage measures documented skill evidence against reviewed career requirements. Unassessed competencies are not credited. It does not verify proficiency or determine career suitability.
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
    <dialog
      ref={rankingsDialogRef}
      className="cf-cv-panel cf-pref-dialog"
    >
      <div className="cf-pref-dialog-header">
        <div>
          <h2>All career recommendations</h2>
          <p className="cf-cv-muted">
            Personalized ranking based on your Random Forest
            predictions and saved career preferences.
          </p>
        </div>

        <button
          type="button"
          className="cf-pref-text-link"
          onClick={() => rankingsDialogRef.current?.close()}
        >
          Close
        </button>
      </div>

      <div className="cf-pref-ranking-list">
        {sortedRecommendations.map((item, index) => {
          const coverage = coreCoverage[item.career_key];

          return (
            <div
              className="cf-pref-ranking-item"
              key={item.career_key}
            >
              <span className="cf-cv-rank">
                {String(index + 1).padStart(2, '0')}
              </span>

              <div className="cf-pref-ranking-name">
                <strong>{careerName(item.career_key)}</strong>

                {preferenceFor(item.career_key) === 'preferred' && (
                  <small>Preferred</small>
                )}

                {skippedKeys.includes(item.career_key) && (
                  <small>Skipped this session</small>
                )}
              </div>

              <div className="cf-pref-ranking-metrics">
                <strong>
                  {coverage?.overall_percentage != null
                    ? `${coverage.overall_percentage.toFixed(1)}% coverage`
                    : 'Coverage unavailable'}
                </strong>

                <span>
                  RF: {(item.score * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          );
        })}
      </div>

      <p className="cf-cv-note">
        Rankings reflect your preferences; RF scores remain
        unchanged. Avoided careers are managed in My Profile.
      </p>
    </dialog>
  </section>
);
}
