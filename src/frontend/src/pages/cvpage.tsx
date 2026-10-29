
import { useEffect, useState } from 'react';
import type { ChangeEvent, FormEvent } from 'react';

import { useAuth } from '../context/AuthContext';

import {
  uploadResume,
  getLatestResumeAnalysis,
} from '../lib/resume';

import type { ResumeAnalysis } from '../lib/resume';



function careerName(key: string): string {
  return key
    .replace(/[_-]/g, ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}


export default function CvPage() {
  const { user } = useAuth();

  // Selected file
  const [file, setFile] = useState<File | null>(null);

  // CV analysis results
  const [analysis, setAnalysis] = useState<ResumeAnalysis | null>(null);
  const [analyzedFilename, setAnalyzedFilename] = useState('');

  // Loading states
  const [loadingSaved, setLoadingSaved] = useState(true);
  const [uploading, setUploading] = useState(false);

  // Error handling
  const [error, setError] = useState('');
  const [savedError, setSavedError] = useState('');


  // Load the latest saved CV analysis when the page opens.
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
        if (active) {
          setLoadingSaved(false);
        }
      }
    }

    void loadSavedAnalysis();

    return () => {
      active = false;
    };
  }, []);


  function selectFile(event: ChangeEvent<HTMLInputElement>) {
    const selected = event.target.files?.[0] ?? null;

    setFile(selected);
    setError('');
  }


  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (
      !file ||
      !user ||
      uploading ||
      loadingSaved
    ) {
      return;
    }

    setUploading(true);
    setError('');
    setSavedError('');

    try {
      const result = await uploadResume(file, user.id);

      // Display the new analysis immediately.
      setAnalysis(result);
      setAnalyzedFilename(file.name);

      // Clear the selected upload.
      setFile(null);

    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Could not analyze your CV.'
      );
    } finally {
      setUploading(false);
    }
  }


  return (
    <section className="cf-cv">

      <header className="cf-cv-header">
        <span className="cf-cv-eyebrow">MY CV</span>

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

      <article className="cf-cv-panel">
        <div className="cf-cv-panel-heading">
          <h2>Upload CV</h2>
          <span>PDF or DOCX · Max 5 MB</span>
        </div>

        <form onSubmit={handleUpload}>

          <label
            htmlFor="cv-file"
            className="cf-cv-upload-area"
          >
            <span
              className="cf-cv-upload-icon"
              aria-hidden="true"
            >
              +
            </span>

            <strong>
              {file ? file.name : 'Choose a file'}
            </strong>

            <span>
              {file
                ? `${(file.size / 1024 / 1024).toFixed(2)} MB`
                : 'Select your PDF or Word document'}
            </span>
          </label>

          <input
            id="cv-file"
            type="file"
            accept=".pdf,.docx"
            onChange={selectFile}
            disabled={uploading || loadingSaved}
            className="cf-cv-file-input"
          />

          {error && (
            <p role="alert" className="cf-cv-error">
              {error}
            </p>
          )}

          <div className="cf-cv-actions">
            <button
              type="submit"
              disabled={!file || uploading || loadingSaved}
              className="cf-cv-primary"
            >
              {uploading ? 'Analyzing CV...' : 'Analyze CV'}
            </button>
          </div>

        </form>
      </article>


      {/* Saved or newly generated analysis */}

      {analysis && (
        <div className="cf-cv-results" aria-live="polite">

          <div className="cf-cv-results-heading">
            <div>
              <span className="cf-cv-eyebrow">
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
                      <span className="cf-cv-rank">
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
