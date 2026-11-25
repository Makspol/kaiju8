import {
  createEffect,
  createResource,
  createSignal,
  onMount,
  Show,
  Switch,
  Match,
} from "solid-js";
import { createStore } from "solid-js/store";

import { user, isLoading, hydrateUser, logout } from "./modules/auth/store";
import { LoginPage } from "./modules/auth/LoginPage";
import { RegisterPage } from "./modules/auth/RegisterPage";
import { WorkflowList } from "./modules/workflows/WorkflowList";
import { FlowCanvas } from "./modules/workflows/FlowCanvas";
import { InspectorPanel } from "./modules/workflows/InspectorPanel";
import { NodeSheet } from "./modules/workflows/NodeSheet";
import { NodePicker } from "./modules/node-catalog/NodePicker";
import { listNodeTypes } from "./modules/node-catalog/api";
import { ExecutionsPanel } from "./modules/executions/ExecutionsPanel";
import { listExecutionSteps } from "./modules/executions/api";
import { ChatPanel } from "./modules/workflows/ChatPanel";
import { CredentialsPanel } from "./modules/credentials/CredentialsPanel";
import {
  listWorkflows,
  listWorkflowTemplates,
  createWorkflow,
  deleteWorkflow,
  updateWorkflow,
  runWorkflow,
} from "./modules/workflows/api";
import type {
  Workflow,
  WorkflowGraph,
  WorkflowNode,
  NodeTypeMetadata,
  ExecutionStep,
  WorkflowTemplate,
  WorkflowRunResult,
} from "./shared/types";

type AuthView = "login" | "register";
type StudioTab = "flow" | "executions" | "credentials";

const EMPTY_GRAPH: WorkflowGraph = {
  nodes: [],
  edges: [],
  settings: { max_steps: 20 },
};
const CANVAS_W = 1800;
const CANVAS_H = 1000;
const NODE_W = 200;
const NODE_H = 90;
const DUPLICATE_OFFSET = 48;

function generateId(): string {
  return Math.random().toString(36).slice(2, 10);
}

function generateNodeId(nodes: WorkflowNode[]): string {
  let id = generateId();
  const existingIds = new Set(nodes.map((node) => node.id));

  while (existingIds.has(id)) {
    id = generateId();
  }

  return id;
}

function cloneConfig(config: Record<string, unknown>): Record<string, unknown> {
  return JSON.parse(JSON.stringify(config));
}

function nodePosition(node: WorkflowNode): { x: number; y: number } {
  const pos = node.config["_pos"];

  if (isPosition(pos)) {
    return pos;
  }

  return { x: 80, y: 80 };
}

function isPosition(value: unknown): value is { x: number; y: number } {
  if (!value || typeof value !== "object") return false;
  const pos = value as { x?: unknown; y?: unknown };
  return typeof pos.x === "number" && typeof pos.y === "number";
}

function duplicatePosition(
  original: { x: number; y: number },
  nodes: WorkflowNode[],
): { x: number; y: number } {
  const occupied = new Set(
    nodes.map((node) => {
      const pos = nodePosition(node);
      return `${Math.round(pos.x)}:${Math.round(pos.y)}`;
    }),
  );

  for (let step = 1; step <= 10; step += 1) {
    const candidate = {
      x: clampCanvasX(original.x + DUPLICATE_OFFSET * step),
      y: clampCanvasY(original.y + DUPLICATE_OFFSET * step),
    };

    if (!occupied.has(`${Math.round(candidate.x)}:${Math.round(candidate.y)}`)) {
      return candidate;
    }
  }

  return {
    x: clampCanvasX(original.x + DUPLICATE_OFFSET),
    y: clampCanvasY(original.y + DUPLICATE_OFFSET),
  };
}

function clampCanvasX(value: number): number {
  return Math.max(0, Math.min(CANVAS_W - NODE_W, value));
}

function clampCanvasY(value: number): number {
  return Math.max(0, Math.min(CANVAS_H - NODE_H, value));
}

function addPositionDefault(
  node: WorkflowNode,
  index: number,
): WorkflowNode {
  if (node.config["_pos"]) return node;
  return {
    ...node,
    config: {
      ...node.config,
      _pos: { x: 80 + (index % 4) * 260, y: 80 + Math.floor(index / 4) * 160 },
    },
  };
}

function defaultConfigForNode(nodeMeta: NodeTypeMetadata): Record<string, unknown> {
  const schema = nodeMeta.config_schema;
  const properties = schema?.properties as Record<string, { default?: unknown }> | undefined;

  if (!properties) return {};

  const config: Record<string, unknown> = {};

  for (const [key, value] of Object.entries(properties)) {
    if ("default" in value) {
      config[key] = JSON.parse(JSON.stringify(value.default));
    }
  }

  for (const field of nodeMeta.config_ui?.fields ?? []) {
    if (field.key && config[field.key] === undefined && "default" in field) {
      config[field.key] = JSON.parse(JSON.stringify(field.default));
    }
  }

  return config;
}

export function App() {
  const [nodeTypes] = createResource(listNodeTypes);
  const [workflowTemplates] = createResource(listWorkflowTemplates);

  function getNodeMeta(type: string) {
    return nodeTypes()?.find((n) => n.type === type);
  }

  const [executionSteps, setExecutionSteps] = createSignal<ExecutionStep[]>([]);
  const [nodeSheetOpen, setNodeSheetOpen] = createSignal(false);

  const [authView, setAuthView] = createSignal<AuthView>("login");
  const [tab, setTab] = createSignal<StudioTab>("flow");
  const [workflows, setWorkflows] = createSignal<Workflow[]>([]);
  const [selectedId, setSelectedId] = createSignal("");
  const [selectedNodeId, setSelectedNodeId] = createSignal("");
  const [lastExecutionId, setLastExecutionId] = createSignal<string | null>(null);
  const [executionRefreshKey, setExecutionRefreshKey] = createSignal(0);
  const [chatTriggerNodeId, setChatTriggerNodeId] = createSignal<string | null>(null);
  const [saving, setSaving] = createSignal(false);
  const [running, setRunning] = createSignal(false);
  const [notice, setNotice] = createSignal("");
  const [error, setError] = createSignal("");
  const [loadingWf, setLoadingWf] = createSignal(false);
  const [graph, setGraph] = createStore<WorkflowGraph>(EMPTY_GRAPH);

  onMount(() => void hydrateUser());

  createEffect(() => {
    if (user()) void loadWorkflows();
  });

  createEffect(() => {
    const wf = workflows().find((w) => w.id === selectedId());
    if (wf) {
      const nodes = wf.graph.nodes.map((n, i) => addPositionDefault(n, i));
      setGraph({ ...wf.graph, nodes });
      setSelectedNodeId(nodes[0]?.id ?? "");
    }
  });

  function showNotice(msg: string) {
    setNotice(msg);
    setTimeout(() => setNotice(""), 2800);
  }

  function showError(msg: string) {
    setError(msg);
    setTimeout(() => setError(""), 4000);
  }

  async function loadWorkflows() {
    setLoadingWf(true);
    try {
      const list = await listWorkflows();
      setWorkflows(list);
      if (!selectedId() && list.length > 0) setSelectedId(list[0].id);
    } catch (err) {
      showError(err instanceof Error ? err.message : "Failed to load workflows");
    } finally {
      setLoadingWf(false);
    }
  }

  async function handleCreateWorkflow() {
    setSaving(true);
    try {
      const wf = await createWorkflow(`Workflow ${workflows().length + 1}`);
      setWorkflows((prev) => [wf, ...prev]);
      setSelectedId(wf.id);
      setLastExecutionId(null);
      setExecutionSteps([]);
      showNotice("Workflow created");
    } catch (err) {
      showError(err instanceof Error ? err.message : "Create failed");
    } finally {
      setSaving(false);
    }
  }

  async function handleCreateWorkflowFromTemplate(template: WorkflowTemplate) {
    setSaving(true);
    try {
      const wf = await createWorkflow(template.name, template.graph);
      setWorkflows((prev) => [wf, ...prev]);
      setSelectedId(wf.id);
      setTab("flow");
      showNotice("Template created");
    } catch (err) {
      showError(err instanceof Error ? err.message : "Create from template failed");
    } finally {
      setSaving(false);
    }
  }

  async function handleDeleteWorkflow(workflow: Workflow) {
    if (!window.confirm(`Delete "${workflow.name}"?`)) return;

    try {
      await deleteWorkflow(workflow.id);
      const nextWorkflows = workflows().filter((item) => item.id !== workflow.id);
      setWorkflows(nextWorkflows);

      if (selectedId() === workflow.id) {
        const nextSelectedId = nextWorkflows[0]?.id ?? "";
        setSelectedId(nextSelectedId);

        if (!nextSelectedId) {
          setSelectedNodeId("");
          setGraph(EMPTY_GRAPH);
        }
      }

      showNotice("Workflow deleted");
    } catch (err) {
      showError(err instanceof Error ? err.message : "Delete failed");
    }
  }

  async function saveCurrentWorkflow(showSaved = true): Promise<boolean> {
    const id = selectedId();
    if (!id) return false;
    setSaving(true);
    try {
      const updated = await updateWorkflow(id, {
        name: workflows().find((w) => w.id === id)?.name,
        graph: { ...graph },
      });
      setWorkflows((prev) => prev.map((w) => (w.id === id ? updated : w)));
      if (showSaved) showNotice("Saved");
      return true;
    } catch (err) {
      showError(err instanceof Error ? err.message : "Save failed");
      return false;
    } finally {
      setSaving(false);
    }
  }

  async function handleSave() {
    await saveCurrentWorkflow(true);
  }

  async function runCurrentWorkflowWithInput(
    input: Record<string, unknown>,
    options: { switchToExecutions?: boolean; notice?: string } = {},
  ): Promise<WorkflowRunResult | null> {
    const id = selectedId();
    if (!id) return null;
    setRunning(true);
    setLastExecutionId(null);

    const saved = await saveCurrentWorkflow(false);
    if (!saved) {
      setRunning(false);
      return null;
    }

    try {
      const result = await runWorkflow(id, input);
      if (!result.execution_id) {
        showError("Run succeeded but no execution ID returned");
        return result;
      }
      setLastExecutionId(result.execution_id);
      setExecutionRefreshKey((key) => key + 1);
      setExecutionSteps([]);
      const steps = await listExecutionSteps(result.execution_id);
      setExecutionSteps(steps);
      if (options.switchToExecutions) setTab("executions");
      if (options.notice) showNotice(options.notice);
      return result;
    } catch (err) {
      showError(err instanceof Error ? err.message : "Run failed");
      return null;
    } finally {
      setRunning(false);
    }
  }

  async function handleRun() {
    await runCurrentWorkflowWithInput({}, {
      switchToExecutions: true,
      notice: "Run complete",
    });
  }

  function handleAddNode(nodeMeta: NodeTypeMetadata) {
    const index = graph.nodes.length;
    const newNode: WorkflowNode = {
      id: generateId(),
      type: nodeMeta.type,
      config: {
        ...defaultConfigForNode(nodeMeta),
        _pos: {
          x: 80 + (index % 4) * 260,
          y: 80 + Math.floor(index / 4) * 160,
        },
      },
    };
    setGraph("nodes", (prev) => [...prev, newNode]);
    setSelectedNodeId(newNode.id);
    setNodeSheetOpen(true);
  }

  function handleUpdateGraph(updated: WorkflowGraph) {
    setGraph(updated);
  }

  function handleUpdateNode(updated: WorkflowNode) {
    setGraph("nodes", (prev) =>
      prev.map((n) => (n.id === updated.id ? updated : n)),
    );
  }

  function handleDuplicateNode(nodeId = selectedNodeId()) {
    const original = graph.nodes.find((node) => node.id === nodeId);

    if (!original) return;

    const duplicateId = generateNodeId(graph.nodes);
    const config = cloneConfig(original.config);
    const duplicate: WorkflowNode = {
      ...original,
      id: duplicateId,
      config: {
        ...config,
        _pos: duplicatePosition(nodePosition(original), graph.nodes),
      },
    };

    setGraph("nodes", (prev) => [...prev, duplicate]);
    setSelectedNodeId(duplicateId);
    showNotice("Node duplicated");
  }

  function handleRemoveNode() {
    const id = selectedNodeId();
    setGraph({
      nodes: graph.nodes.filter((n) => n.id !== id),
      edges: graph.edges.filter((e) => e.source !== id && e.target !== id),
      settings: graph.settings,
    });
    setSelectedNodeId(graph.nodes.find((n) => n.id !== id)?.id ?? "");
  }

  function handleRenameWorkflow(name: string) {
    const id = selectedId();
    setWorkflows((prev) => prev.map((w) => (w.id === id ? { ...w, name } : w)));
  }

  function handleSelectWorkflow(id: string) {
    setSelectedId(id);
    setLastExecutionId(null);
    setExecutionSteps([]);
  }

  const selectedNode = () =>
    graph.nodes.find((n) => n.id === selectedNodeId()) ?? null;

  const selectedNodeStep = () =>
    executionSteps().find((s) => s.node_id === selectedNodeId());

  const selectedWorkflow = () =>
    workflows().find((w) => w.id === selectedId()) ?? null;

  function handleOpenNode(id: string) {
    setSelectedNodeId(id);
    setNodeSheetOpen(true);
  }

  function handleOpenChat(id: string) {
    setSelectedNodeId(id);
    setChatTriggerNodeId(id);
  }

  const chatTriggerNode = () =>
    graph.nodes.find((node) => node.id === chatTriggerNodeId() && node.type === "chat.trigger") ?? null;

  return (
    <Switch>
      <Match when={isLoading()}>
        <div class="auth-shell">
          <div class="subtle">Loading…</div>
        </div>
      </Match>

      <Match when={!user()}>
        <Show
          when={authView() === "login"}
          fallback={
            <RegisterPage onSwitchToLogin={() => setAuthView("login")} />
          }
        >
          <LoginPage onSwitchToRegister={() => setAuthView("register")} />
        </Show>
      </Match>

      <Match when={user()}>
        <div class="studio-shell">
          <aside class="library">
            <div class="app-header">
              <div class="brand-lockup">
                <div class="app-logo">K8</div>
                <div>
                  <div class="workspace-name">{user()?.name ?? "Workspace"}</div>
                  <div class="signed-in">{user()?.email}</div>
                </div>
              </div>
              <button
                class="ghost-button quit-button"
                title={`Signed in as ${user()?.email}`}
                onClick={logout}
              >
                Quit
              </button>
            </div>

            <WorkflowList
              workflows={workflows()}
              selectedId={selectedId()}
              loading={loadingWf()}
              templates={workflowTemplates() ?? []}
              onSelect={handleSelectWorkflow}
              onCreate={handleCreateWorkflow}
              onDelete={handleDeleteWorkflow}
              onCreateFromTemplate={handleCreateWorkflowFromTemplate}
            />

            <div class="library-section">
              <div class="library-heading">
                <span>Add node</span>
              </div>
              <NodePicker onAdd={handleAddNode} />
            </div>
          </aside>

          <main class="editor">
            <header class="editor-topbar">
              <div>
                <div class="breadcrumb">Kaiju8 / Workflows</div>
                <input
                  class="title-input"
                  value={selectedWorkflow()?.name ?? ""}
                  onInput={(e) => handleRenameWorkflow(e.currentTarget.value)}
                  placeholder="Workflow name"
                />
              </div>
              <div class="editor-actions">
                <button
                  class="secondary-button"
                  onClick={handleSave}
                  disabled={saving()}
                >
                  {saving() ? "Saving…" : "⤓ Save"}
                </button>
                <button
                  class="primary-button"
                  onClick={handleRun}
                  disabled={running() || saving()}
                >
                  {running() ? "Running…" : "▶ Run"}
                </button>
              </div>
            </header>

            <div class="editor-tabs">
              {(["flow", "executions", "credentials"] as StudioTab[]).map((t) => (
                <button
                  class={tab() === t ? "active" : ""}
                  onClick={() => setTab(t)}
                >
                  {t}
                </button>
              ))}
            </div>

            {notice() && <div class="toast success">{notice()}</div>}
            {error() && <div class="toast error">{error()}</div>}

            <Show when={tab() === "flow"}>
              <Show
                when={selectedWorkflow()}
                fallback={
                  <div class="block-io-empty">
                    <strong>No workflow selected</strong>
                    <span>Create or select a workflow from the sidebar</span>
                  </div>
                }
              >
                <FlowCanvas
                  graph={graph}
                  selectedNodeId={selectedNodeId()}
                  onSelectNode={setSelectedNodeId}
                  onOpenNode={handleOpenNode}
                  onOpenChat={handleOpenChat}
                  onUpdateGraph={handleUpdateGraph}
                  onDuplicateNode={handleDuplicateNode}
                  getNodeMeta={getNodeMeta}
                />
              </Show>
            </Show>

            <Show when={tab() === "executions"}>
              <ExecutionsPanel
                workflowId={selectedId() || null}
                activeExecutionId={lastExecutionId()}
                refreshKey={executionRefreshKey()}
              />
            </Show>

            <Show when={tab() === "credentials"}>
              <CredentialsPanel />
            </Show>
          </main>

          <aside class="inspector agent-inspector">
            <Show
              when={selectedNode()}
              fallback={<div class="subtle" style={{ padding: "16px" }}>Select a node</div>}
            >
              {(node) => (
                <InspectorPanel
                  node={node()}
                  nodeMeta={getNodeMeta(node().type)}
                  graph={graph}
                  running={running()}
                  onUpdateNode={handleUpdateNode}
                  onRunWithInput={(input) => runCurrentWorkflowWithInput(input, {
                    notice: "Run complete",
                  })}
                  onDuplicateNode={() => handleDuplicateNode(node().id)}
                  onRemoveNode={handleRemoveNode}
                  onOpenSheet={() => setNodeSheetOpen(true)}
                />
              )}
            </Show>
          </aside>
        </div>

        <Show when={nodeSheetOpen() && selectedNode()}>
          {(_) => {
            const node = selectedNode()!;
            return (
              <NodeSheet
                node={node}
                nodeMeta={getNodeMeta(node.type)}
                graph={graph}
                step={selectedNodeStep()}
                running={running()}
                onUpdateNode={handleUpdateNode}
                onRunWithInput={(input) => runCurrentWorkflowWithInput(input, {
                  notice: "Run complete",
                })}
                onDuplicateNode={() => handleDuplicateNode(node.id)}
                onRemoveNode={handleRemoveNode}
                onClose={() => setNodeSheetOpen(false)}
              />
            );
          }}
        </Show>

        <Show when={chatTriggerNode()}>
          {(node) => (
            <ChatPanel
              triggerNode={node()}
              running={running()}
              onClose={() => setChatTriggerNodeId(null)}
              onSend={(input) => runCurrentWorkflowWithInput(input)}
            />
          )}
        </Show>
      </Match>
    </Switch>
  );
}
