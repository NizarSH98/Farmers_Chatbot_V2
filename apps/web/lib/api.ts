import type { StreamEvent, TurnPayload } from "./types";

const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000")
  .replace(/\/$/, "");

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export async function apiFetch<T>(
  path: string,
  token: string,
  init: RequestInit = {}
): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Authorization", "Bearer " + token);
  if (init.body && !(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(API_URL + path, {
    ...init,
    headers,
    cache: "no-store"
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const payload = await response.json();
      detail = payload.detail || detail;
    } catch {
      // Keep the HTTP status text when the body is not JSON.
    }
    throw new ApiError(response.status, detail);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export async function uploadImage(
  file: File,
  token: string
): Promise<{ id: string; preview_url?: string }> {
  const body = new FormData();
  body.set("image", file);
  return apiFetch("/v1/uploads/images", token, {
    method: "POST",
    body
  });
}

export async function* streamTurn(
  payload: TurnPayload,
  token: string,
  signal: AbortSignal
): AsyncGenerator<StreamEvent> {
  const response = await fetch(API_URL + "/v1/turns", {
    method: "POST",
    headers: {
      Authorization: "Bearer " + token,
      "Content-Type": "application/json",
      "X-Request-ID": crypto.randomUUID()
    },
    body: JSON.stringify(payload),
    cache: "no-store",
    signal
  });
  if (!response.ok) {
    let message = response.statusText;
    try {
      const error = await response.json();
      message = error.detail || message;
    } catch {
      // Use status text for non-JSON errors.
    }
    throw new ApiError(response.status, message);
  }
  if (!response.body) {
    throw new ApiError(502, "The response stream is unavailable");
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
    let boundary = buffer.indexOf("\n\n");
    while (boundary >= 0) {
      const block = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      let event = "message";
      const dataLines: string[] = [];
      block.split(/\r?\n/).forEach((line) => {
        if (line.startsWith("event:")) {
          event = line.slice(6).trim();
        } else if (line.startsWith("data:")) {
          dataLines.push(line.slice(5).trim());
        }
      });
      if (dataLines.length) {
        yield {
          event,
          data: JSON.parse(dataLines.join("\n")) as Record<string, unknown>
        };
      }
      boundary = buffer.indexOf("\n\n");
    }
    if (done) break;
  }
}
