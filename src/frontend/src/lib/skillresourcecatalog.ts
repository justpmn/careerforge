import type { RoadmapResource } from './roadmap';

const starterResources: Record<string, RoadmapResource[]> = {
  python: [
    { title: 'The Python Tutorial', provider: 'Python documentation', url: 'https://docs.python.org/3/tutorial/' },
  ],
  notebook_tooling: [
    { title: 'Try Jupyter', provider: 'Project Jupyter', url: 'https://jupyter.org/try' },
  ],
  sql: [
    { title: 'Introduction to SQL', provider: 'SQLBolt', url: 'https://sqlbolt.com/lesson/introduction' },
  ],
  statistics_inference: [
    { title: 'Statistics and Probability', provider: 'Khan Academy', url: 'https://www.khanacademy.org/math/statistics-probability' },
  ],
  data_science_libraries: [
    { title: 'Learn NumPy', provider: 'NumPy', url: 'https://numpy.org/learn/' },
  ],
  data_preparation: [
    { title: 'Getting Started with pandas', provider: 'pandas', url: 'https://pandas.pydata.org/docs/getting_started/' },
  ],
  exploratory_analysis: [
    { title: 'pandas Visualization Guide', provider: 'pandas', url: 'https://pandas.pydata.org/docs/user_guide/visualization.html' },
  ],
  visualization_tools: [
    { title: 'Matplotlib Tutorials', provider: 'Matplotlib', url: 'https://matplotlib.org/stable/tutorials/index.html' },
  ],
  ml_training: [
    { title: 'Supervised Learning', provider: 'scikit-learn', url: 'https://scikit-learn.org/stable/supervised_learning.html' },
  ],
  model_evaluation: [
    { title: 'Model Evaluation', provider: 'scikit-learn', url: 'https://scikit-learn.org/stable/modules/model_evaluation.html' },
  ],
  data_communication: [
    { title: 'pyplot Tutorial', provider: 'Matplotlib', url: 'https://matplotlib.org/stable/tutorials/pyplot.html' },
  ],
};

export function resourcesForSkill(
  careerKey: string,
  skillKey: string,
  mapped: RoadmapResource[]
): { resources: RoadmapResource[]; starter: boolean } {
  if (mapped.length > 0) return { resources: mapped, starter: false };
  if (careerKey !== 'data_scientist') return { resources: [], starter: false };
  return { resources: starterResources[skillKey] ?? [], starter: true };
}
