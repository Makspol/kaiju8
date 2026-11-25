export interface User {
  id: string;
  email: string;
  name: string;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Credential {
  id: string;
  owner_user_id: string;
  name: string;
  provider: "anthropic" | "gemini" | "brave_search" | "tavily" | "custom" | string;
  secret_set: boolean;
  secret_hint: string;
  created_at: string;
  updated_at: string;
}

export interface WorkflowNode {
  id: string;
  type: string;
  config: Record<string, unknown>;
}

export interface WorkflowEdge {
  source: string;
  target: string;
  label?: string;
  branch?: string;
}

export interface WorkflowSettings {
  max_steps: number;
  timeout_seconds?: number;
  budget?: number;
  max_llm_calls?: number;
  max_tokens?: number;
  [key: string]: unknown;
}

export interface WorkflowGraph {
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  settings: WorkflowSettings;
}

export interface Workflow {
  id: string;
  name: string;
  graph: WorkflowGraph;
  owner_user_id: string;
  created_at: string;
  updated_at: string;
}

export interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  graph: WorkflowGraph;
}

export interface NodeTypeMetadata {
  type: string;
  category: string;
  label: string;
  description: string;
  config_schema: Record<string, unknown>;
  config_ui?: ConfigUiSchema;
  ports: { input: boolean; output: boolean };
}

export interface ConfigUiOption {
  value: string | number | boolean;
  label: string;
}

export interface ConfigUiVisibleWhen {
  field: string;
  equals?: unknown;
  in?: unknown[];
}

export interface ConfigUiField {
  key: string;
  label: string;
  widget:
    | "text"
    | "textarea"
    | "select"
    | "segmented_select"
    | "checkbox"
    | "number"
    | "integer"
    | "json"
    | "field_path"
    | "operator_select"
    | "operator_value"
    | string;
  section?: "basic" | "advanced";
  default?: unknown;
  placeholder?: string;
  help?: string;
  source?: string;
  visible_when?: ConfigUiVisibleWhen;
  options?: ConfigUiOption[];
}

export interface ConfigUiSchema {
  version: number;
  title?: string;
  description?: string;
  mode?: "form" | "custom" | string;
  component?: string;
  fields: ConfigUiField[];
}

export interface InferredInputField {
  path: string;
  type: string;
  source_node_id?: string;
  source?: string;
}

export interface InputFieldsResult {
  node_id: string;
  fields: InferredInputField[];
  warnings: string[];
}

export interface ExecutionStep {
  id: string;
  execution_id: string;
  node_id: string;
  node_type: string;
  input?: Record<string, unknown>;
  input_json: Record<string, unknown>;
  output?: Record<string, unknown>;
  output_json: Record<string, unknown>;
  status: "success" | "error";
  error?: string | null;
  error_message?: string | null;
  created_at: string;
}

export interface Execution {
  id: string;
  workflow_id: string;
  input?: Record<string, unknown>;
  input_json?: Record<string, unknown>;
  output?: Record<string, unknown>;
  result?: Record<string, unknown>;
  usage?: Record<string, unknown> | null;
  error?: string | null;
  status: "success" | "error" | "failed";
  created_at: string;
}

export interface WorkflowRunResult {
  execution_id: string;
  status: string;
  output: Record<string, unknown>;
  error: string | null;
  execution: Execution;
}

export type NodePosition = { x: number; y: number };

export interface CanvasNode extends WorkflowNode {
  _pos: NodePosition;
}

export interface AgentModuleMetadata {
  type: string;
  category: string;
  port: string;
  label: string;
  description: string;
  config_schema: Record<string, unknown>;
  attachable_to: {
    node_type: string;
    port: string;
    position: "top" | "bottom";
  };
  ports: { input: boolean; output: boolean };
}

export interface AgentModule {
  id: string;
  type: string;
  port: string;
  config: Record<string, unknown>;
}
