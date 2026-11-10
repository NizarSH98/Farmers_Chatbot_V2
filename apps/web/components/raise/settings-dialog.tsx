"use client";

import { DownloadIcon, MonitorIcon, MoonIcon, SunIcon, Trash2Icon } from "lucide-react";
import { useTheme } from "next-themes";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { apiFetch } from "@/lib/api";
import type { Language } from "@/lib/types";
import { cn } from "@/lib/utils";

import { useAppState } from "./app-state";

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between sm:gap-6">
      <span className="text-sm font-medium">{label}</span>
      <div className="sm:w-72">{children}</div>
    </div>
  );
}

function Segmented<T extends string>({
  value,
  options,
  onChange
}: {
  value: T;
  options: { value: T; label: string; icon?: React.ReactNode }[];
  onChange: (value: T) => void;
}) {
  return (
    <div role="radiogroup" className="bg-muted grid auto-cols-fr grid-flow-col gap-1 rounded-lg p-1">
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          role="radio"
          aria-checked={value === option.value}
          onClick={() => onChange(option.value)}
          className={cn(
            "text-muted-foreground focus-visible:ring-ring/50 flex items-center justify-center gap-1.5 rounded-md px-2 py-1.5 text-sm whitespace-nowrap transition-all outline-none focus-visible:ring-2 [&_svg]:size-3.5",
            value === option.value && "bg-background text-foreground shadow-sm"
          )}
        >
          {option.icon}
          {option.label}
        </button>
      ))}
    </div>
  );
}

function OptionSelect({
  value,
  items,
  onChange,
  label
}: {
  value: string;
  items: { value: string; label: string }[];
  onChange: (value: string) => void;
  label: string;
}) {
  return (
    <Select items={items} value={value} onValueChange={(next) => next && onChange(String(next))}>
      <SelectTrigger aria-label={label} className="w-full">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {items.map((item) => (
          <SelectItem key={item.value} value={item.value}>
            {item.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

export function SettingsDialog({ open, onOpenChange }: { open: boolean; onOpenChange: (open: boolean) => void }) {
  const app = useAppState();
  const { text, language, config, token } = app;
  const { theme = "system", setTheme } = useTheme();
  const [confirmDelete, setConfirmDelete] = useState(false);

  const exportData = async () => {
    try {
      const data = await apiFetch<Record<string, unknown>>("/v1/export", token);
      const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }));
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = "raise-workspace-export.json";
      anchor.click();
      URL.revokeObjectURL(url);
    } catch {
      toast.error(text("error"));
    }
  };

  const deleteAccount = async () => {
    try {
      await apiFetch("/v1/account", token, { method: "DELETE" });
      onOpenChange(false);
      await app.signOut();
    } catch {
      toast.error(text("error"));
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90svh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{text("settings")}</DialogTitle>
        </DialogHeader>
        <div className="flex flex-col gap-5 py-2">
          <Row label={text("language")}>
            <Segmented<Language>
              value={language}
              onChange={app.setLanguage}
              options={[
                { value: "ar", label: "العربية" },
                { value: "en", label: "English" }
              ]}
            />
          </Row>
          <Row label={text("theme")}>
            <Segmented
              value={theme as "light" | "dark" | "system"}
              onChange={setTheme}
              options={[
                { value: "light", label: text("themeLight"), icon: <SunIcon /> },
                { value: "dark", label: text("themeDark"), icon: <MoonIcon /> },
                { value: "system", label: text("themeSystem"), icon: <MonitorIcon /> }
              ]}
            />
          </Row>
          <Separator />
          {config.modes.length > 0 && (
            <Row label={text("mode")}>
              <OptionSelect
                label={text("mode")}
                value={app.mode}
                onChange={app.setMode}
                items={config.modes.map((item) => ({
                  value: item.id,
                  label: language === "ar" ? item.label_ar : item.label_en
                }))}
              />
            </Row>
          )}
          {config.models.length > 1 && (
            <Row label={text("model")}>
              <OptionSelect
                label={text("model")}
                value={app.modelId}
                onChange={app.setModelId}
                items={config.models.map((item) => ({ value: item.id, label: item.label }))}
              />
            </Row>
          )}
          <Row label={text("clarification")}>
            <Segmented
              value={app.clarificationStyle}
              onChange={app.setClarificationStyle}
              options={[
                { value: "auto", label: text("auto") },
                { value: "guided", label: text("guided") },
                { value: "direct", label: text("direct") }
              ]}
            />
          </Row>
          <Separator />
          <div className="flex flex-col gap-2">
            <span className="text-sm font-medium">{text("account")}</span>
            {app.profile?.participant_code && (
              <div className="bg-muted/60 flex flex-col gap-1 rounded-lg px-3 py-2">
                <div className="flex items-center justify-between gap-3">
                  <span className="text-muted-foreground text-xs">{text("participantCode")}</span>
                  <code dir="ltr" className="font-mono text-sm font-semibold tracking-wide select-all">
                    {app.profile.participant_code}
                  </code>
                </div>
                <p className="text-muted-foreground text-xs leading-relaxed">{text("participantCodeHint")}</p>
              </div>
            )}
            <div className="flex flex-wrap gap-2">
              <Button variant="outline" size="sm" onClick={() => void exportData()}>
                <DownloadIcon />
                {text("exportData")}
              </Button>
              <Button variant="ghost" size="sm" className="text-destructive" onClick={() => setConfirmDelete(true)}>
                <Trash2Icon />
                {text("deleteAccount")}
              </Button>
            </div>
          </div>
        </div>
      </DialogContent>

      <Dialog open={confirmDelete} onOpenChange={setConfirmDelete}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{text("deleteAccount")}</DialogTitle>
            <DialogDescription>{text("deleteAccountConfirm")}</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setConfirmDelete(false)}>
              {text("cancel")}
            </Button>
            <Button variant="destructive" onClick={() => void deleteAccount()}>
              {text("delete")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Dialog>
  );
}
