
import type {
  CareerRoadmap,
  RoadmapStep,
} from './roadmap';

type TemplateNode = {
  id: string;
  title: string;
  matches: string[];
  requires: string[];
};

type CareerTemplate = {
  nodes: TemplateNode[];
};

export type SkillTreeItem = {
  id: string;
  title: string;
  requires: string[];
  step?: RoadmapStep;
  unmapped?: boolean;
};

const templates: Record<string, CareerTemplate> = {
  data_scientist: {
    nodes: [
      {
        id: 'python',
        title: 'Python Programming',
        matches: ['Python', 'Python programming'],
        requires: [],
      },
      {
        id: 'statistics',
        title: 'Applied Statistics',
        matches: [
          'Statistics',
          'Statistics fundamentals',
          'Statistics and probability',
          'Statistical analysis and hypothesis testing',
        ],
        requires: ['python'],
      },
      {
        id: 'data_cleaning',
        title: 'Data Cleaning & Feature Engineering',
        matches: [
          'Data cleaning and feature engineering',
        ],
        requires: ['python'],
      },
      {
        id: 'exploratory_analysis',
        title: 'Exploratory Data Analysis',
        matches: ['Exploratory data analysis'],
        requires: ['statistics', 'data_cleaning'],
      },
      {
        id: 'machine_learning',
        title: 'Machine Learning',
        matches: ['Machine learning model development'],
        requires: [
          'statistics',
          'data_cleaning',
          'exploratory_analysis',
        ],
      },
      {
        id: 'model_evaluation',
        title: 'Model Evaluation',
        matches: ['Model evaluation and validation'],
        requires: ['machine_learning'],
      },
    ],
  },
};

function normalize(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]/g, '');
}

function matchesStep(
  node: TemplateNode,
  step: RoadmapStep
): boolean {
  const candidates = [
    step.competency,
    step.competency_key,
  ].map(normalize);

  return node.matches.some((alias) =>
    candidates.includes(normalize(alias))
  );
}

export function buildSkillTree(
  roadmap: CareerRoadmap
): {
  connected: SkillTreeItem[];
  unmapped: SkillTreeItem[];
  hasTemplate: boolean;
} {
  const template = templates[roadmap.career_key];

  if (!template) {
    return {
      connected: [],
      unmapped: roadmap.steps.map((step) => ({
        id: `step:${step.competency_key}`,
        title: step.competency,
        requires: [],
        step,
        unmapped: true,
      })),
      hasTemplate: false,
    };
  }

  const matchedKeys = new Set<string>();

  const connected: SkillTreeItem[] =
    template.nodes.map((node) => {
      const step = roadmap.steps.find(
        (candidate) =>
          !matchedKeys.has(candidate.competency_key) &&
          matchesStep(node, candidate)
      );

      if (step) {
        matchedKeys.add(step.competency_key);
      }

      return {
        id: node.id,
        title: step?.competency ?? node.title,
        requires: node.requires,
        step,
      };
    });

  const unmapped: SkillTreeItem[] = roadmap.steps
    .filter(
      (step) => !matchedKeys.has(step.competency_key)
    )
    .map((step) => ({
      id: `step:${step.competency_key}`,
      title: step.competency,
      requires: [],
      step,
      unmapped: true,
    }));

  return {
    connected,
    unmapped,
    hasTemplate: true,
  };
}
