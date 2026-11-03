import { describe, expect, it } from "vitest";

import { speakableText } from "@/lib/speech";
import type { Message } from "@/lib/types";

import { convertMessage, withCitationMarkers } from "./convert";

const base: Message = {
  id: "m1",
  role: "assistant",
  content: "",
  status: "complete",
  citations: [],
  tools: [],
  attachments: [],
  created_at: "2026-11-03T10:00:00Z"
};

type Part = { type: string; name?: string; data?: Record<string, unknown>; text?: string };
const parts = (message: Message) => convertMessage(message).content as unknown as Part[];
const named = (message: Message, name: string) => parts(message).find((part) => part.name === name);

describe("convertMessage", () => {
  it("shows the live pipeline stage while nothing is visible yet", () => {
    const converted = convertMessage({ ...base, pending: true, stage: "verification" });
    expect(converted.status).toEqual({ type: "running" });
    expect(named({ ...base, pending: true, stage: "verification" }, "raise-progress")?.data).toEqual({
      stage: "verification"
    });
  });

  it("paces the reveal and keeps the turn running until it finishes", () => {
    const message = { ...base, content: "Prune after harvest.", revealChars: 5 };
    expect(convertMessage(message).status).toEqual({ type: "running" });
    expect(parts(message).find((part) => part.type === "text")?.text).toBe("Prune");
  });

  it("holds sources back until the answer is fully shown, then offers them", () => {
    const citation = { source_type: "internal", title: "Olive guide", marker: 1 };
    const revealing = { ...base, content: "Prune [1].", citations: [citation], revealChars: 3 };
    expect(named(revealing, "raise-sources")).toBeUndefined();

    const done = { ...base, content: "Prune [1].", citations: [citation] };
    expect(named(done, "raise-sources")?.data).toEqual({ citations: [citation] });
    expect(parts(done).find((part) => part.type === "text")?.text).toBe("Prune [1](#cite-1).");
    expect(convertMessage(done).status).toEqual({ type: "complete", reason: "stop" });
  });

  it("renders a pending clarification as an interactive part", () => {
    const interaction = {
      schema_version: "1",
      interaction_id: "i1",
      type: "clarification" as const,
      round: 1,
      max_rounds: 2,
      question: "Which crop?",
      options: [{ id: "a", label: "Olive", value: "olive" }],
      missing_fields: ["crop"],
      language: "en"
    };
    const message = { ...base, status: "clarification", interaction };
    expect(named(message, "raise-clarification")?.data).toEqual({ messageId: "m1", interaction });
  });

  it("marks dropped and stopped answers as incomplete with a notice", () => {
    const interrupted = { ...base, content: "Partial", status: "interrupted" };
    expect(convertMessage(interrupted).status).toEqual({ type: "incomplete", reason: "error" });
    expect(named(interrupted, "raise-notice")?.data).toEqual({ status: "interrupted" });

    const cancelled = { ...base, content: "", status: "cancelled" };
    expect(convertMessage(cancelled).status).toEqual({ type: "incomplete", reason: "cancelled" });
  });

  it("carries submitted feedback and follow-up suggestions", () => {
    const message = { ...base, content: "Done", feedback: "helpful" as const, quickReplies: ["Next?"] };
    const converted = convertMessage(message);
    expect(converted.metadata?.submittedFeedback).toEqual({ type: "positive" });
    expect(converted.metadata?.custom).toEqual({ quickReplies: ["Next?"] });
  });

  it("shows a user's attached image from its local preview", () => {
    const converted = convertMessage({
      ...base,
      role: "user",
      content: "What is this?",
      attachments: [{ kind: "image", mime_type: "image/png", name: "leaf.png", preview_url: "blob:x" }]
    });
    expect(converted.attachments?.[0]).toMatchObject({
      type: "image",
      name: "leaf.png",
      content: [{ type: "image", image: "blob:x" }]
    });
  });
});

describe("withCitationMarkers", () => {
  it("links bare markers once and leaves existing links alone", () => {
    expect(withCitationMarkers("A [1] and [12].")).toBe("A [1](#cite-1) and [12](#cite-12).");
    expect(withCitationMarkers("See [2](#cite-2)")).toBe("See [2](#cite-2)");
  });

  it("hides corpus source codes left in older answers", () => {
    expect(withCitationMarkers("General guidance [RAISE-AGRIFOOD-APPROVED-V0.3], not a date.")).toBe(
      "General guidance, not a date."
    );
  });
});

describe("speakableText", () => {
  it("drops markdown and citation markers before reading aloud", () => {
    expect(speakableText("**Prune** after harvest [1](#cite-1).\n- Clean tools [2]")).toBe(
      "Prune after harvest . Clean tools"
    );
  });
});
