import { For, Match, Show, Switch, createMemo, createSignal } from "solid-js";

import type {
  ConfigUiField,
  ConfigUiSchema,
  WorkflowGraph,
  WorkflowNode,
} from "../../shared/types";
import { FieldPathInput } from "./FieldPathInput";

interface Props {
  node: WorkflowNode;
  graph?: WorkflowGraph;
  ui: ConfigUiSchema;
  onUpdateNode: (node: WorkflowNode) => void;
}

function valueAt(config: Record<string, unknown>, field: ConfigUiField): unknown {
  return config[field.key] ?? field.default;
}

function isVisible(field: ConfigUiField, config: Record<string, unknown>): boolean {
  const rule = field.visible_when;

  if (!rule) return true;

  const current = config[rule.field];

  if ("equals" in rule) return current === rule.equals;

  if (Array.isArray(rule.in)) return rule.in.includes(current);

  return true;
}

function toInputValue(value: unknown): string {
  if (value === undefined || value === null) return "";
  if (typeof value === "object") return JSON.stringify(value, null, 2);
  return String(value);
}

export function FriendlyConfigForm(props: Props) {
  const [showAdvanced, setShowAdvanced] = createSignal(false);
  const [jsonErrors, setJsonErrors] = createSignal<Record<string, string>>({});
  const fields = createMemo(() => props.ui.fields ?? []);
  const basicFields = createMemo(() =>
    fields().filter((field) => (field.section ?? "basic") !== "advanced"),
  );
  const advancedFields = createMemo(() =>
    fields().filter((field) => field.section === "advanced"),
  );

  function patch(key: string, value: unknown) {
    props.onUpdateNode({
      ...props.node,
      config: {
        ...props.node.config,
        [key]: value,
      },
    });
  }

  function patchString(key: string, value: string) {
    patch(key, value || undefined);
  }

  function patchJson(key: string, raw: string) {
    if (!raw.trim()) {
      setJsonErrors((previous) => ({ ...previous, [key]: "" }));
      patch(key, undefined);
      return;
    }

    try {
      const parsed = JSON.parse(raw);
      setJsonErrors((previous) => ({ ...previous, [key]: "" }));
      patch(key, parsed);
    } catch {
      setJsonErrors((previous) => ({ ...previous, [key]: "Invalid JSON" }));
    }
  }

  function fieldValue(field: ConfigUiField) {
    return valueAt(props.node.config, field);
  }

  function renderField(field: ConfigUiField) {
    const value = () => fieldValue(field);

    return (
      <Show when={isVisible(field, props.node.config)}>
        <div class="config-field">
          <label class="config-label">{field.label}</label>
          <Switch
            fallback={
              <input
                value={toInputValue(value())}
                placeholder={field.placeholder}
                onInput={(event) => patchString(field.key, event.currentTarget.value)}
              />
            }
          >
            <Match when={field.widget === "textarea"}>
              <textarea
                rows={4}
                value={toInputValue(value())}
                placeholder={field.placeholder}
                onInput={(event) => patchString(field.key, event.currentTarget.value)}
              />
            </Match>

            <Match when={field.widget === "select" || field.widget === "segmented_select"}>
              <select
                value={toInputValue(value())}
                onChange={(event) => patch(field.key, event.currentTarget.value)}
              >
                <For each={field.options ?? []}>
                  {(option) => (
                    <option value={String(option.value)}>
                      {option.label}
                    </option>
                  )}
                </For>
              </select>
            </Match>

            <Match when={field.widget === "checkbox"}>
              <label style={{ display: "flex", "align-items": "center", gap: "8px", "flex-direction": "row" }}>
                <input
                  type="checkbox"
                  checked={Boolean(value())}
                  style={{ width: "auto", "min-height": "unset" }}
                  onChange={(event) => patch(field.key, event.currentTarget.checked)}
                />
                <span>{Boolean(value()) ? "Enabled" : "Disabled"}</span>
              </label>
            </Match>

            <Match when={field.widget === "number" || field.widget === "integer"}>
              <input
                type="number"
                value={toInputValue(value())}
                placeholder={field.placeholder}
                onInput={(event) => {
                  const parsed = field.widget === "integer"
                    ? Number.parseInt(event.currentTarget.value, 10)
                    : Number(event.currentTarget.value);
                  patch(field.key, Number.isFinite(parsed) ? parsed : undefined);
                }}
              />
            </Match>

            <Match when={field.widget === "json"}>
              <textarea
                rows={4}
                value={toInputValue(value())}
                placeholder={field.placeholder}
                onInput={(event) => patchJson(field.key, event.currentTarget.value)}
                style={{ "font-family": "monospace", "font-size": "11px" }}
              />
              <Show when={jsonErrors()[field.key]}>
                <div class="config-hint" style={{ color: "#b42318" }}>
                  {jsonErrors()[field.key]}
                </div>
              </Show>
            </Match>

            <Match when={field.widget === "field_path"}>
              <FieldPathInput
                graph={props.graph}
                nodeId={props.node.id}
                value={toInputValue(value())}
                placeholder={field.placeholder}
                onChange={(next) => patchString(field.key, next)}
              />
            </Match>
          </Switch>
          <Show when={field.help}>
            <div class="config-hint">{field.help}</div>
          </Show>
        </div>
      </Show>
    );
  }

  return (
    <div class="friendly-config-form">
      <Show when={props.ui.description}>
        <div class="config-hint" style={{ "margin-bottom": "10px" }}>
          {props.ui.description}
        </div>
      </Show>

      <For each={basicFields()}>
        {(field) => renderField(field)}
      </For>

      <Show when={advancedFields().length > 0}>
        <button
          class="ghost-button wide"
          style={{ "margin-top": "4px" }}
          onClick={() => setShowAdvanced(!showAdvanced())}
        >
          {showAdvanced() ? "Hide advanced" : "Advanced"}
        </button>
        <Show when={showAdvanced()}>
          <div class="advanced-config-section">
            <For each={advancedFields()}>
              {(field) => renderField(field)}
            </For>
          </div>
        </Show>
      </Show>
    </div>
  );
}
