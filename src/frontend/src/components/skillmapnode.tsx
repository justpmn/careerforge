import { Handle, Position } from '@xyflow/react';
import type { Node, NodeProps } from '@xyflow/react';
import type { IconType } from 'react-icons';
import { SiPython } from 'react-icons/si';
import {
  FiBarChart2,
  FiBookOpen,
  FiCheck,
  FiCheckCircle,
  FiCpu,
  FiDatabase,
  FiLayers,
  FiMessageSquare,
  FiPieChart,
  FiTrendingUp,
  FiGitBranch,
  FiCloud,
  FiBox,
  FiRefreshCw,
  FiCheckSquare,
  FiShare2,
  FiServer,
} from 'react-icons/fi';
import * as FeatherIcons from 'react-icons/fi';

export type SkillMapNodeType = Node<{
  title: string;
  label: string;
  glyph: string;
  status: string;
  related?: boolean;
  dimmed?: boolean;
  learned?: boolean;
}, 'skill'>;

const skillIcons: Record<string, IconType> = {
  python: SiPython,
  notebook_tooling: FiBookOpen,
  sql: FiDatabase,
  statistics_inference: FiPieChart,
  data_science_libraries: FiLayers,
  data_preparation: FiDatabase,
  exploratory_analysis: FiBarChart2,
  visualization_tools: FiTrendingUp,
  ml_training: FiCpu,
  model_evaluation: FiCheckCircle,
  data_communication: FiMessageSquare,

  
  // Data Engineer
  data_programming: SiPython,
  version_control: FiGitBranch,
  sql_querying: FiDatabase,
  data_storage: FiServer,
  data_modeling: FiLayers,
  pipeline_design: FiShare2,
  data_quality: FiCheckSquare,
  cloud_platform: FiCloud,
  containers: FiBox,
  ci_cd: FiRefreshCw,

};


const additionalSkillIcons: Record<string, IconType> = {
  // Frontend and Full Stack Developer
  web_programming: FeatherIcons.FiCode,
  web_fundamentals: FeatherIcons.FiLayout,
  frontend_framework: FeatherIcons.FiLayers,
  build_tools: FeatherIcons.FiTool,
  web_accessibility: FeatherIcons.FiEye,
  testing: FeatherIcons.FiCheckCircle,
  backend_runtime: FeatherIcons.FiServer,
  database: FeatherIcons.FiDatabase,
  api: FeatherIcons.FiLink,
  authentication_security: FeatherIcons.FiLock,

  // Cloud Engineer
  cloud_platform_familiarity: FeatherIcons.FiCloud,
  cloud_infrastructure: FeatherIcons.FiServer,
  cloud_networking: FeatherIcons.FiWifi,
  cloud_iam: FeatherIcons.FiKey,
  infrastructure_as_code: FeatherIcons.FiCode,
  cloud_deployment: FeatherIcons.FiUploadCloud,
  cloud_monitoring: FeatherIcons.FiActivity,
  cloud_reliability: FeatherIcons.FiShield,
  iac_tooling: FeatherIcons.FiTool,
  orchestration_tooling: FeatherIcons.FiGitMerge,

  // DevOps / SRE
  automation_scripting: FeatherIcons.FiTerminal,
  deployment_automation: FeatherIcons.FiRefreshCw,
  configuration_management: FeatherIcons.FiSliders,
  observability: FeatherIcons.FiBarChart2,
  incident_management: FeatherIcons.FiAlertTriangle,
  sre_reliability: FeatherIcons.FiTrendingUp,
  observability_tooling: FeatherIcons.FiActivity,
  automation_platforms: FeatherIcons.FiSettings,

  // Cybersecurity Analyst
  security_monitoring: FeatherIcons.FiActivity,
  threat_detection: FeatherIcons.FiSearch,
  security_incident_response: FeatherIcons.FiAlertTriangle,
  vulnerability_assessment: FeatherIcons.FiTarget,
  security_controls: FeatherIcons.FiShield,
  identity_access_security: FeatherIcons.FiKey,
  network_security: FeatherIcons.FiWifi,
  security_risk: FeatherIcons.FiAlertCircle,
  siem_tooling: FeatherIcons.FiMonitor,
  firewall_tooling: FeatherIcons.FiShield,
  security_scripting: FeatherIcons.FiCode,
  security_os: FeatherIcons.FiMonitor,
  security_compliance: FeatherIcons.FiClipboard,
};


const jsonCareerSkillIcons: Record<string, IconType> = {
  // AI / ML Engineer
  ml_programming: FeatherIcons.FiCode,
  model_serving: FeatherIcons.FiServer,
  model_monitoring: FeatherIcons.FiActivity,
  ml_libraries: FeatherIcons.FiCpu,
  model_api_tooling: FeatherIcons.FiLink,
  ml_workflows: FeatherIcons.FiGitMerge,

  // Database Engineer
  db_platform: FeatherIcons.FiDatabase,
  database_architecture: FeatherIcons.FiDatabase,
  query_optimization: FeatherIcons.FiZap,
  database_administration: FeatherIcons.FiServer,
  backup_recovery: FeatherIcons.FiArchive,
  database_security: FeatherIcons.FiLock,
  database_monitoring: FeatherIcons.FiActivity,
  database_migrations: FeatherIcons.FiGitBranch,
  db_automation: FeatherIcons.FiTerminal,
  nosql_db: FeatherIcons.FiDatabase,

  // Mobile Developer
  mobile_app_development: FeatherIcons.FiSmartphone,
  mobile_ui: FeatherIcons.FiLayout,
  mobile_platform_integration: FeatherIcons.FiSettings,
  mobile_testing: FeatherIcons.FiCheckCircle,
  mobile_languages: FeatherIcons.FiCode,
  mobile_tooling: FeatherIcons.FiTool,
  mobile_storage: FeatherIcons.FiDatabase,
  mobile_api: FeatherIcons.FiLink,
  mobile_release: FeatherIcons.FiUploadCloud,

  // QA and Software Engineering
  test_strategy: FeatherIcons.FiClipboard,
  defect_management: FeatherIcons.FiAlertCircle,
  test_programming: FeatherIcons.FiCode,
  debugging: FeatherIcons.FiTool,
  api_testing: FeatherIcons.FiLink,
  performance_testing: FeatherIcons.FiActivity,
  programming: FeatherIcons.FiCode,
  software_design: FeatherIcons.FiLayers,

  // Data / Business Analyst
  analysis_interpretation: FeatherIcons.FiBarChart2,
  requirements_analysis: FeatherIcons.FiClipboard,
  reporting_dashboards: FeatherIcons.FiPieChart,
  business_metrics: FeatherIcons.FiTrendingUp,
  data_communication: FeatherIcons.FiMessageSquare,
  data_quality: FeatherIcons.FiCheckSquare,
  spreadsheet_tools: FeatherIcons.FiGrid,
  bi_tools: FeatherIcons.FiBarChart2,
  analysis_programming: FeatherIcons.FiCode,
  analytical_databases: FeatherIcons.FiDatabase,

  // Embedded Developer
  embedded_firmware: FeatherIcons.FiCpu,
  embedded_microcontrollers: FeatherIcons.FiCpu,
  embedded_interfaces: FeatherIcons.FiGitMerge,
  embedded_real_time: FeatherIcons.FiClock,
  embedded_debugging: FeatherIcons.FiTool,
  embedded_testing: FeatherIcons.FiCheckCircle,
  embedded_languages: FeatherIcons.FiCode,
  embedded_build_tools: FeatherIcons.FiSettings,

  // Game Developer
  game_engine: FeatherIcons.FiBox,
  gameplay_programming: FeatherIcons.FiCode,
  game_design: FeatherIcons.FiPenTool,
  game_physics: FeatherIcons.FiActivity,
  game_testing: FeatherIcons.FiCheckCircle,
  game_languages: FeatherIcons.FiCode,
  game_rendering: FeatherIcons.FiMonitor,
  game_optimization: FeatherIcons.FiZap,

  // IT Project Manager
  project_planning: FeatherIcons.FiCalendar,
  scope_management: FeatherIcons.FiTarget,
  project_scheduling: FeatherIcons.FiClock,
  budget_management: FeatherIcons.FiDollarSign,
  project_risk_management: FeatherIcons.FiAlertTriangle,
  stakeholder_management: FeatherIcons.FiUsers,
  project_delivery: FeatherIcons.FiCheckCircle,
  project_communication: FeatherIcons.FiMessageSquare,
  project_change_management: FeatherIcons.FiRefreshCw,
  project_quality_management: FeatherIcons.FiCheckSquare,
  delivery_methodologies: FeatherIcons.FiLayers,
  project_management_tools: FeatherIcons.FiTool,
  project_reporting_tools: FeatherIcons.FiFileText,

  // IT Support
  end_user_support: FeatherIcons.FiHeadphones,
  hardware_support: FeatherIcons.FiHardDrive,
  software_support: FeatherIcons.FiMonitor,
  connectivity_support: FeatherIcons.FiWifi,
  account_support: FeatherIcons.FiUserCheck,
  ticket_management: FeatherIcons.FiList,
  customer_communication: FeatherIcons.FiMessageCircle,
  knowledge_documentation: FeatherIcons.FiBookOpen,
  os_familiarity: FeatherIcons.FiTerminal,
  support_ticketing_tooling: FeatherIcons.FiTag,
  directory_tooling: FeatherIcons.FiFolder,

  // Product Manager
  product_strategy: FeatherIcons.FiCompass,
  product_discovery: FeatherIcons.FiSearch,
  product_roadmap: FeatherIcons.FiMap,
  feature_prioritization: FeatherIcons.FiList,
  product_metrics: FeatherIcons.FiTrendingUp,
  product_launch: FeatherIcons.FiSend,
  product_experimentation: FeatherIcons.FiActivity,
  product_management_tools: FeatherIcons.FiTrello,
  product_analytics_tools: FeatherIcons.FiBarChart2,

  // Software Architect
  system_design: FeatherIcons.FiGitBranch,
  scalability_reliability: FeatherIcons.FiTrendingUp,
  security_architecture: FeatherIcons.FiShield,
  technical_leadership: FeatherIcons.FiUsers,

  // Systems / Network Administrator
  systems_administration: FeatherIcons.FiServer,
  network_configuration: FeatherIcons.FiWifi,
  network_troubleshooting: FeatherIcons.FiActivity,
  directory_management: FeatherIcons.FiFolder,
  system_monitoring: FeatherIcons.FiActivity,
  system_backup_recovery: FeatherIcons.FiArchive,
  patch_management: FeatherIcons.FiRefreshCw,
  access_permissions: FeatherIcons.FiLock,
  os_platforms: FeatherIcons.FiMonitor,
  sys_scripting: FeatherIcons.FiTerminal,

  // UI / UX Designer
  user_research: FeatherIcons.FiUsers,
  information_architecture: FeatherIcons.FiGitBranch,
  wireframing: FeatherIcons.FiLayout,
  prototyping: FeatherIcons.FiMousePointer,
  interaction_design: FeatherIcons.FiMousePointer,
  usability_testing: FeatherIcons.FiCheckCircle,
  design_systems: FeatherIcons.FiLayers,
  ux_accessibility: FeatherIcons.FiEye,
  visual_design: FeatherIcons.FiPenTool,
  design_tooling: FeatherIcons.FiPenTool,
  graphics_tooling: FeatherIcons.FiImage,
  frontend_fundamentals: FeatherIcons.FiCode,
  design_handoff: FeatherIcons.FiShare2,
};



const statusLabels: Record<string, string> = {
  evidenced: 'Recorded evidence',
  evidence_found: 'Review evidence',
  not_assessed: 'Not assessed',
  not_evidenced: 'Not evidenced',
  unlinked: 'No assessment linked',
};

export default function SkillMapNode({
  id,
  data,
  selected,
}: NodeProps<SkillMapNodeType>) {
  const Icon =
  skillIcons[id] ??
  additionalSkillIcons[id] ??
  jsonCareerSkillIcons[id];
  const status = Object.hasOwn(statusLabels, data.status)
    ? data.status
    : 'unlinked';

  return (
    <div
      className={[
        'cf-orb-node',
        `cf-orb-node--${status}`,
        selected ? 'is-selected' : '',
        data.related ? 'is-related' : '',
        data.dimmed ? 'is-dimmed' : '',
        data.learned ? 'is-learned' : '',
      ].filter(Boolean).join(' ')}
      title={`${data.title} — ${statusLabels[status]}${data.learned ? ' · Marked learned' : ''}`}
    >
      <Handle
        type="target"
        position={Position.Left}
        className="cf-orb-handle cf-orb-handle--left"
        isConnectable={false}
      />

      <div className="cf-orb-circle">
        {Icon ? (
          <Icon
            className={
                  id === 'python' || id === 'data_programming'
                    ? 'cf-python-icon'
                    : ''
                }
            aria-hidden="true"
          />
        ) : (
          <span className="cf-orb-glyph" aria-hidden="true">
            {data.glyph}
          </span>
        )}
        {status === 'evidenced' && (
          <span className="cf-orb-achieved" title="Evidence recorded" aria-label="Evidence recorded">
            <FiCheck aria-hidden="true" />
          </span>
        )}
        {data.learned && status !== 'evidenced' && (
          <span className="cf-orb-learned-mark" title="Marked learned" aria-label="Marked learned">
            <FiCheck aria-hidden="true" />
          </span>
        )}
      </div>

      <span className="cf-orb-label">{data.label}</span>

      <Handle
        type="source"
        position={Position.Right}
        className="cf-orb-handle cf-orb-handle--right"
        isConnectable={false}
      />
    </div>
  );
}
