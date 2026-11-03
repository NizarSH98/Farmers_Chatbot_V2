"use client";

import {
  AssistantRuntimeProvider,
  WebSpeechDictationAdapter,
  useExternalStoreRuntime,
  type AppendMessage,
  type AttachmentAdapter,
  type CompleteAttachment,
  type ExternalStoreThreadListAdapter,
  type FeedbackAdapter,
  type PendingAttachment,
} from "@assistant-ui/react";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode
} from "react";
import { toast } from "sonner";

import { ApiError, IncompleteTurnError, apiFetch, getTurn, streamTurn, uploadImage } from "@/lib/api";
import { starterPrompts } from "@/lib/i18n";
import { mergePreservingClientState } from "@/lib/messages";
import { LocaleSpeechSynthesisAdapter, speechLocale } from "@/lib/speech";
import type {
  Citation,
  ClarificationInteraction,
  Conversation,
  Message,
  TurnPayload
} from "@/lib/types";

import { useAppState } from "./app-state";
import { convertMessage } from "./convert";

const MAX_IMAGE_BYTES = 5 * 1024 * 1024;

type ClarificationResponse = NonNullable<TurnPayload["clarification_response"]>;

interface ChatState {
  conversations: Conversation[];
  activeId: string | null;
  isRunning: boolean;
  refreshConversations: () => Promise<void>;
  openConversation: (id: string | null) => void;
  startConversation: (projectId?: string, title?: string) => Promise<string | null>;
  answerClarification: (
    messageId: string,
    interaction: ClarificationInteraction,
    answers: Record<string, string | string[]>,
    summary: string
  ) => void;
  downloadArtifact: (artifactId: string, filename?: string) => Promise<void>;
}

const ChatStateContext = createContext<ChatState | null>(null);

export function useChatState(): ChatState {
  const value = useContext(ChatStateContext);
  if (!value) throw new Error("useChatState must be used inside ChatRuntimeProvider");
  return value;
}

function textOf(message: AppendMessage): string {
  return message.content
    .map((part) => (part.type === "text" ? part.text : ""))
    .join("\n")
    .trim();
}

export function ChatRuntimeProvider({ children }: { children: ReactNode }) {
  const app = useAppState();
  const { token, language, text, mode, modelId, clarificationStyle, refreshUsage } = app;

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [sending, setSending] = useState(false);
  // Which conversation's history is currently in `messages`.
  const [loadedFor, setLoadedFor] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  // A conversation created mid-send must not trigger a history reload that
  // would replace the optimistic turn being streamed into it.
  const skipLoadFor = useRef<string | null>(null);
  const previewUrls = useRef(new Set<string>());
  const messagesRef = useRef<Message[]>([]);

  const refreshConversations = useCallback(async () => {
    if (!token) return;
    const result = await apiFetch<{ items: Conversation[] }>("/v1/conversations", token);
    setConversations(result.items);
  }, [token]);

  useEffect(() => {
    if (!token) return;
    let active = true;
    apiFetch<{ items: Conversation[] }>("/v1/conversations", token)
      .then((result) => {
        if (active) setConversations(result.items);
      })
      .catch(() => {
        if (active) toast.error(text("error"));
      });
    return () => {
      active = false;
    };
  }, [text, token]);

  useEffect(() => {
    if (!token || !activeId) return;
    if (skipLoadFor.current === activeId) {
      skipLoadFor.current = null;
      return;
    }
    let active = true;
    const loading = activeId;
    apiFetch<{ items: Message[] }>(
      "/v1/conversations/" + loading + "/messages?limit=100",
      token
    )
      .then((result) => {
        if (active) setMessages((previous) => mergePreservingClientState(result.items, previous));
      })
      .catch(() => {
        if (active) toast.error(text("error"));
      })
      .finally(() => {
        if (active) setLoadedFor(loading);
      });
    return () => {
      active = false;
    };
  }, [activeId, text, token]);

  useEffect(() => {
    const urls = previewUrls.current;
    return () => urls.forEach((url) => URL.revokeObjectURL(url));
  }, []);

  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);

  // Reveal verified answers at reading pace. The text is final when it
  // arrives; this only paces presentation.
  const revealing = messages.some(
    (item) => item.revealChars !== undefined && item.revealChars < item.content.length
  );
  useEffect(() => {
    if (!revealing) return;
    let frame = 0;
    let last = performance.now();
    const step = (now: number) => {
      const elapsed = now - last;
      last = now;
      setMessages((items) =>
        items.map((item) => {
          if (item.revealChars === undefined || item.revealChars >= item.content.length) {
            return item;
          }
          const perSecond = Math.min(6000, Math.max(700, item.content.length / 2.2));
          const advance = Math.max(1, Math.round((perSecond * elapsed) / 1000));
          const next = Math.min(item.content.length, item.revealChars + advance);
          return { ...item, revealChars: next >= item.content.length ? undefined : next };
        })
      );
      frame = window.requestAnimationFrame(step);
    };
    frame = window.requestAnimationFrame(step);
    return () => window.cancelAnimationFrame(frame);
  }, [revealing]);

  const startConversation = useCallback(
    async (projectId?: string, title?: string) => {
      if (!token) return null;
      const created = await apiFetch<Conversation>("/v1/conversations", token, {
        method: "POST",
        body: JSON.stringify({ title: title || text("newChat"), project_id: projectId || null })
      });
      setConversations((items) => [created, ...items]);
      skipLoadFor.current = created.id;
      setLoadedFor(created.id);
      setActiveId(created.id);
      setMessages([]);
      return created.id;
    },
    [text, token]
  );

  const openConversation = useCallback((id: string | null) => {
    abortRef.current?.abort();
    setActiveId(id);
    setMessages([]);
  }, []);

  const patchMessage = useCallback((id: string, patch: Partial<Message>) => {
    setMessages((items) => items.map((item) => (item.id === id ? { ...item, ...patch } : item)));
  }, []);

  const runTurn = useCallback(
    async (
      question: string,
      options: {
        attachment?: { id: string; name: string; mime: string; preview: string };
        clarification?: { messageId: string; response?: ClarificationResponse };
      } = {}
    ) => {
      if (!token || sending) return;
      setSending(true);
      let conversationId = activeId;
      const assistantId = crypto.randomUUID();
      try {
        if (!conversationId) {
          const title = question.replace(/\s+/g, " ").trim();
          conversationId = await startConversation(undefined, title.length > 60 ? title.slice(0, 57) + "…" : title);
        }
        if (!conversationId) throw new Error(text("error"));
        const now = new Date().toISOString();
        const userMessage: Message = {
          id: crypto.randomUUID(),
          role: "user",
          content: question,
          status: "complete",
          citations: [],
          tools: [],
          attachments: options.attachment
            ? [{
                kind: "image",
                mime_type: options.attachment.mime,
                name: options.attachment.name,
                preview_url: options.attachment.preview
              }]
            : [],
          created_at: now
        };
        const assistantMessage: Message = {
          id: assistantId,
          clientKey: assistantId,
          role: "assistant",
          content: "",
          status: "streaming",
          citations: [],
          tools: [],
          attachments: [],
          created_at: now,
          pending: true,
          stage: "analysis_and_retrieval"
        };
        setMessages((items) => [
          ...items.map((item) =>
            options.clarification && item.id === options.clarification.messageId && item.interaction
              ? { ...item, interaction: { ...item.interaction, status: "resolved" as const } }
              : item
          ),
          userMessage,
          assistantMessage
        ]);

        const controller = new AbortController();
        abortRef.current = controller;
        const payload: TurnPayload = {
          conversation_id: conversationId,
          text: question,
          mode,
          model_id: modelId || undefined,
          clarification_style: clarificationStyle,
          attachment_ids: options.attachment ? [options.attachment.id] : [],
          ...(options.clarification?.response
            ? { clarification_response: options.clarification.response }
            : {})
        };

        for await (const event of streamTurn(payload, token, controller.signal)) {
          const data = event.data;
          if (event.event === "status") {
            patchMessage(assistantId, { stage: String(data.stage || "") });
          } else if (event.event === "source") {
            const citation = data.citation as Citation;
            setMessages((items) =>
              items.map((item) =>
                item.id === assistantId &&
                !item.citations.some((entry) => JSON.stringify(entry) === JSON.stringify(citation))
                  ? { ...item, citations: [...item.citations, citation] }
                  : item
              )
            );
          } else if (event.event === "content.delta") {
            const delta = String(data.text || "");
            setMessages((items) =>
              items.map((item) =>
                item.id === assistantId
                  ? { ...item, content: item.content + delta, revealChars: item.revealChars ?? 0 }
                  : item
              )
            );
          } else if (event.event === "clarification") {
            patchMessage(assistantId, {
              content: String(data.content || ""),
              status: "clarification",
              quickReplies: undefined,
              revealChars: undefined,
              interaction:
                data.interaction && typeof data.interaction === "object"
                  ? (data.interaction as ClarificationInteraction)
                  : undefined
            });
          } else if (event.event === "warning") {
            patchMessage(assistantId, { warning: String(data.message || "") });
          } else if (event.event === "turn.completed") {
            const quickReplies = Array.isArray(data.quick_replies)
              ? data.quick_replies.map(String)
              : [];
            const artifactIds = Array.isArray(data.artifact_ids)
              ? data.artifact_ids.map(String)
              : undefined;
            patchMessage(assistantId, {
              // Keep the runtime id stable (changing it reads as a new branch);
              // remember the persisted id for feedback and artifacts.
              ...(data.message_id ? { serverId: String(data.message_id) } : {}),
              status: String(data.kind || "complete"),
              model: String(data.model || modelId),
              pending: false,
              stage: undefined,
              ...(typeof data.content === "string" ? { content: data.content } : {}),
              ...(quickReplies.length ? { quickReplies } : {}),
              ...(artifactIds?.length ? { artifact_ids: artifactIds } : {})
            });
          } else if (event.event === "error") {
            throw new ApiError(500, String(data.message || text("error")));
          }
        }
      } catch (caught) {
        if (caught instanceof DOMException && caught.name === "AbortError") {
          setMessages((items) =>
            items.map((item) =>
              item.pending
                ? { ...item, pending: false, status: "cancelled", revealChars: undefined, stage: undefined }
                : item
            )
          );
        } else if (caught instanceof IncompleteTurnError) {
          let recovered = false;
          if (caught.turnId) {
            try {
              const turn = await getTurn(caught.turnId, token);
              if (turn.terminal && turn.message) {
                const recoveredMessage = turn.message;
                setMessages((items) =>
                  items.map((item) =>
                    item.clientKey === assistantId
                      ? { ...recoveredMessage, id: item.id, serverId: recoveredMessage.id, clientKey: assistantId, pending: false }
                      : item
                  )
                );
                recovered = true;
              }
            } catch {
              // Fall through to the interrupted state below.
            }
          }
          if (!recovered) {
            setMessages((items) =>
              items.map((item) =>
                item.clientKey === assistantId
                  ? { ...item, pending: false, status: "interrupted", stage: undefined, revealChars: undefined }
                  : item
              )
            );
          }
        } else {
          toast.error(caught instanceof Error ? caught.message : text("error"));
          setMessages((items) =>
            items.map((item) =>
              item.pending
                ? { ...item, pending: false, status: "failed", stage: undefined, revealChars: undefined }
                : item
            )
          );
        }
      } finally {
        abortRef.current = null;
        setSending(false);
        void refreshConversations().catch(() => undefined);
        void refreshUsage();
      }
    },
    [
      activeId,
      clarificationStyle,
      mode,
      modelId,
      patchMessage,
      refreshConversations,
      refreshUsage,
      sending,
      startConversation,
      text,
      token
    ]
  );

  const onNew = useCallback(
    async (message: AppendMessage) => {
      const images = (message.attachments ?? []).filter((item) => item.type === "image");
      if (images.length > 1) toast.info(text("onlyOneImage"));
      const image = images[0];
      const preview =
        image?.content?.find((part) => part.type === "image")?.type === "image"
          ? (image.content.find((part) => part.type === "image") as { image: string }).image
          : "";
      const question = textOf(message) || (image ? text("imageQuestion") : "");
      if (!question) return;
      await runTurn(question, {
        attachment: image
          ? { id: image.id, name: image.name, mime: image.contentType || "image/jpeg", preview }
          : undefined
      });
    },
    [runTurn, text]
  );

  // Our conversations are linear on the server, so edit and regenerate
  // replace the visible tail and ask again in the same conversation.
  const onEdit = useCallback(
    async (message: AppendMessage) => {
      const question = textOf(message);
      if (!question) return;
      setMessages((items) => {
        const index = message.parentId ? items.findIndex((item) => item.id === message.parentId) : -1;
        return items.slice(0, index + 1);
      });
      await runTurn(question);
    },
    [runTurn]
  );

  const onReload = useCallback(
    async (parentId: string | null) => {
      const index = parentId ? messages.findIndex((item) => item.id === parentId) : -1;
      const source = index >= 0 ? messages[index] : undefined;
      if (!source || source.role !== "user") return;
      setMessages((items) => items.slice(0, index));
      await runTurn(source.content);
    },
    [messages, runTurn]
  );

  const onCancel = useCallback(async () => {
    abortRef.current?.abort();
  }, []);

  const answerClarification = useCallback(
    (
      messageId: string,
      interaction: ClarificationInteraction,
      answers: Record<string, string | string[]>,
      summary: string
    ) => {
      void runTurn(summary, {
        clarification: {
          messageId,
          response: interaction.interaction_id
            ? { interaction_id: interaction.interaction_id, answers }
            : undefined
        }
      });
    },
    [runTurn]
  );

  const downloadArtifact = useCallback(
    async (artifactId: string, filename?: string) => {
      const { downloadPrivateFile } = await import("@/lib/api");
      await downloadPrivateFile(
        "/v1/artifacts/" + artifactId + "/download",
        token,
        filename || "raise-" + artifactId
      ).catch(() => toast.error(text("error")));
    },
    [text, token]
  );

  const attachmentAdapter = useMemo<AttachmentAdapter>(
    () => ({
      accept: "image/jpeg,image/png",
      async add({ file }): Promise<PendingAttachment> {
        if (!["image/jpeg", "image/png"].includes(file.type) || file.size > MAX_IMAGE_BYTES) {
          throw new Error(text("uploadError"));
        }
        return {
          id: crypto.randomUUID(),
          type: "image",
          name: file.name,
          contentType: file.type,
          file,
          status: { type: "requires-action", reason: "composer-send" }
        };
      },
      async remove() {
        // Uploads happen on send, so nothing is stored server-side yet.
      },
      async send(attachment): Promise<CompleteAttachment> {
        const uploaded = await uploadImage(attachment.file, token).catch(() => {
          toast.error(text("uploadError"));
          throw new Error(text("uploadError"));
        });
        const preview = URL.createObjectURL(attachment.file);
        previewUrls.current.add(preview);
        return {
          ...attachment,
          id: uploaded.id,
          status: { type: "complete" },
          content: [{ type: "image", image: preview }]
        };
      }
    }),
    [text, token]
  );

  const feedbackAdapter = useMemo<FeedbackAdapter>(
    () => ({
      submit: ({ message, type }) => {
        const category = type === "positive" ? "helpful" : "not_helpful";
        const persistedId = messagesRef.current.find((item) => item.id === message.id)?.serverId ?? message.id;
        setMessages((items) =>
          items.map((item) => (item.id === message.id ? { ...item, feedback: category } : item))
        );
        void apiFetch("/v1/feedback", token, {
          method: "POST",
          body: JSON.stringify({
            category,
            comment: type === "positive" ? "Helpful answer" : "Answer needs improvement",
            rating: type === "positive" ? 5 : 2,
            message_id: persistedId,
            language
          })
        }).catch(() => {
          toast.error(text("error"));
          setMessages((items) =>
            items.map((item) => (item.id === message.id ? { ...item, feedback: undefined } : item))
          );
        });
      }
    }),
    [language, text, token]
  );

  const dictationAdapter = useMemo(
    () =>
      typeof window !== "undefined" && WebSpeechDictationAdapter.isSupported()
        ? new WebSpeechDictationAdapter({
            language: speechLocale(language),
            continuous: true,
            interimResults: true
          })
        : undefined,
    [language]
  );

  const speechAdapter = useMemo(
    () =>
      LocaleSpeechSynthesisAdapter.isSupported()
        ? new LocaleSpeechSynthesisAdapter(language)
        : undefined,
    [language]
  );

  const updateConversation = useCallback(
    async (id: string, patch: { title?: string; archived?: boolean }) => {
      await apiFetch("/v1/conversations/" + id, token, {
        method: "PATCH",
        body: JSON.stringify(patch)
      });
      await refreshConversations();
    },
    [refreshConversations, token]
  );

  const threadListAdapter = useMemo<ExternalStoreThreadListAdapter>(
    () => ({
      threadId: activeId ?? undefined,
      threads: conversations
        .filter((item) => !item.archived)
        .map((item) => ({ status: "regular" as const, id: item.id, title: item.title })),
      archivedThreads: conversations
        .filter((item) => item.archived)
        .map((item) => ({ status: "archived" as const, id: item.id, title: item.title })),
      onSwitchToNewThread: () => openConversation(null),
      onSwitchToThread: (id) => openConversation(id),
      onRename: (id, title) => updateConversation(id, { title }),
      onArchive: async (id) => {
        await updateConversation(id, { archived: true });
        if (id === activeId) openConversation(null);
      },
      onUnarchive: (id) => updateConversation(id, { archived: false }),
      onDelete: async (id) => {
        await apiFetch("/v1/conversations/" + id, token, { method: "DELETE" });
        if (id === activeId) openConversation(null);
        await refreshConversations();
      }
    }),
    [activeId, conversations, openConversation, refreshConversations, token, updateConversation]
  );

  const lastAssistant = [...messages].reverse().find((item) => item.role === "assistant");
  const suggestions = useMemo(() => {
    if (messages.length === 0) {
      return starterPrompts(language).map((prompt) => ({ prompt }));
    }
    if (!lastAssistant || lastAssistant.pending || lastAssistant.status === "clarification") {
      return [];
    }
    return (lastAssistant.quickReplies || []).map((prompt) => ({ prompt }));
  }, [language, lastAssistant, messages.length]);

  const runtime = useExternalStoreRuntime<Message>({
    messages,
    convertMessage,
    isRunning: sending || revealing,
    isLoading: Boolean(activeId) && loadedFor !== activeId,
    isDisabled: !token,
    suggestions,
    onNew,
    onEdit,
    onReload,
    onCancel,
    adapters: {
      attachments: attachmentAdapter,
      feedback: feedbackAdapter,
      dictation: dictationAdapter,
      speech: speechAdapter,
      threadList: threadListAdapter
    }
  });

  const chatState = useMemo<ChatState>(
    () => ({
      conversations,
      activeId,
      isRunning: sending,
      refreshConversations,
      openConversation,
      startConversation,
      answerClarification,
      downloadArtifact
    }),
    [
      activeId,
      answerClarification,
      conversations,
      downloadArtifact,
      openConversation,
      refreshConversations,
      sending,
      startConversation
    ]
  );

  return (
    <ChatStateContext.Provider value={chatState}>
      <AssistantRuntimeProvider runtime={runtime}>{children}</AssistantRuntimeProvider>
    </ChatStateContext.Provider>
  );
}
