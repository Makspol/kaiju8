import { createSignal, For, Show } from "solid-js";
import { Copy } from "lucide-solid";
import type { WorkflowNode, AgentModuleMetadata } from "../../shared/types";
import { NodeIcon } from "../../components/shared";
import { listAgentModuleTypes } from "../ai-agent/api";
import { addModule, getModules, getModulesForPort, isPortFull } from "../ai-agent/module-config";

const TOP_PORTS = ["knowledge"] as const;
const BOTTOM_PORTS = ["model", "memory", "tools"] as const;
const PORT_LABELS: Record<string, string> = {
  knowledge: "Knowledge",
  model: "Model",
  memory: "Memory",
  tools: "Tools",
};

interface Props {
  node: WorkflowNode;
  pos: { x: number; y: number };
  nodeWidth: number;
  isSelected: boolean;
  isConnecting: boolean;
  isDragging: boolean;
  showInputHandle: boolean;
  onBodyMouseDown: (e: MouseEvent) => void;
  onBodyClick: () => void;
  onOutputClick: (e: MouseEvent) => void;
  onDelete: (e: MouseEvent) => void;
  onDuplicate: (e: MouseEvent) => void;
  onUpdateNode: (updated: WorkflowNode) => void;
}

export function AgentNodeCard(props: Props) {
  const [pickerPort, setPickerPort] = createSignal<string | null>(null);
  const [pickerOptions, setPickerOptions] = createSignal<AgentModuleMetadata[]>([]);
  const [pickerLoading, setPickerLoading] = createSignal(false);

  const modules = () => getModules(props.node);

  async function openPicker(port: string, e: MouseEvent) {
    e.stopPropagation();
    if (pickerPort() === port) {
      setPickerPort(null);
      return;
    }
    setPickerLoading(true);
    try {
      const options = await listAgentModuleTypes(port);
      setPickerOptions(options);
      setPickerPort(port);
    } finally {
      setPickerLoading(false);
    }
  }

  function selectModule(meta: AgentModuleMetadata, e: MouseEvent) {
    e.stopPropagation();
    props.onUpdateNode(addModule(props.node, meta));
    setPickerPort(null);
  }

  function renderPortRow(port: string) {
    const portModules = () => getModulesForPort(props.node, port);
    const full = () => isPortFull(port, modules());
    return (
      <div class="agent-port-row">
        <span class="agent-port-label">{PORT_LABELS[port]}</span>
        <div class="agent-port-chips">
          <For each={portModules()}>
            {(m) => (
              <span class="agent-module-chip" title={m.type}>
                {m.type.split(".").pop()}
              </span>
            )}
          </For>
        </div>
        <Show when={!full()}>
          <button
            class="agent-port-add"
            title={`Add ${PORT_LABELS[port]}`}
            onClick={(e) => openPicker(port, e)}
          >
            +
          </button>
        </Show>
      </div>
    );
  }

  return (
    <div
      class={`canvas-node agent-node${props.isSelected ? " selected" : ""}${props.isConnecting ? " connecting" : ""}`}
      style={{
        left: `${props.pos.x}px`,
        top: `${props.pos.y}px`,
        width: `${props.nodeWidth}px`,
        cursor: props.isDragging ? "grabbing" : "grab",
      }}
      onMouseDown={props.onBodyMouseDown}
      onClick={props.onBodyClick}
    >
      {/* Top ports: knowledge */}
      <div class="agent-ports">
        <For each={TOP_PORTS}>{(port) => renderPortRow(port)}</For>
      </div>

      <div class="agent-node-divider" />

      {/* Main body */}
      <div class="agent-node-body">
        <button
          class="node-delete-icon"
          onClick={(e) => { e.stopPropagation(); props.onDelete(e); }}
          title="Remove node"
        >
          ×
        </button>
        <button
          class="node-duplicate-icon"
          onClick={(e) => { e.stopPropagation(); props.onDuplicate(e); }}
          title="Duplicate node"
          aria-label="Duplicate node"
        >
          <Copy size={14} strokeWidth={3} />
        </button>
        <div class="node-head">
          <NodeIcon type={props.node.type} category="ai" />
          <strong title={props.node.type}>AI Agent</strong>
          <span class="node-status" />
        </div>
        <div class="node-tags">
          <span>ai</span>
        </div>
        <p>{props.node.type}</p>
        <button
          class="node-handle output"
          title={props.isConnecting ? "Cancel connect" : "Connect to another node"}
          onClick={(e) => { e.stopPropagation(); props.onOutputClick(e); }}
        >
          {props.isConnecting ? "✕" : "+"}
        </button>
        <Show when={props.showInputHandle}>
          <div class="node-handle input" />
        </Show>
      </div>

      <div class="agent-node-divider" />

      {/* Bottom ports: model, memory, tools */}
      <div class="agent-ports">
        <For each={BOTTOM_PORTS}>{(port) => renderPortRow(port)}</For>
      </div>

      {/* Module picker popover */}
      <Show when={pickerPort() !== null}>
        <div class="agent-module-picker" onClick={(e) => e.stopPropagation()}>
          <div class="agent-module-picker-header">
            <span>Add {PORT_LABELS[pickerPort()!] ?? pickerPort()} module</span>
            <button
              class="ghost-button"
              style={{ height: "22px", padding: "0 6px", "font-size": "12px" }}
              onClick={(e) => { e.stopPropagation(); setPickerPort(null); }}
            >
              ×
            </button>
          </div>
          <Show when={pickerLoading()}>
            <div class="subtle" style={{ padding: "8px" }}>Loading…</div>
          </Show>
          <Show when={!pickerLoading()}>
            <For each={pickerOptions()}>
              {(mod) => (
                <button class="agent-module-option" onClick={(e) => selectModule(mod, e)}>
                  <strong>{mod.label}</strong>
                  <small>{mod.description}</small>
                </button>
              )}
            </For>
            <Show when={pickerOptions().length === 0}>
              <div class="subtle" style={{ padding: "8px" }}>No modules available</div>
            </Show>
          </Show>
        </div>
      </Show>
    </div>
  );
}
