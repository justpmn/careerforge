import { Handle, Position } from '@xyflow/react';
import type { NodeProps } from '@xyflow/react';

type SkillStatus =
  | 'evidenced'
  | 'not_assessed'
  | 'in_progress'
  | 'locked';

type SkillOrbData = {
  label: string;
  icon: React.ReactNode;
  status: SkillStatus;
};

export default function SkillOrbNode({
  data,
  selected,
}: NodeProps) {
  const node = data as SkillOrbData;

  return (
    <div className={`cf-skill-orb status-${node.status} ${selected ? 'is-selected' : ''}`}>
      <Handle type="target" position={Position.Top} className="cf-skill-handle" />

      <div className="cf-skill-orb-circle">
        <div className="cf-skill-orb-icon">{node.icon}</div>
      </div>

      <div className="cf-skill-orb-label">{node.label}</div>

      <Handle type="source" position={Position.Bottom} className="cf-skill-handle" />
    </div>
  );
}