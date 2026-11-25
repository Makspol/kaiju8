import { apiRequest } from "../../shared/api-client";
import type { AgentModuleMetadata } from "../../shared/types";
import { defaultAgentModuleTypes, mergeDefaultAgentModuleTypes } from "./defaults";

export function listAgentModuleTypes(port?: string): Promise<AgentModuleMetadata[]> {
  const url = port
    ? `/node-types/ai-agent/modules?port=${encodeURIComponent(port)}`
    : `/node-types/ai-agent/modules`;
  return apiRequest<AgentModuleMetadata[]>(url)
    .then((modules) => mergeDefaultAgentModuleTypes(modules, port))
    .catch(() => defaultAgentModuleTypes(port));
}
