import type {CareerRoadmap, RoadmapStep, RecordedSkill} from './roadmap';



type CareerTemplate = {
  version: number;
  nodes: TemplateNode[];
};

type TemplateNode = {
  id: string;
  title: string;
  requires: string[];
  skillAliases?: string[];
};

export type SkillTreeItem = {
  id: string;
  title: string;
  requires: string[];
  step?: RoadmapStep;
  status?: string;
  source?: string | null;
  unmapped?: boolean;
};

const templates: Record<string, CareerTemplate> = {
  data_scientist: {
    version: 1,
    nodes: [
    {
    id: 'python',
    title: 'Python Programming',
    requires: [],
    skillAliases: ['Python', 'Python 3'],
    },

      {
        id: 'notebook_tooling',
        title: 'Interactive Analysis Environments',
        requires: ['python'],
      },
      {
        id: 'sql',
        title: 'SQL Querying Foundation',
        requires: ['python'],
      },
      {
        id: 'statistics_inference',
        title: 'Statistics and Statistical Inference',
        requires: ['python'],
      },
      {
        id: 'data_science_libraries',
        title: 'Scientific Computing and ML Libraries',
        requires: ['python'],
      },

      {
        id: 'data_preparation',
        title: 'Data Cleaning and Feature Engineering',
        requires: ['notebook_tooling', 'sql'],
      },
      {
        id: 'exploratory_analysis',
        title: 'Exploratory Data Analysis',
        requires: [
          'data_preparation',
          'statistics_inference',
        ],
      },
      {
        id: 'visualization_tools',
        title: 'Data Visualization Tools',
        requires: ['exploratory_analysis'],
      },

      {
        id: 'ml_training',
        title: 'Machine Learning Model Development',
        requires: [
          'exploratory_analysis',
          'statistics_inference',
          'data_science_libraries',
        ],
      },
      {
        id: 'model_evaluation',
        title: 'Model Evaluation and Validation',
        requires: ['ml_training'],
      },

      {
        id: 'data_communication',
        title: 'Communicating Analytical Findings',
        requires: [
          'visualization_tools',
          'model_evaluation',
        ],
      },
    ],
  },
};

function validateTemplate(template: CareerTemplate): void {
  const ids = new Set<string>();

  for (const node of template.nodes) {
    if (ids.has(node.id)) {
      throw new Error(`Duplicate skill node: ${node.id}`);
    }
    ids.add(node.id);
  }

  for (const node of template.nodes) {
    for (const dependency of node.requires) {
      if (!ids.has(dependency)) {
        throw new Error(
          `Unknown dependency ${dependency} for ${node.id}`
        );
      }
    }
  }

  const nodeMap = new Map(
    template.nodes.map((node) => [node.id, node])
  );

  const visiting = new Set<string>();
  const visited = new Set<string>();

  function visit(id: string) {
    if (visiting.has(id)) {
      throw new Error(`Circular skill dependency at ${id}`);
    }

    if (visited.has(id)) return;

    visiting.add(id);

    for (const dependency of nodeMap.get(id)!.requires) {
      visit(dependency);
    }

    visiting.delete(id);
    visited.add(id);
  }

  for (const id of ids) visit(id);
}


export function buildSkillTree(
  roadmap: CareerRoadmap,
  recordedSkills: RecordedSkill[] = []
): {
  connected: SkillTreeItem[];
  unmapped: SkillTreeItem[];
  hasTemplate: boolean;
} {
  const template = templates[roadmap.career_key];

  // Index recorded skills for efficient matching.
  const recordedByName = new Map(
    recordedSkills.map((skill) => [
      skill.name.trim().toLowerCase(),
      skill,
    ])
  );

  // Careers without a dependency template still show
  // their competencies without invented connections.
  if (!template) {
    return {
      connected: [],
      unmapped: roadmap.steps.map((step) => ({
        id: `step:${step.competency_key}`,
        title: step.competency,
        requires: [],
        step,
        status: step.status,
        unmapped: true,
      })),
      hasTemplate: false,
    };
  }

  validateTemplate(template);

  // Match competencies using their canonical keys.
  const stepsByKey = new Map(
    roadmap.steps.map((step) => [
      step.competency_key,
      step,
    ])
  );

  const templateIds = new Set(
    template.nodes.map((node) => node.id)
  );

  const connected: SkillTreeItem[] = template.nodes.map(
    (node) => {
      const step = stepsByKey.get(node.id);

      // Match foundation skills against user_skills.
      const matchedSkill = node.skillAliases
        ?.map((alias) =>
          recordedByName.get(alias.trim().toLowerCase())
        )
        .find((skill) => skill !== undefined);

      // Competency assessments take priority over
      // foundation-level user-skill matching.
      const status = step
        ? step.status
        : matchedSkill
          ? 'evidenced'
          : 'not_assessed';

      return {
        id: node.id,
        title: step?.competency ?? node.title,
        requires: [...node.requires],
        step,
        status,
        source: matchedSkill?.source ?? null,
      };
    }
  );

  // Preserve competencies not yet mapped to the tree.
  const unmapped: SkillTreeItem[] = roadmap.steps
    .filter(
      (step) => !templateIds.has(step.competency_key)
    )
    .map((step) => ({
      id: `step:${step.competency_key}`,
      title: step.competency,
      requires: [],
      step,
      status: step.status,
      unmapped: true,
    }));

  return {
    connected,
    unmapped,
    hasTemplate: true,
  };
}
