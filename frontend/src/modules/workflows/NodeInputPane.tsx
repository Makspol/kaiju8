import { Show } from "solid-js";
import type { ExecutionStep } from "../../shared/types";

interface Props {
  step?: ExecutionStep;
}

export function NodeInputPane(props: Props) {
  return (
    <div class="sheet-pane">
      <div class="sheet-pane-title">Input</div>
      <Show
        when={props.step}
        fallback={
          <div class="sheet-pane-empty">
            <span>Run the workflow to see input data</span>
          </div>
        }
      >
        {(step) => (
          <pre class="io-pre">{JSON.stringify(step().input ?? step().input_json, null, 2)}</pre>
        )}
      </Show>
    </div>
  );
}
