import { Show } from "solid-js";
import type { ExecutionStep } from "../../shared/types";
import { StatusBadge } from "../../components/shared";

interface Props {
  step?: ExecutionStep;
}

export function NodeOutputPane(props: Props) {
  return (
    <div class="sheet-pane">
      <div class="sheet-pane-title">Output</div>
      <Show
        when={props.step}
        fallback={
          <div class="sheet-pane-empty">
            <span>Run the workflow to see output data</span>
          </div>
        }
      >
        {(step) => (
          <>
            <div style={{ "margin-bottom": "8px" }}>
              <StatusBadge status={step().status} />
            </div>
            <Show when={step().error_message ?? step().error}>
              <div
                style={{
                  color: "#b42318",
                  "font-size": "11px",
                  "margin-bottom": "8px",
                  padding: "6px 8px",
                  background: "#fee2e2",
                  "border-radius": "5px",
                }}
              >
                {step().error_message ?? step().error}
              </div>
            </Show>
            <pre class="io-pre">{JSON.stringify(step().output ?? step().output_json, null, 2)}</pre>
          </>
        )}
      </Show>
    </div>
  );
}
