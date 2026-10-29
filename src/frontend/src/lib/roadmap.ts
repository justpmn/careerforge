export type RoadmapResource = {
  id?: number;
  title: string;
  provider?: string | null;
  url?: string | null;
  description?: string | null;
  explanation?: string | null;
  reason?: string | null;
};

export type RoadmapStep = {
  competency_key: string;
  competency: string;
  level: string;
  status: string;
  next_action: string;
  description?: string | null;
  priority_group?: string | null;
  learning_required?: boolean;
  suggested_resources?: RoadmapResource[];
};

export type CareerRoadmap = {
  career_key: string;
  career_name: string;
  total_steps: number;
  roadmap_type?: string;
  steps: RoadmapStep[];
};

export async function getCareerRoadmap(
  userId: string,
  careerKey: string
): Promise<CareerRoadmap> {
  const url =
    `/api/roadmaps/users/${encodeURIComponent(userId)}` +
    `/careers/${encodeURIComponent(careerKey)}`;

  const response = await fetch(url, {
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await response.json().catch(() => null);

    throw new Error(
      typeof error?.detail === 'string'
        ? error.detail
        : `Could not load roadmap (HTTP ${response.status}).`
    );
  }

  const data = await response.json();

  if (!data || !Array.isArray(data.steps)) {
    throw new Error('Unexpected roadmap response from FastAPI.');
  }

  return data as CareerRoadmap;
}
