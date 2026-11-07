
export type JsonSkillTreeNode = {
  id: string;
  title: string;
  requires: string[];
  skillAliases?: string[];
};

export type JsonSkillTreeTemplate = {
  version: 1;
  nodes: JsonSkillTreeNode[];
};

// Vite automatically discovers JSON files in this directory.
const modules = import.meta.glob('./*.json', {
  eager: true,
  import: 'default',
}) as Record<string, unknown>;

function validateTemplate(
  careerKey: string,
  value: unknown
): JsonSkillTreeTemplate {
  if (!value || typeof value !== 'object') {
    throw new Error(`Invalid skill tree: ${careerKey}`);
  }

  const template = value as Partial<JsonSkillTreeTemplate>;

  if (template.version !== 1 || !Array.isArray(template.nodes)) {
    throw new Error(
      `Invalid skill tree structure: ${careerKey}`
    );
  }

  const seen = new Set<string>();

  for (const node of template.nodes) {
    if (
      !node ||
      typeof node.id !== 'string' ||
      !node.id.trim() ||
      typeof node.title !== 'string' ||
      !node.title.trim() ||
      !Array.isArray(node.requires) ||
      !node.requires.every(
        (dependency) => typeof dependency === 'string'
      ) ||
      (
        node.skillAliases !== undefined &&
        (
          !Array.isArray(node.skillAliases) ||
          !node.skillAliases.every(
            (alias) => typeof alias === 'string'
          )
        )
      )
    ) {
      throw new Error(
        `Invalid node in skill tree: ${careerKey}`
      );
    }

    if (seen.has(node.id)) {
      throw new Error(
        `Duplicate node ${node.id} in ${careerKey}`
      );
    }

    seen.add(node.id);
  }

  for (const node of template.nodes) {
    for (const dependency of node.requires) {
      if (!seen.has(dependency)) {
        throw new Error(
          `Missing prerequisite ${dependency} in ${careerKey}`
        );
      }
    }
  }

  // Detect cycles in prerequisite relationships.
  const visiting = new Set<string>();
  const visited = new Set<string>();
  const byId = new Map(
    template.nodes.map((node) => [node.id, node])
  );

  function visit(id: string): void {
    if (visiting.has(id)) {
      throw new Error(
        `Circular dependency at ${id} in ${careerKey}`
      );
    }

    if (visited.has(id)) return;

    visiting.add(id);

    for (const dependency of byId.get(id)!.requires) {
      visit(dependency);
    }

    visiting.delete(id);
    visited.add(id);
  }

  for (const node of template.nodes) {
    visit(node.id);
  }

  return template as JsonSkillTreeTemplate;
}

export const jsonSkillTreeTemplates: Record<
  string,
  JsonSkillTreeTemplate
> = {};

for (const [path, value] of Object.entries(modules)) {
  const careerKey = path
    .split('/')
    .pop()!
    .replace(/\.json$/, '');

  jsonSkillTreeTemplates[careerKey] = validateTemplate(
    careerKey,
    value
  );
}
