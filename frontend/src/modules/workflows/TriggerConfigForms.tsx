import { createMemo, createSignal, Show } from "solid-js";
import type { WorkflowNode, WorkflowRunResult } from "../../shared/types";

interface TriggerFormProps {
  node: WorkflowNode;
  running?: boolean;
  onUpdateNode: (node: WorkflowNode) => void;
  onRunWithInput?: (input: Record<string, unknown>) => Promise<WorkflowRunResult | null>;
}

function parseJsonObject(text: string): Record<string, unknown> | null {
  try {
    const parsed = JSON.parse(text);
    return parsed && typeof parsed === "object" && !Array.isArray(parsed)
      ? (parsed as Record<string, unknown>)
      : null;
  } catch {
    return null;
  }
}

export function ManualTriggerConfigForm(props: TriggerFormProps) {
  const initialPayload = createMemo(() => (
    (props.node.config.test_payload as Record<string, unknown> | undefined) ?? {}
  ));
  const [text, setText] = createSignal(JSON.stringify(initialPayload(), null, 2));
  const [error, setError] = createSignal("");
  const [lastOutput, setLastOutput] = createSignal<Record<string, unknown> | null>(null);

  function applyPayload(value: string) {
    setText(value);
    const parsed = parseJsonObject(value);

    if (!parsed) {
      setError("Test data must be a JSON object.");
      return;
    }

    setError("");
    props.onUpdateNode({
      ...props.node,
      config: {
        ...props.node.config,
        test_payload: parsed,
      },
    });
  }

  async function runTest() {
    const parsed = parseJsonObject(text());

    if (!parsed || !props.onRunWithInput) {
      setError("Test data must be a JSON object.");
      return;
    }

    const result = await props.onRunWithInput(parsed);
    setLastOutput(result?.output ?? null);
  }

  return (
    <>
      <div class="config-field">
        <label class="config-label">Test data</label>
        <textarea
          rows={7}
          value={text()}
          onInput={(event) => applyPayload(event.currentTarget.value)}
          style={{ "font-family": "monospace", "font-size": "11px" }}
        />
        <Show when={error()}>
          <div class="config-hint" style={{ color: "#b42318" }}>{error()}</div>
        </Show>
        <Show when={!error()}>
          <div class="config-hint">This JSON is sent when you run this manual trigger test.</div>
        </Show>
      </div>

      <button
        class="primary-button wide"
        disabled={props.running || !!error() || !props.onRunWithInput}
        onClick={runTest}
      >
        {props.running ? "Running..." : "Run with test data"}
      </button>

      <Show when={lastOutput()}>
        <div class="config-field" style={{ "margin-top": "12px" }}>
          <label class="config-label">Last output</label>
          <pre class="io-pre">{JSON.stringify(lastOutput(), null, 2)}</pre>
        </div>
      </Show>
    </>
  );
}

export function ChatTriggerConfigForm(props: TriggerFormProps) {
  function updateConfig(patch: Record<string, unknown>) {
    props.onUpdateNode({
      ...props.node,
      config: {
        ...props.node.config,
        ...patch,
      },
    });
  }

  return (
    <>
      <div class="config-field">
        <label class="config-label">Sample message</label>
        <input
          type="text"
          value={(props.node.config.sample_message as string | undefined) ?? "Hello"}
          onInput={(event) => updateConfig({ sample_message: event.currentTarget.value })}
        />
        <div class="config-hint">Double-click this node on the canvas to open the chat panel.</div>
      </div>
    </>
  );
}

export function ScheduleTriggerConfigForm(props: TriggerFormProps) {
  const initialPayload = createMemo(() => (
    (props.node.config.test_payload as Record<string, unknown> | undefined) ?? {}
  ));
  const [payloadText, setPayloadText] = createSignal(JSON.stringify(initialPayload(), null, 2));
  const [error, setError] = createSignal("");
  const [lastOutput, setLastOutput] = createSignal<Record<string, unknown> | null>(null);

  function updateConfig(patch: Record<string, unknown>) {
    props.onUpdateNode({
      ...props.node,
      config: {
        ...props.node.config,
        ...patch,
      },
    });
  }

  function applyPayload(value: string) {
    setPayloadText(value);
    const parsed = parseJsonObject(value);

    if (!parsed) {
      setError("Test data must be a JSON object.");
      return;
    }

    setError("");
    updateConfig({ test_payload: parsed });
  }

  async function runTest() {
    const parsed = parseJsonObject(payloadText());

    if (!parsed || !props.onRunWithInput) {
      setError("Test data must be a JSON object.");
      return;
    }

    const result = await props.onRunWithInput(parsed);
    setLastOutput(result?.output ?? null);
  }

  const mode = () => (props.node.config.mode as string | undefined) ?? "interval";

  return (
    <>
      <div class="config-field">
        <label class="config-label">Mode</label>
        <select
          value={mode()}
          onChange={(event) => updateConfig({ mode: event.currentTarget.value })}
        >
          <option value="interval">Interval</option>
          <option value="cron">Cron</option>
        </select>
      </div>

      <Show when={mode() === "interval"}>
        <div class="config-field">
          <label class="config-label">Interval seconds</label>
          <input
            type="number"
            min="1"
            value={(props.node.config.interval_seconds as number | undefined) ?? 3600}
            onInput={(event) => updateConfig({ interval_seconds: Number(event.currentTarget.value) })}
          />
        </div>
      </Show>

      <Show when={mode() === "cron"}>
        <div class="config-field">
          <label class="config-label">Cron</label>
          <input
            type="text"
            value={(props.node.config.cron as string | undefined) ?? "0 9 * * *"}
            onInput={(event) => updateConfig({ cron: event.currentTarget.value })}
          />
          <div class="config-hint">Five fields: minute hour day month weekday.</div>
        </div>
      </Show>

      <div class="config-field">
        <label class="config-label">Timezone</label>
        <input
          type="text"
          value={(props.node.config.timezone as string | undefined) ?? "UTC"}
          onInput={(event) => updateConfig({ timezone: event.currentTarget.value })}
        />
      </div>

      <div class="config-field">
        <label class="config-label">Test data</label>
        <textarea
          rows={6}
          value={payloadText()}
          onInput={(event) => applyPayload(event.currentTarget.value)}
          style={{ "font-family": "monospace", "font-size": "11px" }}
        />
        <Show when={error()}>
          <div class="config-hint" style={{ color: "#b42318" }}>{error()}</div>
        </Show>
        <Show when={!error()}>
          <div class="config-hint">This JSON is sent when you run this schedule test.</div>
        </Show>
      </div>

      <button
        class="primary-button wide"
        disabled={props.running || !!error() || !props.onRunWithInput}
        onClick={runTest}
      >
        {props.running ? "Running..." : "Run with test data"}
      </button>

      <Show when={lastOutput()}>
        <div class="config-field" style={{ "margin-top": "12px" }}>
          <label class="config-label">Last output</label>
          <pre class="io-pre">{JSON.stringify(lastOutput(), null, 2)}</pre>
        </div>
      </Show>
    </>
  );
}
