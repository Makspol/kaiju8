import { For, Show, createMemo } from "solid-js";

import type {
  InferredInputField,
  NodeTypeMetadata,
  WorkflowGraph,
  WorkflowNode,
} from "../../shared/types";
import { FieldPathInput } from "./FieldPathInput";

interface OperatorValueSpec {
  name: "value" | "value_b" | string;
  label: string;
  value_type: "string" | "number" | "date" | "boolean" | string;
  required?: boolean;
}

interface OperatorSpec {
  operator: string;
  label: string;
  values: OperatorValueSpec[];
}

interface Props {
  node: WorkflowNode;
  nodeMeta?: NodeTypeMetadata;
  graph?: WorkflowGraph;
  onUpdateNode: (node: WorkflowNode) => void;
}

const FALLBACK_OPERATOR_SPECS: Record<string, OperatorSpec[]> = {
  string: [
    { operator: "equals", label: "Equals", values: [{ name: "value", label: "Value", value_type: "string" }] },
    { operator: "not_equals", label: "Not equals", values: [{ name: "value", label: "Value", value_type: "string" }] },
    { operator: "contains", label: "Contains", values: [{ name: "value", label: "Text", value_type: "string" }] },
    { operator: "not_contains", label: "Does not contain", values: [{ name: "value", label: "Text", value_type: "string" }] },
    { operator: "starts_with", label: "Starts with", values: [{ name: "value", label: "Text", value_type: "string" }] },
    { operator: "ends_with", label: "Ends with", values: [{ name: "value", label: "Text", value_type: "string" }] },
    { operator: "is_empty", label: "Is empty", values: [] },
    { operator: "is_not_empty", label: "Is not empty", values: [] },
    { operator: "exists", label: "Exists", values: [] },
    { operator: "not_exists", label: "Does not exist", values: [] },
  ],
  number: [
    { operator: "equals", label: "Equals", values: [{ name: "value", label: "Value", value_type: "number" }] },
    { operator: "not_equals", label: "Not equals", values: [{ name: "value", label: "Value", value_type: "number" }] },
    { operator: "gt", label: "Greater than", values: [{ name: "value", label: "Value", value_type: "number" }] },
    { operator: "gte", label: "Greater than or equal", values: [{ name: "value", label: "Value", value_type: "number" }] },
    { operator: "lt", label: "Less than", values: [{ name: "value", label: "Value", value_type: "number" }] },
    { operator: "lte", label: "Less than or equal", values: [{ name: "value", label: "Value", value_type: "number" }] },
    {
      operator: "between",
      label: "Between",
      values: [
        { name: "value", label: "From", value_type: "number" },
        { name: "value_b", label: "To", value_type: "number" },
      ],
    },
    {
      operator: "not_between",
      label: "Not between",
      values: [
        { name: "value", label: "From", value_type: "number" },
        { name: "value_b", label: "To", value_type: "number" },
      ],
    },
    { operator: "is_empty", label: "Is empty", values: [] },
    { operator: "is_not_empty", label: "Is not empty", values: [] },
    { operator: "exists", label: "Exists", values: [] },
    { operator: "not_exists", label: "Does not exist", values: [] },
  ],
  date: [
    { operator: "equals", label: "Same day", values: [{ name: "value", label: "Date", value_type: "date" }] },
    { operator: "not_equals", label: "Not same day", values: [{ name: "value", label: "Date", value_type: "date" }] },
    { operator: "before", label: "Before", values: [{ name: "value", label: "Date", value_type: "date" }] },
    { operator: "after", label: "After", values: [{ name: "value", label: "Date", value_type: "date" }] },
    { operator: "on_or_before", label: "On or before", values: [{ name: "value", label: "Date", value_type: "date" }] },
    { operator: "on_or_after", label: "On or after", values: [{ name: "value", label: "Date", value_type: "date" }] },
    {
      operator: "between",
      label: "Between",
      values: [
        { name: "value", label: "From", value_type: "date" },
        { name: "value_b", label: "To", value_type: "date" },
      ],
    },
    {
      operator: "not_between",
      label: "Not between",
      values: [
        { name: "value", label: "From", value_type: "date" },
        { name: "value_b", label: "To", value_type: "date" },
      ],
    },
    { operator: "is_empty", label: "Is empty", values: [] },
    { operator: "is_not_empty", label: "Is not empty", values: [] },
    { operator: "exists", label: "Exists", values: [] },
    { operator: "not_exists", label: "Does not exist", values: [] },
  ],
  boolean: [
    { operator: "equals", label: "Equals", values: [{ name: "value", label: "Value", value_type: "boolean" }] },
    { operator: "not_equals", label: "Not equals", values: [{ name: "value", label: "Value", value_type: "boolean" }] },
    { operator: "is_true", label: "Is true", values: [] },
    { operator: "is_false", label: "Is false", values: [] },
    { operator: "exists", label: "Exists", values: [] },
    { operator: "not_exists", label: "Does not exist", values: [] },
  ],
};

const DATA_TYPE_OPTIONS = [
  { value: "string", label: "Text" },
  { value: "number", label: "Number" },
  { value: "date", label: "Date" },
  { value: "boolean", label: "True/false" },
];

function normalizeDetectedType(type: string | undefined): string {
  if (type === "number" || type === "date" || type === "boolean") return type;

  return "string";
}

function defaultValueFor(type: string): unknown {
  if (type === "number") return 0;
  if (type === "boolean") return true;
  if (type === "date") return new Date().toISOString().slice(0, 10);

  return "";
}

function parseValue(type: string, raw: string): unknown {
  if (type === "number") {
    const parsed = Number(raw);
    return Number.isFinite(parsed) ? parsed : 0;
  }

  if (type === "boolean") return raw === "true";

  return raw;
}

function valueToString(value: unknown): string {
  if (value === undefined || value === null) return "";
  return String(value);
}

export function IfConfigForm(props: Props) {
  const operatorSpecsByDataType = createMemo(() => {
    const fromSchema = props.nodeMeta?.config_schema?.["operator_specs_by_data_type"];
    const specs = { ...FALLBACK_OPERATOR_SPECS };

    if (fromSchema && typeof fromSchema === "object") {
      for (const [key, value] of Object.entries(fromSchema)) {
        if (Array.isArray(value) && value.length > 0) {
          specs[key] = value as OperatorSpec[];
        }
      }
    }

    return specs;
  });
  const dataType = () => normalizeDetectedType(
    (props.node.config.data_type ?? props.node.config.dataType) as string | undefined,
  );
  const operatorSpecs = () =>
    operatorSpecsByDataType()[dataType()] ?? operatorSpecsByDataType().string ?? [];
  const operator = () => {
    const configured = props.node.config.operator as string | undefined;

    if (configured && operatorSpecs().some((spec) => spec.operator === configured)) {
      return configured;
    }

    return operatorSpecs()[0]?.operator ?? "equals";
  };
  const selectedOperatorSpec = () =>
    operatorSpecs().find((spec) => spec.operator === operator()) ?? operatorSpecs()[0];

  function update(patch: Record<string, unknown>) {
    props.onUpdateNode({
      ...props.node,
      config: {
        ...props.node.config,
        ...patch,
      },
    });
  }

  function updateDataType(nextType: string) {
    const specs = operatorSpecsByDataType()[nextType] ?? FALLBACK_OPERATOR_SPECS.string;
    const nextOperator = specs.some((spec) => spec.operator === operator())
      ? operator()
      : specs[0]?.operator ?? "equals";
    const valueSpec = specs.find((spec) => spec.operator === nextOperator)?.values[0];

    update({
      data_type: nextType,
      dataType: undefined,
      operator: nextOperator,
      value: valueSpec ? defaultValueFor(valueSpec.value_type) : undefined,
      value_b: undefined,
      valueB: undefined,
    });
  }

  function updateOperator(nextOperator: string) {
    const valueSpec = operatorSpecs().find((spec) => spec.operator === nextOperator)?.values[0];

    update({
      operator: nextOperator,
      value: valueSpec ? defaultValueFor(valueSpec.value_type) : undefined,
      value_b: undefined,
      valueB: undefined,
    });
  }

  function onSelectField(field: InferredInputField) {
    const nextType = normalizeDetectedType(field.type);

    update({
      field: field.path,
      data_type: nextType,
      dataType: undefined,
      operator: operatorSpecsByDataType()[nextType]?.[0]?.operator ?? "equals",
      value: operatorSpecsByDataType()[nextType]?.[0]?.values[0]
        ? defaultValueFor(operatorSpecsByDataType()[nextType][0].values[0].value_type)
        : undefined,
      value_b: undefined,
      valueB: undefined,
    });
  }

  function renderValueInput(spec: OperatorValueSpec) {
    const value = () => valueToString(props.node.config[spec.name]);

    return (
      <div class="config-field">
        <label class="config-label">{spec.label}</label>
        <Show
          when={spec.value_type === "boolean"}
          fallback={
            <input
              type={spec.value_type === "number" ? "number" : spec.value_type === "date" ? "date" : "text"}
              value={value()}
              placeholder={spec.label}
              onInput={(event) => update({
                [spec.name]: parseValue(spec.value_type, event.currentTarget.value),
              })}
            />
          }
        >
          <select
            value={value() || "true"}
            onChange={(event) => update({
              [spec.name]: parseValue("boolean", event.currentTarget.value),
            })}
          >
            <option value="true">true</option>
            <option value="false">false</option>
          </select>
        </Show>
      </div>
    );
  }

  return (
    <div class="if-config-form">
      <div class="config-field">
        <label class="config-label">Input field</label>
        <FieldPathInput
          graph={props.graph}
          nodeId={props.node.id}
          value={(props.node.config.field as string | undefined) ?? ""}
          placeholder="message or customer.score"
          onChange={(value) => update({ field: value })}
          onSelectField={onSelectField}
        />
        <div class="config-hint">
          Suggested fields come from previous nodes, so users do not need to guess paths.
        </div>
      </div>

      <div class="config-field">
        <label class="config-label">Field type</label>
        <select
          value={dataType()}
          onChange={(event) => updateDataType(event.currentTarget.value)}
        >
          <For each={DATA_TYPE_OPTIONS}>
            {(item) => <option value={item.value}>{item.label}</option>}
          </For>
        </select>
      </div>

      <div class="config-field">
        <label class="config-label">Comparison</label>
        <select
          value={operator()}
          onChange={(event) => updateOperator(event.currentTarget.value)}
        >
          <For each={operatorSpecs()}>
            {(item) => <option value={item.operator}>{item.label}</option>}
          </For>
        </select>
      </div>

      <For each={selectedOperatorSpec()?.values ?? []}>
        {(spec) => renderValueInput(spec)}
      </For>
    </div>
  );
}
