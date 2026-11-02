
import { csrfHeader } from './auth';

const API_BASE = '/api/roadmaps';

export type CatalogSkill = {
  id: number;
  name: string;
  category: string | null;
};

export type ManualSkill = CatalogSkill & {
  source: 'manual';
  status: string;
};

type CatalogResponse = {
  query: string;
  skills: CatalogSkill[];
};

type ManualSkillsResponse = {
  skills: ManualSkill[];
};

async function readError(response: Response): Promise<string> {
  const body: unknown = await response.json().catch(() => null);

  if (body && typeof body === 'object' && 'detail' in body) {
    const detail = (body as { detail?: unknown }).detail;

    if (typeof detail === 'string') {
      return detail;
    }
  }

  return `Request failed (HTTP ${response.status}).`;
}

export async function searchSkillCatalog(
  query: string
): Promise<CatalogSkill[]> {
  const term = query.trim();

  if (term.length < 2) return [];

  const response = await fetch(
    `${API_BASE}/skill-catalog?query=${encodeURIComponent(term)}`,
    { credentials: 'include' }
  );

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  const result: CatalogResponse = await response.json();

  if (!Array.isArray(result.skills)) {
    throw new Error('Unexpected skill catalog response.');
  }

  return result.skills;
}

export async function getManualSkills(): Promise<ManualSkill[]> {
  const response = await fetch(
    `${API_BASE}/manual-skills`,
    { credentials: 'include' }
  );

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  const result: ManualSkillsResponse = await response.json();

  if (!Array.isArray(result.skills)) {
    throw new Error('Unexpected manual skills response.');
  }

  return result.skills;
}

export async function addManualSkill(
  skillId: number
): Promise<ManualSkill> {
  const response = await fetch(
    `${API_BASE}/manual-skills`,
    {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...csrfHeader(),
      },
      body: JSON.stringify({ skill_id: skillId }),
    }
  );

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return (await response.json()) as ManualSkill;
}

export async function removeManualSkill(
  skillId: number
): Promise<void> {
  const response = await fetch(
    `${API_BASE}/manual-skills/${encodeURIComponent(String(skillId))}`,
    {
      method: 'DELETE',
      credentials: 'include',
      headers: csrfHeader(),
    }
  );

  if (!response.ok) {
    throw new Error(await readError(response));
  }
}
