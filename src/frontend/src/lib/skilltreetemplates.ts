import type {CareerRoadmap, RoadmapStep, RecordedSkill} from './roadmap';
import { jsonSkillTreeTemplates } from './skilltrees';


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
  
  backend_developer: {
    version: 1,
    nodes: [
      {
        id: 'programming',
        title: 'Programming Fundamentals',
        requires: [],
        skillAliases: [
          'Python',
          'JavaScript',
          'Java',
          'C#',
          'Go',
        ],
      },
      {
        id: 'version_control',
        title: 'Version Control with Git',
        requires: [],
        skillAliases: ['Git'],
      },
      {
        id: 'backend_runtime',
        title: 'Backend Languages and Frameworks',
        requires: ['programming'],
      },
      {
        id: 'database',
        title: 'Databases and SQL',
        requires: ['programming'],
      },
      {
        id: 'api',
        title: 'API Design and Development',
        requires: [
          'backend_runtime',
          'database',
        ],
      },
      {
        id: 'debugging',
        title: 'Debugging and Troubleshooting',
        requires: ['backend_runtime'],
      },
      {
        id: 'authentication_security',
        title: 'Authentication and Security',
        requires: ['api'],
      },
      {
        id: 'testing',
        title: 'Backend Testing',
        requires: ['api'],
      },
      {
        id: 'deployment',
        title: 'Application Deployment',
        requires: [
          'api',
          'version_control',
        ],
      },
      {
        id: 'ci_cd',
        title: 'Continuous Integration and Deployment',
        requires: [
          'testing',
          'deployment',
          'version_control',
        ],
      },
    ],
  },

  data_engineer: {
    version: 1,
    nodes: [
      {
        id: 'data_programming',
        title: 'Data Engineering Programming',
        requires: [],
        skillAliases: ['Python', 'Java', 'Scala'],
      },
      {
        id: 'version_control',
        title: 'Version Control',
        requires: [],
        skillAliases: ['Git'],
      },
      {
        id: 'sql_querying',
        title: 'SQL Querying',
        requires: ['data_programming'],
        skillAliases: ['SQL'],
      },
      {
        id: 'data_storage',
        title: 'Databases and Data Storage',
        requires: ['sql_querying'],
      },
      {
        id: 'data_modeling',
        title: 'Data Modeling and Transformation',
        requires: ['data_storage'],
      },
      {
        id: 'pipeline_design',
        title: 'Data Pipelines and Orchestration',
        requires: [
          'data_programming',
          'data_storage',
        ],
      },
      {
        id: 'data_quality',
        title: 'Data Quality and Validation',
        requires: [
          'data_modeling',
          'pipeline_design',
        ],
      },
      {
        id: 'cloud_platform',
        title: 'Cloud Data Platforms',
        requires: ['pipeline_design'],
        skillAliases: [
          'Amazon Web Services (AWS)',
          'Microsoft Azure',
          'Google Cloud',
        ],
      },
      {
        id: 'containers',
        title: 'Containerization',
        requires: ['pipeline_design'],
        skillAliases: ['Docker'],
      },
      {
        id: 'ci_cd',
        title: 'CI/CD for Data Engineering',
        requires: [
          'version_control',
          'containers',
          'cloud_platform',
        ],
      },
    ],
  },

  // =========================================
  // FRONTEND DEVELOPER — 8 COMPETENCIES
  // =========================================
  frontend_developer: {
    version: 1,
    nodes: [
      {
        id: 'web_programming',
        title: 'Frontend Programming',
        requires: [],
        skillAliases: ['JavaScript', 'TypeScript'],
      },
      {
        id: 'web_fundamentals',
        title: 'HTML and CSS Fundamentals',
        requires: [],
        skillAliases: ['HTML/CSS'],
      },
      {
        id: 'version_control',
        title: 'Version Control',
        requires: [],
        skillAliases: ['Git'],
      },
      {
        id: 'frontend_framework',
        title: 'Frontend Frameworks',
        requires: ['web_programming', 'web_fundamentals'],
        skillAliases: ['React', 'Angular', 'Vue.js'],
      },
      {
        id: 'web_accessibility',
        title: 'Responsive Design and Accessibility',
        requires: ['web_fundamentals'],
      },
      {
        id: 'build_tools',
        title: 'Frontend Build Tools',
        requires: ['frontend_framework'],
        skillAliases: ['Vite', 'Webpack'],
      },
      {
        id: 'testing',
        title: 'Frontend Testing',
        requires: ['frontend_framework'],
      },
      {
        id: 'ci_cd',
        title: 'Continuous Integration and Delivery',
        requires: [
          'version_control',
          'build_tools',
          'testing',
        ],
      },
    ],
  },

  // =========================================
  // FULL STACK DEVELOPER — 11 COMPETENCIES
  // =========================================
  full_stack_developer: {
    version: 1,
    nodes: [
      {
        id: 'web_programming',
        title: 'Frontend Programming',
        requires: [],
        skillAliases: ['JavaScript', 'TypeScript'],
      },
      {
        id: 'web_fundamentals',
        title: 'HTML and CSS Fundamentals',
        requires: [],
        skillAliases: ['HTML/CSS'],
      },
      {
        id: 'version_control',
        title: 'Version Control',
        requires: [],
        skillAliases: ['Git'],
      },
      {
        id: 'frontend_framework',
        title: 'Frontend Frameworks',
        requires: ['web_programming', 'web_fundamentals'],
        skillAliases: ['React', 'Angular', 'Vue.js'],
      },
      {
        id: 'backend_runtime',
        title: 'Backend Frameworks and Runtime',
        requires: [],
        skillAliases: [
          'Node.js',
          'Express',
          'FastAPI',
          'Django',
          'Spring Boot',
        ],
      },
      {
        id: 'database',
        title: 'Database Technologies',
        requires: [],
        skillAliases: [
          'MySQL',
          'PostgreSQL',
          'MongoDB',
        ],
      },
      {
        id: 'api',
        title: 'API Development',
        requires: ['backend_runtime', 'database'],
        skillAliases: ['RESTful API'],
      },
      {
        id: 'authentication_security',
        title: 'Authentication and Application Security',
        requires: ['api'],
      },
      {
        id: 'testing',
        title: 'Full Stack Testing',
        requires: ['frontend_framework', 'api'],
      },
      {
        id: 'containers',
        title: 'Containerization',
        requires: ['api'],
        skillAliases: ['Docker'],
      },
      {
        id: 'ci_cd',
        title: 'Continuous Integration and Delivery',
        requires: [
          'version_control',
          'testing',
          'containers',
        ],
      },
    ],
  },

  // =========================================
  // CLOUD ENGINEER — 14 COMPETENCIES
  // =========================================
  cloud_engineer: {
    version: 1,
    nodes: [
      {
        id: 'cloud_platform_familiarity',
        title: 'Cloud Platform Fundamentals',
        requires: [],
        skillAliases: [
          'Amazon Web Services (AWS)',
          'Microsoft Azure',
          'Google Cloud',
        ],
      },
      {
        id: 'automation_scripting',
        title: 'Automation and Scripting',
        requires: [],
        skillAliases: [
          'Python',
          'PowerShell',
          'Bash/Shell (all shells)',
        ],
      },
      {
        id: 'version_control',
        title: 'Version Control',
        requires: [],
        skillAliases: ['Git'],
      },
      {
        id: 'cloud_networking',
        title: 'Cloud Networking',
        requires: ['cloud_platform_familiarity'],
      },
      {
        id: 'cloud_iam',
        title: 'Cloud Identity and Access Management',
        requires: ['cloud_platform_familiarity'],
      },
      {
        id: 'cloud_infrastructure',
        title: 'Cloud Infrastructure Management',
        requires: [
          'cloud_platform_familiarity',
          'cloud_networking',
        ],
      },
      {
        id: 'iac_tooling',
        title: 'Infrastructure Provisioning Tools',
        requires: ['automation_scripting'],
        skillAliases: ['Terraform', 'Ansible'],
      },
      {
        id: 'infrastructure_as_code',
        title: 'Infrastructure as Code',
        requires: [
          'cloud_infrastructure',
          'iac_tooling',
          'version_control',
        ],
      },
      {
        id: 'containers',
        title: 'Containerization',
        requires: [],
        skillAliases: ['Docker'],
      },
      {
        id: 'orchestration_tooling',
        title: 'Container Orchestration',
        requires: ['containers'],
        skillAliases: ['Kubernetes'],
      },
      {
        id: 'cloud_deployment',
        title: 'Cloud Application Deployment',
        requires: [
          'cloud_infrastructure',
          'cloud_iam',
        ],
      },
      {
        id: 'cloud_monitoring',
        title: 'Cloud Monitoring',
        requires: ['cloud_deployment'],
      },
      {
        id: 'cloud_reliability',
        title: 'Cloud Reliability and Recovery',
        requires: [
          'cloud_monitoring',
          'cloud_networking',
        ],
      },
      {
        id: 'ci_cd',
        title: 'Continuous Integration and Delivery',
        requires: [
          'version_control',
          'cloud_deployment',
        ],
      },
    ],
  },

  // =========================================
  // DEVOPS / SRE — 15 COMPETENCIES
  // =========================================
  devops_sre: {
    version: 1,
    nodes: [
      {
        id: 'automation_scripting',
        title: 'Automation and Scripting',
        requires: [],
        skillAliases: [
          'Python',
          'PowerShell',
          'Bash/Shell (all shells)',
        ],
      },
      {
        id: 'version_control',
        title: 'Version Control',
        requires: [],
        skillAliases: ['Git'],
      },
      {
        id: 'cloud_platform',
        title: 'Cloud Platform Experience',
        requires: [],
        skillAliases: [
          'Amazon Web Services (AWS)',
          'Microsoft Azure',
          'Google Cloud',
        ],
      },
      {
        id: 'containers',
        title: 'Containerization',
        requires: [],
        skillAliases: ['Docker'],
      },
      {
        id: 'iac_tooling',
        title: 'Infrastructure Provisioning Tools',
        requires: ['cloud_platform'],
        skillAliases: ['Terraform'],
      },
      {
        id: 'infrastructure_as_code',
        title: 'Infrastructure as Code',
        requires: [
          'automation_scripting',
          'iac_tooling',
        ],
      },
      {
        id: 'configuration_management',
        title: 'Configuration Management',
        requires: ['automation_scripting'],
        skillAliases: ['Ansible'],
      },
      {
        id: 'orchestration_tooling',
        title: 'Container Orchestration',
        requires: ['containers'],
        skillAliases: ['Kubernetes'],
      },
      {
        id: 'automation_platforms',
        title: 'Delivery Automation Tools',
        requires: ['version_control'],
        skillAliases: ['Jenkins CI'],
      },
      {
        id: 'deployment_automation',
        title: 'Build and Deployment Automation',
        requires: [
          'version_control',
          'containers',
        ],
      },
      {
        id: 'ci_cd',
        title: 'CI/CD Pipelines',
        requires: [
          'deployment_automation',
          'automation_platforms',
        ],
      },
      {
        id: 'observability_tooling',
        title: 'Monitoring and Observability Tools',
        requires: ['cloud_platform'],
        skillAliases: ['Prometheus', 'Grafana Labs Grafana Cloud'],
      },
      {
        id: 'observability',
        title: 'Metrics, Logs and Tracing',
        requires: ['observability_tooling'],
      },
      {
        id: 'incident_management',
        title: 'Incident Management',
        requires: ['observability'],
      },
      {
        id: 'sre_reliability',
        title: 'Site Reliability Engineering',
        requires: [
          'observability',
          'incident_management',
          'deployment_automation',
        ],
      },
    ],
  },

  // =========================================
  // CYBERSECURITY ANALYST — 14 COMPETENCIES
  // =========================================
  cybersecurity_analyst: {
    version: 1,
    nodes: [
      {
        id: 'security_os',
        title: 'Operating System Fundamentals',
        requires: [],
        skillAliases: [
          'Linux',
          'Microsoft Windows',
          'Microsoft Windows Server',
        ],
      },
      {
        id: 'cloud_platform',
        title: 'Cloud Platform Fundamentals',
        requires: [],
        skillAliases: [
          'Amazon Web Services (AWS)',
          'Microsoft Azure',
          'Google Cloud',
        ],
      },
      {
        id: 'security_scripting',
        title: 'Security Scripting',
        requires: ['security_os'],
        skillAliases: [
          'Python',
          'PowerShell',
          'Bash/Shell (all shells)',
        ],
      },
      {
        id: 'network_security',
        title: 'Network Security',
        requires: ['security_os'],
      },
      {
        id: 'firewall_tooling',
        title: 'Firewall Technologies',
        requires: ['network_security'],
        skillAliases: ['Firewall software'],
      },
      {
        id: 'identity_access_security',
        title: 'Identity and Access Security',
        requires: [
          'security_os',
          'cloud_platform',
        ],
      },
      {
        id: 'security_controls',
        title: 'Security Controls and Hardening',
        requires: [
          'security_os',
          'network_security',
        ],
      },
      {
        id: 'security_monitoring',
        title: 'Security Event Monitoring',
        requires: [
          'security_os',
          'network_security',
        ],
      },
      {
        id: 'siem_tooling',
        title: 'SIEM Technologies',
        requires: ['security_monitoring'],
        skillAliases: ['Splunk', 'Splunk Enterprise'],
      },
      {
        id: 'threat_detection',
        title: 'Threat Detection and Investigation',
        requires: [
          'security_monitoring',
          'siem_tooling',
        ],
      },
      {
        id: 'vulnerability_assessment',
        title: 'Vulnerability Assessment',
        requires: [
          'security_controls',
          'network_security',
        ],
      },
      {
        id: 'security_incident_response',
        title: 'Security Incident Response',
        requires: [
          'threat_detection',
          'vulnerability_assessment',
        ],
      },
      {
        id: 'security_risk',
        title: 'Security Risk Assessment',
        requires: ['vulnerability_assessment'],
      },
      {
        id: 'security_compliance',
        title: 'Security Compliance and Standards',
        requires: [
          'security_risk',
          'identity_access_security',
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
  const template =
  jsonSkillTreeTemplates[roadmap.career_key] ??
  templates[roadmap.career_key];

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
