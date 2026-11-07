
import { csrfHeader } from './auth';

export type CompetencyEvidenceType =
  | 'project'
  | 'experience'
  | 'certification';

export type CompetencyEvidence = {
  id: number;
  competency_key: string;
  evidence_type: CompetencyEvidenceType;
  description: string;
  verification_status: string;
  created_at: string;
};

export type CompetencyEvidenceCreate = {
  competency_key: string;
  evidence_type: CompetencyEvidenceType;
  description: string;
};

type EvidenceListResponse = {
  user_id: number;
  career_key: string;
  evidence: CompetencyEvidence[];
};

type UserId = number | string;

function evidenceUrl(
  userId: UserId,
  careerKey: string
): string {
  return (
    `/api/users/${encodeURIComponent(String(userId))}` +
    `/careers/${encodeURIComponent(careerKey)}` +
    '/competency-evidence'
  );
}

async function readError(
  response: Response
): Promise<string> {
  const body: unknown = await response.json().catch(() => null);

  if (
    body &&
    typeof body === 'object' &&
    'detail' in body
  ) {
    const detail = (
      body as { detail?: unknown }
    ).detail;

    if (typeof detail === 'string') {
      return detail;
    }
  }

  return `Evidence request failed (HTTP ${response.status}).`;
}

/**
 * Retrieve evidence submitted by the authenticated
 * user for a particular career.
 */
export async function getCompetencyEvidence(
  userId: UserId,
  careerKey: string
): Promise<CompetencyEvidence[]> {
  const response = await fetch(
    evidenceUrl(userId, careerKey),
    {
      method: 'GET',
      credentials: 'include',
    }
  );

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  const result: EvidenceListResponse =
    await response.json();

  if (!Array.isArray(result.evidence)) {
    throw new Error(
      'Unexpected competency evidence response.'
    );
  }

  return result.evidence;
}

/**
 * Submit evidence for one competency.
 *
 * The backend records this as self-reported,
 * not independently verified.
 */
export async function submitCompetencyEvidence(
  userId: UserId,
  careerKey: string,
  payload: CompetencyEvidenceCreate
): Promise<CompetencyEvidence> {
  const description = payload.description.trim();

  if (!description) {
    throw new Error(
      'Please describe your competency evidence.'
    );
  }

  if (description.length > 5000) {
    throw new Error(
      'Evidence descriptions must be 5000 characters or fewer.'
    );
  }

  const response = await fetch(
    evidenceUrl(userId, careerKey),
    {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...csrfHeader(),
      },
      body: JSON.stringify({
        ...payload,
        description,
      }),
    }
  );

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return (await response.json()) as CompetencyEvidence;
}
