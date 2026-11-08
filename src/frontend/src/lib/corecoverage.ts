export type CoreSkillCoverage = {
  percentage: number | null;
  overall_percentage: number | null;
  matched_core: number;
  total_core: number;
  matched_supporting: number;
  total_supporting: number;
  self_reported_core: number;
  self_reported_supporting: number;
  manual_review_core: number;
  manual_review_supporting: number;
  missing_catalog_core: number;
  unmapped_groups: number;
};

export type CoreCoverageResults = Record<
  string,
  CoreSkillCoverage
>;

export async function getCoreSkillCoverage():
  Promise<CoreCoverageResults> {

  const response = await fetch(
    '/api/recommendations/core-skill-coverage',
    {
      credentials: 'include',
    }
  );

  if (!response.ok) {
    throw new Error(
      `Could not load core skill coverage (HTTP ${response.status}).`
    );
  }

  return (await response.json()) as CoreCoverageResults;
}

