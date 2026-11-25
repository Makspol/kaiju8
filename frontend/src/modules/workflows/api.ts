import { apiRequest } from "../../shared/api-client";
import type {
  Execution,
  InputFieldsResult,
  Workflow,
  WorkflowGraph,
  WorkflowTemplate,
  WorkflowRunResult,
} from "../../shared/types";

export function listWorkflows(): Promise<Workflow[]> {
  return apiRequest<Workflow[]>("/workflows");
}

export function getWorkflow(id: string): Promise<Workflow> {
  return apiRequest<Workflow>(`/workflows/${id}`);
}

export function createWorkflow(
  name: string,
  graph?: WorkflowGraph,
): Promise<Workflow> {
  return apiRequest<Workflow>("/workflows", {
    method: "POST",
    body: JSON.stringify({ name, graph }),
  });
}

export function listWorkflowTemplates(): Promise<WorkflowTemplate[]> {
  return apiRequest<WorkflowTemplate[]>("/workflow-templates");
}

export function updateWorkflow(
  id: string,
  patch: { name?: string; graph?: WorkflowGraph },
): Promise<Workflow> {
  return apiRequest<Workflow>(`/workflows/${id}`, {
    method: "PATCH",
    body: JSON.stringify(patch),
  });
}

export function deleteWorkflow(id: string): Promise<{ deleted: boolean }> {
  return apiRequest<{ deleted: boolean }>(`/workflows/${id}`, {
    method: "DELETE",
  });
}

export function validateWorkflow(
  id: string,
): Promise<{ valid: boolean; errors: string[] }> {
  return apiRequest(`/workflows/${id}/validate`, { method: "POST" });
}

export function runWorkflow(
  id: string,
  input: Record<string, unknown> = {},
): Promise<WorkflowRunResult> {
  return apiRequest<Execution>(`/workflows/${id}/run`, {
    method: "POST",
    body: JSON.stringify({ input }),
  }).then((execution) => ({
    execution_id: execution.id,
    status: execution.status,
    output: execution.output ?? execution.result ?? {},
    error: execution.error ?? null,
    execution,
  }));
}

export function analyzeNodeInputFields(
  graph: WorkflowGraph,
  nodeId: string,
): Promise<InputFieldsResult> {
  return apiRequest<InputFieldsResult>("/workflows/input-fields", {
    method: "POST",
    body: JSON.stringify({
      graph,
      node_id: nodeId,
    }),
  });
}
