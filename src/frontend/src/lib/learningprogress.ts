import { csrfHeader } from './auth';

export type LearningSkill = {
  skill_key: string;
  learned: boolean;
};

async function readError(response: Response): Promise<string> {
  const body: unknown = await response.json().catch(() => null);
  if (body && typeof body === 'object' && 'detail' in body) {
    const detail = (body as { detail?: unknown }).detail;
    if (typeof detail === 'string') return detail;
  }
  return `Learning progress request failed (HTTP ${response.status}).`;
}

export async function getLearningProgress(
  careerKey: string
): Promise<LearningSkill[]> {
  const response = await fetch(
    `/api/roadmaps/learning-progress/${encodeURIComponent(careerKey)}`,
    { credentials: 'include' }
  );
  if (!response.ok) throw new Error(await readError(response));
  const data: unknown = await response.json();
  if (!data || typeof data !== 'object' || !('skills' in data) ||
      !Array.isArray(data.skills)) {
    throw new Error('Unexpected learning progress response.');
  }
  return data.skills as LearningSkill[];
}

export async function updateLearningProgress(
  careerKey: string,
  skillKey: string,
  learned: boolean
): Promise<LearningSkill> {
  const response = await fetch(
    `/api/roadmaps/learning-progress/${encodeURIComponent(careerKey)}/${encodeURIComponent(skillKey)}`,
    {
      method: 'PUT',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json', ...csrfHeader() },
      body: JSON.stringify({ learned }),
    }
  );
  if (!response.ok) throw new Error(await readError(response));
  return (await response.json()) as LearningSkill;
}
