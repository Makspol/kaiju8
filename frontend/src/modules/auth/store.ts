import { createSignal } from "solid-js";
import { setToken, getToken } from "../../shared/api-client";
import type { User } from "../../shared/types";
import { getMe } from "./api";

const [user, setUser] = createSignal<User | null>(null);
const [isLoading, setIsLoading] = createSignal(!!getToken());

export { user, isLoading };

export function isAuthenticated(): boolean {
  return user() !== null;
}

export async function hydrateUser(): Promise<void> {
  if (!getToken()) return;
  setIsLoading(true);
  try {
    const me = await getMe();
    setUser(me);
  } catch {
    setToken(null);
  } finally {
    setIsLoading(false);
  }
}

export function storeLogin(token: string, userData: User): void {
  setToken(token);
  setUser(userData);
}

export function logout(): void {
  setToken(null);
  setUser(null);
}
