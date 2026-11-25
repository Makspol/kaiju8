import { Show } from "solid-js";
import { Copy } from "lucide-solid";
import type {
  ExecutionStep,
  NodeTypeMetadata,
  WorkflowGraph,
  WorkflowNode,
  WorkflowRunResult,
} from "../../shared/types";
import { NodeIcon } from "../../components/shared";
import { hasInputPort } from "../node-catalog/helpers";
import { NodeConfigPane } from "./NodeConfigPane";
import { NodeInputPane } from "./NodeInputPane";
import { NodeOutputPane } from "./NodeOutputPane";

interface Props {
  node: WorkflowNode;
  nodeMeta?: NodeTypeMetadata;
  graph?: WorkflowGraph;
  step?: ExecutionStep;
  running?: boolean;
  onUpdateNode: (node: WorkflowNode) => void;
  onRunWithInput?: (input: Record<string, unknown>) => Promise<WorkflowRunResult | null>;
  onDuplicateNode: () => void;
  onRemoveNode: () => void;
  onClose: () => void;
}

export function NodeSheet(props: Props) {
  const category = () => props.node.type.split(".")[0];
  const acceptsInput = () => hasInputPort(props.nodeMeta, props.node.type);

  return (
    <div class="node-sheet-overlay" onClick={props.onClose}>
      <div class="node-sheet" onClick={(e) => e.stopPropagation()}>

        <div class="node-sheet-header">
          <div class="node-head" style={{ gap: "10px" }}>
            <NodeIcon type={props.node.type} category={category()} />
            <div>
              <strong style={{ "font-size": "15px" }}>
                {props.nodeMeta?.label ?? props.node.type}
              </strong>
              <div class="node-tags" style={{ "margin-top": "2px" }}>
                <span>{category()}</span>
                <span>{props.node.id.slice(0, 8)}</span>
              </div>
            </div>
          </div>
          <button
            class="ghost-button"
            style={{ "font-size": "20px", "line-height": 1, padding: "2px 8px" }}
            onClick={props.onClose}
            title="Close"
          >
            ×
          </button>
        </div>

        <div class={`node-sheet-body ${acceptsInput() ? "three-pane" : "two-pane"}`}>

          <Show when={acceptsInput()}>
            <NodeInputPane step={props.step} />
          </Show>

          <div class="sheet-pane">
            <div class="sheet-pane-title">Configuration</div>
            <Show when={props.nodeMeta?.description}>
              <div class="config-hint" style={{ "margin-bottom": "12px" }}>
                {props.nodeMeta!.description}
              </div>
            </Show>
            <NodeConfigPane
              node={props.node}
              nodeMeta={props.nodeMeta}
              graph={props.graph}
              running={props.running}
              onUpdateNode={props.onUpdateNode}
              onRunWithInput={props.onRunWithInput}
            />
          </div>

          <NodeOutputPane step={props.step} />

        </div>

        <div class="node-sheet-footer">
          <button
            class="secondary-button"
            onClick={props.onDuplicateNode}
          >
            <Copy size={16} strokeWidth={3} />
            Duplicate node
          </button>
          <button
            class="secondary-button"
            style={{ color: "#b42318", "border-color": "#fecaca" }}
            onClick={() => { props.onRemoveNode(); props.onClose(); }}
          >
            Remove node
          </button>
        </div>
      </div>
    </div>
  );
}
