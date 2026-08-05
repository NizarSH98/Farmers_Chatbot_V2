"use client";
/* eslint-disable @next/next/no-img-element -- local object URL preview is not a deployable image asset */

import type { Session } from "@supabase/supabase-js";
import {
  Archive,
  Check,
  ChevronDown,
  CircleStop,
  Clipboard,
  Ellipsis,
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
  X
} from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { ApiError, apiFetch, streamTurn, uploadImage } from "@/lib/api";
import { t } from "@/lib/i18n";
import { supabaseBrowser } from "@/lib/supabase";
import type {
  AppConfig,
  Citation,
  Conversation,
  CurrentUser,
  Language,
  Message,
  TurnPayload,
  UsageSummary
} from "@/lib/types";

type DialogState =
  | { kind: "rename"; conversation: Conversation }
  | { kind: "delete"; conversation: Conversation }
  | { kind: "delete-account" }
  | null;

const initialConfig: AppConfig = {
  app_name: "RAISE",
  agreement_version: "",
  default_language: "ar",
  modes: [],
  models: []
};

export function ChatWorkspace() {
  const [language, setLanguage] = useState<Language>("ar");
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
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [statusStage, setStatusStage] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileSidebar, setMobileSidebar] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [agreement, setAgreement] = useState("");
  const [agreementOpen, setAgreementOpen] = useState(false);
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
  const abortRef = useRef<AbortController | null>(null);
  const endRef = useRef<HTMLDivElement | null>(null);
  const fileRef = useRef<HTMLInputElement | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  const token = session?.access_token || "";
  const rtl = language === "ar";
  const text = useCallback(
    (key: Parameters<typeof t>[1]) => t(language, key),
    [language]
  );

  useEffect(() => {
    const supabase = supabaseBrowser();
    supabase.auth.getSession().then(({ data }) => {
      const saved = localStorage.getItem("raise-language");
      if (saved === "en" || saved === "ar") setLanguage(saved);
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

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, statusStage]);

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
        const items = await loadConversations(token);
        if (items[0]) setActiveId((value) => value || items[0].id);
        void loadUsage(token);
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : text("error"));
    } finally {
      setLoading(false);
    }
  }, [language, loadConversations, loadUsage, text, token]);

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
      .then((result) => setMessages(result.items))
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
    await supabaseBrowser().auth.signOut();
  };

  const acceptAgreement = async () => {
    if (!token) return;
    setError("");
    try {
      await apiFetch("/v1/consent", token, { method: "POST" });
      setAgreementOpen(false);
      setProfile((value) => value ? { ...value, consent_current: true } : value);
      const items = await loadConversations(token);
      if (items[0]) setActiveId(items[0].id);
      void loadUsage(token);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : text("error"));
    }
  };

  const createConversation = async () => {
    if (!token) return null;
    const created = await apiFetch<Conversation>("/v1/conversations", token, {
      method: "POST",
      body: JSON.stringify({ title: text("newChat") })
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

  const handleImage = async (file?: File) => {
    if (!file || !token) return;
    setUploading(true);
    setError("");
    try {
      const uploaded = await uploadImage(file, token);
      if (imagePreview) URL.revokeObjectURL(imagePreview);
      setImageFile(file);
      setImageId(uploaded.id);
      setImagePreview(URL.createObjectURL(file));
    } catch {
      setError(text("uploadError"));
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const removeImage = () => {
    if (imagePreview) URL.revokeObjectURL(imagePreview);
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
      item.id === id ? { ...item, content: item.content + delta } : item
    ));
  };

  const submit = async (override?: string) => {
    if (!token || sending) return;
    const question = (override ?? composer).trim();
    if (!question) return;
    setError("");
    setSending(true);
    setStatusStage("analysis_and_retrieval");
    let conversationId = activeId;
    try {
      if (!conversationId) conversationId = await createConversation();
      if (!conversationId) throw new Error(text("error"));
      const userId = crypto.randomUUID();
      const assistantId = crypto.randomUUID();
      const now = new Date().toISOString();
      const optimisticUser: Message = {
        id: userId,
        role: "user",
        content: question,
        status: "complete",
        citations: [],
        tools: [],
        attachments: imageFile ? [{ kind: "image", mime_type: imageFile.type }] : [],
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
      setMessages((items) => [...items, optimisticUser, optimisticAssistant]);
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
        attachment_ids: imageId ? [imageId] : []
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
          const options = Array.isArray(event.data.options) ? event.data.options.map(String) : [];
          patchPending(assistantId, {
            content: String(event.data.content || ""),
            status: "clarification",
            quickReplies: options.length > 0 ? options : undefined
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
      removeImage();
    } catch (caught) {
      if (caught instanceof DOMException && caught.name === "AbortError") {
        setMessages((items) => items.map((item) =>
          item.pending ? { ...item, pending: false, status: "cancelled" } : item
        ));
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

  if (loading) {
    return (
      <main className="center-page" dir={rtl ? "rtl" : "ltr"}>
        <div className="brand-mark"><Leaf aria-hidden="true" /></div>
        <p>{text("loading")}</p>
      </main>
    );
  }

  if (!session) {
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
            <p className="rail-label">{text("conversations")}</p>
            <nav aria-label={text("conversations")} className="conversation-list">
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
              onClick={() => setSettingsOpen(true)}
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
                    {message.attachments.some((item) => item.kind === "image") && (
                      <span className="attachment-chip"><ImagePlus />{text("imageReady")}</span>
                    )}
                    <div className="markdown-body">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {message.content || (message.pending ? stageLabel : "")}
                      </ReactMarkdown>
                    </div>
                    {message.warning && (
                      <div className="warning-box"><strong>{text("warning")}</strong>{message.warning}</div>
                    )}
                    {message.citations.length > 0 && (
                      <details className="evidence-panel">
                        <summary><ChevronDown />{text("sources")} ({message.citations.length})</summary>
                        <ol>
                          {message.citations.map((citation, citationIndex) => (
                            <li key={(citation.url || citation.item_id || "source") + citationIndex}>
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
                    {message.quickReplies && message.quickReplies.length > 0 && !sending && (
                      <div className="quick-replies">
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
              {sending && statusStage && (
                <div className="stage-indicator"><span />{stageLabel}</div>
              )}
              <div ref={endRef} />
            </div>
          )}
        </section>

        <footer className="composer-area">
          {imagePreview && (
            <div className="image-preview">
              <img alt={imageFile?.name || text("imageReady")} src={imagePreview} />
              <div>
                <strong>{imageFile?.name}</strong>
                <span>{text("imageReady")}</span>
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
              <button
                className="mode-pill"
                onClick={() => setSettingsOpen(true)}
                type="button"
              >
                {config.modes.find((item) => item.id === mode)?.[
                  rtl ? "label_ar" : "label_en"
                ] || mode}
              </button>
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
                  disabled={!composer.trim() || uploading}
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
        <div className="modal-layer" onMouseDown={() => setSettingsOpen(false)} role="presentation">
          <section
            aria-labelledby="settings-title"
            aria-modal="true"
            className="modal-card settings-modal"
            onMouseDown={(event) => event.stopPropagation()}
            role="dialog"
          >
            <div className="modal-header">
              <h2 id="settings-title">{text("settings")}</h2>
              <button aria-label={text("close")} className="icon-button" onClick={() => setSettingsOpen(false)} type="button">
                <X />
              </button>
            </div>
            <div className="settings-section">
              <label>{text("language")}</label>
              <div className="segmented-control">
                <button className={rtl ? "selected" : ""} onClick={() => setLanguage("ar")} type="button">
                  العربية
                </button>
                <button className={!rtl ? "selected" : ""} onClick={() => setLanguage("en")} type="button">
                  English
                </button>
              </div>
            </div>
            <div className="settings-section">
              <label htmlFor="mode-select">{text("mode")}</label>
              <select id="mode-select" onChange={(event) => setMode(event.target.value)} value={mode}>
                {config.modes.map((item) => (
                  <option key={item.id} value={item.id}>
                    {rtl ? item.label_ar : item.label_en}
                  </option>
                ))}
              </select>
            </div>
            <div className="settings-section">
              <label htmlFor="model-select">{text("model")}</label>
              <select id="model-select" onChange={(event) => { setModelId(event.target.value); localStorage.setItem("raise-model", event.target.value); }} value={modelId}>
                {config.models.map((item) => (
                  <option key={item.id} value={item.id}>{item.label}</option>
                ))}
              </select>
              <small>{config.models.find((item) => item.id === modelId)?.description}</small>
            </div>
            <div className="settings-section">
              <label htmlFor="clarification-select">{text("clarification")}</label>
              <select
                id="clarification-select"
                onChange={(event) => setClarificationStyle(event.target.value)}
                value={clarificationStyle}
              >
                <option value="auto">{text("auto")}</option>
                <option value="guided">{text("guided")}</option>
                <option value="direct">{text("direct")}</option>
              </select>
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
