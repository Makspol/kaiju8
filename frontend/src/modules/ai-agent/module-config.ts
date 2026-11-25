import type { WorkflowNode, AgentModule, AgentModuleMetadata } from "../../shared/types";

/** Ports that accept only one module at a time */
const SINGLE_MODULE_PORTS = new Set(["model", "memory"]);

export function getModules(node: WorkflowNode): AgentModule[] {
  return (node.config.modules as AgentModule[] | undefined) ?? [];
}

export function getModulesForPort(node: WorkflowNode, port: string): AgentModule[] {
  return getModules(node).filter((m) => m.port === port);
}

export function isPortFull(port: string, modules: AgentModule[]): boolean {
  if (!SINGLE_MODULE_PORTS.has(port)) return false;
  return modules.filter((m) => m.port === port).length >= 1;
}

export function addModule(node: WorkflowNode, meta: AgentModuleMetadata): WorkflowNode {
  const existing = getModules(node);
  const newModule: AgentModule = {
    id: `${meta.port}-${Math.random().toString(36).slice(2, 8)}`,
    type: meta.type,
    port: meta.port,
    config: defaultConfigForModule(meta.type),
  };
  return { ...node, config: { ...node.config, modules: [...existing, newModule] } };
}

export function removeModule(node: WorkflowNode, moduleId: string): WorkflowNode {
  return {
    ...node,
    config: {
      ...node.config,
      modules: getModules(node).filter((m) => m.id !== moduleId),
    },
  };
}

export function updateModuleConfig(
  node: WorkflowNode,
  moduleId: string,
  config: Record<string, unknown>,
): WorkflowNode {
  return {
    ...node,
    config: {
      ...node.config,
      modules: getModules(node).map((m) =>
        m.id === moduleId ? { ...m, config } : m,
      ),
    },
  };
}

function defaultConfigForModule(moduleType: string): Record<string, unknown> {
  if (moduleType === "ai.model.claude") {
    return { provider: "claude" };
  }

  if (moduleType === "ai.model.gemini") {
    return { provider: "gemini" };
  }

  if (moduleType === "ai.memory.basic") {
    return { enabled: true, history: [] };
  }

  if (moduleType === "ai.memory.file" || moduleType === "ai.knowledge.file") {
    return { name: "", content: "", content_type: "text/plain" };
  }

  if (moduleType === "ai.tool.http_request" || moduleType === "ai.tool.external_api") {
    return { method: "GET", url: "", live: false };
  }

  if (moduleType === "ai.tool.web_search") {
    return { provider: "brave", query: "", max_results: 5, live: false };
  }

  return {};
}
