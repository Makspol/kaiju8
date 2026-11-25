import type { NodeTypeMetadata } from "../../shared/types";

export function isTrigger(nodeType: string): boolean {
  const parts = nodeType.split(".");
  return parts[parts.length - 1] === "trigger";
}

export function hasInputPort(meta: NodeTypeMetadata | undefined, fallbackType?: string): boolean {
  if (meta) return meta.ports.input;
  if (fallbackType) return !isTrigger(fallbackType);
  return true;
}
