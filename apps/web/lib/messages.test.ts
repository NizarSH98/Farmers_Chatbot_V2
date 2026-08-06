import { describe, expect, it } from "vitest";

import { mergePreservingClientState } from "./messages";
import type { Message } from "./types";

function makeMessage(overrides: Partial<Message> = {}): Message {
  return {
    id: "a1",
    role: "assistant",
    content: "Answer",
    status: "complete",
    citations: [],
    tools: [],
    attachments: [],
    created_at: "2026-08-05T00:00:00Z",
    ...overrides
  };
}

describe("mergePreservingClientState", () => {
  it("keeps quick replies from local state after a server refetch that omits them", () => {
    const previous = [
      makeMessage({
        id: "a1",
        content: "What symptoms are you seeing?",
        quickReplies: ["Yellowing leaves", "Leaf spots", "Wilting branches"]
      })
    ];
    const serverItems = [
      makeMessage({ id: "a1", content: "What symptoms are you seeing?" })
    ];

    const merged = mergePreservingClientState(serverItems, previous);

    expect(merged[0].quickReplies).toEqual([
      "Yellowing leaves",
      "Leaf spots",
      "Wilting branches"
    ]);
  });

  it("keeps feedback state from local state after a server refetch", () => {
    const previous = [
      makeMessage({ id: "a1", feedback: "helpful", feedbackPending: false })
    ];
    const serverItems = [makeMessage({ id: "a1" })];

    const merged = mergePreservingClientState(serverItems, previous);

    expect(merged[0].feedback).toBe("helpful");
    expect(merged[0].feedbackPending).toBe(false);
  });

  it("takes server content for fields that are not client-only", () => {
    const previous = [makeMessage({ id: "a1", content: "old content" })];
    const serverItems = [makeMessage({ id: "a1", content: "authoritative content" })];

    const merged = mergePreservingClientState(serverItems, previous);

    expect(merged[0].content).toBe("authoritative content");
  });

  it("leaves a brand-new server message (no local match) untouched", () => {
    const serverItems = [makeMessage({ id: "new-message" })];

    const merged = mergePreservingClientState(serverItems, []);

    expect(merged).toEqual(serverItems);
  });
});
