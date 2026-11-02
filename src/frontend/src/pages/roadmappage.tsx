import { useEffect, useMemo, useState } from 'react';
import { Background, BackgroundVariant, Controls, ReactFlow } from '@xyflow/react';
import type { Edge, Node } from '@xyflow/react';
import dagre from '@dagrejs/dagre';
import '@xyflow/react/dist/style.css';
import '../roadmap.css';
import { useAuth } from '../context/AuthContext';
import { onboardingApi } from '../lib/onboarding';
import { getCareerRoadmap, getRecordedSkills } from '../lib/roadmap';
import { buildSkillTree } from '../lib/skilltreetemplates';
import type { CareerRoadmap, RecordedSkill } from '../lib/roadmap';
import type { SkillTreeItem } from '../lib/skilltreetemplates';
import SkillMapNode from '../components/skillmapnode';
import CompetencyEvidencePanel from '../components/competencyevidencepanel';
import {getLearningProgress,updateLearningProgress} from '../lib/learningprogress';
import '../roadmapprogress.css';
import CompetencyAssessmentPanel from '../components/competencyassessmentpanel';

const NODE_WIDTH = 126;
const NODE_HEIGHT = 112;

const statusLabels: Record<string, string> = {
  evidenced: 'Recorded evidence',
  evidence_found: 'Review evidence',
  not_assessed: 'Not assessed',
  not_evidenced: 'Not evidenced',
  self_reported: 'Manually recorded skill',
  confirm_self_reported_skill: 'Confirm your self-reported experience',
};

const actionLabels: Record<string, string> = {
  no_immediate_action: 'No immediate action',
  review_submitted_evidence: 'Review submitted evidence',
  review_resume_evidence: 'Review CV evidence',
  assess_competency: 'Assess this competency',
  confirm_skill_experience: 'Confirm your experience',
};

function readable(value: string): string {
  return value.replace(/_/g, ' ');
}

function safeLink(url?: string | null): string | null {
  if (!url) return null;

  try {
    const parsed = new URL(url);

    return ['http:', 'https:'].includes(parsed.protocol)
      ? parsed.href
      : null;
  } catch {
    return null;
  }
}


const nodeTypes = {
  skill: SkillMapNode,
};

const skillVisuals: Record<
  string,
  { label: string; glyph: string }
> = {
  // Data Scientist
  python: { label: 'Python', glyph: 'Py' },
  notebook_tooling: { label: 'Notebooks', glyph: 'NB' },
  sql: { label: 'SQL', glyph: 'SQL' },
  statistics_inference: { label: 'Statistics', glyph: 'Σ' },
  data_science_libraries: { label: 'ML Libraries', glyph: 'LIB' },
  data_preparation: { label: 'Data Preparation', glyph: 'DP' },
  exploratory_analysis: { label: 'Data Analysis', glyph: 'EDA' },
  visualization_tools: { label: 'Visualization', glyph: 'VIS' },
  ml_training: { label: 'Machine Learning', glyph: 'ML' },
  model_evaluation: { label: 'Model Evaluation', glyph: 'EV' },
  data_communication: { label: 'Communication', glyph: 'COM' },
  
  // Backend Developer
  programming: { label: 'Programming', glyph: 'PF' },
  version_control: { label: 'Git', glyph: 'GIT' },
  backend_runtime: { label: 'Backend Frameworks', glyph: 'BE' },
  database: { label: 'Databases', glyph: 'DB' },
  api: { label: 'API Development', glyph: 'API' },
  debugging: { label: 'Debugging', glyph: 'DBG' },
  authentication_security: { label: 'Authentication', glyph: 'SEC' },
  testing: { label: 'Testing', glyph: 'TST' },
  deployment: { label: 'Deployment', glyph: 'DEP' },
  ci_cd: { label: 'CI/CD', glyph: 'CI' },

  
  // Data Engineer
  data_programming: { label: 'Programming', glyph: 'PY' },
  sql_querying: { label: 'SQL', glyph: 'SQL' },
  data_storage: { label: 'Data Storage', glyph: 'DB' },
  data_modeling: { label: 'Data Modeling', glyph: 'DM' },
  pipeline_design: { label: 'Data Pipelines', glyph: 'ETL' },
  data_quality: { label: 'Data Quality', glyph: 'DQ' },
  cloud_platform: { label: 'Cloud', glyph: 'CLD' },
  containers: { label: 'Containers', glyph: 'CTR' },

};


function skillVisual(item: SkillTreeItem) {
  const predefined = skillVisuals[item.id];

  if (predefined) return predefined;

  const title = item.title.trim();

  const words = title.match(/[A-Za-z0-9]+/g) ?? [];


return {
  label: title,
  glyph:
    words
      .slice(0, 2)
      .map((word) => word[0].toUpperCase())
      .join('') || 'SK',
};

  
}


function getPrerequisitePath(
  items: SkillTreeItem[],
  focusId: string | null
): Set<string> {
  const path = new Set<string>();

  if (!focusId) return path;

  const byId = new Map(
    items.map((item) => [item.id, item])
  );

  function visit(id: string) {
    if (path.has(id)) return;

    path.add(id);

    for (const prerequisite of byId.get(id)?.requires ?? []) {
      visit(prerequisite);
    }
  }

  visit(focusId);
  return path;
}



// Lay out the dependency graph only when the roadmap changes.
// Node selection is applied separately; pointer movement never reruns Dagre.
function layoutSkillGraph(
  items: SkillTreeItem[]
): { nodes: Node[]; edges: Edge[] } {
  const layout = new dagre.graphlib.Graph();

  layout.setDefaultEdgeLabel(() => ({}));
  layout.setGraph({
    rankdir: 'LR',
    nodesep: 80,
    ranksep: 110,
    marginx: 60,
    marginy: 60,
  });

  const ids = new Set(items.map((item) => item.id));
  const statuses = new Map(
    items.map((item) => [item.id, item.step?.status ?? item.status ?? 'unlinked'])
  );

  const nodes: Node[] = items.map((item) => {
    const visual = skillVisual(item);
    layout.setNode(item.id, {
      width: NODE_WIDTH,
      height: NODE_HEIGHT,
    });

    return {
      id: item.id,
      type: 'skill',
      position: { x: 0, y: 0 },
      draggable: false,
      data: {
        title: item.title,
        label: visual.label,
        glyph: visual.glyph,
        status: statuses.get(item.id) ?? 'unlinked',
        related: false,
        dimmed: false,
      },
    };
  });

  const edges: Edge[] = [];

  for (const item of items) {
    for (const prerequisite of item.requires) {
      if (!ids.has(prerequisite)) continue;

      layout.setEdge(prerequisite, item.id);
      const completed =
        statuses.get(prerequisite) === 'evidenced' &&
        statuses.get(item.id) === 'evidenced';

      edges.push({
        id: `${prerequisite}:${item.id}`,
        source: prerequisite,
        target: item.id,
        type: 'smoothstep',
        animated: false,
        className: completed ? 'cf-edge-achieved' : '',
        style: {
          stroke: completed ? '#57c894' : 'var(--muted)',
          strokeWidth: completed ? 2.2 : 1.3,
          opacity: completed ? 0.95 : 0.36,
        },
      });
    }
  }

  dagre.layout(layout);

  return {
    nodes: nodes.map((node) => {
      const position = layout.node(node.id);
      return {
        ...node,
        position: {
          x: position.x - NODE_WIDTH / 2,
          y: position.y - NODE_HEIGHT / 2,
        },
      };
    }),
    edges,
  };
}

type FoundationResource = {
  id?: number;
  title: string;
  provider?: string | null;
  url?: string | null;
  description?: string | null;
  explanation?: string | null;
  reason?: string | null;
};

export default function RoadmapPage() {
  const { user } = useAuth();
  const userId = user?.id;
  const [roadmap, setRoadmap] = useState<CareerRoadmap | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [needsCareer, setNeedsCareer] = useState(false);
  const [recordedSkills, setRecordedSkills] = useState<RecordedSkill[]>([]);
  const [learnedByKey, setLearnedByKey] = useState<Record<string, boolean>>({});
  const [savingLearned, setSavingLearned] = useState(false);
  const [learningError, setLearningError] = useState('');
    
  const [selectedResources, setSelectedResources] =
  useState<FoundationResource[]>([]);

const [selectedResourcesLoading, setSelectedResourcesLoading] =
  useState(false);

const [selectedResourcesError, setSelectedResourcesError] =
  useState('');


  useEffect(() => {
    if (!userId) {
      setLoading(false);
      return;
    }

    let active = true;

    async function initialize() {
      setLoading(true);
      setError('');
      setNeedsCareer(false);

      try {
        const career = await onboardingApi.selectedCareer();

        if (!active) return;

        if (!career.career_key) {
          setNeedsCareer(true);
          return;
        }

        const [result, skills, progress] = await Promise.all([
          getCareerRoadmap(userId!, career.career_key),
          getRecordedSkills(),
          getLearningProgress(career.career_key),
        ]);

        if (!active) return;

        setRoadmap(result);
        setRecordedSkills(skills);
        setLearnedByKey(Object.fromEntries(
          progress.map((item) => [item.skill_key, item.learned])
        ));
        setLearningError('');
        setSelectedId(null);
      } catch (err) {
        if (!active) return;

        setError(
          err instanceof Error
            ? err.message
            : 'Could not load your skill tree.'
        );
      } finally {
        if (active) setLoading(false);
      }
    }

    void initialize();

    return () => {
      active = false;
    };
  }, [userId]);



  const tree = useMemo(() => {
    if (!roadmap) return null;

    const nonManualSkills = recordedSkills.filter(
      (skill) =>
        (skill as { source?: string }).source !== 'manual'
    );

    return buildSkillTree(roadmap, nonManualSkills);
  }, [roadmap, recordedSkills]);

  // Calculate graph positions only when roadmap data changes.
  const baseGraph = useMemo(() => {
    const items = tree
      ? tree.hasTemplate
        ? tree.connected
        : tree.unmapped
      : [];

    return layoutSkillGraph(items);
  }, [tree]);
  // Update visual highlighting without recalculating layout.

  const graph = useMemo(() => {
    const items = tree
      ? tree.hasTemplate
        ? tree.connected
        : tree.unmapped
      : [];

    const hasSelection =
      selectedId !== null && items.some((item) => item.id === selectedId);
    const upstream = getPrerequisitePath(items, selectedId);
    const nextSkills = new Set(
      items
        .filter((item) => selectedId !== null && item.requires.includes(selectedId))
        .map((item) => item.id)
    );

    const statusById = new Map(
      items.map((item) => [item.id, item.step?.status ?? item.status ?? 'unlinked'])
    );

    const skillKeyByNodeId = new Map(
      items.map((item) => [item.id, item.step?.competency_key ?? item.id])
    );

    const nodes = baseGraph.nodes.map((node) => {
      const related = upstream.has(node.id) || nextSkills.has(node.id);
      const skillKey = skillKeyByNodeId.get(node.id) ?? node.id;

      return {
        ...node,
        selected: node.id === selectedId,
        data: {
          ...node.data,
          related: hasSelection && related,
          dimmed: hasSelection && !related,
          learned: Boolean(learnedByKey[skillKey]),
        },
      };
    });

    const edges = baseGraph.edges.map((edge) => {
      const completed =
        statusById.get(edge.source) === 'evidenced' &&
        statusById.get(edge.target) === 'evidenced';

      const highlighted =
        hasSelection &&
        ((upstream.has(edge.source) && upstream.has(edge.target)) ||
          edge.source === selectedId);

      return {
        ...edge,
        animated: false,
        className: [
          completed ? 'cf-edge-achieved' : '',
          highlighted ? 'cf-edge-focused' : '',
        ]
          .filter(Boolean)
          .join(' '),
        style: {
          ...edge.style,
          stroke: completed
            ? '#57c894'
            : highlighted
              ? 'var(--accent)'
              : 'var(--muted)',
          strokeWidth: highlighted ? 2.5 : completed ? 2.2 : 1.3,
          opacity: highlighted ? 1 : completed ? 0.95 : 0.36,
        },
      };
    });

    return { nodes, edges };
  }, [tree, baseGraph, selectedId, learnedByKey]);

  const selectedItem = [
    ...(tree?.connected ?? []),
    ...(tree?.unmapped ?? []),
  ].find((item) => item.id === selectedId);

  const step = selectedItem?.step;
  const selectedStatus = step?.status ?? selectedItem?.status ?? 'unlinked';
  const selectedSkillKey = step?.competency_key ?? selectedItem?.id;
  
useEffect(() => {
  const careerKey = roadmap?.career_key;
  const skillKey = selectedSkillKey;

  setSelectedResources([]);
  setSelectedResourcesError('');

  if (!careerKey || !skillKey) {
    setSelectedResourcesLoading(false);
    return;
  }

  const controller = new AbortController();
  setSelectedResourcesLoading(true);

  async function fetchSkillResources() {
    try {
      const url =
        `/api/roadmaps/skill-resources/` +
        `${encodeURIComponent(careerKey!)}/` +
        `${encodeURIComponent(skillKey!)}`;

      const response = await fetch(url, {
        credentials: 'include',
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(
          `Unable to load resources (HTTP ${response.status}).`
        );
      }

      const data: unknown = await response.json();

      if (
        !data ||
        typeof data !== 'object' ||
        !('resources' in data) ||
        !Array.isArray(data.resources)
      ) {
        throw new Error('Invalid learning resource response.');
      }

      if (!controller.signal.aborted) {
        setSelectedResources(
          data.resources as FoundationResource[]
        );
      }
    } catch (error) {
      if (!controller.signal.aborted) {
        setSelectedResourcesError(
          error instanceof Error
            ? error.message
            : 'Unable to retrieve learning resources.'
        );
      }
    } finally {
      if (!controller.signal.aborted) {
        setSelectedResourcesLoading(false);
      }
    }
  }

  void fetchSkillResources();

  return () => controller.abort();
}, [roadmap?.career_key, selectedSkillKey]);

  const isLearned = Boolean(selectedSkillKey && learnedByKey[selectedSkillKey]);
  
const resources =
  selectedResourcesLoading
    ? []
    : selectedResources.length > 0
      ? selectedResources
      : step?.suggested_resources ?? [];

  async function toggleLearned() {
    if (!roadmap || !selectedSkillKey || savingLearned) return;

    setSavingLearned(true);
    setLearningError('');
    try {
      const saved = await updateLearningProgress(
        roadmap.career_key,
        selectedSkillKey,
        !isLearned
      );
      setLearnedByKey((previous) => ({
        ...previous,
        [saved.skill_key]: saved.learned,
      }));
    } catch (cause) {
      setLearningError(
        cause instanceof Error ? cause.message : 'Could not save learning progress.'
      );
    } finally {
      setSavingLearned(false);
    }
  }

  if (loading) {
    return (
      <div className="cf-roadmap-state">
        Loading your skill tree...
      </div>
    );
  }

  if (error) {
    return (
      <div className="cf-roadmap-state" role="alert">
        {error}
      </div>
    );
  }

  if (needsCareer) {
    return (
      <div className="cf-roadmap-state">
        Select a target career before viewing your roadmap.
      </div>
    );
  }

  if (!roadmap || !tree) return null;

  return (
    <section className="cf-roadmap">
      <header className="cf-roadmap-header">
        <div>
          <span className="cf-roadmap-eyebrow">
            LEARNING ROADMAP
          </span>

          <h1>{roadmap.career_name}</h1>

          <p>
            Follow connected skills, explore branches and
            select a node to view your next steps.
          </p>
        </div>

        <span className="cf-roadmap-step-count">
          {roadmap.steps.length} competencies
        </span>
      </header>

      {!tree.hasTemplate && (
        <p className="cf-roadmap-info">
          This career does not have a dependency template
          yet. Its competencies are shown without invented
          prerequisite connections.
        </p>
      )}

      <div className="cf-roadmap-map">
        <ReactFlow
            key={roadmap.career_key}
            nodeTypes={nodeTypes}
            nodes={graph.nodes}
            edges={graph.edges}
            fitView
            fitViewOptions={{ padding: 0.18, maxZoom: 1.1 }}
            minZoom={0.2}
            maxZoom={1.8}
            nodesDraggable={false}
            nodesConnectable={false}
            onNodeClick={(_, node) => setSelectedId(node.id)}
            onPaneClick={() => setSelectedId(null)}
            proOptions={{ hideAttribution: false }}
            >
          <Background
            variant={BackgroundVariant.Dots}
            gap={24}
            size={1}
            color="var(--line)"
          />

          <Controls
            position="bottom-left"
            showInteractive={false}
          />
        </ReactFlow>

        <div className="cf-roadmap-map-hint">
          Drag to pan · Scroll to zoom · Select a skill
        </div>

        {selectedItem && (
          <aside
            className="cf-skill-inspector"
            aria-label="Selected skill details"
          >
            <div className="cf-skill-inspector-top">
              <span className="cf-roadmap-eyebrow">
                SELECTED SKILL
              </span>

              <button
                type="button"
                onClick={() => setSelectedId(null)}
                aria-label="Close skill details"
                className="cf-skill-inspector-close"
              >
                ×
              </button>
            </div>

            <h2>{selectedItem.title}</h2>

            <div className="cf-skill-inspector-tags">
              {step && (
                <span>{readable(step.level)}</span>
              )}

              <span>
                {statusLabels[selectedStatus] ??
                  (selectedStatus === 'unlinked'
                    ? 'Assessment not linked'
                    : readable(selectedStatus))}
              </span>
            </div>

            {selectedItem.requires.length > 0 && (
              <div className="cf-skill-inspector-section">
                <h3>Builds on</h3>

                <p>
                  {selectedItem.requires
                    .map(
                      (id) =>
                        tree.connected.find(
                          (item) => item.id === id
                        )?.title ?? id
                    )
                    .join(' · ')}
                </p>
              </div>
            )}

            {step?.description && (
              <p className="cf-skill-description">
                {step.description}
              </p>
            )}

            <div className="cf-skill-inspector-section">
              <h3>Next action</h3>

              <p>
                {step
                  ? actionLabels[step.next_action] ??
                    readable(step.next_action)
                  : selectedItem?.source === 'resume'
                    ? 'This skill was identified in your uploaded CV. Review your experience to confirm proficiency; this does not represent independently verified mastery.'
                    : selectedItem?.source
                      ? 'This skill is recorded in your profile. Review its supporting evidence to confirm proficiency.'
                      : 'No matching skill record was found. You can assess or document your experience.'}
              </p>
            </div>
            
            {step?.competency_key && (
              <CompetencyAssessmentPanel
                key={`${roadmap.career_key}:${step.competency_key}`}
                careerKey={roadmap.career_key}
                competencyKey={step.competency_key}
              />
            )}

              {step?.competency_key && userId != null && (
                <CompetencyEvidencePanel
                  key={`${roadmap.career_key}:${step.competency_key}`}
                  userId={userId}
                  careerKey={roadmap.career_key}
                  competencyKey={step.competency_key}
                  onSaved={async () => {
                    const refreshedRoadmap = await getCareerRoadmap(
                      userId,
                      roadmap.career_key
                    );

                    setRoadmap(refreshedRoadmap);
                  }}
                />
              )}


            {step?.priority_group && (
              <div className="cf-skill-inspector-section">
                <h3>Priority</h3>

                <p>{readable(step.priority_group)}</p>
              </div>
            )}

            <div className="cf-skill-inspector-section">
              <h3>Learning resources</h3>

              {selectedResourcesLoading ? (
                <p>Loading learning resources...</p>
              ) : selectedResourcesError ? (
                <p role="alert">{selectedResourcesError}</p>
              ) : resources.length > 0 ? (
                <div className="cf-skill-resources">
                  {resources.map((resource, index) => {
                    const url = safeLink(resource.url);

                    return (
                      <div
                        key={`${resource.id ?? index}-${resource.title}`}
                        className="cf-skill-resource"
                      >
                        {url ? (
                          <a
                            href={url}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            {resource.title} ↗
                          </a>
                        ) : (
                          <strong>{resource.title}</strong>
                        )}

                        {resource.provider && (
                          <small>{resource.provider}</small>
                        )}

                        {(resource.description ??
                          resource.explanation ??
                          resource.reason) && (
                          <p>
                            {resource.description ??
                              resource.explanation ??
                              resource.reason}
                          </p>
                        )}
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p>
                  No learning resources are linked
                  to this skill yet.
                </p>
              )}
            </div>

            <div className="cf-skill-inspector-section cf-learning-section">
              <h3>Your learning progress</h3>
              <p className="cf-learning-helper">
                When you've finished studying, mark this skill as learned.
                This is self-reported and does not verify proficiency.
              </p>
              <button
                type="button"
                className={`cf-learning-toggle ${isLearned ? 'is-learned' : ''}`}
                aria-pressed={isLearned}
                disabled={savingLearned}
                onClick={() => void toggleLearned()}
              >
                {savingLearned
                  ? 'Saving…'
                  : isLearned
                    ? '✓ Learned · Undo'
                    : 'Mark as learned'}
              </button>
              {learningError && (
                <p className="cf-learning-error" role="alert">{learningError}</p>
              )}
              {isLearned && (
                <p className="cf-learning-helper">
                  Next: build something using this skill, then update and upload
                  your CV so CareerForge can identify supporting evidence.
                </p>
              )}
            </div>
          </aside>
        )}
      </div>

      {tree.hasTemplate && tree.unmapped.length > 0 && (
        <div className="cf-roadmap-unmapped">
          <h3>
            Other competencies
            <span> · Connections not mapped yet</span>
          </h3>

          <div className="cf-roadmap-unmapped-list">
            {tree.unmapped.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => setSelectedId(item.id)}
              >
                {item.title}
              </button>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}