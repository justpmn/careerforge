
import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { csrfHeader } from '../lib/auth';
import AdminTotpModal from '../components/AdminTotpModal';
import '../adminresourcepage.css';

type Assignment = {
  career_key: string;
  competency_key: string;
};

type Resource = {
  id: number;
  title: string;
  provider: string | null;
  resource_type: string;
  url: string;
  description: string | null;
  archived_at: string | null;
  assignments: Assignment[];
  skills: SkillOption[];
};

type ResourceAction = {
  id: number;
  title: string;
  mode: 'archive' | 'restore';
};


type ResourceList = {
  total: number;
  page: number;
  page_size: number;
  resources: Resource[];
};

type CareerOption = {
  key: string;
  name: string;
  competencies: { key: string; name: string }[];
};

type SkillOption = {
  id: number;
  name: string;
  category?: string | null;
};


type MappingMode = 'global' | 'career' | 'both';

type ResourceDraft = {
  title: string;
  provider: string;
  resource_type: string;
  url: string;
  description: string;
};

const emptyDraft: ResourceDraft = {
  title: '',
  provider: '',
  resource_type: 'course',
  url: '',
  description: '',
};

const emptyAssignment = (): Assignment => ({
  career_key: '',
  competency_key: '',
});

async function api<T>(
  path: string,
  method = 'GET',
  data?: object,
): Promise<T> {
  const response = await fetch(path, {
    method,
    credentials: 'include',
    cache: 'no-store',
    headers: data
      ? {
          'Content-Type': 'application/json',
          ...csrfHeader(),
        }
      : {},
    ...(data ? { body: JSON.stringify(data) } : {}),
  });

  const body = await response.json().catch(() => null);

  if (!response.ok) {
    const detail = body?.detail;
    const message =
      typeof detail === 'string'
        ? detail
        : typeof detail?.message === 'string'
          ? detail.message
          : `Request failed (HTTP ${response.status}).`;

    throw new Error(message);
  }

  return body as T;
}

export default function AdminResourcesPage() {
  const [resources, setResources] = useState<Resource[]>([]);
  const [careers, setCareers] = useState<CareerOption[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [includeArchived, setIncludeArchived] = useState(false);
  const [reload, setReload] = useState(0);
  const [loading, setLoading] = useState(true);
  const [listError, setListError] = useState('');
  const [optionsError, setOptionsError] = useState('');

  const [showCreate, setShowCreate] = useState(false);
  const [editingResource, setEditingResource] = useState<Resource | null>(null);
  const [draft, setDraft] = useState<ResourceDraft>(emptyDraft);
  const [assignments, setAssignments] = useState<Assignment[]>([
    emptyAssignment(),
  ]);
  const [mappingMode, setMappingMode] = useState<MappingMode>('global');
  const [skillSearch, setSkillSearch] = useState('');
  const [skillOptions, setSkillOptions] = useState<SkillOption[]>([]);
  const [selectedSkills, setSelectedSkills] = useState<SkillOption[]>([]);
  const [skillError, setSkillError] = useState('');
  const [totpOpen, setTotpOpen] = useState(false);
  const [totpError, setTotpError] = useState('');
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState('');
  const [notice, setNotice] = useState('');
  const [pendingResourceAction, setPendingResourceAction] =
    useState<ResourceAction | null>(null);
  const [resourceActionBusy, setResourceActionBusy] = useState(false);
  const [resourceActionError, setResourceActionError] = useState('');


  useEffect(() => {
    let active = true;

    api<{ careers: CareerOption[] }>('/api/admin/resources/options')
      .then((result) => {
        if (active) setCareers(result.careers);
      })
      .catch((err: unknown) => {
        if (active) {
          setOptionsError(
            err instanceof Error
              ? err.message
              : 'Could not load career options.'
          );
        }
      });

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;

    const timer = setTimeout(() => {
      setLoading(true);
      setListError('');

      const params = new URLSearchParams({
        q: search.trim(),
        page: String(page),
        page_size: '20',
        include_archived: String(includeArchived),
      });

      api<ResourceList>(`/api/admin/resources?${params}`)
        .then((result) => {
          if (!active) return;

          setResources(result.resources);
          setTotal(result.total);
        })
        .catch((err: unknown) => {
          if (!active) return;

          setListError(
            err instanceof Error
              ? err.message
              : 'Unable to load resources.'
          );
        })
        .finally(() => {
          if (active) setLoading(false);
        });
    }, 250);

    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [search, page, includeArchived, reload]);
useEffect(() => {
  if (mappingMode === 'career') return;

  let active = true;

  const timer = setTimeout(() => {
    setSkillError('');

    api<{ skills: SkillOption[] }>(
      `/api/admin/resources/skills?q=${encodeURIComponent(skillSearch)}&limit=30`
    )
      .then((result) => {
        if (active) setSkillOptions(result.skills);
      })
      .catch((error: unknown) => {
        if (active) {
          setSkillError(
            error instanceof Error
              ? error.message
              : 'Unable to search skills.'
          );
        }
      });
  }, 250);

  return () => {
    active = false;
    clearTimeout(timer);
  };
}, [mappingMode, skillSearch]);

function updateAssignment(index: number, value: Assignment) {
    setAssignments((current) =>
      current.map((item, i) => (i === index ? value : item))
    );
  }
function openCreateForm() {
  if (saving) return;

  setEditingResource(null);
  setDraft({ ...emptyDraft });
  setAssignments([emptyAssignment()]);
  setSelectedSkills([]);
  setMappingMode('global');
  setSkillSearch('');
  setFormError('');
  setTotpError('');
  setNotice('');
  setShowCreate(true);
}

function openEditForm(resource: Resource) {
  if (saving || resourceActionBusy || resource.archived_at) return;

  const hasSkills = resource.skills.length > 0;
  const hasAssignments = resource.assignments.length > 0;

  setEditingResource(resource);
  setDraft({
    title: resource.title,
    provider: resource.provider ?? '',
    resource_type: resource.resource_type,
    url: resource.url,
    description: resource.description ?? '',
  });

  setSelectedSkills(
    resource.skills.map((skill) => ({
      ...skill,
      category: skill.category ?? null,
    }))
  );

  setAssignments(
    hasAssignments
      ? resource.assignments.map((item) => ({ ...item }))
      : [emptyAssignment()]
  );

  setMappingMode(
    hasSkills && hasAssignments
      ? 'both'
      : hasAssignments
        ? 'career'
        : 'global'
  );

  setSkillSearch('');
  setFormError('');
  setTotpError('');
  setNotice('');
  setShowCreate(true);

  window.scrollTo({ top: 0, behavior: 'smooth' });
}


function closeCreateForm() {
  if (saving) return;

  setShowCreate(false);
  setEditingResource(null);
  setTotpOpen(false);
  setTotpError('');
  setFormError('');
}

function createResource(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError('');
    setTotpError('');
    setNotice('');

    const useSkills = mappingMode !== 'career';
    const useCareers = mappingMode !== 'global';
    if (useSkills && selectedSkills.length === 0) {
    setFormError('Select at least one global skill.');
    return;
    }

    if (
    useCareers &&
    assignments.some((item) =>
        !item.career_key || !item.competency_key
    )
    ) {
    setFormError('Complete every career competency assignment.');
    return;
    }

    if (useCareers) {
    const unique = new Set(
        assignments.map(
        (item) => `${item.career_key}:${item.competency_key}`
        )
    );

    if (unique.size !== assignments.length) {
        setFormError('Remove duplicate competency assignments.');
        return;
    }
    }

    setTotpOpen(true);
  }


async function confirmCreateResource(code: string) {
  if (saving) return;

  const editingId = editingResource?.id;
  setSaving(true);
  setTotpError('');

  try {
    const saved = await api<{ id: number }>(
      editingId !== undefined
        ? `/api/admin/resources/${editingId}`
        : '/api/admin/resources',
      editingId !== undefined ? 'PATCH' : 'POST',
      {
        ...draft,
        skill_ids: mappingMode !== 'career'
          ? selectedSkills.map((skill) => skill.id)
          : [],
        assignments: mappingMode !== 'global'
          ? assignments
          : [],
        totp_code: code,
      }
    );

    setTotpOpen(false);
    setShowCreate(false);
    setEditingResource(null);
    setNotice(
      `Resource #${saved.id} ${
        editingId !== undefined ? 'updated' : 'created'
      } successfully.`
    );

    setDraft({ ...emptyDraft });
    setAssignments([emptyAssignment()]);
    setSelectedSkills([]);
    setMappingMode('global');
    setSkillSearch('');
    setSearch('');
    setPage(1);
    setIncludeArchived(false);
    setReload((value) => value + 1);
  } catch (err) {
    setTotpError(
      err instanceof Error
        ? err.message
        : 'Unable to save resource.'
    );
  } finally {
    setSaving(false);
  }
}
  
function requestResourceAction(resource: Resource) {
  setResourceActionError('');
  setPendingResourceAction({
    id: resource.id,
    title: resource.title,
    mode: resource.archived_at ? 'restore' : 'archive',
  });
}

async function confirmResourceAction(code: string) {
  if (!pendingResourceAction) return;

  const action = pendingResourceAction;
  setResourceActionBusy(true);
  setResourceActionError('');
  setNotice('');

  try {
    const path = `/api/admin/resources/${action.id}`;
    const endpoint = action.mode === 'restore'
      ? `${path}/restore`
      : path;

    await api<unknown>(
      endpoint,
      action.mode === 'archive' ? 'DELETE' : 'POST',
      { totp_code: code },
    );

    setPendingResourceAction(null);
    setNotice(
      `"${action.title}" ${
        action.mode === 'archive' ? 'archived' : 'restored'
      } successfully.`
    );

    if (
      action.mode === 'archive' &&
      !includeArchived &&
      resources.length === 1 &&
      page > 1
    ) {
      setPage((value) => value - 1);
    }

    setReload((value) => value + 1);
  } catch (err) {
    setResourceActionError(
      err instanceof Error
        ? err.message
        : 'Unable to update resource status.'
    );
  } finally {
    setResourceActionBusy(false);
  }
}


  return (
    <main className="cf-resources">
      <Link to="/admin" className="cf-resources-back">
        ← Back to admin dashboard
      </Link>

      <header className="cf-resources-header">
        <div>
          <div className="cf-resources-eyebrow">
            ADMIN
          </div>
          <h1>Learning resources</h1>
          <p>
            Maintain the resources available in career learning roadmaps.
          </p>
        </div>

        <button
          type="button"
          className="cf-resources-primary"
          onClick={() => {
          if (showCreate) {
            closeCreateForm();
          } else {
            openCreateForm();
          }
        }}
        >
          {showCreate
          ? editingResource
            ? 'Close editor'
            : 'Close form'
          : '+ Add resource'}
        </button>
      </header>

      {notice && (
        <p className="cf-resources-notice" role="status">
          {notice}
        </p>
      )}

      {showCreate && (
        <section
          className="cf-resources-panel"
          aria-labelledby="new-resource-heading"
        >
          <div className="cf-resources-section-header">
            <h2 id="new-resource-heading">
            {editingResource
              ? `Edit resource #${editingResource.id}`
              : 'New learning resource'}
          </h2>
          </div>

          <form
            onSubmit={createResource}
            className="cf-resources-form"
          >
            <div className="cf-resources-fields">
              <label>
                Resource title
                <input
                  required
                  maxLength={255}
                  value={draft.title}
                  onChange={(e) =>
                    setDraft({ ...draft, title: e.target.value })
                  }
                  placeholder="e.g. Python testing fundamentals"
                />
              </label>

              <label>
                Provider
                <input
                  maxLength={150}
                  value={draft.provider}
                  onChange={(e) =>
                    setDraft({ ...draft, provider: e.target.value })
                  }
                  placeholder="e.g. Python Software Foundation"
                />
              </label>

              <label>
                Resource type
                <select
                  value={draft.resource_type}
                  onChange={(e) =>
                    setDraft({
                      ...draft,
                      resource_type: e.target.value,
                    })
                  }
                >
                  <option value="course">Course</option>
                  <option value="documentation">Documentation</option>
                  <option value="tutorial">Tutorial</option>
                  <option value="video">Video</option>
                  <option value="article">Article</option>
                  <option value="project">Project</option>
                  <option value="resource">Other resource</option>
                </select>
              </label>

              <label>
                Resource URL
                <input
                  type="url"
                  required
                  maxLength={500}
                  pattern="https://.*"
                  value={draft.url}
                  onChange={(e) =>
                    setDraft({ ...draft, url: e.target.value })
                  }
                  placeholder="https://..."
                />
              </label>
            </div>

            <label>
              Description
              <textarea
                rows={3}
                maxLength={5000}
                value={draft.description}
                onChange={(e) =>
                  setDraft({
                    ...draft,
                    description: e.target.value,
                  })
                }
                placeholder="What will learners gain from this resource?"
              />
            </label>

                            
                <div className="cf-resources-section-header">
                <h3>Resource mapping</h3>
                </div>
                <div className="cf-resources-scope">
                {([
                    ['global', 'Global skills'],
                    ['career', 'Career-specific'],
                    ['both', 'Both'],
                ] as const).map(([value, label]) => (
                    <label key={value}>
                    <input
                        type="radio"
                        name="mapping-mode"
                        value={value}
                        checked={mappingMode === value}
                        onChange={() => setMappingMode(value)}
                    />
                    {label}
                    </label>
                ))}
                </div>

                {mappingMode !== 'career' && (
                <div className="cf-resources-skill-picker">
                    <label>
                    Search skills or programming languages
                    <input
                        type="search"
                        value={skillSearch}
                        onChange={(event) => setSkillSearch(event.target.value)}
                        placeholder="Try Python, JavaScript, SQL, Docker..."
                    />
                    </label>

                    {skillError && (
                    <p className="cf-resources-error" role="alert">
                        {skillError}
                    </p>
                    )}

                    <div className="cf-resources-skill-results">
                    {skillOptions.map((skill) => {
                        const selected = selectedSkills.some(
                        (item) => item.id === skill.id
                        );

                        return (
                        <button
                            type="button"
                            key={skill.id}
                            disabled={selected}
                            onClick={() =>
                            setSelectedSkills((current) => [...current, skill])
                            }
                        >
                            {selected ? '✓ ' : '+ '}
                            {skill.name}
                        </button>
                        );
                    })}
                    </div>

                    {selectedSkills.length > 0 && (
                    <div className="cf-resources-selected-skills">
                        {selectedSkills.map((skill) => (
                        <button
                            type="button"
                            key={skill.id}
                            onClick={() =>
                            setSelectedSkills((current) =>
                                current.filter((item) => item.id !== skill.id)
                            )
                            }
                            title={`Remove ${skill.name}`}
                        >
                            {skill.name} ×
                        </button>
                        ))}
                    </div>
                    )}

                    <p className="cf-resources-help">
                    Skill-linked resources can appear across careers where
                    the selected skills are part of a competency.
                    </p>
                </div>
                )}

                {mappingMode !== 'global' && (
                <>
                    <div className="cf-resources-section-header">
                    <h3>Career competency assignments</h3>
                    <span>OPTIONAL CAREER-SPECIFIC MAPPING</span>
                    </div>

                    {assignments.map((item, index) => {
                    const career = careers.find(
                        (option) => option.key === item.career_key
                    );

                    return (
                        <div className="cf-resources-assignment" key={index}>
                        <label>
                            Career
                            <select
                            required
                            value={item.career_key}
                            onChange={(event) =>
                                updateAssignment(index, {
                                career_key: event.target.value,
                                competency_key: '',
                                })
                            }
                            >
                            <option value="">Select career</option>
                            {careers.map((option) => (
                                <option key={option.key} value={option.key}>
                                {option.name}
                                </option>
                            ))}
                            </select>
                        </label>

                        <label>
                            Competency
                            <select
                            required
                            disabled={!career}
                            value={item.competency_key}
                            onChange={(event) =>
                                updateAssignment(index, {
                                ...item,
                                competency_key: event.target.value,
                                })
                            }
                            >
                            <option value="">Select competency</option>
                            {career?.competencies.map((option) => (
                                <option key={option.key} value={option.key}>
                                {option.name}
                                </option>
                            ))}
                            </select>
                        </label>

                        <button
                            type="button"
                            className="cf-resources-text-button"
                            disabled={assignments.length === 1}
                            onClick={() =>
                            setAssignments((current) =>
                                current.filter((_, i) => i !== index)
                            )
                            }
                        >
                            Remove
                        </button>
                        </div>
                    );
                    })}

                    <button
                    type="button"
                    className="cf-resources-text-button"
                    disabled={assignments.length >= 50}
                    onClick={() =>
                        setAssignments((current) => [
                        ...current,
                        emptyAssignment(),
                        ])
                    }
                    >
                    + Add another assignment
                    </button>
                </>
                )}


            {formError && (
              <p className="cf-resources-error" role="alert">
                {formError}
              </p>
            )}

            <div className="cf-resources-actions">
              <button
                type="button"
                className="cf-resources-secondary"
                disabled={saving}
                onClick={closeCreateForm}
              >
                Cancel
              </button>

              <button
                type="submit"
                className="cf-resources-primary"
                disabled={saving || careers.length === 0}
              >
                {editingResource
                ? 'Save changes & verify'
                : 'Continue to verification'}
              </button>
            </div>
          </form>
        </section>
      )}

      <section
        className="cf-resources-panel"
        aria-labelledby="catalog-heading"
      >
        <div className="cf-resources-section-header">
          <h2 id="catalog-heading">Resource catalog</h2>
          <span>{total} RESOURCES</span>
        </div>

        <div className="cf-resources-toolbar">
          <input
            type="search"
            aria-label="Search learning resources"
            placeholder="Search title, provider or URL..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
          />

          <label className="cf-resources-check">
            <input
              type="checkbox"
              checked={includeArchived}
              onChange={(e) => {
                setIncludeArchived(e.target.checked);
                setPage(1);
              }}
            />
            Include archived
          </label>
        </div>

        {listError && (
          <p className="cf-resources-error" role="alert">
            {listError}
          </p>
        )}

        <div className="cf-resources-table-wrap">
          <table className="cf-resources-table">
            <thead>
              <tr>
                <th>Resource</th>
                <th>Type</th>
                <th>Assignments</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>

            <tbody>
              {!loading && resources.length === 0 && (
               <tr><td colSpan={5}>No resources found.</td></tr>
              )}


              {resources.map((resource) => (
                <tr key={resource.id}>
                  <td>
                    <a
                      href={resource.url}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      {resource.title}
                    </a>
                    <small>
                      {resource.provider || 'Unknown provider'}
                      {' · '}#{resource.id}
                    </small>
                  </td>

                  <td>{resource.resource_type}</td>

                  <td>
                    <strong>{resource.skills?.length ?? 0} global skills</strong>
                    <small>
                      {resource.skills?.map((skill) => skill.name).join(', ') || '—'}
                    </small>
                    <small>
                      {resource.assignments.length} direct assignments
                    </small>
                  </td>

                  <td>
                    <span className="cf-resources-status">
                      {resource.archived_at ? 'Archived' : 'Active'}
                    </span>
                  </td>

                  <td>
                    <div className="cf-resources-row-actions">
                      <button
                        type="button"
                        className="cf-resources-action-btn"
                        disabled={
                          Boolean(resource.archived_at) ||
                          saving ||
                          resourceActionBusy
                        }
                        onClick={() => openEditForm(resource)}
                        title={
                          resource.archived_at
                            ? 'Restore this resource before editing'
                            : 'Edit learning resource'
                        }
                        aria-label={`Edit ${resource.title}`}
                      >
                        Edit
                      </button>

                      <button
                        type="button"
                        className={`cf-resources-action-btn ${
                          resource.archived_at
                            ? 'cf-resources-action-restore'
                            : 'cf-resources-action-archive'
                        }`}
                        disabled={saving || resourceActionBusy}
                        onClick={() => requestResourceAction(resource)}
                        aria-label={`${
                          resource.archived_at ? 'Restore' : 'Archive'
                        } ${resource.title}`}
                      >
                        {resource.archived_at ? 'Restore' : 'Archive'}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}

            </tbody>
          </table>
        </div>

        <footer className="cf-resources-pagination">
          <span>
            {loading
              ? 'Loading resources...'
              : `Page ${page} of ${Math.max(
                  1,
                  Math.ceil(total / 20)
                )}`}
          </span>

          <div>
            <button
              type="button"
              disabled={page <= 1 || loading}
              onClick={() => setPage((value) => value - 1)}
            >
              Previous
            </button>

            <button
              type="button"
              disabled={page * 20 >= total || loading}
              onClick={() => setPage((value) => value + 1)}
            >
              Next
            </button>
          </div>
        </footer>
      </section>

      <AdminTotpModal
        open={totpOpen}
        title={
          editingResource
            ? 'Confirm resource changes'
            : 'Confirm resource creation'
        }
        description={
          editingResource
            ? `Enter a fresh authenticator code to save changes to "${editingResource.title}".`
            : 'Enter a fresh authenticator code to add this learning resource to CareerForge.'
        }
        busy={saving}
        error={totpError}
        onClose={() => {
          if (saving) return;
          setTotpOpen(false);
          setTotpError('');
        }}
        onConfirm={confirmCreateResource}
      />
      
        <AdminTotpModal
        open={pendingResourceAction !== null}
        title={
            pendingResourceAction?.mode === 'archive'
            ? 'Archive learning resource'
            : 'Restore learning resource'
        }
        description={
            pendingResourceAction?.mode === 'archive'
            ? `Enter a fresh authenticator code to archive "${pendingResourceAction.title}". It will no longer appear in active learning recommendations.`
            : `Enter a fresh authenticator code to restore "${pendingResourceAction?.title}". It will become available to learners again.`
        }
        busy={resourceActionBusy}
        error={resourceActionError}
        onClose={() => {
            if (resourceActionBusy) return;
            setPendingResourceAction(null);
            setResourceActionError('');
        }}
        onConfirm={confirmResourceAction}
        />

    </main>
  );
}
