import { apiRequest } from "../../shared/api-client";
import type { Execution, ExecutionStep } from "../../shared/types";

export function listExecutions(workflowId: string): Promise<Execution[]> {
  return apiRequest<Execution[]>(`/executions?workflow_id=${encodeURIComponent(workflowId)}`);
}

export function getExecution(id: string): Promise<Execution> {
  return apiRequest<Execution>(`/executions/${id}`);
}

export function listExecutionSteps(id: string): Promise<ExecutionStep[]> {
  return apiRequest<ExecutionStep[]>(`/executions/${id}/steps`);
}
