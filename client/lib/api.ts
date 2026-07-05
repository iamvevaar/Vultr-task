/**
 * The single gateway to the backend API.
 *
 * apiFetch():
 *   - prefixes the base URL (NEXT_PUBLIC_API_BASE_URL — the local/prod switch),
 *   - sends credentials so the browser attaches our httpOnly auth cookie,
 *   - unwraps the backend's { error: { code, message } } envelope into a typed
 *     ApiError the UI can catch.
 *
 * Note: there is NO token handling here. The JWT lives in an httpOnly cookie the
 * browser manages automatically — JavaScript never sees it.
 */

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";

/** Mirrors the backend's error envelope so the UI can react to code/status. */
export class ApiError extends Error {
  status: number;
  code: string;
  details?: unknown;

  constructor(status: number, code: string, message: string, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

/**
 * Turn any thrown error into a precise, user-facing message.
 * - Validation (422): surface the first field-level detail (e.g. the password rule).
 * - Other ApiErrors: use the backend's message (login stays generic on purpose).
 * - Network/unexpected: a friendly fallback (never a raw "Failed to fetch").
 */
export function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.code === "VALIDATION_ERROR" && Array.isArray(error.details) && error.details.length > 0) {
      const first = error.details[0] as { loc?: unknown[]; msg?: string };
      const field = Array.isArray(first.loc) ? String(first.loc[first.loc.length - 1]) : "";
      let msg = first.msg ?? "Invalid input";
      // Soften Pydantic's phrasing a little.
      msg = msg
        .replace(/^String should have/i, "Must have")
        .replace(/^value is not a valid email address.*/i, "Enter a valid email address");
      return field ? `${field[0].toUpperCase()}${field.slice(1)}: ${msg}` : msg;
    }
    return error.message;
  }
  return "Something went wrong. Please try again.";
}

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");

  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: "include", // send/receive the httpOnly auth cookie
    headers,
  });

  // 204 has no body; otherwise parse JSON (null if empty/non-JSON).
  const data = res.status === 204 ? null : await res.json().catch(() => null);

  if (!res.ok) {
    const err = (data as { error?: { code: string; message: string; details?: unknown } } | null)?.error;
    throw new ApiError(res.status, err?.code ?? "UNKNOWN", err?.message ?? res.statusText, err?.details);
  }

  return data as T;
}
