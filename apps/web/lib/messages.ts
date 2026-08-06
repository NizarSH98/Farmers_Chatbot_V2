import type { Message } from "./types";

/**
 * Merge a fresh server message list into local state without losing fields
 * that only ever exist client-side (quick replies, feedback state), since
 * those are never persisted server-side and would otherwise disappear the
 * moment a background refetch replaces the message objects.
 */
export function mergePreservingClientState(
  serverItems: Message[],
  previous: Message[]
): Message[] {
  const previousById = new Map(previous.map((item) => [item.id, item]));
  return serverItems.map((item) => {
    const existing = previousById.get(item.id);
    if (!existing) return item;
    return {
      ...item,
      quickReplies: existing.quickReplies,
      feedback: existing.feedback,
      feedbackPending: existing.feedbackPending
    };
  });
}
