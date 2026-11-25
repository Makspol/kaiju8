import type { NodeTypeMetadata } from "../../shared/types";

const REMOVED_NODE_TYPES = new Set([
  "transform.set_fields",
  "logic.condition",
]);

const DEFAULT_AI_NODES: NodeTypeMetadata[] = [
  {
    type: "chat.trigger",
    category: "trigger",
    label: "Chat Trigger",
    description: "Starts workflow when a chat message is sent.",
    config_schema: {
      type: "object",
      properties: {
        sample_message: { type: "string", default: "Hello" },
        test_payload: {
          type: "object",
          default: { message: "Hello" },
        },
      },
    },
    ports: { input: false, output: true },
  },
  {
    type: "schedule.trigger",
    category: "trigger",
    label: "Schedule Trigger",
    description: "Starts workflow from a planned interval or cron schedule.",
    config_schema: {
      type: "object",
      properties: {
        mode: { type: "string", enum: ["cron", "interval"], default: "interval" },
        interval_seconds: { type: "integer", default: 3600 },
        cron: { type: "string", default: "0 9 * * *" },
        timezone: { type: "string", default: "UTC" },
        test_payload: { type: "object", default: {} },
      },
    },
    ports: { input: false, output: true },
  },
  {
    type: "ai.agent",
    category: "ai",
    label: "AI Agent",
    description: "Runs a model with memory, knowledge, and tools such as HTTP requests.",
    config_schema: {
      module_port_layout: {
        top: ["knowledge"],
        bottom: ["model", "memory", "tools"],
      },
      properties: {
        model: {
          properties: {
            budget: { type: "number" },
            max_llm_calls: { type: "integer" },
            max_tokens: { type: "integer" },
          },
        },
      },
      module_ports: [
        {
          id: "knowledge",
          position: "top",
          label: "Knowledge",
          description: "Files and facts the AI Agent can use without user input.",
          required: false,
          multiple: true,
          allowed_module_types: ["ai.knowledge.file"],
        },
        {
          id: "model",
          position: "bottom",
          label: "Model",
          description: "Model provider used by the AI Agent.",
          required: true,
          multiple: false,
          allowed_module_types: ["ai.model.claude", "ai.model.gemini"],
        },
        {
          id: "memory",
          position: "bottom",
          label: "Memory",
          description: "Conversation history available to the AI Agent.",
          required: false,
          multiple: false,
          allowed_module_types: ["ai.memory.basic", "ai.memory.file"],
        },
        {
          id: "tools",
          position: "bottom",
          label: "Tools",
          description: "External tools the AI Agent can call.",
          required: false,
          multiple: true,
          allowed_module_types: [
            "ai.tool.http_request",
            "ai.tool.external_api",
            "ai.tool.web_search",
          ],
        },
      ],
    },
    ports: { input: true, output: true },
  },
  {
    type: "transform.edit_fields",
    category: "transform",
    label: "Data Editor",
    description: "Adds, updates, or removes fields in workflow data.",
    config_schema: {
      type: "object",
      required: ["operations"],
      properties: {
        operations: {
          type: "array",
          default: [
            {
              operation: "set",
              path: "review.approved",
              value: false,
            },
          ],
        },
      },
    },
    ports: { input: true, output: true },
  },
  {
    type: "logic.if",
    category: "logic",
    label: "IF",
    description: "Routes workflow data to true or false based on one condition.",
    config_schema: {
      type: "object",
      required: ["field", "operator"],
      properties: {
        field: { type: "string" },
        operator: {
          type: "string",
          enum: ["equals", "not_equals", "is_empty", "is_not_empty", "exists", "not_exists"],
          default: "equals",
        },
        value: {},
      },
    },
    ports: { input: true, output: true },
  },
  {
    type: "logic.merge",
    category: "logic",
    label: "Merge",
    description: "Passes the active branch data forward.",
    config_schema: {
      type: "object",
      properties: {
        strategy: { type: "string", default: "pass_through" },
      },
    },
    ports: { input: true, output: true },
  },
];

export function mergeDefaultNodeTypes(remoteNodes: NodeTypeMetadata[]): NodeTypeMetadata[] {
  const activeRemoteNodes = remoteNodes.filter((node) => !REMOVED_NODE_TYPES.has(node.type));
  const existingTypes = new Set(activeRemoteNodes.map((node) => node.type));
  const missingDefaults = DEFAULT_AI_NODES.filter((node) => !existingTypes.has(node.type));

  return [...activeRemoteNodes, ...missingDefaults];
}

export function defaultNodeTypes(): NodeTypeMetadata[] {
  return DEFAULT_AI_NODES.filter((node) => !REMOVED_NODE_TYPES.has(node.type));
}
