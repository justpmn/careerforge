
const BASE = '/api/admin';

export type AdminIdentity = {
  id: number;
  full_name: string;
  role: string;
};

export type AdminOverview = {
  users: {
    total: number;
    administrators: number;
    onboarding_completed: number;
  };
  careers: {
    total: number;
  };
  activity: {
    recorded_user_skills: number;
    competency_assessments: number;
  };
};

export type AdminUser = {
  id: number;
  full_name: string;
  email: string;
  role: string;
  onboarding_completed: boolean;
  created_at: string;
};

export type AdminUsersPage = {
  page: number;
  page_size: number;
  total: number;
  users: AdminUser[];
};

export type AdminLogEvent = {
  timestamp: string;
  severity: string;
  category: string;
  action: string;
  actor_user_id?: number;
  status_code?: number;
  error_type?: string;
  route?: string;
  duration_ms?: number;
};

export type AdminLogsPage = {
  events: AdminLogEvent[];
  page: number;
  page_size: number;
  window_count: number;
  has_more: boolean;
};

export class AdminApiError extends Error {
  constructor(
    message: string,
    public readonly status: number
  ) {
    super(message);
    this.name = 'AdminApiError';
  }
}

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    credentials: 'include',
    cache: 'no-store',
  });

  if (!response.ok) {
    const body: unknown = await response.json().catch(() => null);

    let message = `Request failed (HTTP ${response.status}).`;

    if (body && typeof body === 'object' && 'detail' in body) {
      const detail = (body as { detail?: unknown }).detail;
      if (typeof detail === 'string') message = detail;
    }

    throw new AdminApiError(message, response.status);
  }

  return (await response.json()) as T;
}

export function getAdminIdentity() {
  return request<AdminIdentity>('/me');
}

export function getAdminOverview() {
  return request<AdminOverview>('/overview');
}

export function getAdminUsers(page = 1) {
  return request<AdminUsersPage>(
    `/users?page=${page}&page_size=20`
  );
}

export function getAdminLogs(
  page = 1,
  severity = '',
  category = ''
) {
  const params = new URLSearchParams({
    page: String(page),
    page_size: '25',
  });

  if (severity) params.set('severity', severity);
  if (category) params.set('category', category);

  return request<AdminLogsPage>(`/logs?${params.toString()}`);
}

export type AdminCareerResource = {
  title: string;
  provider: string;
  resource_type: string;
  url: string;
  description: string;
};

export type AdminCareerCompetency = {
  key: string;
  name: string;
  level: string;
  resources: AdminCareerResource[];
};

export type AdminCareerDetails = {
  career_key: string;
  competency_count: number;
  covered_competencies: number;
  unique_resources: number;
  competencies: AdminCareerCompetency[];
};

export function getAdminCareerResources(
  careerKey: string
): Promise<AdminCareerDetails> {
  return request<AdminCareerDetails>(
    `/careers/${encodeURIComponent(careerKey)}/resources`
  );
}


export type AdminHealthCheck = {
  status: 'healthy' | 'unhealthy' | 'not_checked';
  message: string;
  latency_ms?: number | null;
  resources?: number;
  mappings?: number;
};

export type AdminSystemHealth = {
  status: 'healthy' | 'degraded';
  checked_at: string;
  checks: Record<string, AdminHealthCheck>;
};

export function getAdminSystemHealth(): Promise<AdminSystemHealth> {
  return request<AdminSystemHealth>('/health');
}
