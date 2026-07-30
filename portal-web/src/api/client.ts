// Thin fetch wrapper. Always sends the session cookie (credentials: include)
// so the HttpOnly portal_session cookie authenticates requests.
const BASE = import.meta.env.VITE_API_BASE ?? "";

export function api(path: string, options: RequestInit = {}): Promise<Response> {
  return fetch(`${BASE}${path}`, { credentials: "include", ...options });
}
