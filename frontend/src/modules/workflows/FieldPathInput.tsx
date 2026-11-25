import { createMemo, createResource, For, Show } from "solid-js";

import type { InferredInputField, WorkflowGraph } from "../../shared/types";
import { analyzeNodeInputFields } from "./api";

interface Props {
  graph?: WorkflowGraph;
  nodeId: string;
  value: string;
  placeholder?: string;
  onChange: (value: string) => void;
  onSelectField?: (field: InferredInputField) => void;
}

export function FieldPathInput(props: Props) {
  const [result] = createResource(
    () => props.graph
      ? JSON.stringify({ graph: props.graph, nodeId: props.nodeId })
      : "",
    (source) => source
      ? (() => {
          const parsed = JSON.parse(source) as { graph: WorkflowGraph; nodeId: string };
          return analyzeNodeInputFields(parsed.graph, parsed.nodeId);
        })()
      : Promise.resolve({ node_id: props.nodeId, fields: [], warnings: [] }),
  );

  const fields = createMemo(() => result()?.fields ?? []);
  const selectedField = createMemo(() =>
    fields().find((field) => field.path === props.value),
  );

  function applyFieldValue(path: string) {
    const field = fields().find((item) => item.path === path);

    props.onChange(path);

    if (field) props.onSelectField?.(field);
  }

  function selectField(path: string) {
    applyFieldValue(path);
  }

  return (
    <>
      <input
        value={props.value}
        list={`fields-${props.nodeId}`}
        placeholder={props.placeholder ?? "Select or type a field path"}
        onInput={(event) => applyFieldValue(event.currentTarget.value)}
      />
      <datalist id={`fields-${props.nodeId}`}>
        <For each={fields()}>
          {(field) => (
            <option value={field.path}>
              {field.type}
            </option>
          )}
        </For>
      </datalist>
      <Show when={fields().length > 0}>
        <select
          value={props.value}
          onChange={(event) => selectField(event.currentTarget.value)}
          style={{ "margin-top": "6px" }}
        >
          <option value="">Choose from previous nodes</option>
          <For each={fields()}>
            {(field) => (
              <option value={field.path}>
                {field.path} ({field.type})
              </option>
            )}
          </For>
        </select>
      </Show>
      <Show when={selectedField()}>
        {(field) => (
          <div class="config-hint">
            Detected as {field().type}.
          </div>
        )}
      </Show>
    </>
  );
}
