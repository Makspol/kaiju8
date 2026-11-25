import { createEffect, createMemo, createSignal, For, Show, on } from "solid-js";
import type { WorkflowGraph, WorkflowNode, NodeTypeMetadata, AgentModule, WorkflowRunResult } from "../../shared/types";
import { getModules, removeModule, updateModuleConfig } from "../ai-agent/module-config";
import { AgentModuleConfigForm } from "../ai-agent/AgentModuleConfigForm";
import { ChatTriggerConfigForm, ManualTriggerConfigForm, ScheduleTriggerConfigForm } from "./TriggerConfigForms";
import { EditFieldsConfigForm } from "./EditFieldsConfigForm";
import { IfConfigForm } from "./IfConfigForm";
import { FriendlyConfigForm } from "./FriendlyConfigForm";

export interface NodeConfigPaneProps {
  node: WorkflowNode;
  nodeMeta?: NodeTypeMetadata;
  graph?: WorkflowGraph;
  running?: boolean;
  onUpdateNode: (node: WorkflowNode) => void;
  onRunWithInput?: (input: Record<string, unknown>) => Promise<WorkflowRunResult | null>;
}

function stripInternalKeys(config: Record<string, unknown>): Record<string, unknown> {
  const result: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(config)) {
    if (!k.startsWith("_")) result[k] = v;
  }
  return result;
}

function AgentModulesSection(props: {
  node: WorkflowNode;
  onUpdateNode: (n: WorkflowNode) => void;
}) {
  const modules = () => getModules(props.node);
  const prompt = () =>
    typeof props.node.config.prompt === "string"
      ? props.node.config.prompt
      : "";
  const outputPath = () =>
    typeof props.node.config.output_path === "string"
      ? props.node.config.output_path
      : "";
  const timeoutSeconds = () =>
    typeof props.node.config.timeout_seconds === "number"
      ? String(props.node.config.timeout_seconds)
      : "";

  function onPromptChange(value: string) {
    const { prompt: _prompt, ...configWithoutPrompt } = props.node.config;
    const config = value.trim()
      ? { ...props.node.config, prompt: value }
      : configWithoutPrompt;

    props.onUpdateNode({ ...props.node, config });
  }

  function onOutputPathChange(value: string) {
    const { output_path: _outputPath, ...configWithoutOutputPath } = props.node.config;
    const config = value.trim()
      ? { ...props.node.config, output_path: value.trim() }
      : configWithoutOutputPath;

    props.onUpdateNode({ ...props.node, config });
  }

  function onTimeoutChange(value: string) {
    const { timeout_seconds: _timeoutSeconds, ...configWithoutTimeout } = props.node.config;
    const parsed = Number(value);
    const config = value.trim() && Number.isFinite(parsed) && parsed > 0
      ? { ...props.node.config, timeout_seconds: parsed }
      : configWithoutTimeout;

    props.onUpdateNode({ ...props.node, config });
  }

  function onRemove(moduleId: string) {
    props.onUpdateNode(removeModule(props.node, moduleId));
  }

  function onModuleConfigChange(mod: AgentModule, config: Record<string, unknown>) {
    props.onUpdateNode(updateModuleConfig(props.node, mod.id, config));
  }

  return (
    <>
      <div class="config-field">
        <label class="config-label" for={`agent-prompt-${props.node.id}`}>
          Agent prompt
        </label>
        <textarea
          id={`agent-prompt-${props.node.id}`}
          rows={5}
          value={prompt()}
          placeholder="Classify the incoming lead and draft a concise response."
          onInput={(event) => onPromptChange(event.currentTarget.value)}
        />
      </div>

      <div class="config-field">
        <label class="config-label" for={`agent-output-path-${props.node.id}`}>
          Save response as
        </label>
        <input
          id={`agent-output-path-${props.node.id}`}
          value={outputPath()}
          placeholder="reviews.brand"
          onInput={(event) => onOutputPathChange(event.currentTarget.value)}
        />
        <div class="config-hint">
          Optional. Use this when several AI Agent branches feed one later node.
        </div>
      </div>

      <div class="config-field">
        <label class="config-label" for={`agent-timeout-${props.node.id}`}>
          Timeout seconds
        </label>
        <input
          id={`agent-timeout-${props.node.id}`}
          type="number"
          min="0.001"
          step="1"
          value={timeoutSeconds()}
          placeholder="Workflow default"
          onInput={(event) => onTimeoutChange(event.currentTarget.value)}
        />
        <div class="config-hint">
          Optional. Stops only this AI Agent if a model or tool call takes too long.
        </div>
      </div>

      <Show when={modules().length === 0}>
        <div class="subtle">
          No modules attached. Use the + buttons on the AI Agent node to add modules.
        </div>
      </Show>
      <For each={modules()}>
        {(mod) => (
          <div class="agent-module-config-item">
            <div class="agent-module-config-header">
              <span class="agent-module-chip">{mod.type.split(".").pop()}</span>
              <span class="config-label" style={{ flex: 1 }}>{mod.type}</span>
              <button
                class="icon-button small"
                style={{ color: "#b42318", "border-color": "#fecaca" }}
                onClick={() => onRemove(mod.id)}
                title="Remove module"
              >
                ×
              </button>
            </div>
            <div style={{ "margin-top": "8px" }}>
              <AgentModuleConfigForm
                module={mod}
                onUpdateConfig={(config) => onModuleConfigChange(mod, config)}
              />
            </div>
          </div>
        )}
      </For>
    </>
  );
}

export function NodeConfigPane(props: NodeConfigPaneProps) {
  const isAiAgent = () => props.node.type === "ai.agent";
  const isManualTrigger = () => props.node.type === "manual.trigger";
  const isChatTrigger = () => props.node.type === "chat.trigger";
  const isScheduleTrigger = () => props.node.type === "schedule.trigger";
  const isEditFields = () => props.node.type === "transform.edit_fields";
  const isIfNode = () => props.node.type === "logic.if";
  const isTriggerWithForm = () => isManualTrigger() || isChatTrigger() || isScheduleTrigger();
  const hasFriendlyForm = () => props.nodeMeta?.config_ui?.mode === "form";
  const isOtherNode = () => !isAiAgent() && !isTriggerWithForm() && !isEditFields() && !isIfNode() && !hasFriendlyForm();

  const userConfig = createMemo(() => stripInternalKeys(props.node.config));
  const [jsonText, setJsonText] = createSignal(JSON.stringify(userConfig(), null, 2));
  const [jsonError, setJsonError] = createSignal("");

  createEffect(
    on(
      () => props.node.id,
      () => {
        setJsonText(JSON.stringify(stripInternalKeys(props.node.config), null, 2));
        setJsonError("");
      },
    ),
  );

  function handleJsonChange(text: string) {
    setJsonText(text);
    try {
      const parsed = JSON.parse(text) as Record<string, unknown>;
      setJsonError("");
      props.onUpdateNode({ ...props.node, config: { ...props.node.config, ...parsed } });
    } catch {
      setJsonError("Invalid JSON");
    }
  }

  return (
    <>
      {/* ai.agent — modules list */}
      <Show when={isAiAgent()}>
        <AgentModulesSection node={props.node} onUpdateNode={props.onUpdateNode} />
      </Show>

      <Show when={isManualTrigger()}>
        <ManualTriggerConfigForm
          node={props.node}
          running={props.running}
          onUpdateNode={props.onUpdateNode}
          onRunWithInput={props.onRunWithInput}
        />
      </Show>

      <Show when={isChatTrigger()}>
        <ChatTriggerConfigForm
          node={props.node}
          running={props.running}
          onUpdateNode={props.onUpdateNode}
          onRunWithInput={props.onRunWithInput}
        />
      </Show>

      <Show when={isScheduleTrigger()}>
        <ScheduleTriggerConfigForm
          node={props.node}
          running={props.running}
          onUpdateNode={props.onUpdateNode}
          onRunWithInput={props.onRunWithInput}
        />
      </Show>

      <Show when={isEditFields()}>
        <EditFieldsConfigForm
          node={props.node}
          graph={props.graph}
          onUpdateNode={props.onUpdateNode}
        />
      </Show>

      <Show when={isIfNode()}>
        <IfConfigForm
          node={props.node}
          nodeMeta={props.nodeMeta}
          graph={props.graph}
          onUpdateNode={props.onUpdateNode}
        />
      </Show>

      <Show when={hasFriendlyForm() && props.nodeMeta?.config_ui}>
        <FriendlyConfigForm
          node={props.node}
          graph={props.graph}
          ui={props.nodeMeta!.config_ui!}
          onUpdateNode={props.onUpdateNode}
        />
      </Show>

      {/* all other node types — generic JSON editor */}
      <Show when={isOtherNode()}>
        <Show when={jsonError()}>
          <div class="toast error" style={{ "margin-bottom": "8px" }}>{jsonError()}</div>
        </Show>
        <textarea
          rows={12}
          value={jsonText()}
          onInput={(e) => handleJsonChange(e.currentTarget.value)}
          style={{ "font-family": "monospace", "font-size": "12px" }}
        />
        <div class="config-hint">Keys starting with _ are reserved.</div>
        <div style={{ "margin-top": "10px" }}>
          <For each={Object.entries(userConfig())}>
            {([key, value]) => (
              <div class="code-line" style={{ "margin-bottom": "6px" }}>
                <span>{key}</span>
                <code>{JSON.stringify(value)}</code>
              </div>
            )}
          </For>
          <Show when={Object.keys(userConfig()).length === 0}>
            <div class="subtle">No config keys set</div>
          </Show>
        </div>
      </Show>
    </>
  );
}
