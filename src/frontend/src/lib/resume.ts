
import { csrfHeader } from './auth';

export type CareerRecommendation = {
  rank: number;
  career_key: string;
  score: number;
};

export type ResumeAnalysis = {
  extracted_skills: string[];
  model_skills: string[];
  ignored_skills: string[];
  recommendations: CareerRecommendation[];
};

const MAX_FILE_SIZE = 5 * 1024 * 1024;

export async function uploadResume(
  file: File,
  userId: string
): Promise<ResumeAnalysis> {
  const extension = file.name.split('.').pop()?.toLowerCase();

  if (extension !== 'pdf' && extension !== 'docx') {
    throw new Error('Only PDF and DOCX files are supported.');
  }

  if (file.size === 0) {
    throw new Error('The selected file is empty.');
  }

  if (file.size > MAX_FILE_SIZE) {
    throw new Error('Your CV must not exceed 5 MB.');
  }

  const parsedUserId = Number(userId);

  if (!Number.isSafeInteger(parsedUserId) || parsedUserId <= 0) {
    throw new Error('Invalid authenticated user.');
  }

  const form = new FormData();
  form.append('file', file);
  form.append('user_id', String(parsedUserId));
  form.append('top_k', '5');

  let response: Response;

  try {
    response = await fetch('/api/recommendations/upload', {
      method: 'POST',
      credentials: 'include',
      headers: csrfHeader(),
      body: form,
    });
  } catch {
    throw new Error(
      'Cannot reach CareerForge. Check that FastAPI is running.'
    );
  }

  if (!response.ok) {
    const error = await response.json().catch(() => null);

    throw new Error(
      typeof error?.detail === 'string'
        ? error.detail
        : `CV analysis failed (HTTP ${response.status}).`
    );
  }

  return (await response.json()) as ResumeAnalysis;
}



export type SavedResumeAnalysis = ResumeAnalysis & {
  filename: string;
};

export async function getLatestResumeAnalysis():
  Promise<SavedResumeAnalysis | null> {

  let response: Response;

  try {
    response = await fetch(
      '/api/recommendations/resumes/latest',
      {
        method: 'GET',
        credentials: 'include',
      }
    );
  } catch {
    throw new Error(
      'Cannot connect to CareerForge. Check that FastAPI is running.'
    );
  }

  if (!response.ok) {
    throw new Error(
      `Could not load saved CV analysis (HTTP ${response.status}).`
    );
  }

  return (await response.json()) as SavedResumeAnalysis | null;
}

export async function refreshResumeRecommendations():
  Promise<CareerRecommendation[]> {

  const response = await fetch(
    '/api/recommendations/resumes/latest/recommendations',
    {
      method: 'POST',
      credentials: 'include',
      headers: csrfHeader(),
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => null);

    throw new Error(
      typeof error?.detail === 'string'
        ? error.detail
        : `Could not refresh recommendations (HTTP ${response.status}).`
    );
  }

  return (await response.json()) as CareerRecommendation[];
}