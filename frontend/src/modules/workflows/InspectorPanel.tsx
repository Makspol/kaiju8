import { Show } from "solid-js";
import { Copy } from "lucide-solid";
import type { WorkflowGraph, WorkflowNode, NodeTypeMetadata, WorkflowRunResult } from "../../shared/types";
import { NodeIcon } from "../../components/shared";
import { NodeConfigPane } from "./NodeConfigPane";

interface Props {
  node: WorkflowNode;
  nodeMeta?: NodeTypeMetadata;
  graph?: WorkflowGraph;
  running?: boolean;
  onUpdateNode: (node: WorkflowNode) => void;
  onRunWithInput?: (input: Record<string, unknown>) => Promise<WorkflowRunResult | null>;
  onDuplicateNode: () => void;
  onRemoveNode: () => void;
  onOpenSheet: () => void;
}

export function InspectorPanel(props: Props) {
  const category = () => props.node.type.split(".")[0];

  return (
    <div class="inspector-content">
      <div class="inspector-section">
        <div class="inspector-title">Node</div>
        <div class="node-head" style={{ "margin-bottom": "10px" }}>
          <NodeIcon type={props.node.type} category={category()} />
          <strong>{props.nodeMeta?.label ?? props.node.type}</strong>
        </div>
        <div class="node-tags">
          <span>{category()}</span>
          <span>{props.node.id.slice(0, 8)}</span>
        </div>
        <Show when={props.nodeMeta?.description}>
          <div class="subtle" style={{ "margin-top": "6px", "font-size": "11px" }}>
            {props.nodeMeta!.description}
          </div>
        </Show>
        <button
          class="secondary-button"
          style={{ "margin-top": "10px", width: "100%" }}
          onClick={props.onOpenSheet}
        >
          ⊞ Open details
        </button>
      </div>

      <div class="inspector-section">
        <div class="inspector-title">Config</div>
        <NodeConfigPane
          node={props.node}
          nodeMeta={props.nodeMeta}
          graph={props.graph}
          running={props.running}
          onUpdateNode={props.onUpdateNode}
          onRunWithInput={props.onRunWithInput}
        />
      </div>

      <div class="inspector-section">
        <button
          class="secondary-button wide"
          style={{ width: "100%", "margin-bottom": "10px" }}
          onClick={props.onDuplicateNode}
        >
          <Copy size={16} strokeWidth={3} />
          Duplicate node
        </button>
        <button
          class="secondary-button wide"
          style={{ color: "#b42318", "border-color": "#fecaca", width: "100%" }}
          onClick={props.onRemoveNode}
        >
          Remove node
        </button>
      </div>
    </div>
  );
}
