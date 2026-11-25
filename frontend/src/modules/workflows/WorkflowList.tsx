import { For, Show } from "solid-js";
import type { Workflow, WorkflowTemplate } from "../../shared/types";

interface Props {
  workflows: Workflow[];
  selectedId: string;
  loading: boolean;
  templates?: WorkflowTemplate[];
  onSelect: (id: string) => void;
  onCreate: () => void;
  onDelete: (workflow: Workflow) => void;
  onCreateFromTemplate?: (template: WorkflowTemplate) => void;
}

export function WorkflowList(props: Props) {
  return (
    <div class="library-section">
      <div class="library-heading">
        <span>Workflows</span>
        <button
          class="icon-button small"
          onClick={props.onCreate}
          title="New workflow"
        >
          +
        </button>
      </div>

      <div class="workflow-list">
        <Show when={props.loading}>
          <div class="subtle">Loading…</div>
        </Show>
        <Show when={!props.loading && props.workflows.length === 0}>
          <div class="subtle">No workflows yet</div>
        </Show>
        <For each={props.workflows}>
          {(wf) => (
            <div
              class={`workflow-list-item${wf.id === props.selectedId ? " active" : ""}`}
            >
              <button
                class="workflow-list-select"
                onClick={() => props.onSelect(wf.id)}
                title={wf.name}
              >
                <span>{wf.name}</span>
              </button>
              <button
                class="icon-button small workflow-delete-button"
                title="Delete workflow"
                onClick={() => props.onDelete(wf)}
              >
                ×
              </button>
            </div>
          )}
        </For>
      </div>

      <Show when={(props.templates ?? []).length > 0 && props.onCreateFromTemplate}>
        <div class="library-heading" style={{ "margin-top": "14px" }}>
          <span>Quick starts</span>
        </div>
        <div class="workflow-template-list">
          <For each={props.templates ?? []}>
            {(template) => (
              <button
                class="workflow-template-item"
                onClick={() => props.onCreateFromTemplate?.(template)}
                title={template.description}
              >
                <span>{template.name}</span>
                <span>{template.category}</span>
              </button>
            )}
          </For>
        </div>
      </Show>
    </div>
  );
}
