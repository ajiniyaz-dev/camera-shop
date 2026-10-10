export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export function readCsrfCookie(): string {
  if (typeof document === "undefined") {
    return "";
  }
  const parts = document.cookie.split("; ");
  for (const part of parts) {
    if (part.startsWith("hikvision_csrf=")) {
      return decodeURIComponent(part.slice("hikvision_csrf=".length));
    }
  }
  return "";
}

export async function adminFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers);
  const method = (init.method ?? "GET").toUpperCase();
  if (method !== "GET" && method !== "HEAD") {
    headers.set("X-CSRF-Token", readCsrfCookie());
  }
  const response = await fetch(path, { ...init, method, headers, credentials: "include" });
  if (response.status === 401 && !path.startsWith("/api/auth/login")) {
    window.location.assign("/admin/login");
  }
  return response;
}

export async function adminJson<T>(path: string, init: RequestInit = {}, body?: unknown): Promise<T> {
  const headers = new Headers(init.headers);
  if (body !== undefined) {
    headers.set("Content-Type", "application/json");
  }
  const response = await adminFetch(path, {
    ...init,
    headers,
    body: body === undefined ? init.body : JSON.stringify(body),
  });
  if (!response.ok) {
    throw new ApiError(response.status, await errorMessage(response));
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export async function errorMessage(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (typeof body.detail === "string") {
      return body.detail;
    }
    if (body.detail && typeof body.detail === "object" && "message" in body.detail) {
      const message = (body.detail as { message?: unknown }).message;
      if (typeof message === "string") {
        return message;
      }
    }
  } catch {
    return String(response.status);
  }
  return String(response.status);
}
