"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  useSyncExternalStore,
  type ReactNode
} from "react";

import { apiFetch } from "@/lib/api";
import { beginLogin, endSession, loadAuthSession, type BrowserSession } from "@/lib/auth";
import { t, type CopyKey } from "@/lib/i18n";
import type { AppConfig, CurrentUser, Language, UsageSummary } from "@/lib/types";

export const LOCAL_AUTH = process.env.NEXT_PUBLIC_LOCAL_AUTH === "true";

const EMPTY_CONFIG: AppConfig = {
  app_name: "RAISE",
  agreement_version: "",
  default_language: "ar",
  modes: [],
  models: []
};

type Phase = "loading" | "signed-out" | "consent" | "ready" | "error";

interface AppState {
  phase: Phase;
  language: Language;
  setLanguage: (language: Language) => void;
  text: (key: CopyKey) => string;
  token: string;
  session: BrowserSession | null;
  profile: CurrentUser | null;
  isAdmin: boolean;
  config: AppConfig;
  agreement: string;
  usage: UsageSummary | null;
  refreshUsage: () => Promise<void>;
  mode: string;
  setMode: (mode: string) => void;
  modelId: string;
  setModelId: (modelId: string) => void;
  clarificationStyle: string;
  setClarificationStyle: (style: string) => void;
  error: string;
  setError: (message: string) => void;
  signIn: () => void;
  signOut: () => Promise<void>;
  acceptAgreement: () => Promise<void>;
  retry: () => void;
}

const AppStateContext = createContext<AppState | null>(null);

export function useAppState(): AppState {
  const value = useContext(AppStateContext);
  if (!value) throw new Error("useAppState must be used inside AppStateProvider");
  return value;
}

function readStored(key: string): string {
  try {
    return localStorage.getItem(key) || "";
  } catch {
    return "";
  }
}

function subscribeStorage(callback: () => void): () => void {
  window.addEventListener("storage", callback);
  return () => window.removeEventListener("storage", callback);
}

function writeStored(key: string, value: string): void {
  try {
    localStorage.setItem(key, value);
  } catch {
    // Preferences are a convenience; private browsing must still work.
  }
}

export function AppStateProvider({ children }: { children: ReactNode }) {
  // The server and the first client render agree on Arabic; the stored
  // choice applies immediately after hydration without a mismatch.
  const storedLanguage = useSyncExternalStore(
    subscribeStorage,
    () => readStored("raise-language"),
    () => ""
  );
  const [chosenLanguage, setChosenLanguage] = useState<Language | null>(null);
  const language: Language = chosenLanguage ?? (storedLanguage === "en" ? "en" : "ar");
  const [session, setSession] = useState<BrowserSession | null>(null);
  const [sessionChecked, setSessionChecked] = useState(LOCAL_AUTH);
  const [profile, setProfile] = useState<CurrentUser | null>(null);
  const [config, setConfig] = useState<AppConfig>(EMPTY_CONFIG);
  const [agreement, setAgreement] = useState("");
  const [usage, setUsage] = useState<UsageSummary | null>(null);
  const [mode, setModeState] = useState("standard");
  const [modelId, setModelIdState] = useState("");
  const [clarificationStyle, setClarificationStyleState] = useState("auto");
  const [boot, setBoot] = useState<{ key: string; phase: Phase }>({ key: "", phase: "loading" });
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);

  const token = LOCAL_AUTH ? "local-development" : session?.csrf_token || "";
  const text = useCallback((key: CopyKey) => t(language, key), [language]);

  const bootKey = `${token}|${attempt}`;
  const phase: Phase = !sessionChecked
    ? "loading"
    : !token
      ? "signed-out"
      : boot.key === bootKey
        ? boot.phase
        : "loading";

  useEffect(() => {
    document.documentElement.lang = language;
    document.documentElement.dir = language === "ar" ? "rtl" : "ltr";
  }, [language]);

  const setLanguage = useCallback((next: Language) => {
    setChosenLanguage(next);
    writeStored("raise-language", next);
  }, []);
  const setMode = useCallback((next: string) => {
    setModeState(next);
    writeStored("raise-mode", next);
  }, []);
  const setModelId = useCallback((next: string) => {
    setModelIdState(next);
    writeStored("raise-model", next);
  }, []);
  const setClarificationStyle = useCallback((next: string) => {
    setClarificationStyleState(next);
    writeStored("raise-clarification", next);
  }, []);

  useEffect(() => {
    if (LOCAL_AUTH) return;
    let active = true;
    loadAuthSession()
      .then((next) => {
        if (!active) return;
        setSession(next);
        setSessionChecked(true);
      })
      .catch(() => {
        if (!active) return;
        setSessionChecked(true);
      });
    return () => {
      active = false;
    };
  }, []);

  const refreshUsage = useCallback(async () => {
    if (!token) return;
    try {
      setUsage(await apiFetch<UsageSummary>("/v1/usage", token));
    } catch {
      // Usage is informational; a failed refresh must not block chat.
    }
  }, [token]);

  useEffect(() => {
    if (!sessionChecked || !token) return;
    let active = true;
    (async () => {
      try {
        const [appConfig, user] = await Promise.all([
          apiFetch<AppConfig>("/v1/config", token),
          apiFetch<CurrentUser>("/v1/me", token)
        ]);
        if (!active) return;
        setConfig(appConfig);
        setProfile(user);
        const storedMode = readStored("raise-mode");
        setModeState(
          appConfig.modes.some((item) => item.id === storedMode)
            ? storedMode
            : user.default_mode || "standard"
        );
        const storedModel = readStored("raise-model");
        setModelIdState(
          appConfig.models.some((item) => item.id === storedModel)
            ? storedModel
            : appConfig.models[0]?.id || ""
        );
        const storedStyle = readStored("raise-clarification");
        if (["auto", "guided", "direct"].includes(storedStyle)) {
          setClarificationStyleState(storedStyle);
        }
        if (!user.consent_current) {
          const legal = await apiFetch<{ markdown: string }>(
            "/v1/legal/agreement?language=" + language,
            token
          );
          if (!active) return;
          setAgreement(legal.markdown);
          setBoot({ key: bootKey, phase: "consent" });
          return;
        }
        setBoot({ key: bootKey, phase: "ready" });
        void refreshUsage();
      } catch (caught) {
        if (!active) return;
        setError(caught instanceof Error ? caught.message : t(language, "error"));
        setBoot({ key: bootKey, phase: "error" });
      }
    })();
    return () => {
      active = false;
    };
    // `language` only selects the agreement text; changing it later must not
    // re-run the whole bootstrap.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionChecked, token, bootKey, refreshUsage]);

  const acceptAgreement = useCallback(async () => {
    if (!token) return;
    try {
      await apiFetch("/v1/consent", token, { method: "POST" });
      setProfile((value) => (value ? { ...value, consent_current: true } : value));
      setBoot({ key: bootKey, phase: "ready" });
      void refreshUsage();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : t(language, "error"));
    }
  }, [bootKey, language, refreshUsage, token]);

  const signOut = useCallback(async () => {
    if (LOCAL_AUTH) return;
    await endSession(token);
    setSession(null);
    setProfile(null);
  }, [token]);

  const value = useMemo<AppState>(
    () => ({
      phase,
      language,
      setLanguage,
      text,
      token,
      session,
      profile,
      isAdmin: Boolean(session?.identity?.is_admin || profile?.role === "admin"),
      config,
      agreement,
      usage,
      refreshUsage,
      mode,
      setMode,
      modelId,
      setModelId,
      clarificationStyle,
      setClarificationStyle,
      error,
      setError,
      signIn: beginLogin,
      signOut,
      acceptAgreement,
      retry: () => {
        setError("");
        setAttempt((value) => value + 1);
      }
    }),
    [
      acceptAgreement,
      agreement,
      clarificationStyle,
      config,
      error,
      language,
      mode,
      modelId,
      phase,
      profile,
      refreshUsage,
      session,
      setClarificationStyle,
      setLanguage,
      setMode,
      setModelId,
      signOut,
      text,
      token,
      usage
    ]
  );

  return <AppStateContext.Provider value={value}>{children}</AppStateContext.Provider>;
}
