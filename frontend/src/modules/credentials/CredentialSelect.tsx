import { createResource, For, onCleanup, onMount, Show } from "solid-js";

import { listCredentials } from "./api";
import type { Credential } from "../../shared/types";

interface Props {
  value?: string;
  providers?: string[];
  onChange: (value: string | undefined) => void;
  label?: string;
  hint?: string;
}

export function CredentialSelect(props: Props) {
  const [credentials, { refetch }] = createResource(listCredentials);

  onMount(() => {
    const refresh = () => void refetch();
    window.addEventListener("kaiju8:credentials-updated", refresh);
    onCleanup(() => window.removeEventListener("kaiju8:credentials-updated", refresh));
  });

  const filteredCredentials = () => {
    const allowedProviders = new Set(props.providers ?? []);

    if (allowedProviders.size === 0) return credentials() ?? [];

    return (credentials() ?? []).filter((credential) =>
      allowedProviders.has(credential.provider),
    );
  };

  return (
    <div class="config-field">
      <label class="config-label">{props.label ?? "Credential"}</label>
      <select
        onChange={(e) => props.onChange(e.currentTarget.value || undefined)}
        disabled={credentials.loading}
      >
        <option value="" selected={!props.value}>
          {credentials.loading ? "Loading credentials..." : "No credential"}
        </option>
        <For each={filteredCredentials()}>
          {(credential: Credential) => (
            <option
              value={credential.id}
              selected={props.value === credential.id}
            >
              {credential.name} ({credential.provider})
            </option>
          )}
        </For>
      </select>
      <Show when={props.hint || credentials.error}>
        <div class="config-hint">
          {credentials.error ? "Could not load credentials." : props.hint}
        </div>
      </Show>
    </div>
  );
}
