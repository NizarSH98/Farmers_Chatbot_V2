import { afterEach, describe, expect, it, vi } from "vitest";

import { getTurn, IncompleteTurnError, streamTurn } from "./api";

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

  it("accepts CRLF frames and a terminal event without a trailing separator", async () => {
    const stream = [
      "event: status\r\n",
      "data: " + JSON.stringify({ stage: "generation", turn_id: "t1" }) + "\r\n\r\n",
      "event: turn.completed\r\n",
      "data: " + JSON.stringify({ message_id: "m1", turn_id: "t1" })
    ].join("");
    vi.stubGlobal("fetch", vi.fn(async () => new Response(stream, { status: 200 })));

    const received = [];
    for await (const event of streamTurn({
      conversation_id: "c1",
      text: "question",
      mode: "standard",
      clarification_style: "auto",
      attachment_ids: []
    }, "token", new AbortController().signal)) {
      received.push(event.event);
    }

    expect(received).toEqual(["status", "turn.completed"]);
  });

  it("reports a recoverable error when the stream ends before a terminal event", async () => {
    const stream = [
      "event: status\n",
      "data: " + JSON.stringify({ stage: "generation", turn_id: "t-recover" }) + "\n\n"
    ].join("");
    vi.stubGlobal("fetch", vi.fn(async () => new Response(stream, { status: 200 })));

    const consume = async () => {
      for await (const _event of streamTurn({
        conversation_id: "c1",
        text: "question",
        mode: "standard",
        clarification_style: "auto",
        attachment_ids: []
      }, "token", new AbortController().signal)) {
        // Consume the stream to reach EOF.
        void _event;
      }
    };

    await expect(consume()).rejects.toMatchObject({
      name: "IncompleteTurnError",
      turnId: "t-recover"
    } satisfies Partial<IncompleteTurnError>);
  });

  it("fetches persisted turn state for stream recovery", async () => {
    const fetchMock = vi.fn(async (_input: RequestInfo | URL) => {
      void _input;
      return new Response(JSON.stringify({
        turn_id: "turn/1",
        request_id: "request-1",
        status: "complete",
        terminal: true,
        message: null,
        error: null
      }), { status: 200, headers: { "Content-Type": "application/json" } });
    });
    vi.stubGlobal("fetch", fetchMock);

    const turn = await getTurn("turn/1", "token");

    expect(turn.terminal).toBe(true);
    expect(String(fetchMock.mock.calls[0][0]).endsWith("/v1/turns/turn%2F1")).toBe(true);
  });
});
