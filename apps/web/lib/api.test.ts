import { afterEach, describe, expect, it, vi } from "vitest";

import { streamTurn } from "./api";

describe("streamTurn", () => {
  afterEach(() => vi.restoreAllMocks());

  it("parses named SSE events and their JSON payloads", async () => {
    const stream = [
      "event: status\n",
      "data: " + JSON.stringify({ stage: "generation" }) + "\n\n",
      "event: content.delta\n",
      "data: " + JSON.stringify({ text: "مرحبا" }) + "\n\n",
      "event: turn.completed\n",
      "data: " + JSON.stringify({ message_id: "m1" }) + "\n\n"
    ].join("");
    vi.stubGlobal("fetch", vi.fn(async () => new Response(stream, {
      headers: { "Content-Type": "text/event-stream" },
      status: 200
    })));
    const controller = new AbortController();
    const received = [];
    for await (const event of streamTurn({
      conversation_id: "c1",
      text: "سؤال",
      mode: "standard",
      clarification_style: "auto",
      attachment_ids: []
    }, "token", controller.signal)) {
      received.push(event);
    }
    expect(received).toEqual([
      { event: "status", data: { stage: "generation" } },
      { event: "content.delta", data: { text: "مرحبا" } },
      { event: "turn.completed", data: { message_id: "m1" } }
    ]);
  });
});
