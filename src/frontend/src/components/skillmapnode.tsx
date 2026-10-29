
import { Handle, Position } from '@xyflow/react';
import type { Node, NodeProps } from '@xyflow/react';
import type { IconType } from 'react-icons';

import { SiPython } from 'react-icons/si';
import {
  FiBarChart2,
  FiCheckCircle,
  FiCpu,
  FiDatabase,
  FiPieChart,
} from 'react-icons/fi';

export type SkillMapNodeType = Node<
  {
    title: string;
    label: string;
    glyph: string;
    status: string;
  },
  'skill'
>;

const skillIcons: Record<string, IconType> = {
  python: SiPython,
  statistics: FiPieChart,
  data_cleaning: FiDatabase,
  exploratory_analysis: FiBarChart2,
  machine_learning: FiCpu,
  model_evaluation: FiCheckCircle,
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
  const Icon = skillIcons[id];

  const status = Object.hasOwn(statusLabels, data.status)
    ? data.status
    : 'unlinked';

  return (
    <div
      className={[
        'cf-orb-node',
        `cf-orb-node--${status}`,
        selected ? 'is-selected' : '',
      ].join(' ')}
      title={`${data.title} — ${statusLabels[status]}`}
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
            className={id === 'python' ? 'cf-python-icon' : ''}
            aria-hidden="true"
          />
        ) : (
          <span className="cf-orb-glyph" aria-hidden="true">
            {data.glyph}
          </span>
        )}
      </div>

      <span className="cf-orb-label">
        {data.label}
      </span>

        <Handle
        type="source"
        position={Position.Right}
        className="cf-orb-handle cf-orb-handle--right"
        isConnectable={false}
        />
    </div>
  );
}
