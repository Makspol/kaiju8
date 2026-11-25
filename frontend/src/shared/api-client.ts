let authToken: string | null = localStorage.getItem("kaiju8_token");

export function setToken(token: string | null) {
  authToken = token;
  if (token) {
    localStorage.setItem("kaiju8_token", token);
  } else {
    localStorage.removeItem("kaiju8_token");
  }
}

export function getToken(): string | null {
  return authToken;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

export async function apiRequest<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (authToken) {
    headers["Authorization"] = `Bearer ${authToken}`;
  }

  const response = await fetch(path, {
    ...init,
    headers: { ...headers, ...(init?.headers as Record<string, string>) },
  });

  const text = await response.text();
  const data = text ? JSON.parse(text) : null;

  if (!response.ok) {
    const message =
      data?.detail ??
      data?.message ??
      `Request failed with status ${response.status}`;
    throw new ApiError(response.status, message);
  }

  return data as T;
}
