
import { csrfHeader } from './auth';

export type ProficiencyLevel =
  | 'beginner'
  | 'intermediate'
  | 'advanced';

export type CompetencyAssessment = {
  competency_key: string;
  proficiency_level: ProficiencyLevel;
  notes: string | null;
  verification_status: string;
  created_at: string;
  updated_at: string;
};

export type AssessmentUpdate = {
  proficiency_level: ProficiencyLevel;
  notes: string | null;
};

type AssessmentListResponse = {
  career_key: string;
  assessments: CompetencyAssessment[];
};

const BASE_URL = '/api/roadmaps/competency-assessments';

async function readError(response: Response): Promise<string> {
  const body: unknown = await response.json().catch(() => null);

  if (body && typeof body === 'object' && 'detail' in body) {
    const detail = (body as { detail?: unknown }).detail;

    if (typeof detail === 'string') {
      return detail;
    }
  }

  return `Assessment request failed (HTTP ${response.status}).`;
}

export async function getCompetencyAssessments(
  careerKey: string
): Promise<CompetencyAssessment[]> {
  const response = await fetch(
    `${BASE_URL}/${encodeURIComponent(careerKey)}`,
    {
      credentials: 'include',
    }
  );

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  const result: AssessmentListResponse = await response.json();

  if (!Array.isArray(result.assessments)) {
    throw new Error('Unexpected assessment response.');
  }

  return result.assessments;
}

export async function saveCompetencyAssessment(
  careerKey: string,
  competencyKey: string,
  payload: AssessmentUpdate
): Promise<CompetencyAssessment> {
  const response = await fetch(
    `${BASE_URL}/${encodeURIComponent(careerKey)}/` +
      encodeURIComponent(competencyKey),
    {
      method: 'PUT',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...csrfHeader(),
      },
      body: JSON.stringify(payload),
    }
  );

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return (await response.json()) as CompetencyAssessment;
}
