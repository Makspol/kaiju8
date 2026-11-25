import { apiRequest } from "../../shared/api-client";
import type { Credential } from "../../shared/types";

export interface CreateCredentialInput {
  name: string;
  provider: string;
  secret_value: string;
}

export interface UpdateCredentialInput {
  name?: string;
  provider?: string;
  secret_value?: string;
}

export function listCredentials(): Promise<Credential[]> {
  return apiRequest<Credential[]>("/credentials");
}

export function createCredential(
  payload: CreateCredentialInput,
): Promise<Credential> {
  return apiRequest<Credential>("/credentials", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateCredential(
  id: string,
  payload: UpdateCredentialInput,
): Promise<Credential> {
  return apiRequest<Credential>(`/credentials/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteCredential(id: string): Promise<{ deleted: boolean }> {
  return apiRequest<{ deleted: boolean }>(`/credentials/${id}`, {
    method: "DELETE",
  });
}
