import { createResource, For, Show } from "solid-js";
import { listNodeTypes } from "./api";
import type { NodeTypeMetadata } from "../../shared/types";
import { NodeIcon } from "../../components/shared";

interface Props {
  onAdd: (nodeType: NodeTypeMetadata) => void;
}

const CATEGORY_ORDER = ["trigger", "ai", "transform", "logic", "action", "output"];
const CATEGORY_LABELS: Record<string, string> = {
  trigger: "Triggers",
  ai: "AI Agents",
  transform: "Data Transform",
  logic: "Logic",
  action: "Actions",
  output: "Output",
};

export function NodePicker(props: Props) {
  const [nodeTypes] = createResource(listNodeTypes);

  function byCategory(): Record<string, NodeTypeMetadata[]> {
    const types = nodeTypes();
    if (!types) return {};
    const groups: Record<string, NodeTypeMetadata[]> = {};
    for (const node of types) {
      if (!groups[node.category]) groups[node.category] = [];
      groups[node.category].push(node);
    }
    return groups;
  }

  return (
    <div class="node-library">
      <Show when={nodeTypes.loading}>
        <div class="subtle">Loading nodes…</div>
      </Show>
      <Show when={nodeTypes.error}>
        <div class="subtle">Failed to load node types</div>
      </Show>
      <For each={CATEGORY_ORDER.filter((c) => byCategory()[c])}>
        {(category) => (
          <div class="node-group">
            <div class="node-group-label">{CATEGORY_LABELS[category] ?? category}</div>
            <For each={byCategory()[category]}>
              {(node) => (
                <button
                  class="node-template"
                  onClick={() => props.onAdd(node)}
                  title={node.description}
                >
                  <NodeIcon type={node.type} category={node.category} />
                  <span>
                    <strong>{node.label}</strong>
                    <small>{node.description}</small>
                  </span>
                </button>
              )}
            </For>
          </div>
        )}
      </For>
    </div>
  );
}
