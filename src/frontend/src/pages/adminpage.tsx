import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {FiActivity, FiBookOpen, FiGrid, FiRefreshCw, FiShield, FiUsers,} from 'react-icons/fi';
import { onboardingApi } from '../lib/onboarding';
import type { Career } from '../lib/onboarding';
import {
  AdminApiError,
  getAdminIdentity,
  getAdminOverview,
  getAdminUsers,
  getAdminLogs,
  getAdminCareerResources,
  getAdminSystemHealth,
} from '../lib/admin';
import type {
  AdminIdentity,
  AdminOverview,
  AdminUsersPage,
  AdminLogsPage,
  AdminLogEvent,
  AdminCareerDetails,
  AdminSystemHealth,
} from '../lib/admin';
import AdminTotpModal from '../components/AdminTotpModal';
import { csrfHeader } from '../lib/auth';
import '../admin.css';
import MfaQrEnrollment from '../components/MfaQrEnrollment';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../context/AuthContext';
import { queryKeys } from '../lib/queryclient';

type Tab = 'overview' | 'users' | 'careers' | 'logs';
type Access = 'checking' | 'authorized' | 'denied' | 'error';
type UserAction = {
  user: AdminUsersPage['users'][number];
  mode: 'suspend' | 'reactivate' | 'delete';
  reason: string;
};

const navigation = [
  { id: 'overview', label: 'Overview', Icon: FiGrid },
  { id: 'users', label: 'Users', Icon: FiUsers },
  { id: 'careers', label: 'Career Catalog', Icon: FiBookOpen },
  { id: 'logs', label: 'System Logs', Icon: FiActivity },
] as const;

const HEALTH_SERVICES = [
  { key: 'database', label: 'Database' },
  { key: 'resource_catalog', label: 'Resource Catalog' },
  { key: 'logging', label: 'Logging' },
  { key: 'recommendation_model', label: 'Recommendation Model' },
  { key: 'ai_mentor', label: 'AI Mentor' },
] as const;

const formatNumber = (value: number) =>
  new Intl.NumberFormat().format(value);

function formatDate(value?: string) {
  if (!value) return '—';

  const date = new Date(value);

  return Number.isNaN(date.getTime())
    ? '—'
    : date.toLocaleString();
}

function readable(value: string) {
  return value.replace(/_/g, ' ');
}

function Metric({
  label,
  value,
}: {
  label: string;
  value?: number;
}) {
  return (
    <div className="cf-admin-metric">
      <strong>
        {value == null ? '—' : formatNumber(value)}
      </strong>
      <span>{label}</span>
    </div>
  );
}

function LogRow({ event }: { event: AdminLogEvent }) {
  return (
    <div className="cf-admin-log-row">
      <div className="cf-admin-log-top">
        <span
          className={`cf-admin-severity cf-admin-severity--${event.severity.toLowerCase()}`}
        >
          {event.severity}
        </span>

        <time>{formatDate(event.timestamp)}</time>
      </div>

      <strong>{readable(event.action)}</strong>

      <div className="cf-admin-log-details">
        <span>{event.category}</span>

        {event.duration_ms != null && (
          <span>
            Duration: {event.duration_ms.toFixed(2)} ms
          </span>
        )}

        {event.status_code != null && (
          <span>HTTP {event.status_code}</span>
        )}

        {event.actor_user_id != null && (
          <span>Actor #{event.actor_user_id}</span>
        )}

        {event.error_type && (
          <span>{event.error_type}</span>
        )}

        {event.route && (
          <code>{event.route}</code>
        )}
      </div>
    </div>
  );
}

export default function AdminPage() {
  const [access, setAccess] = useState<Access>('checking');
  const [admin, setAdmin] = useState<AdminIdentity | null>(null);
  const [accessError, setAccessError] = useState('');
  const [activeTab, setActiveTab] = useState<Tab>('overview');
  const { user } = useAuth();
  const userId = user?.id ?? '';
  const cache = useQueryClient();

  const [usersPage, setUsersPage] = useState(1);
  const [logsPage, setLogsPage] = useState(1);
  const [severity, setSeverity] = useState('');
  const [category, setCategory] = useState('');
  const [careerSearch, setCareerSearch] = useState('');
  const [userSearch, setUserSearch] = useState('');
  const [selectedCareerKey, setSelectedCareerKey] = useState('');

  const [pendingUserAction, setPendingUserAction] =
    useState<UserAction | null>(null);
  const [userActionBusy, setUserActionBusy] = useState(false);
  const [userActionError, setUserActionError] = useState('');
  const [userActionNotice, setUserActionNotice] = useState('');

  const authorized = access === 'authorized' && Boolean(userId);


  const overviewQuery = useQuery({
    queryKey: queryKeys.adminOverview(userId),
    queryFn: getAdminOverview,
    enabled: authorized && activeTab === 'overview',
    staleTime: 30_000,
  });

  const usersQuery = useQuery({
    queryKey: queryKeys.adminUsers(userId, usersPage),
    queryFn: () => getAdminUsers(usersPage),
    enabled: authorized && activeTab === 'users',
    staleTime: 30_000,
  });

  const careersQuery = useQuery({
    queryKey: queryKeys.careers,
    queryFn: onboardingApi.careers,
    enabled: authorized && activeTab === 'careers',
    staleTime: 30 * 60 * 1000,
  });

  const logsQuery = useQuery({
    queryKey: queryKeys.adminLogs(
      userId, logsPage, severity, category
    ),
    queryFn: () => getAdminLogs(logsPage, severity, category),
    enabled: authorized && activeTab === 'logs',
    staleTime: 15_000,
  });

  const healthQuery = useQuery({
    queryKey: queryKeys.adminHealth(userId),
    queryFn: getAdminSystemHealth,
    enabled: authorized && activeTab === 'overview',
    staleTime: 15_000,
    retry: 0,
  });

  const careerDetailsQuery = useQuery({
    queryKey: queryKeys.adminCareer(userId, selectedCareerKey),
    queryFn: () => getAdminCareerResources(selectedCareerKey),
    enabled:
      authorized &&
      activeTab === 'careers' &&
      Boolean(selectedCareerKey),
    staleTime: 60_000,
  });

  const overview: AdminOverview | null = overviewQuery.data ?? null;
  const users: AdminUsersPage | null = usersQuery.data ?? null;
  const careers: Career[] = careersQuery.data ?? [];
  const logs: AdminLogsPage | null = logsQuery.data ?? null;
  const systemHealth: AdminSystemHealth | null =
    healthQuery.data ?? null;
  const careerDetails: AdminCareerDetails | null =
    careerDetailsQuery.data ?? null;

  const activeQuery =
    activeTab === 'overview' ? overviewQuery :
    activeTab === 'users' ? usersQuery :
    activeTab === 'careers' ? careersQuery :
    logsQuery;

  const loading = authorized && activeQuery.isPending;
  const error = activeQuery.isError
    ? activeQuery.error.message
    : '';

  const healthLoading = healthQuery.isPending;
  const healthError = healthQuery.isError
    ? healthQuery.error.message
    : '';

  const careerDetailLoading =
    Boolean(selectedCareerKey) && careerDetailsQuery.isPending;

  const careerDetailError = careerDetailsQuery.isError
    ? careerDetailsQuery.error.message
    : '';

  function refreshAdmin() {
    if (!userId) return;

    void cache.invalidateQueries({
      queryKey: queryKeys.admin(userId),
    });

    if (activeTab === 'careers') {
      void cache.invalidateQueries({
        queryKey: queryKeys.careers,
      });
    }
  }

  // 1. Verify administrator authorization.

function requestUserAction(
  user: AdminUsersPage['users'][number],
  mode: UserAction['mode'],
) {
  if (user.role === 'admin' || user.id === admin?.id) return;

  setUserActionError('');
  setUserActionNotice('');

  let reason = '';

  if (mode === 'delete') {
    const typed = window.prompt(
      `Permanently delete ${user.email}?\n\n` +
      'This cannot be undone.\n\n' +
      'Type the account email to continue:'
    );

    if (typed !== user.email) {
      if (typed !== null) {
        setUserActionError('Email confirmation did not match.');
      }
      return;
    }
  }

  if (mode === 'suspend') {
    const entered = window.prompt('Reason for suspension:', '');
    if (entered === null) return;
    reason = entered.trim().slice(0, 500);
  }

  setPendingUserAction({ user, mode, reason });
}

async function confirmUserAction(code: string) {
  if (!pendingUserAction || userActionBusy) return;

  const { user, mode, reason } = pendingUserAction;
  setUserActionBusy(true);
  setUserActionError('');

  try {
    const endpoint = `/api/admin/users/${user.id}` +
      (mode === 'delete' ? '' : `/${mode}`);

    const response = await fetch(endpoint, {
      method: mode === 'delete' ? 'DELETE' : 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...csrfHeader(),
      },
      body: JSON.stringify(
        mode === 'delete'
          ? { totp_code: code, confirm_email: user.email }
          : { totp_code: code, reason }
      ),
    });

    if (!response.ok) {
      const result = await response.json().catch(() => null);
      throw new Error(
        typeof result?.detail === 'string'
          ? result.detail
          : `Action failed (HTTP ${response.status}).`
      );
    }

    setPendingUserAction(null);
    setUserActionNotice(
      mode === 'delete'
        ? 'Account deleted successfully.'
        : mode === 'suspend'
          ? 'Account suspended successfully.'
          : 'Account reactivated successfully.'
    );
    void cache.invalidateQueries({
      queryKey: queryKeys.admin(userId),
    });
  } catch (err) {
    setUserActionError(
      err instanceof Error ? err.message : 'Could not update account.'
    );
  } finally {
    setUserActionBusy(false);
  }
}


  useEffect(() => {
    if (!userId) return;

    let active = true;

    setAccess('checking');
    setAccessError('');

    void getAdminIdentity()
      .then((identity) => {
        if (!active) return;

        setAdmin(identity);
        setAccess('authorized');
      })
      .catch((cause: unknown) => {
        if (!active) return;

        setAdmin(null);

        if (
          cause instanceof AdminApiError &&
          (cause.status === 401 || cause.status === 403)
        ) {
          cache.removeQueries({
            queryKey: queryKeys.admin(userId),
          });

          setAccess('denied');
        } else {
          setAccess('error');
          setAccessError(
            cause instanceof Error
              ? cause.message
              : 'Could not verify administrator access.'
          );
        }
      });

    return () => {
      active = false;
    };
  }, [cache, userId]);


  // Conditional returns follow all React hooks.

  if (access === 'checking') {
    return (
      <section className="cf-admin-state" role="status">
        Verifying administrator access...
      </section>
    );
  }

  if (access === 'denied') {
    return (
      <section className="cf-admin-state">
        <FiShield size={30} />

        <h1>Access restricted</h1>

        <p>
          This workspace is available only to authorized
          CareerForge administrators.
        </p>

        <Link to="/dashboard">
          Return to your workspace
        </Link>
      </section>
    );
  }

  if (access === 'error') {
    return (
      <section className="cf-admin-state" role="alert">
        <h1>Administrator check unavailable</h1>

        <p>{accessError}</p>

        <Link to="/profile">
          Return to My Profile
        </Link>
      </section>
    );
  }

  const filteredCareers = careers.filter((career) => {
    const term = careerSearch.trim().toLowerCase();

    return (
      career.name.toLowerCase().includes(term) ||
      career.career_key.toLowerCase().includes(term)
    );
  });

  const filteredUsers = (users?.users ?? []).filter((user) => {
    const term = userSearch.trim().toLowerCase();

    return (
      user.full_name.toLowerCase().includes(term) ||
      user.email.toLowerCase().includes(term) ||
      String(user.id).includes(term)
    );
  });

  const checkingHealth =
    healthLoading || (!systemHealth && !healthError);

  return (
    <section className="cf-admin">
      <header className="cf-admin-header">
        <div>

          <h1 className="cf-admin-heading">System Administration</h1>

          <p>
            Monitor platform activity, users, career profiles
            and operational events.
          </p>
        </div>

        <div className="cf-admin-header-actions">
          <button
            type="button"
            onClick={refreshAdmin}
            disabled={loading}
          >
            <FiRefreshCw />
            Refresh
          </button>

          <Link to="/profile">
            Back to My Profile
          </Link>
        </div>
      </header>

      <div className="cf-admin-identity">
        <FiShield />

        <span>
          Signed in as <strong>{admin?.full_name}</strong>
        </span>

        <span className="cf-admin-identity-role">
          Administrator
        </span>
      </div>
      <div className="cf-admin-security-action">
        <MfaQrEnrollment
          mode="replace"
          onComplete={() => window.location.replace('/login')}
        />
      </div>

      <div className="cf-admin-workspace">
        <nav
          className="cf-admin-navigation"
          aria-label="Administration sections"
        >
          {navigation.map(({ id, label, Icon }) => (
            <button
              key={id}
              type="button"
              className={
                activeTab === id ? 'is-active' : ''
              }
              aria-current={
                activeTab === id ? 'page' : undefined
              }
              onClick={() => setActiveTab(id)}
            >
              <Icon />
              {label}
            </button>
          ))}
        </nav>

        <main className="cf-admin-content">
          {loading && (
            <p
              className="cf-admin-feedback"
              role="status"
            >
              Loading data...
            </p>
          )}

          {error && (
            <p
              className="cf-admin-error"
              role="alert"
            >
              {error}
            </p>
          )}

          {/* OVERVIEW */}

          {activeTab === 'overview' && (
            <div className="cf-admin-section">
              <div className="cf-admin-section-heading">
                <h2 className="cf-admin-heading">Overview</h2>

                <p>
                  Live account and activity totals from PostgreSQL.
                </p>
              </div>

              <div
                className="cf-admin-metrics"
                aria-busy={!overview && loading}
              >
                <Metric
                  label="Registered users"
                  value={overview?.users.total}
                />

                <Metric
                  label="Administrators"
                  value={overview?.users.administrators}
                />

                <Metric
                  label="Career profiles"
                  value={overview?.careers.total}
                />

                <Metric
                  label="Completed onboarding"
                  value={overview?.users.onboarding_completed}
                />
              </div>

              <div className="cf-admin-panel">
                <h3>Recorded platform activity</h3>

                <div className="cf-admin-metrics cf-admin-metrics-small">
                  <Metric
                    label="Recorded user skills"
                    value={
                      overview?.activity.recorded_user_skills
                    }
                  />

                  <Metric
                    label="Competency assessments"
                    value={
                      overview?.activity.competency_assessments
                    }
                  />
                </div>

                <p className="cf-admin-note">
                  These are cumulative records, not usage
                  statistics or verified learning outcomes.
                </p>
              </div>

              {/* Independent System Health Panel */}

              <div className="cf-admin-panel">
                <h3>System health</h3>

                <p>
                  Live status of CareerForge's supporting
                  services.
                </p>

                <div className="cf-admin-health-summary">
                  <strong>
                    {healthLoading
                      ? 'Checking services...'
                      : systemHealth
                        ? `Measured services: ${
                            systemHealth.status === 'healthy'
                              ? 'Healthy'
                              : 'Attention required'
                          }`
                        : healthError
                          ? 'Health checks unavailable'
                          : 'Waiting for health checks'}
                  </strong>

                  {systemHealth && (
                    <small>
                      Last checked:{' '}
                      {formatDate(systemHealth.checked_at)}
                    </small>
                  )}
                </div>

                {healthError && (
                  <p
                    className="cf-admin-error"
                    role="alert"
                  >
                    {healthError}
                  </p>
                )}

                <div
                  className="cf-admin-health-list"
                  aria-busy={checkingHealth}
                >
                  {HEALTH_SERVICES.map(({ key, label }) => {
                    const check =
                      systemHealth?.checks[key];

                    return (
                      <div
                        key={key}
                        className="cf-admin-health-row"
                      >
                        <div>
                          <strong>{label}</strong>

                          <small>
                            {checkingHealth
                              ? 'Checking service availability...'
                              : check?.message ??
                                'Health information unavailable.'}
                          </small>

                          {!checkingHealth &&
                            check?.latency_ms != null && (
                              <small>
                                Response:{' '}
                                {check.latency_ms} ms
                              </small>
                            )}
                        </div>

                        {checkingHealth ? (
                          <span
                            className="cf-admin-health-checking"
                            role="status"
                          >
                            <span
                              className="cf-admin-health-spinner"
                              aria-hidden="true"
                            />

                            Checking...
                          </span>
                        ) : (
                          <span
                            className={`cf-admin-health-status is-${
                              check?.status ?? 'not_checked'
                            }`}
                          >
                            {!check
                              ? 'Unavailable'
                              : check.status === 'healthy'
                                ? 'Healthy'
                                : check.status === 'unhealthy'
                                  ? 'Unhealthy'
                                  : 'Not checked'}
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {/* USERS */}

          {activeTab === 'users' && (
            <div className="cf-admin-section">
              <div className="cf-admin-section-heading">

                <h2 className="cf-admin-heading">Registered accounts</h2>

                <p>
                  Review registered accounts, manage access, and remove
                  users when necessary. Sensitive actions require
                  authenticator verification.
                </p>
              </div>

              <div className="cf-admin-toolbar">
                <input
                  aria-label="Filter visible users"
                  placeholder="Filter users on this page..."
                  value={userSearch}
                  onChange={(event) =>
                    setUserSearch(event.target.value)
                  }
                />

                <span>
                  {users
                    ? `${users.total} total accounts`
                    : ''}
                </span>
              </div>



              {userActionNotice && (
                <p className="cf-admin-note" role="status">
                  {userActionNotice}
                </p>
              )}

              {userActionError && !pendingUserAction && (
                <p className="cf-admin-error" role="alert">
                  {userActionError}
                </p>
              )}


              {users && (
                <>
                  <div className="cf-admin-table-scroll">
                    <table className="cf-admin-table">
                      <thead>
                        <tr>
                          <th>Account</th>
                          <th>Role</th>
                          <th>Onboarding</th>
                          <th>Registered</th>
                          <th>Status</th>
                          <th>Actions</th>
                        </tr>
                      </thead>

                      <tbody>
                        {filteredUsers.map((user) => (
                          <tr key={user.id}>
                            <td>
                              <strong>{user.full_name}</strong>
                              <small>{user.email}</small>
                              <small>#{user.id}</small>
                            </td>

                            <td>{user.role}</td>

                            <td>
                              {user.onboarding_completed
                                ? 'Completed'
                                : 'Pending'}
                            </td>

                            <td>
                              {formatDate(user.created_at)}
                            </td>
                            <td>
                              <span
                                className={
                                  user.suspended_at
                                    ? 'cf-admin-user-status is-suspended'
                                    : 'cf-admin-user-status is-active'
                                }
                              >
                                {user.suspended_at ? 'Suspended' : 'Active'}
                              </span>
                            </td>

                            <td>
                              {user.role === 'admin' || user.id === admin?.id ? (
                                <span className="cf-admin-user-protected">
                                  Protected
                                </span>
                              ) : (
                                <div className="cf-admin-user-actions">
                                  <button
                                    type="button"
                                    onClick={() => requestUserAction(
                                      user,
                                      user.suspended_at ? 'reactivate' : 'suspend'
                                    )}
                                  >
                                    {user.suspended_at ? 'Reactivate' : 'Suspend'}
                                  </button>

                                  <button
                                    type="button"
                                    className="cf-admin-user-delete"
                                    onClick={() => requestUserAction(user, 'delete')}
                                  >
                                    Delete
                                  </button>
                                </div>
                              )}
                            </td>

                          </tr>
                            ))}

                        {filteredUsers.length === 0 && (
                          <tr>
                            <td colSpan={6}>
                              No matching accounts.
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>

                  <div className="cf-admin-pagination">
                    <button
                      type="button"
                      disabled={
                        usersPage <= 1 || loading
                      }
                      onClick={() =>
                        setUsersPage((page) => page - 1)
                      }
                    >
                      Previous
                    </button>

                    <span>Page {usersPage}</span>

                    <button
                      type="button"
                      disabled={
                        loading ||
                        usersPage * users.page_size >=
                          users.total
                      }
                      onClick={() =>
                        setUsersPage((page) => page + 1)
                      }
                    >
                      Next
                    </button>
                  </div>
                </>
              )}
            </div>
          )}

          {/* CAREERS */}

          {activeTab === 'careers' && (
            <div className="cf-admin-section">
              <div className="cf-admin-section-heading">

                <h2 className="cf-admin-heading">Supported career paths</h2>

                <p>
                  Review the career profiles available
                  through CareerForge.
                </p>
              </div>
              <Link
                  to="/admin/resources"
                  className="cf-admin-manage-resources"
                >
                  <FiBookOpen />
                  Manage learning resources
                </Link>

              <div className="cf-admin-toolbar">
                <input
                  aria-label="Search career catalog"
                  placeholder="Search career paths..."
                  value={careerSearch}
                  onChange={(event) =>
                    setCareerSearch(event.target.value)
                  }
                />

                <span>
                  {careers.length} career records
                </span>
              </div>

              <div className="cf-admin-careers">
                {filteredCareers.map((career) => (
                  <button
                    key={career.career_key}
                    type="button"
                    className={
                      'cf-admin-career' +
                      (selectedCareerKey ===
                      career.career_key
                        ? ' is-selected'
                        : '')
                    }
                    aria-expanded={
                      selectedCareerKey ===
                      career.career_key
                    }
                    onClick={() =>
                      setSelectedCareerKey((current) =>
                        current === career.career_key
                          ? ''
                          : career.career_key
                      )
                    }
                  >
                    <strong>{career.name}</strong>

                    <code>{career.career_key}</code>

                    {career.description && (
                      <p>{career.description}</p>
                    )}

                    <span className="cf-admin-career-view">
                      {selectedCareerKey ===
                      career.career_key
                        ? 'Hide competencies'
                        : 'View competencies and resources'}
                    </span>
                  </button>
                ))}

                {filteredCareers.length === 0 && (
                  <p className="cf-admin-note">
                    No matching career profiles.
                  </p>
                )}
              </div>

              {selectedCareerKey && (
                <section className="cf-admin-panel cf-admin-career-details">
                  <h3>
                    Career competencies and learning resources
                  </h3>

                  {careerDetailLoading && (
                    <p className="cf-admin-note">
                      Loading resource mappings...
                    </p>
                  )}

                  {careerDetailError && (
                    <p
                      className="cf-admin-error"
                      role="alert"
                    >
                      {careerDetailError}
                    </p>
                  )}

                  {careerDetails && (
                    <>
                      <p className="cf-admin-note">
                        {careerDetails.covered_competencies}{' '}
                        of {careerDetails.competency_count}{' '}
                        competencies have catalog resource
                        mappings.{' '}
                        {careerDetails.unique_resources}{' '}
                        unique resources.
                      </p>

                      <div className="cf-admin-competency-list">
                        {careerDetails.competencies.map(
                          (competency) => (
                            <details
                              key={competency.key}
                              className="cf-admin-competency"
                            >
                              <summary>
                                <span>
                                  <strong>
                                    {competency.name}
                                  </strong>

                                  <small>
                                    {competency.level}
                                  </small>
                                </span>

                                <span>
                                  {competency.resources.length}{' '}
                                  resources
                                </span>
                              </summary>

                              <div className="cf-admin-resource-list">
                                {competency.resources.map(
                                  (resource) => (
                                    <a
                                      key={resource.url}
                                      href={resource.url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="cf-admin-resource"
                                    >
                                      <strong>
                                        {resource.title}
                                      </strong>

                                      <small>
                                        {resource.provider} ·{' '}
                                        {resource.resource_type}
                                      </small>

                                      {resource.description && (
                                        <p>
                                          {resource.description}
                                        </p>
                                      )}
                                    </a>
                                  )
                                )}

                                {competency.resources.length ===
                                  0 && (
                                  <p className="cf-admin-note">
                                    No learning resources mapped
                                    in the catalog.
                                  </p>
                                )}
                              </div>
                            </details>
                          )
                        )}
                      </div>
                    </>
                  )}
                </section>
              )}
            </div>
          )}

          {/* SYSTEM LOGS */}

          {activeTab === 'logs' && (
            <div className="cf-admin-section">
              <div className="cf-admin-section-heading">
                <h2 className="cf-admin-heading">System events</h2>

                <p>
                  Recent structured application and
                  administrative events.
                </p>
              </div>

              <div className="cf-admin-filters">
                <label>
                  Severity

                  <select
                    value={severity}
                    onChange={(event) => {
                      setSeverity(event.target.value);
                      setLogsPage(1);
                    }}
                  >
                    <option value="">
                      All levels
                    </option>

                    <option value="INFO">
                      Info
                    </option>

                    <option value="WARNING">
                      Warning
                    </option>

                    <option value="ERROR">
                      Error
                    </option>

                    <option value="CRITICAL">
                      Critical
                    </option>
                  </select>
                </label>

                <label>
                  Category

                  <select
                    value={category}
                    onChange={(event) => {
                      setCategory(event.target.value);
                      setLogsPage(1);
                    }}
                  >
                    <option value="">
                      All categories
                    </option>

                    <option value="admin">
                      Admin
                    </option>

                    <option value="application">
                      Application
                    </option>

                    <option value="security">
                      Security
                    </option>

                    <option value="model">
                      Machine learning
                    </option>

                    <option value="ai_mentor">
                      AI mentor
                    </option>

                    <option value="mentor">
                      AI mentor (legacy logs)
                    </option>

                    <option value="database">
                      Database
                    </option>
                  </select>
                </label>
              </div>

              {logs && (
                <>
                  <div className="cf-admin-log-list">
                    {logs.events.map((event, index) => (
                      <LogRow
                        key={`${event.timestamp}-${index}`}
                        event={event}
                      />
                    ))}

                    {logs.events.length === 0 && (
                      <p className="cf-admin-note">
                        No events match these filters.
                      </p>
                    )}
                  </div>

                  <div className="cf-admin-pagination">
                    <button
                      type="button"
                      disabled={
                        logsPage <= 1 || loading
                      }
                      onClick={() =>
                        setLogsPage((page) => page - 1)
                      }
                    >
                      Previous
                    </button>

                    <span>Page {logsPage}</span>

                    <button
                      type="button"
                      disabled={
                        !logs.has_more || loading
                      }
                      onClick={() =>
                        setLogsPage((page) => page + 1)
                      }
                    >
                      Next
                    </button>
                  </div>

                  <p className="cf-admin-note">
                    Showing a bounded recent log history.
                    Older events may be outside the retained
                    window. Log viewing itself is recorded.
                  </p>
                </>
              )}
            </div>
          )}
        </main>
      </div>

      <AdminTotpModal
        open={pendingUserAction !== null}
        title={
          pendingUserAction?.mode === 'delete'
            ? 'Permanently delete account'
            : pendingUserAction?.mode === 'suspend'
              ? 'Suspend account'
              : 'Reactivate account'
        }
        description={
          `Enter a fresh authenticator code to confirm this action for ` +
          `${pendingUserAction?.user.email ?? 'the selected account'}.`
        }
        busy={userActionBusy}
        error={userActionError}
        onClose={() => {
          if (userActionBusy) return;
          setPendingUserAction(null);
          setUserActionError('');
        }}
        onConfirm={confirmUserAction}
      />
    </section>
  );
}