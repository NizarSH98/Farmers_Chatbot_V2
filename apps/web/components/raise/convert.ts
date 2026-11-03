import type { ThreadMessageLike } from "@assistant-ui/react";

import type { Message } from "@/lib/types";

/** The backend writes `[n]`; markdown links let us style them as markers. */
export function withCitationMarkers(content: string): string {
  return content
    // Corpus source codes the backend now strips; also clean older stored answers.
    .replace(/\s?\[RAISE-[A-Z0-9][A-Z0-9._-]{1,120}\]/gi, "")
    .replace(/\[(\d{1,2})\](?!\()/g, (_match, digits) => `[${digits}](#cite-${digits})`);
}

function messageStatus(message: Message, revealing: boolean): ThreadMessageLike["status"] {
  if (message.pending || revealing) return { type: "running" };
  if (message.status === "cancelled") return { type: "incomplete", reason: "cancelled" };
  if (message.status === "failed" || message.status === "interrupted") {
    return { type: "incomplete", reason: "error" };
  }
  return { type: "complete", reason: "stop" };
}

export function convertMessage(message: Message): ThreadMessageLike {
  if (message.role === "user") {
    return {
      id: message.id,
      role: "user",
      createdAt: new Date(message.created_at),
      content: [{ type: "text", text: message.content }],
      attachments: message.attachments
        .filter((item) => item.kind === "image")
        .map((item, index) => ({
          id: `${message.id}-attachment-${index}`,
          type: "image" as const,
          name: item.name || "image",
          contentType: item.mime_type,
          status: { type: "complete" as const },
          content: item.preview_url
            ? [{ type: "image" as const, image: item.preview_url }]
            : []
        }))
    };
  }

  const revealing =
    message.revealChars !== undefined && message.revealChars < message.content.length;
  const visible =
    message.revealChars === undefined
      ? message.content
      : message.content.slice(0, message.revealChars);
  const parts: Exclude<ThreadMessageLike["content"], string>[number][] = [];

  if (message.pending && !visible) {
    parts.push({ type: "data", name: "raise-progress", data: { stage: message.stage || "" } });
  }
  const clarifying = message.status === "clarification" && message.interaction;
  // A clarification's lead text usually repeats its first question; the card
  // already shows it, so only keep genuinely additional framing.
  const repeatsQuestion =
    clarifying &&
    [message.interaction?.question, ...(message.interaction?.questions ?? []).map((item) => item.prompt)]
      .filter(Boolean)
      .some((prompt) => prompt!.trim() === visible.trim());
  if (visible && !repeatsQuestion) parts.push({ type: "text", text: withCitationMarkers(visible) });
  if (message.interaction && message.status === "clarification") {
    parts.push({
      type: "data",
      name: "raise-clarification",
      data: { messageId: message.id, interaction: message.interaction }
    });
  }
  if (message.warning) {
    parts.push({ type: "data", name: "raise-warning", data: { message: message.warning } });
  }
  if (!message.pending && !revealing && message.citations.length > 0) {
    parts.push({ type: "data", name: "raise-sources", data: { citations: message.citations } });
  }
  if (!message.pending && !revealing && message.artifact_ids?.length) {
    parts.push({ type: "data", name: "raise-artifacts", data: { ids: message.artifact_ids } });
  }
  if (message.status === "interrupted" || message.status === "cancelled") {
    parts.push({ type: "data", name: "raise-notice", data: { status: message.status } });
  }

  return {
    id: message.id,
    role: "assistant",
    createdAt: new Date(message.created_at),
    content: parts,
    status: messageStatus(message, revealing),
    metadata: {
      submittedFeedback: message.feedback
        ? { type: message.feedback === "helpful" ? "positive" : "negative" }
        : undefined,
      custom: { quickReplies: message.quickReplies || [] }
    }
  };
}
