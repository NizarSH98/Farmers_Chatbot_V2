"use client";
/* eslint-disable @next/next/no-img-element -- local object URL preview is not a deployable image asset */

import type { Session } from "@supabase/supabase-js";
import {
  Archive,
  Check,
  ChevronDown,
  CircleStop,
  Clipboard,
  DatabaseBackup,
  Download,
  Ellipsis,
  FileText,
  FolderKanban,
  Globe2,
  ImagePlus,
  Leaf,
  LogOut,
  Menu,
  MessageSquarePlus,
  PanelLeftClose,
  PanelLeftOpen,
  Pencil,
  RefreshCw,
  Search,
  Send,
  Settings,
  ThumbsDown,
  ThumbsUp,
  Trash2,
  Upload,
  X
} from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import {
  ApiError,
  downloadPrivateFile,
  getTurn,
  IncompleteTurnError,
  apiFetch,
  streamTurn,
  uploadImage
} from "@/lib/api";
import { t, thinkingLines } from "@/lib/i18n";
import { mergePreservingClientState } from "@/lib/messages";
import { supabaseBrowser } from "@/lib/supabase";
import type {
  AppConfig,
  Artifact,
  Citation,
  ClarificationQuestion,
  ClarificationInteraction,
  Conversation,
  CurrentUser,
  Language,
  Message,
  Project,
  ProjectDocument,
  TurnPayload,
  UsageSummary
} from "@/lib/types";

const LOCAL_AUTH = process.env.NEXT_PUBLIC_LOCAL_AUTH === "true";

type DialogState =
  | { kind: "rename"; conversation: Conversation }
  | { kind: "delete"; conversation: Conversation }
  | { kind: "delete-account" }
  | null;

interface SettingsDraft {
  language: Language;
  mode: string;
  modelId: string;
  clarificationStyle: string;
}

const initialConfig: AppConfig = {
  app_name: "RAISE",
  agreement_version: "",
  default_language: "ar",
  modes: [],
  models: []
};

// The backend replaces internal evidence IDs with `[n]`. Render those as
// anchors so they can be styled as superscripts and scrolled to, rather than
// appearing as literal bracketed digits in the prose.
function withCitationMarkers(content: string): string {
  return content.replace(/\[(\d{1,2})\]/g, (match, digits) => `[${digits}](#cite-${digits})`);
}

function clarificationQuestions(
  interaction: ClarificationInteraction
): ClarificationQuestion[] {
  if (interaction.questions?.length) return interaction.questions;
  return [{
    id: "detail",
    prompt: interaction.question,
    answer_type: "single",
    required: true,
    allow_other: false,
    options: interaction.options || []
  }];
}


export function ChatWorkspace() {
  const [language, setLanguage] = useState<Language>(() => {
    if (typeof window === "undefined") return "ar";
    const saved = localStorage.getItem("raise-language");
    return saved === "en" || saved === "ar" ? saved : "ar";
  });
  const [session, setSession] = useState<Session | null>(null);
  const [profile, setProfile] = useState<CurrentUser | null>(null);
  const [config, setConfig] = useState<AppConfig>(initialConfig);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [composer, setComposer] = useState("");
  const [mode, setMode] = useState("standard");
  const [modelId, setModelId] = useState("");
  const [clarificationStyle, setClarificationStyle] = useState("auto");
  const [loading, setLoading] = useState(!LOCAL_AUTH);
  const [sending, setSending] = useState(false);
  const [statusStage, setStatusStage] = useState("");
  const [thinkingIndex, setThinkingIndex] = useState(0);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [conversationsOpen, setConversationsOpen] = useState(true);
  const [mobileSidebar, setMobileSidebar] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [settingsDraft, setSettingsDraft] = useState<SettingsDraft>({
    language: "ar",
    mode: "standard",
    modelId: "",
    clarificationStyle: "auto"
  });
  const [agreement, setAgreement] = useState("");
  const [agreementOpen, setAgreementOpen] = useState(false);
  const [corpusWarningVisible, setCorpusWarningVisible] = useState(false);
  const [search, setSearch] = useState("");
  const [dialog, setDialog] = useState<DialogState>(null);
  const [renameValue, setRenameValue] = useState("");
  const [error, setError] = useState("");
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imageId, setImageId] = useState("");
  const [imagePreview, setImagePreview] = useState("");
  const [uploading, setUploading] = useState(false);
  const [copiedId, setCopiedId] = useState("");
  const [usage, setUsage] = useState<UsageSummary | null>(null);
  const [workspaceOpen, setWorkspaceOpen] = useState(false);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [projectDocuments, setProjectDocuments] = useState<ProjectDocument[]>([]);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [projectName, setProjectName] = useState("");
  const [projectInstructions, setProjectInstructions] = useState("");
  const [workspaceBusy, setWorkspaceBusy] = useState(false);
  const [clarificationAnswers, setClarificationAnswers] = useState<
    Record<string, Record<string, string | string[]>>
  >({});
  const [customAnswerFor, setCustomAnswerFor] = useState("");
  const abortRef = useRef<AbortController | null>(null);
  const endRef = useRef<HTMLDivElement | null>(null);
  const fileRef = useRef<HTMLInputElement | null>(null);
  const documentRef = useRef<HTMLInputElement | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const localPreviewUrls = useRef(new Set<string>());

  const token = LOCAL_AUTH ? "local-development" : session?.access_token || "";
  const rtl = language === "ar";
  const text = useCallback(
    (key: Parameters<typeof t>[1]) => t(language, key),
    [language]
  );
  const pendingClarificationId = useMemo(() => {
    for (let index = messages.length - 1; index >= 0; index -= 1) {
      const message = messages[index];
      if (message.role === "user") return "";
      if (
        message.role === "assistant" &&
        message.status === "clarification" &&
        message.interaction?.status !== "resolved"
      ) return message.id;
    }
    return "";
  }, [messages]);

  useEffect(() => {
    if (LOCAL_AUTH) {
      return;
    }

    const supabase = supabaseBrowser();
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session);
      setLoading(false);
    });
    const { data } = supabase.auth.onAuthStateChange((_event, next) => {
      setSession(next);
      if (!next) {
        setProfile(null);
        setConversations([]);
        setMessages([]);
        setActiveId(null);
      }
    });
    return () => data.subscription.unsubscribe();
  }, []);

  useEffect(() => {
    document.documentElement.lang = language;
    document.documentElement.dir = rtl ? "rtl" : "ltr";
    localStorage.setItem("raise-language", language);
  }, [language, rtl]);

  useEffect(() => () => {
    localPreviewUrls.current.forEach((url) => URL.revokeObjectURL(url));
    localPreviewUrls.current.clear();
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, statusStage]);

  // Rotate the waiting copy so a long turn reads as progress rather than a
  // stalled spinner. The lines describe what the pipeline is actually doing.
  useEffect(() => {
    if (!sending) return;
    const lines = thinkingLines(language);
    const timer = window.setInterval(() => {
      setThinkingIndex((value) => (value + 1) % lines.length);
    }, 2600);
    return () => window.clearInterval(timer);
  }, [language, sending]);

  // Reveal the finished answer at reading pace. The text is verified before it
  // arrives, so this is presentation only: it never shows unverified content.
  // Long answers reveal faster so the total wait stays roughly constant.
  useEffect(() => {
    const pending = messages.find(
      (item) =>
        item.revealChars !== undefined && item.revealChars < item.content.length
    );
    if (!pending) return;
    let frame = 0;
    let last = performance.now();
    const step = (now: number) => {
      const elapsed = now - last;
      last = now;
      setMessages((items) =>
        items.map((item) => {
          if (item.id !== pending.id || item.revealChars === undefined) return item;
          const remaining = item.content.length - item.revealChars;
          if (remaining <= 0) return item;
          const perSecond = Math.min(6000, Math.max(700, item.content.length / 2.2));
          const advance = Math.max(1, Math.round((perSecond * elapsed) / 1000));
          const next = Math.min(item.content.length, item.revealChars + advance);
          return { ...item, revealChars: next };
        })
      );
      frame = window.requestAnimationFrame(step);
    };
    frame = window.requestAnimationFrame(step);
    return () => window.cancelAnimationFrame(frame);
  }, [messages]);

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        if (dialog) setDialog(null);
        else if (settingsOpen) setSettingsOpen(false);
      }
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [dialog, settingsOpen]);

  const loadConversations = useCallback(async (accessToken: string) => {
    const result = await apiFetch<{ items: Conversation[] }>(
      "/v1/conversations",
      accessToken
    );
    setConversations(result.items);
    return result.items;
  }, []);

  const loadUsage = useCallback(async (accessToken: string) => {
    try {
      const result = await apiFetch<UsageSummary>("/v1/usage", accessToken);
      setUsage(result);
    } catch {
      // Usage display is informational; a failed refresh should not block chat.
    }
  }, []);

  const revealCorpusWarning = useCallback((appConfig: AppConfig) => {
    if (!appConfig.corpus_warning) return;
    const key = `raise-corpus-warning:${appConfig.agreement_version}`;
    if (sessionStorage.getItem(key)) return;
    sessionStorage.setItem(key, "shown");
    setCorpusWarningVisible(true);
  }, []);

  const bootstrap = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      const [appConfig, user] = await Promise.all([
        apiFetch<AppConfig>("/v1/config", token),
        apiFetch<CurrentUser>("/v1/me", token)
      ]);
      setConfig(appConfig);
      setProfile(user);
      setMode(user.default_mode || "standard");
      const savedModel = localStorage.getItem("raise-model");
      const validModel = appConfig.models.find((item) => item.id === savedModel);
      setModelId(validModel ? savedModel! : appConfig.models[0]?.id || "");
      if (!user.consent_current) {
        const legal = await apiFetch<{ markdown: string }>(
          "/v1/legal/agreement?language=" + language,
          token
        );
        setAgreement(legal.markdown);
        setAgreementOpen(true);
      } else {
        revealCorpusWarning(appConfig);
        const items = await loadConversations(token);
        if (items[0]) setActiveId((value) => value || items[0].id);
        void loadUsage(token);
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : text("error"));
    } finally {
      setLoading(false);
    }
  }, [language, loadConversations, loadUsage, revealCorpusWarning, text, token]);

  useEffect(() => {
    const timer = window.setTimeout(() => void bootstrap(), 0);
    return () => window.clearTimeout(timer);
  }, [bootstrap]);

  useEffect(() => {
    if (!token || !activeId || agreementOpen || sending) return;
    apiFetch<{ items: Message[] }>(
      "/v1/conversations/" + activeId + "/messages?limit=100",
      token
    )
      .then((result) => {
        setMessages((previous) => mergePreservingClientState(result.items, previous));
      })
      .catch((caught) => {
        setError(caught instanceof Error ? caught.message : text("error"));
      });
  }, [activeId, agreementOpen, sending, text, token]);

  const signIn = async () => {
    setError("");
    const { error: authError } = await supabaseBrowser().auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: window.location.origin + "/auth/callback",
        queryParams: { prompt: "select_account" }
      }
    });
    if (authError) setError(authError.message);
  };

  const signOut = async () => {
    abortRef.current?.abort();
    if (LOCAL_AUTH) return;
    await supabaseBrowser().auth.signOut();
  };

  const acceptAgreement = async () => {
    if (!token) return;
    setError("");
    try {
      await apiFetch("/v1/consent", token, { method: "POST" });
      setAgreementOpen(false);
      setProfile((value) => value ? { ...value, consent_current: true } : value);
      revealCorpusWarning(config);
      const items = await loadConversations(token);
      if (items[0]) setActiveId(items[0].id);
      void loadUsage(token);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : text("error"));
    }
  };

  const createConversation = async (projectId?: string, title?: string) => {
    if (!token) return null;
    const created = await apiFetch<Conversation>("/v1/conversations", token, {
      method: "POST",
      body: JSON.stringify({
        title: title || text("newChat"),
        project_id: projectId || null
      })
    });
    setConversations((items) => [created, ...items]);
    setActiveId(created.id);
    setMessages([]);
    setMobileSidebar(false);
    return created.id;
  };

  const chooseConversation = (id: string) => {
    if (sending) abortRef.current?.abort();
    setActiveId(id);
    setMobileSidebar(false);
    setError("");
  };

  const openSettings = () => {
    setSettingsDraft({ language, mode, modelId, clarificationStyle });
    setSettingsOpen(true);
  };

  const closeSettings = () => setSettingsOpen(false);

  const saveSettings = () => {
    setLanguage(settingsDraft.language);
    setMode(settingsDraft.mode);
    setModelId(settingsDraft.modelId);
    setClarificationStyle(settingsDraft.clarificationStyle);
    localStorage.setItem("raise-model", settingsDraft.modelId);
    setSettingsOpen(false);
  };

  const handleImage = async (file?: File) => {
    if (!file || !token) return;
    setUploading(true);
    setError("");
    try {
      const uploaded = await uploadImage(file, token);
      if (imagePreview) {
        URL.revokeObjectURL(imagePreview);
        localPreviewUrls.current.delete(imagePreview);
      }
      const previewUrl = URL.createObjectURL(file);
      localPreviewUrls.current.add(previewUrl);
      setImageFile(file);
      setImageId(uploaded.id);
      setImagePreview(previewUrl);
    } catch {
      setError(text("uploadError"));
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const removeImage = () => {
    if (imagePreview) {
      URL.revokeObjectURL(imagePreview);
      localPreviewUrls.current.delete(imagePreview);
    }
    setImageFile(null);
    setImageId("");
    setImagePreview("");
  };

  const patchPending = (id: string, patch: Partial<Message>) => {
    setMessages((items) => items.map((item) =>
      item.id === id ? { ...item, ...patch } : item
    ));
  };

  const appendPending = (id: string, delta: string) => {
    setMessages((items) => items.map((item) =>
      item.id === id
        ? {
            ...item,
            content: item.content + delta,
            // Hold the reveal at its current position; the animation advances
            // it. Undefined would mean "already fully shown".
            revealChars: item.revealChars ?? 0
          }
        : item
    ));
  };

  const submit = async (
    override?: string,
    clarificationResponse?: TurnPayload["clarification_response"]
  ) => {
    if (!token || sending) return;
    const typedQuestion = (override ?? composer).trim();
    const question = typedQuestion || (imageId ? text("imageQuestion") : "");
    if (!question) return;
    setError("");
    setSending(true);
    setThinkingIndex(0);
    setStatusStage("analysis_and_retrieval");
    let conversationId = activeId;
    let assistantId = "";
    try {
      if (!conversationId) conversationId = await createConversation();
      if (!conversationId) throw new Error(text("error"));
      const userId = crypto.randomUUID();
      assistantId = crypto.randomUUID();
      const now = new Date().toISOString();
      const submittedImagePreview = imageFile ? URL.createObjectURL(imageFile) : "";
      if (submittedImagePreview) {
        localPreviewUrls.current.add(submittedImagePreview);
      }
      const optimisticUser: Message = {
        id: userId,
        role: "user",
        content: question,
        status: "complete",
        citations: [],
        tools: [],
        attachments: imageFile ? [{
          kind: "image",
          mime_type: imageFile.type,
          name: imageFile.name,
          preview_url: submittedImagePreview
        }] : [],
        created_at: now
      };
      const optimisticAssistant: Message = {
        id: assistantId,
        clientKey: assistantId,
        role: "assistant",
        content: "",
        status: "streaming",
        citations: [],
        tools: [],
        attachments: [],
        created_at: now,
        pending: true
      };
      setMessages((items) => [
        ...items.map((item) => (
          clarificationResponse && item.id === pendingClarificationId && item.interaction
            ? {
                ...item,
                interaction: { ...item.interaction, status: "resolved" as const }
              }
            : item
        )),
        optimisticUser,
        optimisticAssistant
      ]);
      setComposer("");
      if (textareaRef.current) textareaRef.current.style.height = "auto";
      const controller = new AbortController();
      abortRef.current = controller;
      const payload: TurnPayload = {
        conversation_id: conversationId,
        text: question,
        mode,
        model_id: modelId || undefined,
        clarification_style: clarificationStyle,
        attachment_ids: imageId ? [imageId] : [],
        ...(clarificationResponse ? { clarification_response: clarificationResponse } : {})
      };
      for await (const event of streamTurn(payload, token, controller.signal)) {
        if (event.event === "status") {
          setStatusStage(String(event.data.stage || ""));
        } else if (event.event === "source") {
          const citation = event.data.citation as Citation;
          setMessages((items) => items.map((item) =>
            item.id === assistantId && !item.citations.some((entry) =>
              JSON.stringify(entry) === JSON.stringify(citation)
            ) ? { ...item, citations: [...item.citations, citation] } : item
          ));
        } else if (event.event === "content.delta") {
          appendPending(assistantId, String(event.data.text || ""));
        } else if (event.event === "clarification") {
          const interaction = event.data.interaction && typeof event.data.interaction === "object"
            ? event.data.interaction as ClarificationInteraction
            : undefined;
          patchPending(assistantId, {
            content: String(event.data.content || ""),
            status: "clarification",
            quickReplies: undefined,
            interaction
          });
        } else if (event.event === "warning") {
          patchPending(assistantId, { warning: String(event.data.message || "") });
        } else if (event.event === "turn.completed") {
          const quickReplies = Array.isArray(event.data.quick_replies)
            ? event.data.quick_replies.map(String)
            : [];
          patchPending(assistantId, {
            id: String(event.data.message_id || assistantId),
            status: String(event.data.kind || "complete"),
            model: String(event.data.model || modelId),
            pending: false,
            ...(typeof event.data.content === "string"
              ? { content: event.data.content }
              : {}),
            ...(quickReplies.length > 0 ? { quickReplies } : {})
          });
        } else if (event.event === "error") {
          throw new Error(String(event.data.message || text("error")));
        }
      }
      if (imagePreview) {
        URL.revokeObjectURL(imagePreview);
        localPreviewUrls.current.delete(imagePreview);
      }
      setImageFile(null);
      setImageId("");
      setImagePreview("");
      if (fileRef.current) fileRef.current.value = "";
    } catch (caught) {
      if (caught instanceof DOMException && caught.name === "AbortError") {
        setMessages((items) => items.map((item) =>
          item.pending
            ? { ...item, pending: false, status: "cancelled", revealChars: undefined }
            : item
        ));
      } else if (caught instanceof IncompleteTurnError) {
        let recovered = false;
        if (caught.turnId) {
          try {
            const turn = await getTurn(caught.turnId, token);
            if (turn.terminal && turn.message) {
              setMessages((items) => items.map((item) =>
                item.id === assistantId
                  ? { ...turn.message!, clientKey: item.clientKey, pending: false }
                  : item
              ));
              recovered = true;
            } else if (turn.terminal && turn.error) {
              setError(turn.error);
              patchPending(assistantId, { pending: false, status: "failed" });
              recovered = true;
            }
          } catch {
            // The conversation refresh below is the final recovery source.
          }
        }
        if (!recovered) {
          patchPending(assistantId, { pending: false, status: "interrupted" });
          setError(text("error"));
        }
        try {
          const fresh = await apiFetch<{ items: Message[] }>(
            "/v1/conversations/" + conversationId + "/messages?limit=100",
            token
          );
          setMessages((previous) => {
            const merged = mergePreservingClientState(fresh.items, previous);
            const localAssistant = previous.find((item) =>
              item.clientKey === assistantId
            );
            return localAssistant && !fresh.items.some((item) => item.id === localAssistant.id)
              ? [...merged, localAssistant]
              : merged;
          });
        } catch {
          // Keep the recovered/interrupted local state when refresh is unavailable.
        }
      } else {
        const message = caught instanceof ApiError
          ? caught.message
          : caught instanceof Error ? caught.message : text("error");
        setError(message);
        setMessages((items) => items.map((item) =>
          item.pending ? { ...item, pending: false, status: "failed" } : item
        ));
      }
    } finally {
      abortRef.current = null;
      setSending(false);
      setStatusStage("");
      if (token) {
        void loadConversations(token);
        void loadUsage(token);
      }
    }
  };

  const stop = () => abortRef.current?.abort();

  const copyMessage = async (message: Message) => {
    await navigator.clipboard.writeText(message.content);
    setCopiedId(message.id);
    window.setTimeout(() => setCopiedId(""), 1500);
  };

  const sendFeedback = async (message: Message, helpful: boolean) => {
    if (!token || message.pending || message.feedbackPending) return;
    const category = helpful ? "helpful" : "not_helpful";
    if (message.feedback === category) return;
    const previousFeedback = message.feedback;
    setMessages((items) => items.map((item) =>
      item.id === message.id ? { ...item, feedback: category, feedbackPending: true } : item
    ));
    try {
      await apiFetch("/v1/feedback", token, {
        method: "POST",
        body: JSON.stringify({
          category,
          comment: helpful ? "Helpful answer" : "Answer needs improvement",
          rating: helpful ? 5 : 2,
          message_id: message.id,
          language
        })
      });
      setMessages((items) => items.map((item) =>
        item.id === message.id ? { ...item, feedbackPending: false } : item
      ));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : text("error"));
      setMessages((items) => items.map((item) =>
        item.id === message.id
          ? { ...item, feedback: previousFeedback, feedbackPending: false }
          : item
      ));
    }
  };

  const regenerate = (messageIndex: number) => {
    const previous = [...messages].slice(0, messageIndex).reverse()
      .find((message) => message.role === "user");
    if (previous) void submit(previous.content);
    // Note: image attachments from original messages cannot be re-sent because
    // uploads are single-use. The regenerated answer proceeds without the image.
  };

  const updateConversation = async (
    conversation: Conversation,
    changes: { title?: string; archived?: boolean }
  ) => {
    if (!token) return;
    try {
      await apiFetch("/v1/conversations/" + conversation.id, token, {
        method: "PATCH",
        body: JSON.stringify(changes)
      });
      await loadConversations(token);
      setDialog(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : text("error"));
    }
  };

  const deleteConversation = async (conversation: Conversation) => {
    if (!token) return;
    try {
      await apiFetch("/v1/conversations/" + conversation.id, token, {
        method: "DELETE"
      });
      const items = await loadConversations(token);
      setActiveId(items[0]?.id || null);
      setMessages([]);
      setDialog(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : text("error"));
    }
  };

  const deleteAccount = async () => {
    if (!token) return;
    try {
      await apiFetch("/v1/account", token, { method: "DELETE" });
      await supabaseBrowser().auth.signOut({ scope: "local" });
      setDialog(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : text("error"));
    }
  };

  const loadWorkspace = async (preferredProjectId?: string) => {
    if (!token) return;
    setWorkspaceBusy(true);
    try {
      const [projectResult, artifactResult] = await Promise.all([
        apiFetch<{ items: Project[] }>("/v1/projects", token),
        apiFetch<{ items: Artifact[] }>("/v1/artifacts", token)
      ]);
      setProjects(projectResult.items);
      setArtifacts(artifactResult.items);
      const nextProjectId = preferredProjectId
        || selectedProjectId
        || projectResult.items[0]?.id
        || "";
      setSelectedProjectId(nextProjectId);
      if (nextProjectId) {
        const documentResult = await apiFetch<{ items: ProjectDocument[] }>(
          "/v1/projects/" + nextProjectId + "/documents",
          token
        );
        setProjectDocuments(documentResult.items);
      } else {
        setProjectDocuments([]);
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : text("error"));
    } finally {
      setWorkspaceBusy(false);
    }
  };

  const openWorkspace = () => {
    setWorkspaceOpen(true);
    setMobileSidebar(false);
    void loadWorkspace();
  };

  const chooseProject = async (projectId: string) => {
    if (!token) return;
    setSelectedProjectId(projectId);
    setWorkspaceBusy(true);
    try {
      const result = await apiFetch<{ items: ProjectDocument[] }>(
        "/v1/projects/" + projectId + "/documents",
        token
      );
      setProjectDocuments(result.items);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : text("error"));
    } finally {
      setWorkspaceBusy(false);
    }
  };

  const createProject = async () => {
    if (!token || !projectName.trim()) return;
    setWorkspaceBusy(true);
    try {
      const created = await apiFetch<Project>("/v1/projects", token, {
        method: "POST",
        body: JSON.stringify({
          name: projectName.trim(),
          instructions: projectInstructions.trim()
        })
      });
      setProjectName("");
      setProjectInstructions("");
      await loadWorkspace(created.id);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : text("error"));
      setWorkspaceBusy(false);
    }
  };

  const deleteProject = async (projectId: string) => {
    if (!token) return;
    setWorkspaceBusy(true);
    try {
      await apiFetch("/v1/projects/" + projectId, token, { method: "DELETE" });
      setSelectedProjectId("");
      await loadWorkspace();
      await loadConversations(token);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : text("error"));
      setWorkspaceBusy(false);
    }
  };

  const uploadProjectDocument = async (file?: File) => {
    if (!file || !token || !selectedProjectId) return;
    setWorkspaceBusy(true);
    try {
      const form = new FormData();
      form.set("document", file);
      await apiFetch(
        "/v1/projects/" + selectedProjectId + "/documents",
        token,
        { method: "POST", body: form }
      );
      await chooseProject(selectedProjectId);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : text("error"));
      setWorkspaceBusy(false);
    } finally {
      if (documentRef.current) documentRef.current.value = "";
    }
  };

  const deleteProjectDocument = async (documentId: string) => {
    if (!token || !selectedProjectId) return;
    await apiFetch(
      "/v1/projects/" + selectedProjectId + "/documents/" + documentId,
      token,
      { method: "DELETE" }
    );
    await chooseProject(selectedProjectId);
  };

  const startProjectChat = async () => {
    const project = projects.find((item) => item.id === selectedProjectId);
    if (!project) return;
    await createConversation(project.id, project.name);
    setWorkspaceOpen(false);
  };

  const exportWorkspace = async () => {
    if (!token) return;
    try {
      const data = await apiFetch<Record<string, unknown>>("/v1/export", token);
      const url = URL.createObjectURL(new Blob([
        JSON.stringify(data, null, 2)
      ], { type: "application/json" }));
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = "raise-workspace-export.json";
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : text("error"));
    }
  };

  const filteredConversations = useMemo(() => {
    const query = search.trim().toLocaleLowerCase(language);
    return conversations.filter((conversation) =>
      !conversation.archived &&
      (!query || conversation.title.toLocaleLowerCase(language).includes(query))
    );
  }, [conversations, language, search]);

  const stageLabel = statusStage === "generation"
    ? text("generation")
    : statusStage === "verification"
      ? text("verification")
      : text("analyzing");

  const clarificationIsComplete = (message: Message): boolean => {
    if (!message.interaction) return false;
    const answers = clarificationAnswers[message.id] || {};
    return clarificationQuestions(message.interaction).every((question) => {
      if (!question.required) return true;
      const answer = answers[question.id];
      return Array.isArray(answer)
        ? answer.some((value) => value.trim())
        : Boolean(String(answer || "").trim());
    });
  };


  const setClarificationAnswer = (
    messageId: string,
    questionId: string,
    value: string,
    multiple: boolean
  ) => {
    setClarificationAnswers((current) => {
      const form = current[messageId] || {};
      if (!multiple) {
        return { ...current, [messageId]: { ...form, [questionId]: value } };
      }
      const previous = Array.isArray(form[questionId]) ? form[questionId] as string[] : [];
      const selected = previous.includes(value)
        ? previous.filter((item) => item !== value)
        : [...previous, value];
      return { ...current, [messageId]: { ...form, [questionId]: selected } };
    });
  };

  const submitClarification = (message: Message) => {
    const interaction = message.interaction;
    if (!interaction) return;
    const questions = clarificationQuestions(interaction);
    const answers = clarificationAnswers[message.id] || {};
    const complete = questions.every((question) => (
      !question.required ||
      (Array.isArray(answers[question.id])
        ? (answers[question.id] as string[]).some((value) => value.trim())
        : Boolean(String(answers[question.id] || "").trim()))
    ));
    if (!complete) return;
    const summary = questions.map((question) => {
      const raw = answers[question.id];
      const answer = Array.isArray(raw) ? raw.join(", ") : String(raw || "");
      return question.prompt + ": " + answer;
    }).join("\n");
    const response = interaction.interaction_id
      ? {
          interaction_id: interaction.interaction_id,
          answers
        }
      : undefined;
    setCustomAnswerFor("");
    setClarificationAnswers((current) => {
      const next = { ...current };
      delete next[message.id];
      return next;
    });
    void submit(summary, response);
  };


  if (loading) {
    return (
      <main className="center-page" dir={rtl ? "rtl" : "ltr"}>
        <div className="brand-mark"><Leaf aria-hidden="true" /></div>
        <p>{text("loading")}</p>
      </main>
    );
  }

  if (!session && !LOCAL_AUTH) {
    return (
      <main className="auth-page" dir={rtl ? "rtl" : "ltr"}>
        <button
          className="language-switch auth-language"
          onClick={() => setLanguage(rtl ? "en" : "ar")}
          type="button"
        >
          <Globe2 aria-hidden="true" />
          {rtl ? "English" : "العربية"}
        </button>
        <section className="auth-card">
          <div className="brand-mark"><Leaf aria-hidden="true" /></div>
          <p className="eyebrow">{text("appName")}</p>
          <h1>{text("signInTitle")}</h1>
          <p>{text("signInBody")}</p>
          {error && <div className="error-banner" role="alert">{error}</div>}
          <button className="primary-button google-button" onClick={signIn} type="button">
            <span className="google-g">G</span>
            {text("signInGoogle")}
          </button>
          <small>{text("privacyNote")}</small>
        </section>
      </main>
    );
  }

  return (
    <div className="app-shell" dir={rtl ? "rtl" : "ltr"}>
      {mobileSidebar && (
        <button
          aria-label={text("close")}
          className="mobile-scrim"
          onClick={() => setMobileSidebar(false)}
          type="button"
        />
      )}
      <aside className={[
        "history-rail",
        sidebarOpen ? "" : "history-rail-collapsed",
        mobileSidebar ? "history-rail-mobile-open" : ""
      ].join(" ")}>
        <div className="rail-header">
          <div className="wordmark">
            <span className="brand-mark small"><Leaf aria-hidden="true" /></span>
            {sidebarOpen && <strong>RAISE</strong>}
          </div>
          <button
            aria-label={sidebarOpen ? text("close") : text("conversations")}
            className="icon-button desktop-only"
            onClick={() => setSidebarOpen((value) => !value)}
            type="button"
          >
            {sidebarOpen ? <PanelLeftClose /> : <PanelLeftOpen />}
          </button>
          <button
            aria-label={text("close")}
            className="icon-button mobile-only"
            onClick={() => setMobileSidebar(false)}
            type="button"
          >
            <X />
          </button>
        </div>
        <button
          className={sidebarOpen ? "new-chat-button" : "icon-button rail-new"}
          onClick={() => void createConversation()}
          type="button"
        >
          <MessageSquarePlus aria-hidden="true" />
          {sidebarOpen && <span>{text("newChat")}</span>}
        </button>
        <button
          className={sidebarOpen ? "workspace-button" : "icon-button rail-new"}
          onClick={openWorkspace}
          type="button"
        >
          <FolderKanban aria-hidden="true" />
          {sidebarOpen && <span>{text("workspace")}</span>}
        </button>
        {sidebarOpen && (
          <>
            <label className="search-box">
              <Search aria-hidden="true" />
              <input
                aria-label={text("search")}
                onChange={(event) => setSearch(event.target.value)}
                placeholder={text("search")}
                value={search}
              />
            </label>
            <button
              aria-controls="conversation-list"
              aria-expanded={conversationsOpen}
              className="rail-label rail-label-toggle"
              onClick={() => setConversationsOpen((value) => !value)}
              type="button"
            >
              <span>{text("conversations")}</span>
              <ChevronDown
                aria-label={
                  conversationsOpen
                    ? text("hideConversations")
                    : text("showConversations")
                }
                className={conversationsOpen ? "disclosure open" : "disclosure"}
              />
            </button>
            <nav
              aria-label={text("conversations")}
              className={
                conversationsOpen
                  ? "conversation-list"
                  : "conversation-list is-collapsed"
              }
              id="conversation-list"
            >
              {filteredConversations.length === 0 && (
                <p className="empty-rail">{text("noConversations")}</p>
              )}
              {filteredConversations.map((conversation) => (
                <div
                  className={[
                    "conversation-row",
                    activeId === conversation.id ? "active" : ""
                  ].join(" ")}
                  key={conversation.id}
                >
                  <button
                    className="conversation-title"
                    onClick={() => chooseConversation(conversation.id)}
                    type="button"
                  >
                    {conversation.title}
                  </button>
                  <details className="row-menu">
                    <summary aria-label={text("settings")}><Ellipsis /></summary>
                    <div className="menu-popover">
                      <button
                        onClick={() => {
                          setRenameValue(conversation.title);
                          setDialog({ kind: "rename", conversation });
                        }}
                        type="button"
                      >
                        <Pencil />{text("rename")}
                      </button>
                      <button
                        onClick={() => void updateConversation(conversation, { archived: true })}
                        type="button"
                      >
                        <Archive />{text("archive")}
                      </button>
                      <button
                        className="danger-text"
                        onClick={() => setDialog({ kind: "delete", conversation })}
                        type="button"
                      >
                        <Trash2 />{text("delete")}
                      </button>
                    </div>
                  </details>
                </div>
              ))}
            </nav>
          </>
        )}
        {sidebarOpen && (
          <div className="rail-account">
            <div className="avatar" aria-hidden="true">
              {(profile?.name || profile?.email || "R").slice(0, 1).toUpperCase()}
            </div>
            <div>
              <strong>{profile?.name || "RAISE"}</strong>
              <span>{profile?.email}</span>
            </div>
          </div>
        )}
      </aside>

      <main className="chat-column">
        <header className="top-bar">
          <button
            aria-label={text("conversations")}
            className="icon-button mobile-only"
            onClick={() => setMobileSidebar(true)}
            type="button"
          >
            <Menu />
          </button>
          <div className="top-title">
            <strong>{conversations.find((item) => item.id === activeId)?.title || text("newChat")}</strong>
            <span>{config.models.find((item) => item.id === modelId)?.label || "RAISE"}</span>
          </div>
          <div className="top-actions">
            <button
              className="language-switch"
              onClick={() => setLanguage(rtl ? "en" : "ar")}
              type="button"
            >
              <Globe2 aria-hidden="true" />
              {rtl ? "EN" : "ع"}
            </button>
            <button
              aria-label={text("settings")}
              className="icon-button"
              onClick={openSettings}
              type="button"
            >
              <Settings />
            </button>
          </div>
        </header>

        {error && (
          <div className="error-banner floating-error" role="alert">
            <span>{error}</span>
            <button aria-label={text("close")} onClick={() => setError("")} type="button">
              <X />
            </button>
          </div>
        )}

        {corpusWarningVisible && config.corpus_warning && (
          <div className="corpus-warning" role="status">
            <span>{config.corpus_warning[language]}</span>
            <button
              aria-label={text("close")}
              onClick={() => setCorpusWarningVisible(false)}
              type="button"
            >
              <X />
            </button>
          </div>
        )}

        <section className="message-scroll" aria-live="polite">
          {messages.length === 0 ? (
            <div className="welcome-panel">
              <div className="brand-mark"><Leaf aria-hidden="true" /></div>
              <h1>{text("welcome")}</h1>
              <p>{text("welcomeHint")}</p>
              <div className="suggestion-grid">
                {(rtl ? [
                  "كيف أجهّز أرض البطاطا في عكار قبل الزراعة؟",
                  "احسب لي كلفة مشروع زراعي صغير ونقطة التعادل.",
                  "لدي هذه الأعراض على النبات، ما المعلومات التي تحتاجها؟"
                ] : [
                  "How should I prepare a potato field in Akkar?",
                  "Help me estimate a small farm budget and break-even point.",
                  "My plant has these symptoms. What details do you need?"
                ]).map((suggestion) => (
                  <button key={suggestion} onClick={() => setComposer(suggestion)} type="button">
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="message-list">
              {messages.map((message, index) => (
                <article className={"message " + message.role} key={message.clientKey || message.id}>
                  <div className="message-avatar" aria-hidden="true">
                    {message.role === "assistant" ? <Leaf /> : (profile?.name || "U").slice(0, 1)}
                  </div>
                  <div className="message-body">
                    {message.attachments.filter((item) => item.kind === "image").map((attachment, attachmentIndex) => (
                      <div className="message-image-attachment" key={(attachment.storage_path || attachment.name || "image") + attachmentIndex}>
                        {attachment.preview_url ? (
                          <img alt={attachment.name || text("imageAttached")} src={attachment.preview_url} />
                        ) : (
                          <ImagePlus aria-hidden="true" />
                        )}
                        <span>{attachment.name || text("imageAttached")}</span>
                      </div>
                    ))}
                    <div className="markdown-body">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {message.content
                          ? withCitationMarkers(
                              message.revealChars === undefined
                                ? message.content
                                : message.content.slice(0, message.revealChars)
                            )
                          : ""}
                      </ReactMarkdown>
                    </div>
                    {message.pending && !message.content && (
                      <div aria-live="polite" className="thinking">
                        <span aria-hidden="true" className="thinking-dots">
                          <i /><i /><i />
                        </span>
                        <span className="thinking-copy">
                          <strong>{stageLabel}</strong>
                          <em key={thinkingIndex}>
                            {thinkingLines(language)[thinkingIndex]}
                          </em>
                        </span>
                      </div>
                    )}
                    {message.warning && (
                      <div className="warning-box"><strong>{text("warning")}</strong>{message.warning}</div>
                    )}
                    {message.citations.length > 0 && (
                      <details className="evidence-panel">
                        <summary><ChevronDown />{text("sources")} ({message.citations.length})</summary>
                        <ol>
                          {message.citations.map((citation, citationIndex) => (
                            <li
                              id={"cite-" + (citation.marker ?? citationIndex + 1)}
                              key={(citation.url || citation.item_id || "source") + citationIndex}
                            >
                              {citation.url ? (
                                <a href={citation.url} rel="noreferrer" target="_blank">
                                  {citation.title || citation.url}
                                </a>
                              ) : (
                                <span>{citation.title || citation.item_id || citation.document_id}</span>
                              )}
                              {citation.status && <small>{citation.status}</small>}
                            </li>
                          ))}
                        </ol>
                      </details>
                    )}
                    {message.artifact_ids && message.artifact_ids.length > 0 && (
                      <div className="artifact-actions">
                        {message.artifact_ids.map((artifactId, artifactIndex) => (
                          <button
                            key={artifactId}
                            onClick={() => void downloadPrivateFile(
                              "/v1/artifacts/" + artifactId + "/download",
                              token,
                              "RAISE-artifact-" + (artifactIndex + 1)
                            )}
                            type="button"
                          >
                            <Download />{text("download")} {artifactIndex + 1}
                          </button>
                        ))}
                      </div>
                    )}
                    {message.quickReplies && message.quickReplies.length > 0 &&
                      message.status !== "clarification" && !sending && (
                      <div className="quick-replies follow-up-replies">
                        {message.quickReplies.map((reply, replyIndex) => (
                          <button
                            key={replyIndex}
                            className="quick-reply-btn"
                            onClick={() => void submit(reply)}
                            type="button"
                          >
                            <span className="quick-reply-number">{replyIndex + 1}</span>
                            {reply}
                          </button>
                        ))}
                      </div>
                    )}
                    {message.interaction && message.status === "clarification" && (
                      <div
                        className={"clarification-form " + (
                          pendingClarificationId === message.id ? "active" : "resolved"
                        )}
                      >
                        {clarificationQuestions(message.interaction).map((question, questionIndex) => {
                          const formAnswers = clarificationAnswers[message.id] || {};
                          const answer = formAnswers[question.id];
                          const customKey = message.id + ":" + question.id;
                          const options = [
                            ...question.options,
                            ...(question.allow_other ? [{
                              id: question.id + "_other",
                              label: text("somethingElse"),
                              value: "",
                              kind: "other" as const
                            }] : [])
                          ];
                          return (
                            <fieldset key={question.id} disabled={pendingClarificationId !== message.id || sending}>
                              <legend>
                                <span>{questionIndex + 1}</span>
                                {question.prompt}
                              </legend>
                              {question.answer_type !== "text" && (
                                <div className="clarification-options">
                                  {options.map((option, optionIndex) => {
                                    const selected = option.kind !== "other" && (
                                      Array.isArray(answer)
                                        ? answer.includes(option.value)
                                        : answer === option.value
                                    );
                                    const otherSelected = option.kind === "other" &&
                                      customAnswerFor === customKey;
                                    return (
                                      <button
                                        aria-pressed={selected || otherSelected}
                                        className={"quick-reply-btn " + (
                                          selected || otherSelected ? "selected" : ""
                                        )}
                                        key={option.id}
                                        onClick={() => {
                                          if (option.kind === "other") {
                                            setCustomAnswerFor(customKey);
                                          } else {
                                            if (customAnswerFor === customKey) {
                                              setCustomAnswerFor("");
                                            }
                                            setClarificationAnswer(
                                              message.id,
                                              question.id,
                                              option.value,
                                              question.answer_type === "multiple"
                                            );
                                          }
                                        }}
                                        type="button"
                                      >
                                        <span className="quick-reply-number">{optionIndex + 1}</span>
                                        {option.label}
                                      </button>
                                    );
                                  })}
                                </div>
                              )}
                              {(question.answer_type === "text" || customAnswerFor === customKey) && (
                                <input
                                  autoFocus={customAnswerFor === customKey}
                                  className="clarification-text-answer"
                                  onChange={(event) => setClarificationAnswer(
                                    message.id,
                                    question.id,
                                    event.target.value,
                                    false
                                  )}
                                  placeholder={text("typeOwnOption")}
                                  value={Array.isArray(answer) ? answer.join(", ") : String(answer || "")}
                                />
                              )}
                            </fieldset>
                          );
                        })}
                        {pendingClarificationId === message.id && (
                          <button
                            className="clarification-submit"
                            disabled={!clarificationIsComplete(message) || sending}
                            onClick={() => submitClarification(message)}
                            type="button"
                          >
                            <Send />{text("submitAnswers")}
                          </button>
                        )}
                      </div>
                    )}
                    {message.role === "assistant" && message.content && (
                      <div className="message-actions">
                        <button onClick={() => void copyMessage(message)} type="button">
                          {copiedId === message.id ? <Check /> : <Clipboard />}
                          <span>{copiedId === message.id ? text("copied") : text("copy")}</span>
                        </button>
                        <button onClick={() => regenerate(index)} type="button">
                          <RefreshCw /><span>{text("regenerate")}</span>
                        </button>
                        <button
                          aria-label={text("helpful")}
                          aria-pressed={message.feedback === "helpful"}
                          className={message.feedback === "helpful" ? "feedback-active" : undefined}
                          disabled={message.feedbackPending}
                          onClick={() => void sendFeedback(message, true)}
                          type="button"
                        >
                          <ThumbsUp />
                        </button>
                        <button
                          aria-label={text("notHelpful")}
                          aria-pressed={message.feedback === "not_helpful"}
                          className={message.feedback === "not_helpful" ? "feedback-active" : undefined}
                          disabled={message.feedbackPending}
                          onClick={() => void sendFeedback(message, false)}
                          type="button"
                        >
                          <ThumbsDown />
                        </button>
                      </div>
                    )}
                  </div>
                </article>
              ))}

              <div ref={endRef} />
            </div>
          )}
        </section>

        <footer className="composer-area">
          {imagePreview && (
            <div className="image-preview">
              <img alt={imageFile?.name || text("imageAttached")} src={imagePreview} />
              <div>
                <strong>{imageFile?.name}</strong>
              </div>
              <button aria-label={text("delete")} onClick={removeImage} type="button"><X /></button>
            </div>
          )}
          <div className="composer-box">
            <textarea
              aria-label={text("composer")}
              disabled={sending}
              onChange={(event) => {
                setComposer(event.target.value);
                const element = textareaRef.current;
                if (element) {
                  element.style.height = "auto";
                  element.style.height = Math.min(element.scrollHeight, 180) + "px";
                }
              }}
              onKeyDown={(event) => {
                if (
                  event.key === "Enter" &&
                  !event.shiftKey &&
                  !event.nativeEvent.isComposing
                ) {
                  event.preventDefault();
                  void submit();
                }
              }}
              placeholder={text("composer")}
              ref={textareaRef}
              rows={1}
              value={composer}
            />
            <div className="composer-tools">
              <input
                accept="image/jpeg,image/png"
                className="visually-hidden"
                onChange={(event) => void handleImage(event.target.files?.[0])}
                ref={fileRef}
                type="file"
              />
              <button
                aria-label={text("attach")}
                className="icon-button"
                disabled={uploading || sending}
                onClick={() => fileRef.current?.click()}
                type="button"
              >
                <ImagePlus />
              </button>
              <div className="composer-mode-select">
                <select
                  aria-label={text("mode")}
                  disabled={sending}
                  onChange={(event) => setMode(event.target.value)}
                  value={mode}
                >
                  {config.modes.map((item) => (
                    <option key={item.id} value={item.id}>
                      {rtl ? item.label_ar : item.label_en}
                    </option>
                  ))}
                </select>
                <ChevronDown aria-hidden="true" />
              </div>
              <span className="composer-spacer" />
              {sending ? (
                <button
                  aria-label={text("stop")}
                  className="send-button stop-button"
                  onClick={stop}
                  type="button"
                >
                  <CircleStop />
                </button>
              ) : (
                <button
                  aria-label={text("send")}
                  className="send-button"
                  disabled={(!composer.trim() && !imageId) || uploading}
                  onClick={() => void submit()}
                  type="button"
                >
                  <Send />
                </button>
              )}
            </div>
          </div>
          <p className="composer-note">{text("disclaimer")}</p>
        </footer>
      </main>

      {workspaceOpen && (
        <div className="modal-layer" onMouseDown={() => setWorkspaceOpen(false)} role="presentation">
          <section
            aria-labelledby="workspace-title"
            aria-modal="true"
            className="modal-card workspace-modal"
            onMouseDown={(event) => event.stopPropagation()}
            role="dialog"
          >
            <div className="modal-header">
              <div>
                <p className="eyebrow">RAISE</p>
                <h2 id="workspace-title">{text("workspace")}</h2>
              </div>
              <button aria-label={text("close")} className="icon-button" onClick={() => setWorkspaceOpen(false)} type="button">
                <X />
              </button>
            </div>
            <div className="workspace-grid">
              <aside className="project-panel">
                <h3>{text("projects")}</h3>
                <div className="project-create">
                  <input
                    aria-label={text("projectName")}
                    maxLength={100}
                    onChange={(event) => setProjectName(event.target.value)}
                    placeholder={text("projectName")}
                    value={projectName}
                  />
                  <textarea
                    aria-label={text("projectInstructions")}
                    maxLength={5000}
                    onChange={(event) => setProjectInstructions(event.target.value)}
                    placeholder={text("projectInstructions")}
                    rows={3}
                    value={projectInstructions}
                  />
                  <button className="primary-button" disabled={!projectName.trim() || workspaceBusy} onClick={() => void createProject()} type="button">
                    <FolderKanban />{text("createProject")}
                  </button>
                </div>
                <nav className="project-list" aria-label={text("projects")}>
                  {projects.length === 0 && <p>{text("noItems")}</p>}
                  {projects.map((project) => (
                    <button
                      className={selectedProjectId === project.id ? "selected" : ""}
                      key={project.id}
                      onClick={() => void chooseProject(project.id)}
                      type="button"
                    >
                      <FolderKanban />
                      <span><strong>{project.name}</strong><small>{project.instructions}</small></span>
                    </button>
                  ))}
                </nav>
              </aside>
              <div className="workspace-detail">
                {selectedProjectId ? (
                  <>
                    <div className="workspace-detail-header">
                      <div>
                        <h3>{projects.find((item) => item.id === selectedProjectId)?.name}</h3>
                        <p>{projects.find((item) => item.id === selectedProjectId)?.instructions}</p>
                      </div>
                      <div className="workspace-inline-actions">
                        <button className="secondary-button" onClick={() => void startProjectChat()} type="button">
                          <MessageSquarePlus />{text("projectChat")}
                        </button>
                        <button
                          aria-label={text("delete")}
                          className="icon-button danger-text"
                          onClick={() => {
                            if (window.confirm(text("deleteConfirm"))) void deleteProject(selectedProjectId);
                          }}
                          type="button"
                        >
                          <Trash2 />
                        </button>
                      </div>
                    </div>
                    <section className="workspace-section">
                      <div className="workspace-section-title">
                        <h4><FileText />{text("documents")}</h4>
                        <input
                          accept=".pdf,.docx,.txt,.csv,.xlsx"
                          className="visually-hidden"
                          onChange={(event) => void uploadProjectDocument(event.target.files?.[0])}
                          ref={documentRef}
                          type="file"
                        />
                        <button className="secondary-button" disabled={workspaceBusy} onClick={() => documentRef.current?.click()} type="button">
                          <Upload />{text("uploadDocument")}
                        </button>
                      </div>
                      {projectDocuments.length === 0 ? <p>{text("noItems")}</p> : (
                        <div className="workspace-file-list">
                          {projectDocuments.map((document) => (
                            <div key={document.id}>
                              <FileText />
                              <span><strong>{document.filename}</strong><small>{Math.ceil(document.size_bytes / 1024)} KB</small></span>
                              <button aria-label={text("download")} className="icon-button" onClick={() => void downloadPrivateFile(
                                "/v1/projects/" + selectedProjectId + "/documents/" + document.id + "/download",
                                token,
                                document.filename
                              )} type="button"><Download /></button>
                              <button
                                aria-label={text("delete")}
                                className="icon-button danger-text"
                                onClick={() => {
                                  if (window.confirm(text("deleteConfirm"))) void deleteProjectDocument(document.id);
                                }}
                                type="button"
                              ><Trash2 /></button>
                            </div>
                          ))}
                        </div>
                      )}
                    </section>
                    <section className="workspace-section">
                      <div className="workspace-section-title"><h4><Download />{text("artifacts")}</h4></div>
                      {artifacts.filter((item) => item.project_id === selectedProjectId).length === 0 ? <p>{text("noItems")}</p> : (
                        <div className="workspace-file-list">
                          {artifacts.filter((item) => item.project_id === selectedProjectId).map((artifact) => (
                            <div key={artifact.id}>
                              <FileText />
                              <span><strong>{artifact.filename}</strong><small>{artifact.artifact_type}</small></span>
                              <button aria-label={text("download")} className="icon-button" onClick={() => void downloadPrivateFile(
                                "/v1/artifacts/" + artifact.id + "/download",
                                token,
                                artifact.filename
                              )} type="button"><Download /></button>
                            </div>
                          ))}
                        </div>
                      )}
                    </section>
                  </>
                ) : (
                  <div className="workspace-empty"><FolderKanban /><p>{text("noItems")}</p></div>
                )}
              </div>
            </div>
            <div className="workspace-footer">
              <button className="secondary-button" onClick={() => void exportWorkspace()} type="button">
                <DatabaseBackup />{text("exportData")}
              </button>
              {workspaceBusy && <span>{text("loading")}</span>}
            </div>
          </section>
        </div>
      )}

      {agreementOpen && (
        <div className="modal-layer" role="presentation">
          <section
            aria-labelledby="agreement-title"
            aria-modal="true"
            className="modal-card agreement-modal"
            role="dialog"
          >
            <div className="modal-header">
              <h2 id="agreement-title">{text("agreementTitle")}</h2>
            </div>
            <div className="agreement-copy">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{agreement}</ReactMarkdown>
            </div>
            {error && <div className="error-banner" role="alert">{error}</div>}
            <div className="modal-actions">
              <button className="secondary-button" onClick={() => void signOut()} type="button">
                {text("agreementReject")}
              </button>
              <button className="primary-button" onClick={() => void acceptAgreement()} type="button">
                {text("agreementAccept")}
              </button>
            </div>
          </section>
        </div>
      )}

      {settingsOpen && (
        <div className="modal-layer" onMouseDown={closeSettings} role="presentation">
          <section
            aria-labelledby="settings-title"
            aria-modal="true"
            className="modal-card settings-modal"
            onMouseDown={(event) => event.stopPropagation()}
            role="dialog"
          >
            <div className="modal-header">
              <h2 id="settings-title">{text("settings")}</h2>
              <button aria-label={text("close")} className="icon-button" onClick={closeSettings} type="button">
                <X />
              </button>
            </div>
            <div className="settings-section">
              <label>{text("language")}</label>
              <div className="segmented-control">
                <button className={settingsDraft.language === "ar" ? "selected" : ""} onClick={() => setSettingsDraft((draft) => ({ ...draft, language: "ar" }))} type="button">
                  العربية
                </button>
                <button className={settingsDraft.language === "en" ? "selected" : ""} onClick={() => setSettingsDraft((draft) => ({ ...draft, language: "en" }))} type="button">
                  English
                </button>
              </div>
            </div>
            <div className="settings-section">
              <label htmlFor="mode-select">{text("mode")}</label>
              <div className="select-control">
                <select id="mode-select" onChange={(event) => setSettingsDraft((draft) => ({ ...draft, mode: event.target.value }))} value={settingsDraft.mode}>
                  {config.modes.map((item) => (
                    <option key={item.id} value={item.id}>
                      {settingsDraft.language === "ar" ? item.label_ar : item.label_en}
                    </option>
                  ))}
                </select>
                <ChevronDown aria-hidden="true" />
              </div>
            </div>
            <div className="settings-section">
              <label htmlFor="model-select">{text("model")}</label>
              <div className="select-control">
                <select id="model-select" onChange={(event) => setSettingsDraft((draft) => ({ ...draft, modelId: event.target.value }))} value={settingsDraft.modelId}>
                  {config.models.map((item) => (
                    <option key={item.id} value={item.id}>{item.label}</option>
                  ))}
                </select>
                <ChevronDown aria-hidden="true" />
              </div>
              <small>{config.models.find((item) => item.id === settingsDraft.modelId)?.description}</small>
            </div>
            <div className="settings-section">
              <label htmlFor="clarification-select">{text("clarification")}</label>
              <div className="select-control">
                <select
                  id="clarification-select"
                  onChange={(event) => setSettingsDraft((draft) => ({ ...draft, clarificationStyle: event.target.value }))}
                  value={settingsDraft.clarificationStyle}
                >
                  <option value="auto">{text("auto")}</option>
                  <option value="guided">{text("guided")}</option>
                  <option value="direct">{text("direct")}</option>
                </select>
                <ChevronDown aria-hidden="true" />
              </div>
            </div>
            {usage && (
              <div className="settings-section usage-section">
                <label>{text("weeklyUsage")}</label>
                <div className="usage-bar" role="progressbar" aria-valuemin={0} aria-valuemax={usage.weekly_limit_usd} aria-valuenow={Math.min(usage.weekly_spend_usd, usage.weekly_limit_usd)}>
                  <div
                    className="usage-bar-fill"
                    style={{
                      width: Math.min(
                        100,
                        (usage.weekly_spend_usd / Math.max(usage.weekly_limit_usd, 0.01)) * 100
                      ) + "%"
                    }}
                  />
                </div>
                <p>${usage.weekly_spend_usd.toFixed(2)} / ${usage.weekly_limit_usd.toFixed(2)}</p>
                <small>{text("weeklyUsageHint")}</small>
              </div>
            )}
            <div className="settings-section account-section">
              <label>{text("account")}</label>
              <p>{profile?.email}</p>
              <button className="secondary-button" onClick={() => void signOut()} type="button">
                <LogOut />{text("logout")}
              </button>
              <button
                className="danger-button"
                onClick={() => {
                  setSettingsOpen(false);
                  setDialog({ kind: "delete-account" });
                }}
                type="button"
              >
                <Trash2 />{text("deleteAccount")}
              </button>
            </div>
            <div className="settings-actions">
              <button className="secondary-button" onClick={closeSettings} type="button">
                {text("cancel")}
              </button>
              <button className="primary-button" onClick={saveSettings} type="button">
                <Check />{text("saveChanges")}
              </button>
            </div>
          </section>
        </div>
      )}

      {dialog && (
        <div className="modal-layer" onMouseDown={() => setDialog(null)} role="presentation">
          <section
            aria-modal="true"
            className="modal-card confirm-modal"
            onMouseDown={(event) => event.stopPropagation()}
            role="dialog"
          >
            <div className="modal-header">
              <h2>
                {dialog.kind === "rename"
                  ? text("rename")
                  : dialog.kind === "delete-account"
                    ? text("deleteAccount")
                    : text("delete")}
              </h2>
              <button aria-label={text("close")} className="icon-button" onClick={() => setDialog(null)} type="button">
                <X />
              </button>
            </div>
            {dialog.kind === "rename" ? (
              <input
                autoFocus
                className="dialog-input"
                maxLength={120}
                onChange={(event) => setRenameValue(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && renameValue.trim()) {
                    void updateConversation(dialog.conversation, { title: renameValue.trim() });
                  }
                }}
                value={renameValue}
              />
            ) : (
              <p>
                {dialog.kind === "delete-account"
                  ? text("deleteAccountConfirm")
                  : text("deleteConfirm")}
              </p>
            )}
            <div className="modal-actions">
              <button className="secondary-button" onClick={() => setDialog(null)} type="button">
                {text("close")}
              </button>
              {dialog.kind === "rename" ? (
                <button
                  className="primary-button"
                  disabled={!renameValue.trim()}
                  onClick={() => void updateConversation(dialog.conversation, { title: renameValue.trim() })}
                  type="button"
                >
                  {text("rename")}
                </button>
              ) : (
                <button
                  className="danger-button"
                  onClick={() => dialog.kind === "delete-account"
                    ? void deleteAccount()
                    : void deleteConversation(dialog.conversation)}
                  type="button"
                >
                  <Trash2 />
                  {dialog.kind === "delete-account" ? text("deleteAccount") : text("delete")}
                </button>
              )}
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
