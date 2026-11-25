import { createEffect, createSignal, For, Match, on, Show, Switch } from "solid-js";
import type { WorkflowGraph, WorkflowNode } from "../../shared/types";
import { FieldPathInput } from "./FieldPathInput";

type EditOperation = "set" | "add_if_missing" | "delete" | "rename";
type ValueType = "string" | "number" | "boolean" | "null" | "json" | "field";

interface PersistedOperation {
  operation: EditOperation | "add" | "remove";
  path: string;
  to_path?: string;
  value?: unknown;
}

interface UiOperation extends PersistedOperation {
  value_type: ValueType;
}

interface Props {
  node: WorkflowNode;
  graph?: WorkflowGraph;
  onUpdateNode: (node: WorkflowNode) => void;
}

const DEFAULT_OPERATION: UiOperation = {
  operation: "set",
  path: "isCorrect",
  value: true,
  value_type: "boolean",
};

function inferValueType(value: unknown): ValueType {
  if (typeof value === "boolean") return "boolean";
  if (typeof value === "number") return "number";
  if (value === null) return "null";
  if (typeof value === "string" && /^\{\{\s*[^}]+\s*\}\}$/.test(value)) return "field";
  if (typeof value === "object" && value !== null) return "json";
  return "string";
}

function operationsFrom(node: WorkflowNode): UiOperation[] {
  const operations = node.config.operations;

  if (!Array.isArray(operations) || operations.length === 0) {
    return [{ ...DEFAULT_OPERATION }];
  }

  return operations.map((operation) => {
    const item = operation as PersistedOperation;
    return {
      operation: normalizeOperation(item.operation),
      path: item.path,
      to_path: item.to_path,
      value: item.value,
      value_type: inferValueType(item.value),
    };
  });
}

function normalizeOperation(operation: PersistedOperation["operation"]): EditOperation {
  if (operation === "add") return "add_if_missing";
  if (operation === "remove") return "delete";
  return operation;
}

function displayValue(operation: UiOperation): string {
  if (operation.value_type === "field" && typeof operation.value === "string") {
    return operation.value.replace(/^\{\{\s*/, "").replace(/\s*\}\}$/, "");
  }

  if (operation.value === null || operation.value === undefined) return "";
  if (typeof operation.value === "object") return JSON.stringify(operation.value);
  return String(operation.value);
}

function defaultValueFor(type: ValueType): unknown {
  if (type === "boolean") return true;
  if (type === "number") return 0;
  if (type === "null") return null;
  if (type === "json") return {};
  return "";
}

function parseValue(type: ValueType, raw: string): unknown {
  if (type === "number") {
    const parsed = Number(raw);
    return Number.isFinite(parsed) ? parsed : 0;
  }

  if (type === "boolean") return raw === "true";
  if (type === "null") return null;
  if (type === "field") return raw.trim() ? `{{ ${raw.trim()} }}` : "";

  if (type === "json") {
    try {
      return JSON.parse(raw || "{}");
    } catch {
      return raw;
    }
  }

  return raw;
}

function toPersistedOperations(operations: UiOperation[]): PersistedOperation[] {
  return operations
    .filter((operation) => operation.path.trim())
    .map((operation) => {
      const path = operation.path.trim();

      if (operation.operation === "delete") {
        return {
          operation: "delete",
          path,
        };
      }

      if (operation.operation === "rename") {
        return {
          operation: "rename",
          path,
          to_path: operation.to_path?.trim() ?? "",
        };
      }

      return {
        operation: operation.operation,
        path,
        value: operation.value,
      };
    });
}

export function EditFieldsConfigForm(props: Props) {
  const [operations, setOperations] = createSignal<UiOperation[]>(operationsFrom(props.node));

  createEffect(on(
    () => props.node.id,
    () => setOperations(operationsFrom(props.node)),
  ));

  function commit(next: UiOperation[]) {
    setOperations(next);
    props.onUpdateNode({
      ...props.node,
      config: {
        ...props.node.config,
        operations: toPersistedOperations(next),
      },
    });
  }

  function update(index: number, patch: Partial<UiOperation>) {
    commit(
      operations().map((operation, currentIndex) =>
        currentIndex === index ? { ...operation, ...patch } : operation,
      ),
    );
  }

  function changeType(index: number, valueType: ValueType) {
    update(index, {
      value_type: valueType,
      value: defaultValueFor(valueType),
    });
  }

  function addOperation() {
    commit([
      ...operations(),
      {
        operation: "add_if_missing",
        path: "",
        value: "",
        value_type: "string",
      },
    ]);
  }

  function removeOperation(index: number) {
    const next = operations().filter((_, currentIndex) => currentIndex !== index);
    commit(next.length ? next : [{ ...DEFAULT_OPERATION }]);
  }

  return (
    <div class="edit-fields-form">
      <For each={operations()}>
        {(operation, index) => (
          <div class="edit-field-row">
            <div class="edit-field-row-head">
              <select
                value={operation.operation}
                onChange={(event) => update(index(), {
                  operation: event.currentTarget.value as EditOperation,
                })}
              >
                <option value="set">Set field</option>
                <option value="add_if_missing">Add if missing</option>
                <option value="delete">Delete field</option>
                <option value="rename">Rename field</option>
              </select>
              <button
                class="icon-button small"
                title="Remove operation"
                onClick={() => removeOperation(index())}
              >
                ×
              </button>
            </div>

            <div class="config-field">
              <label class="config-label">Field name</label>
              <Show
                when={operation.operation === "delete" || operation.operation === "rename"}
                fallback={
                  <input
                    value={operation.path}
                    placeholder="message, isCorrect, review.approved"
                    onInput={(event) => update(index(), { path: event.currentTarget.value })}
                  />
                }
              >
                <FieldPathInput
                  graph={props.graph}
                  nodeId={props.node.id}
                  value={operation.path}
                  placeholder="Select field to change"
                  onChange={(value) => update(index(), { path: value })}
                />
              </Show>
            </div>

            <Show when={operation.operation === "rename"}>
              <div class="config-field">
                <label class="config-label">New field name</label>
                <input
                  value={operation.to_path ?? ""}
                  placeholder="review.isCorrect"
                  onInput={(event) => update(index(), { to_path: event.currentTarget.value })}
                />
              </div>
            </Show>

            <Show when={operation.operation !== "delete" && operation.operation !== "rename"}>
              <div class="edit-field-value-grid">
                <div class="config-field">
                  <label class="config-label">Value type</label>
                  <select
                    value={operation.value_type}
                    onChange={(event) => changeType(index(), event.currentTarget.value as ValueType)}
                  >
                    <option value="string">Text</option>
                    <option value="number">Number</option>
                    <option value="boolean">Boolean</option>
                    <option value="null">Empty</option>
                    <option value="json">JSON</option>
                    <option value="field">Input field</option>
                  </select>
                </div>

                <div class="config-field">
                  <label class="config-label">Value</label>
                  <Switch>
                    <Match when={operation.value_type === "boolean"}>
                      <select
                        value={String(operation.value ?? true)}
                        onChange={(event) => update(index(), {
                          value: event.currentTarget.value === "true",
                        })}
                      >
                        <option value="true">true</option>
                        <option value="false">false</option>
                      </select>
                    </Match>

                    <Match when={operation.value_type === "number"}>
                      <input
                        type="number"
                        value={displayValue(operation)}
                        onInput={(event) => update(index(), {
                          value: parseValue("number", event.currentTarget.value),
                        })}
                      />
                    </Match>

                    <Match when={operation.value_type === "json"}>
                      <textarea
                        rows={3}
                        value={displayValue(operation)}
                        placeholder='{"key": "value"}'
                        onInput={(event) => update(index(), {
                          value: parseValue("json", event.currentTarget.value),
                        })}
                        style={{ "font-family": "monospace", "font-size": "11px" }}
                      />
                    </Match>

                    <Match when={operation.value_type === "field"}>
                      <FieldPathInput
                        graph={props.graph}
                        nodeId={props.node.id}
                        value={displayValue(operation)}
                        placeholder="message or user.name"
                        onChange={(value) => update(index(), {
                          value: parseValue("field", value),
                        })}
                      />
                    </Match>

                    <Match when={operation.value_type === "null"}>
                      <input value="" disabled placeholder="No value" />
                    </Match>

                    <Match when={operation.value_type === "string"}>
                      <input
                        value={displayValue(operation)}
                        placeholder="Text value"
                        onInput={(event) => update(index(), {
                          value: event.currentTarget.value,
                        })}
                      />
                    </Match>
                  </Switch>
                </div>
              </div>
            </Show>
          </div>
        )}
      </For>

      <button class="secondary-button wide" onClick={addOperation}>
        Add operation
      </button>
    </div>
  );
}
