import { createEffect, createResource, createSignal, For, Show } from "solid-js";
import { getExecution, listExecutions, listExecutionSteps } from "./api";
import type { Execution, ExecutionStep } from "../../shared/types";
import { ExecutionBadge } from "../../components/shared";

interface Props {
  workflowId: string | null;
  activeExecutionId: string | null;
  refreshKey: number;
}

export function ExecutionsPanel(props: Props) {
  const [selectedExecutionId, setSelectedExecutionId] = createSignal<string | null>(null);
  const [selectedWorkflowId, setSelectedWorkflowId] = createSignal<string | null>(null);
  const [history] = createResource(
    () => props.workflowId ? `${props.workflowId}:${props.refreshKey}` : null,
    () => (props.workflowId ? listExecutions(props.workflowId) : []),
  );
  const [execution] = createResource(
    () => selectedExecutionId(),
    (id) => (id ? getExecution(id) : null),
  );
  const [steps] = createResource(
    () => selectedExecutionId(),
    (id) => (id ? listExecutionSteps(id) : []),
  );

  createEffect(() => {
    if (props.workflowId !== selectedWorkflowId()) {
      setSelectedWorkflowId(props.workflowId);
      setSelectedExecutionId(null);
    }
  });

  createEffect(() => {
    if (props.activeExecutionId) {
      setSelectedExecutionId(props.activeExecutionId);
      return;
    }

    const firstExecution = history()?.[0];
    if (firstExecution && !selectedExecutionId()) {
      setSelectedExecutionId(firstExecution.id);
    } else if (history() && !firstExecution) {
      setSelectedExecutionId(null);
    }
  });

  return (
    <div class="logs-view">
      <Show when={!props.workflowId}>
        <div class="block-io-empty">
          <strong>No workflow selected</strong>
          <span>Select a workflow to see run history</span>
        </div>
      </Show>

      <Show when={props.workflowId}>
        <div class="executions-layout">
          <aside class="execution-history">
            <div class="execution-history-head">
              <span>Run history</span>
              <small>{history()?.length ?? 0}</small>
            </div>

            <Show when={history.loading}>
              <div class="subtle">Loading history...</div>
            </Show>

            <For each={history() ?? []}>
              {(item) => (
                <ExecutionHistoryItem
                  execution={item}
                  active={selectedExecutionId() === item.id}
                  onSelect={() => setSelectedExecutionId(item.id)}
                />
              )}
            </For>

            <Show when={!history.loading && !history()?.length}>
              <div class="block-io-empty compact">
                <strong>No runs yet</strong>
                <span>Run this workflow to create the first history entry</span>
              </div>
            </Show>
          </aside>

          <section class="execution-detail">
            <Show when={execution.loading}>
              <div class="subtle">Loading execution...</div>
            </Show>

            <Show when={!selectedExecutionId() && !history.loading && history()?.length}>
              <div class="block-io-empty">
                <strong>No execution selected</strong>
                <span>Select a run from history</span>
              </div>
            </Show>

            <Show when={execution()}>
              {(exec) => (
                <div class="run-detail">
                  <div class="detail-head">
                    <div>
                      <span>{formatDateTime(exec().created_at)}</span>
                      <strong>{exec().id.slice(0, 16)}...</strong>
                    </div>
                    <ExecutionBadge status={exec().status} />
                  </div>

                  <Show when={exec().error}>
                    <div class="execution-error">
                      <strong>Error</strong>
                      <span>{exec().error}</span>
                    </div>
                  </Show>

                  <div class="inspector-section">
                    <div class="inspector-title">Input</div>
                    <pre class="io-pre">{JSON.stringify(exec().input ?? exec().input_json, null, 2)}</pre>
                  </div>

                  <div class="inspector-section">
                    <div class="inspector-title">Result</div>
                    <pre class="io-pre">{JSON.stringify(exec().output ?? exec().result, null, 2)}</pre>
                  </div>

                  <Show when={exec().usage}>
                    <div class="inspector-section">
                      <div class="inspector-title">Usage</div>
                      <UsageSummary usage={exec().usage!} />
                    </div>
                  </Show>

                  <div class="inspector-title" style={{ "margin-top": "14px" }}>
                    Steps ({steps()?.length ?? 0})
                  </div>
                  <div class="timeline" style={{ "margin-top": "8px" }}>
                    <For each={steps() ?? []}>
                      {(step) => <StepRow step={step} />}
                    </For>
                    <Show when={!steps()?.length && !steps.loading}>
                      <div class="subtle">No steps recorded</div>
                    </Show>
                  </div>
                </div>
              )}
            </Show>
          </section>
        </div>
      </Show>
    </div>
  );
}

function ExecutionHistoryItem(props: {
  execution: Execution;
  active: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      class={`execution-history-item${props.active ? " active" : ""}`}
      onClick={props.onSelect}
    >
      <span>{formatDateTime(props.execution.created_at)}</span>
      <strong>{props.execution.id.slice(0, 8)}</strong>
      <ExecutionBadge status={props.execution.status} />
      <Show when={props.execution.error}>
        <small>{props.execution.error}</small>
      </Show>
    </button>
  );
}

function UsageSummary(props: { usage: Record<string, unknown> }) {
  const byProvider = () =>
    (props.usage.by_provider as Record<string, Record<string, unknown>> | undefined) ?? {};

  return (
    <div class="usage-summary">
      <div class="usage-grid">
        <UsageMetric label="LLM calls" value={props.usage.llm_calls} />
        <UsageMetric label="Tokens" value={props.usage.tokens_used} />
        <UsageMetric label="Budget" value={props.usage.budget_used} />
      </div>

      <For each={Object.entries(byProvider())}>
        {([provider, usage]) => (
          <div class="provider-usage-card">
            <div class="provider-limit-title">{provider}</div>
            <div class="usage-grid">
              <UsageMetric label="LLM calls" value={usage.llm_calls} />
              <UsageMetric label="Tokens" value={usage.tokens_used} />
              <UsageMetric label="Budget" value={usage.budget_used} />
            </div>
          </div>
        )}
      </For>
    </div>
  );
}

function UsageMetric(props: { label: string; value: unknown }) {
  return (
    <div class="usage-metric">
      <span>{props.label}</span>
      <strong>{props.value === undefined ? "-" : String(props.value)}</strong>
    </div>
  );
}

function StepRow(props: { step: ExecutionStep }) {
  const [expanded, setExpanded] = createSignal(false);
  const stepError = () => props.step.error_message ?? props.step.error;

  return (
    <div class={`step${props.step.status === "error" ? " failed" : ""}`}>
      <div class="step-marker">
        {props.step.status === "error" ? "x" : "OK"}
      </div>
      <div class="step-body">
        <div class="step-title">
          <strong>{props.step.node_type}</strong>
          <span>{props.step.node_id.slice(0, 8)}</span>
          <button
            class="link-button"
            style={{ "font-size": "10px" }}
            onClick={() => setExpanded((v) => !v)}
          >
            {expanded() ? "hide" : "show"} I/O
          </button>
        </div>
        <Show when={props.step.status === "error" && stepError()}>
          <small style={{ color: "#b42318" }}>{stepError()}</small>
        </Show>
        <Show when={expanded()}>
          <div class="io-row-label" style={{ "margin-top": "8px" }}>Input</div>
          <pre class="io-pre">{JSON.stringify(props.step.input_json ?? props.step.input, null, 2)}</pre>
          <div class="io-row-label" style={{ "margin-top": "6px" }}>Output</div>
          <pre class="io-pre">{JSON.stringify(props.step.output_json ?? props.step.output, null, 2)}</pre>
        </Show>
      </div>
    </div>
  );
}

function formatDateTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(date);
}
