import { createSignal, Match, Show, Switch } from "solid-js";
import type { AgentModule } from "../../shared/types";
import { CredentialSelect } from "../credentials/CredentialSelect";

// ── Internal form prop type ───────────────────────────────────────────────

interface FormProps {
  config: Record<string, unknown>;
  onChange: (config: Record<string, unknown>) => void;
}

interface ModelFormProps extends FormProps {
  provider: "anthropic" | "gemini";
}

function str(config: Record<string, unknown>, key: string): string {
  return (config[key] as string) ?? "";
}

function patchStr(
  config: Record<string, unknown>,
  onChange: (c: Record<string, unknown>) => void,
  key: string,
  value: string,
) {
  onChange({ ...config, [key]: value || undefined });
}

function patchOptionalBoundedNumber(
  config: Record<string, unknown>,
  onChange: (c: Record<string, unknown>) => void,
  key: string,
  value: string,
  min: number,
) {
  if (!value.trim()) {
    onChange({ ...config, [key]: undefined });
    return;
  }

  const parsed = Number(value);
  onChange({
    ...config,
    [key]: Number.isFinite(parsed) && parsed >= min ? parsed : undefined,
  });
}

function patchOptionalBoundedInt(
  config: Record<string, unknown>,
  onChange: (c: Record<string, unknown>) => void,
  key: string,
  value: string,
  min: number,
) {
  if (!value.trim()) {
    onChange({ ...config, [key]: undefined });
    return;
  }

  const parsed = Number.parseInt(value, 10);
  onChange({
    ...config,
    [key]: Number.isFinite(parsed) && parsed >= min ? parsed : undefined,
  });
}

// ── ai.model.claude / ai.model.gemini ────────────────────────────────────

function ModelModuleConfig(props: ModelFormProps) {
  return (
    <>
      <CredentialSelect
        value={str(props.config, "credential_id")}
        providers={[props.provider]}
        onChange={(value) => patchStr(props.config, props.onChange, "credential_id", value ?? "")}
        hint="Create and manage API keys in the Credentials tab."
      />
      <div class="config-field">
        <label class="config-label">Model Name (optional)</label>
        <input
          name="model_name"
          type="text"
          value={str(props.config, "model_name")}
          placeholder="Uses provider default"
          onInput={(e) => patchStr(props.config, props.onChange, "model_name", e.currentTarget.value)}
        />
      </div>
      <div class="config-field">
        <label class="config-label">Budget limit</label>
        <input
          name="budget"
          type="number"
          min="0"
          step="0.01"
          value={props.config.budget === undefined ? "" : String(props.config.budget)}
          placeholder="No node limit"
          onInput={(e) => patchOptionalBoundedNumber(props.config, props.onChange, "budget", e.currentTarget.value, 0)}
        />
      </div>
      <div class="config-field">
        <label class="config-label">Max calls</label>
        <input
          name="max_llm_calls"
          type="number"
          min="0"
          step="1"
          value={props.config.max_llm_calls === undefined ? "" : String(props.config.max_llm_calls)}
          placeholder="No node limit"
          onInput={(e) => patchOptionalBoundedInt(props.config, props.onChange, "max_llm_calls", e.currentTarget.value, 0)}
        />
      </div>
      <div class="config-field">
        <label class="config-label">Max tokens</label>
        <input
          name="max_tokens"
          type="number"
          min="1"
          step="1"
          value={props.config.max_tokens === undefined ? "" : String(props.config.max_tokens)}
          placeholder="No node limit"
          onInput={(e) => patchOptionalBoundedInt(props.config, props.onChange, "max_tokens", e.currentTarget.value, 1)}
        />
        <div class="config-hint">These limits apply only to this model module.</div>
      </div>
    </>
  );
}

// ── ai.memory.basic ───────────────────────────────────────────────────────

function BasicMemoryConfig(props: FormProps) {
  const enabled = () => (props.config["enabled"] as boolean) ?? true;
  return (
    <div class="config-field">
      <label style={{ display: "flex", "align-items": "center", gap: "8px", "flex-direction": "row" }}>
        <input
          type="checkbox"
          checked={enabled()}
          style={{ width: "auto", "min-height": "unset" }}
          onChange={(e) =>
            props.onChange({ ...props.config, enabled: e.currentTarget.checked })
          }
        />
        <span class="config-label" style={{ margin: 0 }}>Enabled</span>
      </label>
    </div>
  );
}

// ── ai.memory.file / ai.knowledge.file ───────────────────────────────────

function FileModuleConfig(props: FormProps) {
  return (
    <>
      <div class="config-field">
        <label class="config-label">Name</label>
        <input
          name="name"
          type="text"
          value={str(props.config, "name")}
          placeholder="My file"
          onInput={(e) => patchStr(props.config, props.onChange, "name", e.currentTarget.value)}
        />
      </div>
      <div class="config-field">
        <label class="config-label">Content</label>
        <textarea
          name="content"
          rows={5}
          value={str(props.config, "content")}
          placeholder="Paste file content here…"
          onInput={(e) => patchStr(props.config, props.onChange, "content", e.currentTarget.value)}
          style={{ "font-size": "12px" }}
        />
      </div>
      <div class="config-field">
        <label class="config-label">Content Type (optional)</label>
        <input
          name="content_type"
          type="text"
          value={str(props.config, "content_type")}
          placeholder="text/plain"
          onInput={(e) => patchStr(props.config, props.onChange, "content_type", e.currentTarget.value)}
        />
      </div>
      <div class="config-field">
        <label class="config-label">Reference</label>
        <input
          name="reference"
          type="text"
          value={str(props.config, "reference")}
          placeholder="knowledge://id"
          onInput={(e) => patchStr(props.config, props.onChange, "reference", e.currentTarget.value)}
        />
        <div class="config-hint">
          Format: <code style={{ "font-size": "10px" }}>knowledge://&lt;id&gt;</code> — leave empty to
          use inline content above.
        </div>
      </div>
    </>
  );
}

// ── ai.tool.http_request / ai.tool.external_api ───────────────────────────

const HTTP_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"] as const;

function HttpRequestConfig(props: FormProps) {
  const method = () => (props.config["method"] as string) ?? "GET";
  const [headersErr, setHeadersErr] = createSignal("");

  const headersText = () => {
    const h = props.config["headers"];
    return h ? JSON.stringify(h, null, 2) : "";
  };

  const bodyText = () => {
    const b = props.config["body"];
    if (b === undefined || b === null) return "";
    return typeof b === "string" ? b : JSON.stringify(b, null, 2);
  };

  function onHeadersInput(text: string) {
    if (!text) {
      setHeadersErr("");
      props.onChange({ ...props.config, headers: undefined });
      return;
    }
    try {
      const parsed = JSON.parse(text) as Record<string, unknown>;
      setHeadersErr("");
      props.onChange({ ...props.config, headers: parsed });
    } catch {
      setHeadersErr("Invalid JSON");
    }
  }

  return (
    <>
      <div class="config-field">
        <label class="config-label">Method</label>
        <select onChange={(e) => props.onChange({ ...props.config, method: e.currentTarget.value })}>
          {HTTP_METHODS.map((m) => (
            <option value={m} selected={method() === m}>{m}</option>
          ))}
        </select>
      </div>
      <div class="config-field">
        <label class="config-label">URL</label>
        <input
          name="url"
          type="url"
          value={str(props.config, "url")}
          placeholder="https://api.example.com/endpoint"
          onInput={(e) => patchStr(props.config, props.onChange, "url", e.currentTarget.value)}
        />
      </div>
      <div class="config-field">
        <label class="config-label">Headers (JSON)</label>
        <Show when={headersErr()}>
          <div class="config-hint" style={{ color: "#b42318" }}>{headersErr()}</div>
        </Show>
        <textarea
          rows={3}
          value={headersText()}
          placeholder={'{"Content-Type": "application/json"}'}
          onInput={(e) => onHeadersInput(e.currentTarget.value)}
          style={{ "font-family": "monospace", "font-size": "11px" }}
        />
      </div>
      <CredentialSelect
        value={str(props.config, "credential_id")}
        providers={["custom"]}
        onChange={(value) => patchStr(props.config, props.onChange, "credential_id", value ?? "")}
        hint="Optional. Used with the API key header below."
      />
      <div class="config-field">
        <label class="config-label">API Key Header</label>
        <input
          name="api_key_header"
          type="text"
          value={str(props.config, "api_key_header")}
          placeholder="Authorization or X-Api-Key"
          onInput={(e) => patchStr(props.config, props.onChange, "api_key_header", e.currentTarget.value)}
        />
      </div>
      <div class="config-field">
        <label class="config-label">Body</label>
        <textarea
          name="body"
          rows={3}
          value={bodyText()}
          placeholder={'{"key": "value"}'}
          onInput={(e) => patchStr(props.config, props.onChange, "body", e.currentTarget.value)}
          style={{ "font-family": "monospace", "font-size": "11px" }}
        />
      </div>
      <div class="config-field">
        <label style={{ display: "flex", "align-items": "center", gap: "8px", "flex-direction": "row" }}>
          <input
            type="checkbox"
            checked={(props.config["live"] as boolean | undefined) ?? false}
            style={{ width: "auto", "min-height": "unset" }}
            onChange={(e) => props.onChange({ ...props.config, live: e.currentTarget.checked })}
          />
          <span class="config-label" style={{ margin: 0 }}>Live request</span>
        </label>
        <div class="config-hint">Leave off for dry-run testing.</div>
      </div>
    </>
  );
}

// ── ai.tool.web_search ───────────────────────────────────────────────────

function WebSearchConfig(props: FormProps) {
  const provider = () => (props.config["provider"] as string | undefined) ?? "brave";
  const credentialProviders = () => {
    if (provider() === "brave") return ["brave_search"];
    if (provider() === "tavily") return ["tavily"];
    return ["custom"];
  };

  return (
    <>
      <div class="config-field">
        <label class="config-label">Provider</label>
        <select onChange={(e) => props.onChange({ ...props.config, provider: e.currentTarget.value })}>
          {["brave", "tavily", "custom"].map((item) => (
            <option value={item} selected={provider() === item}>{item}</option>
          ))}
        </select>
      </div>
      <div class="config-field">
        <label class="config-label">Query</label>
        <input
          name="query"
          type="text"
          value={str(props.config, "query")}
          placeholder="{{ question }}"
          onInput={(e) => patchStr(props.config, props.onChange, "query", e.currentTarget.value)}
        />
      </div>
      <div class="config-field">
        <label class="config-label">Max results</label>
        <input
          name="max_results"
          type="number"
          min="1"
          step="1"
          value={props.config.max_results === undefined ? "5" : String(props.config.max_results)}
          onInput={(e) => patchOptionalBoundedInt(props.config, props.onChange, "max_results", e.currentTarget.value, 1)}
        />
      </div>
      <CredentialSelect
        value={str(props.config, "credential_id")}
        providers={credentialProviders()}
        onChange={(value) => patchStr(props.config, props.onChange, "credential_id", value ?? "")}
        hint="Create and manage search/API keys in the Credentials tab."
      />
      <Show when={provider() === "custom"}>
        <div class="config-field">
          <label class="config-label">Endpoint</label>
          <input
            name="endpoint"
            type="url"
            value={str(props.config, "endpoint")}
            placeholder="https://search.example.com/search"
            onInput={(e) => patchStr(props.config, props.onChange, "endpoint", e.currentTarget.value)}
          />
        </div>
        <div class="config-field">
          <label class="config-label">API Key Header</label>
          <input
            name="api_key_header"
            type="text"
            value={str(props.config, "api_key_header")}
            placeholder="X-API-Key"
            onInput={(e) => patchStr(props.config, props.onChange, "api_key_header", e.currentTarget.value)}
          />
        </div>
      </Show>
      <div class="config-field">
        <label style={{ display: "flex", "align-items": "center", gap: "8px", "flex-direction": "row" }}>
          <input
            type="checkbox"
            checked={(props.config["live"] as boolean | undefined) ?? false}
            style={{ width: "auto", "min-height": "unset" }}
            onChange={(e) => props.onChange({ ...props.config, live: e.currentTarget.checked })}
          />
          <span class="config-label" style={{ margin: 0 }}>Live search</span>
        </label>
        <div class="config-hint">Leave off for dry-run testing.</div>
      </div>
    </>
  );
}

// ── JSON fallback for unknown types ───────────────────────────────────────

function JsonFallback(props: FormProps) {
  return (
    <textarea
      rows={4}
      value={JSON.stringify(props.config, null, 2)}
      onInput={(e) => {
        try {
          props.onChange(JSON.parse(e.currentTarget.value) as Record<string, unknown>);
        } catch { /* keep typing */ }
      }}
      style={{ "font-family": "monospace", "font-size": "11px" }}
      placeholder="{}"
    />
  );
}

// ── Dispatcher ────────────────────────────────────────────────────────────

const MODEL_TYPES = new Set(["ai.model.claude", "ai.model.gemini"]);
const FILE_TYPES = new Set(["ai.memory.file", "ai.knowledge.file"]);

interface Props {
  module: AgentModule;
  onUpdateConfig: (config: Record<string, unknown>) => void;
}

export function AgentModuleConfigForm(props: Props) {
  const config = () => props.module.config;
  const onChange = (c: Record<string, unknown>) => props.onUpdateConfig(c);

  return (
    <Switch fallback={<JsonFallback config={config()} onChange={onChange} />}>
      <Match when={MODEL_TYPES.has(props.module.type)}>
        <ModelModuleConfig
          config={config()}
          provider={props.module.type === "ai.model.gemini" ? "gemini" : "anthropic"}
          onChange={onChange}
        />
      </Match>
      <Match when={props.module.type === "ai.memory.basic"}>
        <BasicMemoryConfig config={config()} onChange={onChange} />
      </Match>
      <Match when={FILE_TYPES.has(props.module.type)}>
        <FileModuleConfig config={config()} onChange={onChange} />
      </Match>
      <Match when={props.module.type === "ai.tool.http_request" || props.module.type === "ai.tool.external_api"}>
        <HttpRequestConfig config={config()} onChange={onChange} />
      </Match>
      <Match when={props.module.type === "ai.tool.web_search"}>
        <WebSearchConfig config={config()} onChange={onChange} />
      </Match>
    </Switch>
  );
}
