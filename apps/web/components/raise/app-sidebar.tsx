"use client";

import {
  ArchiveIcon,
  ArchiveRestoreIcon,
  ChevronsUpDownIcon,
  FolderKanbanIcon,
  LogOutIcon,
  MessageSquareIcon,
  MoreHorizontalIcon,
  PencilIcon,
  SearchIcon,
  Settings2Icon,
  ShieldIcon,
  SquarePenIcon,
  Trash2Icon
} from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuAction,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar
} from "@/components/ui/sidebar";
import { apiFetch } from "@/lib/api";
import type { Conversation } from "@/lib/types";
import { cn } from "@/lib/utils";

import { useAppState } from "./app-state";
import { BrandLockup } from "./brand";
import { useChatState } from "./chat-runtime";

type PendingAction =
  | { kind: "rename"; conversation: Conversation }
  | { kind: "delete"; conversation: Conversation }
  | null;

function ConversationRow({
  conversation,
  active,
  onAction
}: {
  conversation: Conversation;
  active: boolean;
  onAction: (action: Exclude<PendingAction, null> | { kind: "archive" | "restore"; conversation: Conversation }) => void;
}) {
  const { text } = useAppState();
  const { openConversation } = useChatState();
  const { isMobile, setOpenMobile } = useSidebar();
  return (
    <SidebarMenuItem>
      <SidebarMenuButton
        isActive={active}
        onClick={() => {
          openConversation(conversation.id);
          if (isMobile) setOpenMobile(false);
        }}
        className="h-9"
      >
        <span className="truncate">{conversation.title}</span>
      </SidebarMenuButton>
      <DropdownMenu>
        <DropdownMenuTrigger
          render={
            <SidebarMenuAction showOnHover aria-label={text("more")}>
              <MoreHorizontalIcon />
            </SidebarMenuAction>
          }
        />
        <DropdownMenuContent align="start" className="min-w-44">
          <DropdownMenuItem onClick={() => onAction({ kind: "rename", conversation })}>
            <PencilIcon />
            {text("rename")}
          </DropdownMenuItem>
          {conversation.archived ? (
            <DropdownMenuItem onClick={() => onAction({ kind: "restore", conversation })}>
              <ArchiveRestoreIcon />
              {text("archived")}
            </DropdownMenuItem>
          ) : (
            <DropdownMenuItem onClick={() => onAction({ kind: "archive", conversation })}>
              <ArchiveIcon />
              {text("archive")}
            </DropdownMenuItem>
          )}
          <DropdownMenuSeparator />
          <DropdownMenuItem variant="destructive" onClick={() => onAction({ kind: "delete", conversation })}>
            <Trash2Icon />
            {text("delete")}
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </SidebarMenuItem>
  );
}

function UsageMeter() {
  const { usage, text } = useAppState();
  if (!usage || usage.weekly_limit_usd <= 0) return null;
  const ratio = Math.min(1, usage.weekly_spend_usd / usage.weekly_limit_usd);
  return (
    <div className="px-2 pb-1" title={text("weeklyUsageHint")}>
      <div className="text-muted-foreground mb-1.5 flex justify-between text-[0.7rem]">
        <span>{text("weeklyUsage")}</span>
        <span className="tabular-nums">{Math.round(ratio * 100)}%</span>
      </div>
      <div
        role="progressbar"
        aria-label={text("weeklyUsage")}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round(ratio * 100)}
        className="bg-sidebar-accent h-1.5 overflow-hidden rounded-full"
      >
        <div
          className={cn(
            "h-full rounded-full transition-[width] duration-500",
            ratio > 0.85 ? "bg-primary" : "bg-leaf"
          )}
          style={{ width: `${Math.max(2, ratio * 100)}%` }}
        />
      </div>
    </div>
  );
}

export function AppSidebar({
  onOpenSettings,
  onOpenWorkspace
}: {
  onOpenSettings: () => void;
  onOpenWorkspace: () => void;
}) {
  const { language, text, token, profile, session, isAdmin, signOut } = useAppState();
  const { conversations, activeId, openConversation, refreshConversations } = useChatState();
  const { isMobile, setOpenMobile } = useSidebar();
  const [query, setQuery] = useState("");
  const [pending, setPending] = useState<PendingAction>(null);
  const [renameValue, setRenameValue] = useState("");
  const [showArchived, setShowArchived] = useState(false);

  const { active, archived } = useMemo(() => {
    const needle = query.trim().toLowerCase();
    const matches = (item: Conversation) => !needle || item.title.toLowerCase().includes(needle);
    return {
      active: conversations.filter((item) => !item.archived && matches(item)),
      archived: conversations.filter((item) => item.archived && matches(item))
    };
  }, [conversations, query]);

  const patch = async (id: string, body: { title?: string; archived?: boolean }) => {
    try {
      await apiFetch("/v1/conversations/" + id, token, { method: "PATCH", body: JSON.stringify(body) });
      await refreshConversations();
    } catch {
      toast.error(text("error"));
    }
  };

  const handleAction = (
    action: Exclude<PendingAction, null> | { kind: "archive" | "restore"; conversation: Conversation }
  ) => {
    if (action.kind === "rename") {
      setRenameValue(action.conversation.title);
      setPending(action);
    } else if (action.kind === "delete") {
      setPending(action);
    } else {
      const archive = action.kind === "archive";
      void patch(action.conversation.id, { archived: archive });
      if (archive && action.conversation.id === activeId) openConversation(null);
    }
  };

  const confirmPending = async () => {
    if (!pending) return;
    if (pending.kind === "rename") {
      const title = renameValue.trim();
      if (title) await patch(pending.conversation.id, { title });
    } else {
      try {
        await apiFetch("/v1/conversations/" + pending.conversation.id, token, { method: "DELETE" });
        if (pending.conversation.id === activeId) openConversation(null);
        await refreshConversations();
      } catch {
        toast.error(text("error"));
      }
    }
    setPending(null);
  };

  const displayName = profile?.name || session?.identity?.name || profile?.email || "RAISE";
  const email = profile?.email || session?.identity?.email || "";

  return (
    <Sidebar side={language === "ar" ? "right" : "left"}>
      <SidebarHeader className="gap-3 px-3 pt-3">
        <div className="flex items-center justify-between px-1">
          <BrandLockup tagline={text("tagline")} />
        </div>
        <Button
          variant="outline"
          className="bg-background/60 hover:bg-background h-9 justify-start gap-2"
          onClick={() => {
            openConversation(null);
            if (isMobile) setOpenMobile(false);
          }}
        >
          <SquarePenIcon />
          {text("newChat")}
        </Button>
        <div className="relative">
          <SearchIcon className="text-muted-foreground pointer-events-none absolute start-2.5 top-1/2 size-4 -translate-y-1/2" />
          <Input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder={text("search")}
            aria-label={text("search")}
            className="bg-background/60 h-9 ps-8"
          />
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>{text("conversations")}</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {active.length === 0 && (
                <p className="text-muted-foreground flex items-center gap-2 px-2 py-3 text-sm">
                  <MessageSquareIcon className="size-4" />
                  {text("noConversations")}
                </p>
              )}
              {active.map((conversation) => (
                <ConversationRow
                  key={conversation.id}
                  conversation={conversation}
                  active={conversation.id === activeId}
                  onAction={handleAction}
                />
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
        {archived.length > 0 && (
          <SidebarGroup>
            <SidebarGroupLabel
              render={<button type="button" onClick={() => setShowArchived((value) => !value)} />}
              className="cursor-pointer"
            >
              <ArchiveIcon className="me-1" />
              {text("archived")} · {archived.length}
            </SidebarGroupLabel>
            {showArchived && (
              <SidebarGroupContent>
                <SidebarMenu>
                  {archived.map((conversation) => (
                    <ConversationRow
                      key={conversation.id}
                      conversation={conversation}
                      active={conversation.id === activeId}
                      onAction={handleAction}
                    />
                  ))}
                </SidebarMenu>
              </SidebarGroupContent>
            )}
          </SidebarGroup>
        )}
      </SidebarContent>

      <SidebarFooter className="gap-2 px-3 pb-3">
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton onClick={onOpenWorkspace}>
              <FolderKanbanIcon />
              {text("workspace")}
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
        <UsageMeter />
        <DropdownMenu>
          <DropdownMenuTrigger
            render={
              <SidebarMenuButton size="lg" className="data-[popup-open]:bg-sidebar-accent">
                <span className="bg-brand text-brand-foreground flex size-8 shrink-0 items-center justify-center rounded-full text-sm font-semibold">
                  {displayName.slice(0, 1).toUpperCase()}
                </span>
                <span className="grid min-w-0 flex-1 text-start leading-tight">
                  <span className="truncate text-sm font-medium">{displayName}</span>
                  {email && <span className="text-muted-foreground truncate text-xs">{email}</span>}
                </span>
                <ChevronsUpDownIcon className="text-muted-foreground ms-auto size-4" />
              </SidebarMenuButton>
            }
          />
          <DropdownMenuContent side="top" align="start" className="w-(--anchor-width) min-w-56">
            <DropdownMenuItem onClick={onOpenSettings}>
              <Settings2Icon />
              {text("settings")}
            </DropdownMenuItem>
            {isAdmin && (
              <DropdownMenuItem render={<Link href="/admin" />}>
                <ShieldIcon />
                {text("admin")}
              </DropdownMenuItem>
            )}
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => void signOut()}>
              <LogOutIcon />
              {text("logout")}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarFooter>

      <Dialog open={pending !== null} onOpenChange={(open) => !open && setPending(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{pending?.kind === "rename" ? text("rename") : text("delete")}</DialogTitle>
            {pending?.kind === "delete" && <DialogDescription>{text("deleteConfirm")}</DialogDescription>}
          </DialogHeader>
          {pending?.kind === "rename" && (
            <form
              onSubmit={(event) => {
                event.preventDefault();
                void confirmPending();
              }}
            >
              <Input autoFocus value={renameValue} maxLength={120} onChange={(event) => setRenameValue(event.target.value)} />
            </form>
          )}
          <DialogFooter>
            <Button variant="ghost" onClick={() => setPending(null)}>
              {text("cancel")}
            </Button>
            <Button
              variant={pending?.kind === "delete" ? "destructive" : "default"}
              onClick={() => void confirmPending()}
            >
              {pending?.kind === "delete" ? text("delete") : text("saveChanges")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Sidebar>
  );
}
