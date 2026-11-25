import { apiRequest } from "../../shared/api-client";
import type { AuthResponse, User } from "../../shared/types";

export function login(email: string, password: string): Promise<AuthResponse> {
  return apiRequest<AuthResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function register(
  email: string,
  name: string,
  password: string,
): Promise<AuthResponse> {
  return apiRequest<AuthResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, name, password }),
  });
}

export function getMe(): Promise<User> {
  return apiRequest<User>("/auth/me");
}
