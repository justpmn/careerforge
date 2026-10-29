import { useEffect, useMemo, useState } from 'react';
import { Background, BackgroundVariant, Controls, ReactFlow } from '@xyflow/react';
import type { Edge, Node } from '@xyflow/react';
import dagre from '@dagrejs/dagre';
import '@xyflow/react/dist/style.css';
import '../roadmap.css';
import { useAuth } from '../context/AuthContext';
import { onboardingApi } from '../lib/onboarding';
import { getCareerRoadmap } from '../lib/roadmap';
import { buildSkillTree } from '../lib/skilltreetemplates';
import type { CareerRoadmap } from '../lib/roadmap';
import type { SkillTreeItem } from '../lib/skilltreetemplates';
import SkillMapNode from '../components/skillmapnode';

const NODE_WIDTH = 126;
const NODE_HEIGHT = 112;

const statusLabels: Record<string, string> = {
  evidenced: 'Recorded evidence',
  evidence_found: 'Review evidence',
  not_assessed: 'Not assessed',
  not_evidenced: 'Not evidenced',
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
};

function skillVisual(item: SkillTreeItem) {
  const predefined = skillVisuals[item.id];

  if (predefined) return predefined;

  const title = item.title.trim();

  const words = title.match(/[A-Za-z0-9]+/g) ?? [];

  return {
    label:
      title.length > 27
        ? `${title.slice(0, 24).trimEnd()}…`
        : title,
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
    items.map((item) => [item.id, item.step?.status ?? 'unlinked'])
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


export default function RoadmapPage() {
  const { user } = useAuth();
  const userId = user?.id;
  const [roadmap, setRoadmap] = useState<CareerRoadmap | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [needsCareer, setNeedsCareer] = useState(false);

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

        const result = await getCareerRoadmap(
          userId!,
          career.career_key
        );

        if (!active) return;

        setRoadmap(result);
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

  const tree = useMemo(
    () => (roadmap ? buildSkillTree(roadmap) : null),
    [roadmap]
  );

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
      items.map((item) => [item.id, item.step?.status ?? 'unlinked'])
    );

    const nodes = baseGraph.nodes.map((node) => {
      const related = upstream.has(node.id) || nextSkills.has(node.id);

      return {
        ...node,
        selected: node.id === selectedId,
        data: {
          ...node.data,
          related: hasSelection && related,
          dimmed: hasSelection && !related,
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
  }, [tree, baseGraph, selectedId]);

  const selectedItem = [
    ...(tree?.connected ?? []),
    ...(tree?.unmapped ?? []),
  ].find((item) => item.id === selectedId);

  const step = selectedItem?.step;
  const resources = step?.suggested_resources ?? [];

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
                {step
                  ? statusLabels[step.status] ??
                    readable(step.status)
                  : 'Assessment not linked'}
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
                  : 'This foundation has not been linked to an assessed competency yet.'}
              </p>
            </div>

            {step?.priority_group && (
              <div className="cf-skill-inspector-section">
                <h3>Priority</h3>

                <p>{readable(step.priority_group)}</p>
              </div>
            )}

            <div className="cf-skill-inspector-section">
              <h3>Learning resources</h3>

              {resources.length > 0 ? (
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
