import type { StreamEvent, TurnPayload, TurnStatusResponse } from "./types";

const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000")
  .replace(/\/$/, "");

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export class IncompleteTurnError extends Error {
  turnId?: string;
  requestId: string;

  constructor(requestId: string, turnId?: string) {
    super("The response stream ended before the turn completed");
    this.name = "IncompleteTurnError";
    this.requestId = requestId;
    this.turnId = turnId;
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

export async function downloadPrivateFile(
  path: string,
  token: string,
  filename: string
): Promise<void> {
  const response = await fetch(API_URL + path, {
    headers: { Authorization: "Bearer " + token },
    cache: "no-store"
  });
  if (!response.ok) throw new ApiError(response.status, response.statusText);
  const url = URL.createObjectURL(await response.blob());
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

export async function getTurn(
  turnId: string,
  token: string
): Promise<TurnStatusResponse> {
  return apiFetch<TurnStatusResponse>(
    "/v1/turns/" + encodeURIComponent(turnId),
    token
  );
}

export async function* streamTurn(
  payload: TurnPayload,
  token: string,
  signal: AbortSignal
): AsyncGenerator<StreamEvent> {
  const requestId = crypto.randomUUID();
  const response = await fetch(API_URL + "/v1/turns", {
    method: "POST",
    headers: {
      Authorization: "Bearer " + token,
      "Content-Type": "application/json",
      "Idempotency-Key": requestId,
      "X-Request-ID": requestId
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
  let completed = false;
  let turnId: string | undefined;

  const parseBlock = (block: string): StreamEvent | null => {
    let event = "message";
    const dataLines: string[] = [];
    block.split(/\r?\n/).forEach((line) => {
      if (line.startsWith("event:")) {
        event = line.slice(6).trim();
      } else if (line.startsWith("data:")) {
        dataLines.push(line.slice(5).trim());
      }
    });
    if (!dataLines.length) return null;
    return {
      event,
      data: JSON.parse(dataLines.join("\n")) as Record<string, unknown>
    };
  };

  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
    let boundary = buffer.match(/\r?\n\r?\n/);
    while (boundary?.index !== undefined) {
      const block = buffer.slice(0, boundary.index);
      buffer = buffer.slice(boundary.index + boundary[0].length);
      const parsed = parseBlock(block);
      if (parsed) {
        if (typeof parsed.data.turn_id === "string") turnId = parsed.data.turn_id;
        if (parsed.event === "turn.completed") completed = true;
        yield parsed;
      }
      boundary = buffer.match(/\r?\n\r?\n/);
    }
    if (done) {
      const parsed = parseBlock(buffer);
      if (parsed) {
        if (typeof parsed.data.turn_id === "string") turnId = parsed.data.turn_id;
        if (parsed.event === "turn.completed") completed = true;
        yield parsed;
      }
      break;
    }
  }
  if (!completed) throw new IncompleteTurnError(requestId, turnId);
}
