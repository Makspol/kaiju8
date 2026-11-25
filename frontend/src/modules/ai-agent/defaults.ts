import type { AgentModuleMetadata } from "../../shared/types";

export const DEFAULT_AGENT_MODULES: AgentModuleMetadata[] = [
  {
    type: "ai.model.claude",
    category: "ai_agent_module",
    port: "model",
    label: "Claude Model",
    description: "Connects a Claude model to an AI Agent.",
    config_schema: {
      type: "object",
      properties: {
        provider: { type: "string", const: "claude", default: "claude" },
        credential_id: { type: "string" },
        model_name: { type: "string" },
      },
    },
    attachable_to: { node_type: "ai.agent", port: "model", position: "bottom" },
    ports: { input: false, output: false },
  },
  {
    type: "ai.model.gemini",
    category: "ai_agent_module",
    port: "model",
    label: "Gemini Model",
    description: "Connects a Gemini model to an AI Agent.",
    config_schema: {
      type: "object",
      properties: {
        provider: { type: "string", const: "gemini", default: "gemini" },
        credential_id: { type: "string" },
        model_name: { type: "string" },
      },
    },
    attachable_to: { node_type: "ai.agent", port: "model", position: "bottom" },
    ports: { input: false, output: false },
  },
  {
    type: "ai.memory.basic",
    category: "ai_agent_module",
    port: "memory",
    label: "Basic Memory",
    description: "Stores conversation history used by the AI Agent.",
    config_schema: {
      type: "object",
      properties: {
        enabled: { type: "boolean", default: true },
        history: { type: "array", default: [] },
      },
    },
    attachable_to: { node_type: "ai.agent", port: "memory", position: "bottom" },
    ports: { input: false, output: false },
  },
  {
    type: "ai.memory.file",
    category: "ai_agent_module",
    port: "memory",
    label: "Memory File",
    description: "Adds file-based conversation memory for an AI Agent.",
    config_schema: {
      type: "object",
      properties: {
        name: { type: "string" },
        content: { type: "string" },
        content_type: { type: "string" },
        reference: { type: "string" },
      },
    },
    attachable_to: { node_type: "ai.agent", port: "memory", position: "bottom" },
    ports: { input: false, output: false },
  },
  {
    type: "ai.tool.http_request",
    category: "ai_agent_module",
    port: "tools",
    label: "HTTP Request Tool",
    description: "Allows an AI Agent to call an HTTP endpoint.",
    config_schema: {
      type: "object",
      properties: {
        method: { type: "string", default: "GET" },
        url: { type: "string" },
        headers: { type: "object" },
        body: {},
        credential_id: { type: "string" },
        api_key_header: { type: "string" },
      },
    },
    attachable_to: { node_type: "ai.agent", port: "tools", position: "bottom" },
    ports: { input: false, output: false },
  },
  {
    type: "ai.tool.external_api",
    category: "ai_agent_module",
    port: "tools",
    label: "External API",
    description: "Allows an AI Agent to call an external API endpoint.",
    config_schema: {
      type: "object",
      properties: {
        method: { type: "string", default: "GET" },
        url: { type: "string" },
        headers: { type: "object" },
        body: {},
        live: { type: "boolean", default: false },
      },
    },
    attachable_to: { node_type: "ai.agent", port: "tools", position: "bottom" },
    ports: { input: false, output: false },
  },
  {
    type: "ai.tool.web_search",
    category: "ai_agent_module",
    port: "tools",
    label: "Internet Search",
    description: "Allows an AI Agent to search the internet through a configured search provider.",
    config_schema: {
      type: "object",
      properties: {
        provider: { type: "string", enum: ["brave", "tavily", "custom"], default: "brave" },
        query: { type: "string" },
        max_results: { type: "integer", default: 5 },
        credential_id: { type: "string" },
        endpoint: { type: "string" },
        query_param: { type: "string", default: "q" },
        max_results_param: { type: "string", default: "count" },
        api_key_header: { type: "string" },
        live: { type: "boolean", default: false },
      },
    },
    attachable_to: { node_type: "ai.agent", port: "tools", position: "bottom" },
    ports: { input: false, output: false },
  },
  {
    type: "ai.knowledge.file",
    category: "ai_agent_module",
    port: "knowledge",
    label: "Knowledge File",
    description: "Adds file-based facts for an AI Agent to use.",
    config_schema: {
      type: "object",
      properties: {
        name: { type: "string" },
        content: { type: "string" },
        content_type: { type: "string" },
        reference: { type: "string" },
      },
    },
    attachable_to: { node_type: "ai.agent", port: "knowledge", position: "top" },
    ports: { input: false, output: false },
  },
];

export function defaultAgentModuleTypes(port?: string): AgentModuleMetadata[] {
  if (!port) return [...DEFAULT_AGENT_MODULES];

  return DEFAULT_AGENT_MODULES.filter((module) => module.port === port);
}

export function mergeDefaultAgentModuleTypes(
  remoteModules: AgentModuleMetadata[],
  port?: string,
): AgentModuleMetadata[] {
  const existingTypes = new Set(remoteModules.map((module) => module.type));
  const missingDefaults = defaultAgentModuleTypes(port).filter(
    (module) => !existingTypes.has(module.type),
  );

  return [...remoteModules, ...missingDefaults];
}
