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
  const Icon = skillIcons[id] ?? additionalSkillIcons[id];
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
