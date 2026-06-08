/** Shared API helpers for dashboard pages. */

export function apiPath(path: string): string {
  if (path.startsWith("http")) return path;
  return path.startsWith("/") ? path : `/${path}`;
}

export async function apiFetch(
  path: string,
  options: RequestInit = {},
  accessToken?: string | null
): Promise<Response> {
  const headers = new Headers(options.headers);
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }
  if (!headers.has("Content-Type") && options.body && typeof options.body === "string") {
    headers.set("Content-Type", "application/json");
  }
  return fetch(apiPath(path), { ...options, headers });
}
