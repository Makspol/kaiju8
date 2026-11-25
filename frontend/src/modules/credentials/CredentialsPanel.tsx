import { createResource, createSignal, For, Show } from "solid-js";

import {
  createCredential,
  deleteCredential,
  listCredentials,
} from "./api";

const PROVIDERS = [
  { value: "anthropic", label: "Anthropic / Claude" },
  { value: "gemini", label: "Gemini" },
  { value: "brave_search", label: "Brave Search" },
  { value: "tavily", label: "Tavily" },
  { value: "custom", label: "Custom API" },
];

function notifyCredentialsChanged() {
  window.dispatchEvent(new CustomEvent("kaiju8:credentials-updated"));
}

export function CredentialsPanel() {
  const [credentials, { refetch }] = createResource(listCredentials);
  const [name, setName] = createSignal("");
  const [provider, setProvider] = createSignal("gemini");
  const [secret, setSecret] = createSignal("");
  const [saving, setSaving] = createSignal(false);
  const [error, setError] = createSignal("");
  const [notice, setNotice] = createSignal("");

  function showNotice(message: string) {
    setNotice(message);
    setTimeout(() => setNotice(""), 2800);
  }

  function showError(message: string) {
    setError(message);
    setTimeout(() => setError(""), 4000);
  }

  async function handleCreate() {
    if (!name().trim() || !secret().trim()) {
      showError("Name and secret are required");
      return;
    }

    setSaving(true);

    try {
      await createCredential({
        name: name(),
        provider: provider(),
        secret_value: secret(),
      });
      setName("");
      setSecret("");
      await refetch();
      notifyCredentialsChanged();
      showNotice("Credential saved");
    } catch (err) {
      showError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: string) {
    if (!window.confirm("Delete this credential?")) return;

    try {
      await deleteCredential(id);
      await refetch();
      notifyCredentialsChanged();
      showNotice("Credential deleted");
    } catch (err) {
      showError(err instanceof Error ? err.message : "Delete failed");
    }
  }

  return (
    <div class="credentials-panel">
      <div class="credentials-header">
        <div>
          <div class="breadcrumb">Kaiju8 / Credentials</div>
          <h2>API Credentials</h2>
        </div>
      </div>

      <div class="credentials-layout">
        <section class="credentials-form">
          <div class="panel-title">Add credential</div>
          <div class="config-field">
            <label class="config-label">Name</label>
            <input
              type="text"
              value={name()}
              placeholder="Gemini production"
              onInput={(e) => setName(e.currentTarget.value)}
            />
          </div>
          <div class="config-field">
            <label class="config-label">Provider</label>
            <select onChange={(e) => setProvider(e.currentTarget.value)}>
              <For each={PROVIDERS}>
                {(item) => (
                  <option value={item.value} selected={provider() === item.value}>
                    {item.label}
                  </option>
                )}
              </For>
            </select>
          </div>
          <div class="config-field">
            <label class="config-label">API key</label>
            <input
              type="password"
              value={secret()}
              placeholder="Stored on backend only"
              autocomplete="off"
              onInput={(e) => setSecret(e.currentTarget.value)}
            />
            <div class="config-hint">
              Nodes save only the credential id. The secret is not returned by the API.
            </div>
          </div>
          <button class="primary-button" onClick={handleCreate} disabled={saving()}>
            {saving() ? "Saving..." : "Save credential"}
          </button>
        </section>

        <section class="credentials-list">
          <div class="panel-title">Saved credentials</div>
          <Show
            when={(credentials() ?? []).length > 0}
            fallback={
              <div class="block-io-empty">
                <strong>No credentials</strong>
                <span>Add a key once, then select it in AI and tool nodes.</span>
              </div>
            }
          >
            <For each={credentials() ?? []}>
              {(credential) => (
                <div class="credential-row">
                  <div>
                    <strong>{credential.name}</strong>
                    <div class="subtle">
                      {credential.provider} / {credential.secret_hint}
                    </div>
                  </div>
                  <button
                    class="secondary-button"
                    onClick={() => handleDelete(credential.id)}
                  >
                    Delete
                  </button>
                </div>
              )}
            </For>
          </Show>
        </section>
      </div>

      <Show when={notice()}>
        <div class="toast success">{notice()}</div>
      </Show>
      <Show when={error()}>
        <div class="toast error">{error()}</div>
      </Show>
    </div>
  );
}
