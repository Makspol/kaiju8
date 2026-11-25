import { apiRequest } from "../../shared/api-client";
import type { NodeTypeMetadata } from "../../shared/types";
import { defaultNodeTypes, mergeDefaultNodeTypes } from "./defaults";

export function listNodeTypes(): Promise<NodeTypeMetadata[]> {
  return apiRequest<NodeTypeMetadata[]>("/node-types")
    .then(mergeDefaultNodeTypes)
    .catch(() => defaultNodeTypes());
}
