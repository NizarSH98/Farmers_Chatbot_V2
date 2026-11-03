"use client";

import { CheckIcon, ChevronDownIcon, Settings2Icon, SlidersHorizontalIcon, SquarePenIcon } from "lucide-react";
import { useState } from "react";

import { Thread } from "@/components/assistant-ui/elements/thread.aui";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger
} from "@/components/ui/dropdown-menu";
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";

import { AppSidebar } from "./app-sidebar";
import { AppStateProvider, useAppState } from "./app-state";
import { BrandMark } from "./brand";
import { ChatRuntimeProvider, useChatState } from "./chat-runtime";
import { ConsentScreen, ErrorScreen, LoadingScreen, SignInScreen } from "./gates";
import { RaiseMessageParts } from "./message-parts";
import { SettingsDialog } from "./settings-dialog";
import { WorkspaceSheet } from "./workspace-sheet";

function Welcome() {
  const { text } = useAppState();
  return (
    <div className="animate-in fade-in slide-in-from-bottom-2 mb-8 flex flex-col items-center px-2 text-center duration-500">
      <BrandMark size="lg" />
      <h1 className="text-foreground mt-5 text-2xl font-semibold tracking-tight sm:text-3xl">{text("welcome")}</h1>
      <p className="text-muted-foreground mt-2 max-w-md text-[0.95rem] leading-relaxed">{text("welcomeHint")}</p>
    </div>
  );
}

function Footnote() {
  const { text } = useAppState();
  return <p className="text-muted-foreground -mt-2 px-4 text-center text-[0.7rem] leading-relaxed">{text("disclaimer")}</p>;
}

function ModePicker() {
  const { config, mode, setMode, language, text } = useAppState();
  if (config.modes.length < 2) return null;
  const current = config.modes.find((item) => item.id === mode) ?? config.modes[0];
  const label = (item: (typeof config.modes)[number]) => (language === "ar" ? item.label_ar : item.label_en);
  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        render={
          <Button
            variant="ghost"
            size="sm"
            aria-label={text("mode")}
            className="text-muted-foreground hover:text-foreground h-7 gap-1 rounded-full px-2.5 text-xs"
          >
            <SlidersHorizontalIcon className="size-3.5" />
            {label(current)}
            <ChevronDownIcon className="size-3" />
          </Button>
        }
      />
      <DropdownMenuContent align="start" side="top" className="min-w-56">
        {config.modes.map((item) => (
          <DropdownMenuItem key={item.id} onClick={() => setMode(item.id)} className="items-start py-2">
            <CheckIcon className={item.id === current.id ? "mt-0.5 opacity-100" : "mt-0.5 opacity-0"} />
            <span className="flex flex-col">
              <span className="font-medium">{label(item)}</span>
              {item.description && <span className="text-muted-foreground text-xs">{item.description}</span>}
            </span>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

const THREAD_COMPONENTS = { Welcome, Footnote, ComposerExtra: ModePicker };

function Header({ onOpenSettings }: { onOpenSettings: () => void }) {
  const { text, config, language } = useAppState();
  const { conversations, activeId, openConversation } = useChatState();
  const title = conversations.find((item) => item.id === activeId)?.title;
  const warning = config.corpus_warning?.[language];
  return (
    <header className="bg-background/85 supports-[backdrop-filter]:bg-background/70 border-border/60 sticky top-0 z-20 flex flex-col border-b backdrop-blur">
      <div className="flex h-14 items-center gap-2 px-3">
        <SidebarTrigger className="text-muted-foreground" aria-label={text("menu")} />
        <h2 className="text-foreground min-w-0 flex-1 truncate text-sm font-medium">{title ?? ""}</h2>
        <Button
          variant="ghost"
          size="icon"
          className="text-muted-foreground"
          aria-label={text("newChat")}
          onClick={() => openConversation(null)}
        >
          <SquarePenIcon />
        </Button>
        <Button variant="ghost" size="icon" className="text-muted-foreground" aria-label={text("settings")} onClick={onOpenSettings}>
          <Settings2Icon />
        </Button>
      </div>
      {warning && (
        <p className="bg-warning text-warning-foreground border-warning-border border-y px-4 py-1.5 text-center text-xs">{warning}</p>
      )}
    </header>
  );
}

function Workspace() {
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [workspaceOpen, setWorkspaceOpen] = useState(false);
  return (
    <ChatRuntimeProvider>
      <RaiseMessageParts />
      <SidebarProvider>
        <AppSidebar onOpenSettings={() => setSettingsOpen(true)} onOpenWorkspace={() => setWorkspaceOpen(true)} />
        <SidebarInset className="flex h-svh min-w-0 flex-col">
          <Header onOpenSettings={() => setSettingsOpen(true)} />
          <div className="min-h-0 flex-1">
            <Thread components={THREAD_COMPONENTS} />
          </div>
        </SidebarInset>
      </SidebarProvider>
      <SettingsDialog open={settingsOpen} onOpenChange={setSettingsOpen} />
      <WorkspaceSheet open={workspaceOpen} onOpenChange={setWorkspaceOpen} />
    </ChatRuntimeProvider>
  );
}

function Gate() {
  const { phase } = useAppState();
  if (phase === "loading") return <LoadingScreen />;
  if (phase === "signed-out") return <SignInScreen />;
  if (phase === "consent") return <ConsentScreen />;
  if (phase === "error") return <ErrorScreen />;
  return <Workspace />;
}

export function AppShell() {
  return (
    <AppStateProvider>
      <Gate />
    </AppStateProvider>
  );
}
