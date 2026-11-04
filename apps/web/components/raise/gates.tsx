"use client";

import { LanguagesIcon, Loader2Icon, LogOutIcon, RotateCwIcon, ShieldCheckIcon } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { Button } from "@/components/ui/button";

import { useAppState } from "./app-state";
import { BrandMark } from "./brand";

function LanguageToggle() {
  const { language, setLanguage } = useAppState();
  return (
    <Button
      variant="ghost"
      size="sm"
      className="text-muted-foreground absolute end-4 top-4"
      onClick={() => setLanguage(language === "ar" ? "en" : "ar")}
    >
      <LanguagesIcon />
      {language === "ar" ? "English" : "العربية"}
    </Button>
  );
}

function GoogleGlyph() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="size-4">
      <path fill="#4285F4" d="M22.6 12.3c0-.8-.1-1.6-.2-2.3H12v4.3h5.9a5 5 0 0 1-2.2 3.3v2.8h3.6c2.1-2 3.3-4.8 3.3-8.1Z" />
      <path fill="#34A853" d="M12 23c3 0 5.5-1 7.3-2.7l-3.6-2.8c-1 .7-2.2 1-3.7 1-2.8 0-5.2-1.9-6.1-4.5H2.2v2.9A11 11 0 0 0 12 23Z" />
      <path fill="#FBBC05" d="M5.9 14a6.6 6.6 0 0 1 0-4.1V7H2.2a11 11 0 0 0 0 9.9L5.9 14Z" />
      <path fill="#EA4335" d="M12 5.4c1.6 0 3 .6 4.1 1.6l3.1-3.1A11 11 0 0 0 2.2 7l3.7 2.9C6.8 7.3 9.2 5.4 12 5.4Z" />
    </svg>
  );
}

export function LoadingScreen() {
  const { text } = useAppState();
  return (
    <main className="bg-background flex min-h-svh flex-col items-center justify-center gap-4">
      <BrandMark size="lg" className="animate-in fade-in zoom-in-95 duration-500" />
      <p className="text-muted-foreground flex items-center gap-2 text-sm">
        <Loader2Icon className="size-4 animate-spin" />
        {text("loading")}
      </p>
    </main>
  );
}

export function SignInScreen() {
  const { text, signIn } = useAppState();
  return (
    <main className="bg-background relative flex min-h-svh items-center justify-center px-4 py-16">
      <LanguageToggle />
      <div className="animate-in fade-in slide-in-from-bottom-2 flex w-full max-w-sm flex-col items-center text-center duration-500">
        <BrandMark size="lg" />
        <h1 className="text-foreground mt-6 text-3xl font-semibold tracking-tight">{text("signInTitle")}</h1>
        <p className="text-muted-foreground mt-3 text-[0.95rem] leading-relaxed">{text("signInBody")}</p>
        <Button size="lg" className="mt-8 h-11 w-full gap-2.5 text-[0.95rem]" onClick={signIn}>
          <span className="flex size-6 items-center justify-center rounded-full bg-white">
            <GoogleGlyph />
          </span>
          {text("signInGoogle")}
        </Button>
        <p className="text-muted-foreground mt-5 flex items-start gap-2 text-start text-xs leading-relaxed">
          <ShieldCheckIcon className="text-leaf mt-0.5 size-4 shrink-0" />
          {text("privacyNote")}
        </p>
      </div>
    </main>
  );
}

export function ConsentScreen() {
  const { text, agreement, acceptAgreement, signOut, error } = useAppState();
  return (
    <main className="bg-background relative flex min-h-svh items-center justify-center px-4 pt-16 pb-6 sm:py-12">
      <LanguageToggle />
      <div className="bg-card border-border animate-in fade-in slide-in-from-bottom-2 flex max-h-[calc(100svh-6rem)] w-full max-w-2xl flex-col sm:max-h-[85svh] rounded-3xl border shadow-sm duration-500">
        <div className="flex items-center gap-3 border-b px-6 py-5">
          <BrandMark size="sm" />
          <h1 className="text-lg font-semibold">{text("agreementTitle")}</h1>
        </div>
        {/* Native scrolling: the agreement must stay inside the card so the
            accept button is always visible and clickable. */}
        <div
          tabIndex={0}
          role="region"
          aria-label={text("agreementTitle")}
          className="focus-visible:ring-ring/50 min-h-0 flex-1 overflow-y-auto overscroll-contain px-6 outline-none focus-visible:ring-2 focus-visible:ring-inset"
        >
          <div className="prose-raise text-foreground/90 py-5 text-sm leading-relaxed [&_h1]:mb-3 [&_h1]:text-lg [&_h1]:font-semibold [&_h2]:mt-5 [&_h2]:mb-2 [&_h2]:font-semibold [&_li]:ms-5 [&_li]:list-disc [&_p]:mb-3">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{agreement}</ReactMarkdown>
          </div>
        </div>
        {error && <p className="text-destructive px-6 pb-2 text-sm">{error}</p>}
        <div className="flex flex-col-reverse gap-2 border-t px-6 py-4 sm:flex-row sm:justify-end">
          <Button variant="ghost" onClick={() => void signOut()}>
            <LogOutIcon />
            {text("agreementReject")}
          </Button>
          <Button onClick={() => void acceptAgreement()}>{text("agreementAccept")}</Button>
        </div>
      </div>
    </main>
  );
}

export function ErrorScreen() {
  const { text, error, retry } = useAppState();
  return (
    <main className="bg-background flex min-h-svh flex-col items-center justify-center gap-4 px-4 text-center">
      <BrandMark size="lg" />
      <p className="text-foreground max-w-sm">{error || text("error")}</p>
      <Button variant="outline" onClick={retry}>
        <RotateCwIcon />
        {text("regenerate")}
      </Button>
    </main>
  );
}
