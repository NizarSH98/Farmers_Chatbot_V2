"use client";

import {
  DownloadIcon,
  FileIcon,
  FolderPlusIcon,
  Loader2Icon,
  MessageSquarePlusIcon,
  Trash2Icon,
  UploadIcon
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Textarea } from "@/components/ui/textarea";
import { apiFetch, downloadPrivateFile } from "@/lib/api";
import type { Artifact, Project, ProjectDocument } from "@/lib/types";
import { cn } from "@/lib/utils";

import { useAppState } from "./app-state";
import { useChatState } from "./chat-runtime";

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="flex flex-col gap-2">
      <h3 className="text-muted-foreground text-xs font-semibold tracking-wide uppercase">{title}</h3>
      {children}
    </section>
  );
}

function Empty({ label }: { label: string }) {
  return <p className="text-muted-foreground rounded-lg border border-dashed px-3 py-4 text-center text-sm">{label}</p>;
}

function WorkspaceContent({ onClose }: { onClose: () => void }) {
  const { text, token } = useAppState();
  const { startConversation, refreshConversations } = useChatState();
  const [projects, setProjects] = useState<Project[]>([]);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [documents, setDocuments] = useState<ProjectDocument[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [name, setName] = useState("");
  const [instructions, setInstructions] = useState("");
  const [busy, setBusy] = useState(true);
  const fileRef = useRef<HTMLInputElement>(null);

  const fail = useCallback(() => toast.error(text("error")), [text]);

  const loadDocuments = useCallback(
    async (projectId: string) => {
      if (!projectId) {
        setDocuments([]);
        return;
      }
      const result = await apiFetch<{ items: ProjectDocument[] }>(`/v1/projects/${projectId}/documents`, token);
      setDocuments(result.items);
    },
    [token]
  );

  const load = useCallback(
    async (preferred?: string) => {
      setBusy(true);
      try {
        const [projectResult, artifactResult] = await Promise.all([
          apiFetch<{ items: Project[] }>("/v1/projects", token),
          apiFetch<{ items: Artifact[] }>("/v1/artifacts", token)
        ]);
        setProjects(projectResult.items);
        setArtifacts(artifactResult.items);
        const next =
          (preferred && projectResult.items.some((item) => item.id === preferred) && preferred) ||
          projectResult.items[0]?.id ||
          "";
        setSelectedId(next);
        await loadDocuments(next);
      } catch {
        fail();
      } finally {
        setBusy(false);
      }
    },
    [fail, loadDocuments, token]
  );

  // The panel mounts this content each time it opens; fetch on mount and
  // set state only once the requests resolve.
  useEffect(() => {
    let active = true;
    Promise.all([
      apiFetch<{ items: Project[] }>("/v1/projects", token),
      apiFetch<{ items: Artifact[] }>("/v1/artifacts", token)
    ])
      .then(async ([projectResult, artifactResult]) => {
        const first = projectResult.items[0]?.id || "";
        const documentResult = first
          ? await apiFetch<{ items: ProjectDocument[] }>(`/v1/projects/${first}/documents`, token)
          : { items: [] };
        if (!active) return;
        setProjects(projectResult.items);
        setArtifacts(artifactResult.items);
        setSelectedId(first);
        setDocuments(documentResult.items);
      })
      .catch(() => {
        if (active) fail();
      })
      .finally(() => {
        if (active) setBusy(false);
      });
    return () => {
      active = false;
    };
  }, [fail, token]);

  const choose = async (projectId: string) => {
    setSelectedId(projectId);
    setBusy(true);
    await loadDocuments(projectId).catch(fail);
    setBusy(false);
  };

  const create = async () => {
    if (!name.trim()) return;
    setBusy(true);
    try {
      const created = await apiFetch<Project>("/v1/projects", token, {
        method: "POST",
        body: JSON.stringify({ name: name.trim(), instructions: instructions.trim() })
      });
      setName("");
      setInstructions("");
      await load(created.id);
    } catch {
      fail();
      setBusy(false);
    }
  };

  const remove = async (projectId: string) => {
    setBusy(true);
    try {
      await apiFetch(`/v1/projects/${projectId}`, token, { method: "DELETE" });
      await load();
      await refreshConversations();
    } catch {
      fail();
      setBusy(false);
    }
  };

  const upload = async (file?: File) => {
    if (!file || !selectedId) return;
    setBusy(true);
    try {
      const form = new FormData();
      form.set("document", file);
      await apiFetch(`/v1/projects/${selectedId}/documents`, token, { method: "POST", body: form });
      await loadDocuments(selectedId);
    } catch {
      fail();
    } finally {
      setBusy(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const removeDocument = async (documentId: string) => {
    try {
      await apiFetch(`/v1/projects/${selectedId}/documents/${documentId}`, token, { method: "DELETE" });
      await loadDocuments(selectedId);
    } catch {
      fail();
    }
  };

  const chatInProject = async () => {
    const project = projects.find((item) => item.id === selectedId);
    if (!project) return;
    await startConversation(project.id, project.name);
    onClose();
  };

  const selected = projects.find((item) => item.id === selectedId);

  return (
    <>
        <SheetHeader className="border-b">
          <SheetTitle className="flex items-center gap-2">
            {text("workspace")}
            {busy && <Loader2Icon className="text-muted-foreground size-4 animate-spin" />}
          </SheetTitle>
          <SheetDescription>{text("projectInstructions")}</SheetDescription>
        </SheetHeader>

        <div className="flex flex-col gap-6 p-4">
          <Section title={text("createProject")}>
            <form
              className="flex flex-col gap-2"
              onSubmit={(event) => {
                event.preventDefault();
                void create();
              }}
            >
              <Input value={name} maxLength={100} onChange={(event) => setName(event.target.value)} placeholder={text("projectName")} />
              <Textarea
                value={instructions}
                maxLength={5000}
                rows={3}
                onChange={(event) => setInstructions(event.target.value)}
                placeholder={text("projectInstructions")}
              />
              <Button type="submit" variant="secondary" disabled={!name.trim() || busy} className="self-start">
                <FolderPlusIcon />
                {text("createProject")}
              </Button>
            </form>
          </Section>

          <Section title={text("projects")}>
            {projects.length === 0 ? (
              <Empty label={text("noItems")} />
            ) : (
              <ul className="flex flex-col gap-1">
                {projects.map((project) => (
                  <li key={project.id} className="group flex items-center gap-1">
                    <button
                      type="button"
                      onClick={() => void choose(project.id)}
                      className={cn(
                        "hover:bg-muted flex-1 truncate rounded-lg px-3 py-2 text-start text-sm transition-colors",
                        project.id === selectedId && "bg-accent text-accent-foreground font-medium"
                      )}
                    >
                      {project.name}
                    </button>
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      aria-label={text("delete")}
                      className="opacity-60 group-hover:opacity-100"
                      onClick={() => void remove(project.id)}
                    >
                      <Trash2Icon />
                    </Button>
                  </li>
                ))}
              </ul>
            )}
          </Section>

          {selected && (
            <Section title={`${text("documents")} · ${selected.name}`}>
              <div className="flex flex-wrap gap-2">
                <Button size="sm" onClick={() => void chatInProject()}>
                  <MessageSquarePlusIcon />
                  {text("projectChat")}
                </Button>
                <Button size="sm" variant="outline" disabled={busy} onClick={() => fileRef.current?.click()}>
                  <UploadIcon />
                  {text("uploadDocument")}
                </Button>
                <input
                  ref={fileRef}
                  type="file"
                  hidden
                  accept=".pdf,.docx,.txt,.csv,.xlsx"
                  onChange={(event) => void upload(event.target.files?.[0])}
                />
              </div>
              {documents.length === 0 ? (
                <Empty label={text("noItems")} />
              ) : (
                <ul className="flex flex-col gap-1">
                  {documents.map((document) => (
                    <li key={document.id} className="bg-muted/50 flex items-center gap-2 rounded-lg px-3 py-2 text-sm">
                      <FileIcon className="text-muted-foreground size-4 shrink-0" />
                      <span className="flex-1 truncate">{document.filename}</span>
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        aria-label={text("download")}
                        onClick={() =>
                          void downloadPrivateFile(
                            `/v1/projects/${selectedId}/documents/${document.id}/download`,
                            token,
                            document.filename
                          ).catch(fail)
                        }
                      >
                        <DownloadIcon />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        aria-label={text("delete")}
                        onClick={() => void removeDocument(document.id)}
                      >
                        <Trash2Icon />
                      </Button>
                    </li>
                  ))}
                </ul>
              )}
            </Section>
          )}

          <Section title={text("artifacts")}>
            {artifacts.length === 0 ? (
              <Empty label={text("noItems")} />
            ) : (
              <ul className="flex flex-col gap-1">
                {artifacts.map((artifact) => (
                  <li key={artifact.id} className="bg-muted/50 flex items-center gap-2 rounded-lg px-3 py-2 text-sm">
                    <FileIcon className="text-muted-foreground size-4 shrink-0" />
                    <span className="flex-1 truncate">{artifact.filename}</span>
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      aria-label={text("download")}
                      onClick={() =>
                        void downloadPrivateFile(`/v1/artifacts/${artifact.id}/download`, token, artifact.filename).catch(fail)
                      }
                    >
                      <DownloadIcon />
                    </Button>
                  </li>
                ))}
              </ul>
            )}
          </Section>
        </div>
    </>
  );
}

export function WorkspaceSheet({ open, onOpenChange }: { open: boolean; onOpenChange: (open: boolean) => void }) {
  const { language } = useAppState();
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side={language === "ar" ? "left" : "right"} className="w-full gap-0 overflow-y-auto sm:max-w-md">
        {open && <WorkspaceContent onClose={() => onOpenChange(false)} />}
      </SheetContent>
    </Sheet>
  );
}
