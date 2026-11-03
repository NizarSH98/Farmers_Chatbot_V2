"use client";

import { makeAssistantDataUI } from "@assistant-ui/react";
import {
  AlertTriangleIcon,
  BookOpenCheckIcon,
  ChevronDownIcon,
  DownloadIcon,
  FileTextIcon,
  GlobeIcon,
  PauseCircleIcon,
  SendHorizontalIcon
} from "lucide-react";
import { Collapsible } from "radix-ui";
import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { thinkingLines } from "@/lib/i18n";
import { groupSources } from "@/lib/sources";
import type { Citation, ClarificationInteraction, ClarificationQuestion } from "@/lib/types";
import { cn } from "@/lib/utils";

import { useAppState } from "./app-state";
import { useChatState } from "./chat-runtime";

/* ---------------------------------------------------------------- progress */

function ProgressLine({ stage }: { stage: string }) {
  const { language, text } = useAppState();
  const lines = thinkingLines(language);
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const timer = window.setInterval(() => setIndex((value) => (value + 1) % lines.length), 2600);
    return () => window.clearInterval(timer);
  }, [lines.length]);

  const label =
    stage === "verification"
      ? text("verification")
      : stage === "generation"
        ? text("generation")
        : lines[index];

  return (
    <div role="status" aria-live="polite" className="flex items-center gap-2.5 py-1.5">
      <span aria-hidden="true" className="relative flex size-2.5">
        <span className="bg-leaf/60 absolute inline-flex size-full animate-ping rounded-full motion-reduce:hidden" />
        <span className="bg-leaf relative inline-flex size-2.5 rounded-full" />
      </span>
      <span
        key={label}
        className="shimmer text-muted-foreground animate-in fade-in text-sm duration-300 motion-reduce:animate-none"
      >
        {label}
      </span>
    </div>
  );
}

export const ProgressUI = makeAssistantDataUI<{ stage: string }>({
  name: "raise-progress",
  render: ({ data }) => <ProgressLine stage={data.stage} />
});

/* ----------------------------------------------------------- clarification */

function questionsOf(interaction: ClarificationInteraction): ClarificationQuestion[] {
  if (interaction.questions?.length) return interaction.questions;
  return [
    {
      id: "detail",
      prompt: interaction.question,
      answer_type: "single",
      required: true,
      allow_other: false,
      options: interaction.options || []
    }
  ];
}

function ClarificationCard({
  messageId,
  interaction
}: {
  messageId: string;
  interaction: ClarificationInteraction;
}) {
  const { text } = useAppState();
  const { answerClarification, isRunning } = useChatState();
  const questions = useMemo(() => questionsOf(interaction), [interaction]);
  const [answers, setAnswers] = useState<Record<string, string | string[]>>({});
  const [otherFor, setOtherFor] = useState<string | null>(null);
  const resolved = interaction.status === "resolved";
  const singleTap = questions.length === 1 && questions[0].answer_type === "single";

  const isComplete = questions.every((question) => {
    if (!question.required) return true;
    const value = answers[question.id];
    return Array.isArray(value) ? value.some((item) => item.trim()) : Boolean(String(value || "").trim());
  });

  const submit = (next: Record<string, string | string[]>) => {
    const summary = questions
      .map((question) => {
        const raw = next[question.id];
        const answer = Array.isArray(raw) ? raw.join("، ") : String(raw || "");
        return questions.length === 1 ? answer : `${question.prompt}: ${answer}`;
      })
      .join("\n");
    answerClarification(messageId, interaction, next, summary);
  };

  const choose = (question: ClarificationQuestion, value: string) => {
    if (question.answer_type === "multiple") {
      setAnswers((current) => {
        const existing = Array.isArray(current[question.id]) ? (current[question.id] as string[]) : [];
        const nextValues = existing.includes(value)
          ? existing.filter((item) => item !== value)
          : [...existing, value];
        return { ...current, [question.id]: nextValues };
      });
      return;
    }
    const next = { ...answers, [question.id]: value };
    setAnswers(next);
    if (singleTap) submit(next);
  };

  return (
    <div
      className={cn(
        "border-border bg-card animate-in fade-in slide-in-from-bottom-1 my-3 rounded-2xl border p-4 duration-300",
        resolved && "opacity-60"
      )}
    >
      <p className="text-muted-foreground mb-3 text-xs">{text("clarifyHint")}</p>
      <div className="flex flex-col gap-4">
        {questions.map((question) => {
          const value = answers[question.id];
          return (
            <fieldset key={question.id} disabled={resolved || isRunning} className="flex flex-col gap-2">
              <legend className="text-foreground mb-1 text-[0.95rem] font-medium">{question.prompt}</legend>
              {question.answer_type !== "text" && (
                <div className="flex flex-wrap gap-2">
                  {question.options
                    .filter((option) => option.kind !== "other")
                    .map((option) => {
                      const selected = Array.isArray(value)
                        ? value.includes(option.value)
                        : value === option.value;
                      return (
                        <button
                          key={option.id}
                          type="button"
                          aria-pressed={selected}
                          onClick={() => choose(question, option.value)}
                          className={cn(
                            "border-border hover:border-primary/60 hover:bg-primary/5 focus-visible:ring-ring/50 rounded-full border px-3.5 py-1.5 text-sm transition-all outline-none focus-visible:ring-2 active:scale-[0.97] disabled:pointer-events-none motion-reduce:transition-none",
                            selected && "border-primary bg-primary text-primary-foreground hover:bg-primary"
                          )}
                        >
                          {option.label}
                        </button>
                      );
                    })}
                  {(question.allow_other || question.options.some((option) => option.kind === "other")) && (
                    <button
                      type="button"
                      onClick={() => setOtherFor(question.id)}
                      className="text-muted-foreground hover:text-foreground rounded-full border border-dashed px-3.5 py-1.5 text-sm transition-colors"
                    >
                      {text("otherAnswer")}
                    </button>
                  )}
                </div>
              )}
              {(question.answer_type === "text" || otherFor === question.id) && (
                <form
                  className="flex items-center gap-2"
                  onSubmit={(event) => {
                    event.preventDefault();
                    if (singleTap && String(answers[question.id] || "").trim()) submit(answers);
                  }}
                >
                  <Input
                    autoFocus={otherFor === question.id}
                    placeholder={text("typeOwnOption")}
                    value={Array.isArray(value) ? "" : String(value || "")}
                    onChange={(event) =>
                      setAnswers((current) => ({ ...current, [question.id]: event.target.value }))
                    }
                  />
                  {singleTap && (
                    <Button type="submit" size="icon" aria-label={text("submitOption")}>
                      <SendHorizontalIcon className="rtl:-scale-x-100" />
                    </Button>
                  )}
                </form>
              )}
            </fieldset>
          );
        })}
      </div>
      {!singleTap && !resolved && (
        <div className="mt-4 flex justify-end">
          <Button disabled={!isComplete || isRunning} onClick={() => submit(answers)}>
            {text("submitAnswers")}
          </Button>
        </div>
      )}
    </div>
  );
}

export const ClarificationUI = makeAssistantDataUI<{
  messageId: string;
  interaction: ClarificationInteraction;
}>({
  name: "raise-clarification",
  render: ({ data }) => <ClarificationCard messageId={data.messageId} interaction={data.interaction} />
});

/* ----------------------------------------------------------------- sources */

function SourceIcon({ type }: { type: string }) {
  if (type === "web" || type === "trusted_web") return <GlobeIcon className="size-3.5" />;
  if (type === "project" || type === "project_document") return <FileTextIcon className="size-3.5" />;
  return <BookOpenCheckIcon className="size-3.5" />;
}

function SourcesDisclosure({ citations }: { citations: Citation[] }) {
  const { text } = useAppState();
  const groups = useMemo(() => groupSources(citations), [citations]);
  const kindLabel = (type: string) =>
    type === "web" || type === "trusted_web"
      ? text("sourceWeb")
      : type === "project" || type === "project_document"
        ? text("sourceProject")
        : text("reviewedSource");

  return (
    <Collapsible.Root className="group/sources mt-2">
      <Collapsible.Trigger className="text-muted-foreground hover:text-foreground hover:bg-muted focus-visible:ring-ring/50 inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium transition-colors outline-none focus-visible:ring-2">
        <BookOpenCheckIcon className="text-leaf size-3.5" />
        {text("showSources")}
        <span className="bg-muted text-foreground rounded-full px-1.5 tabular-nums">{groups.length}</span>
        <ChevronDownIcon className="size-3.5 transition-transform group-data-[state=open]/sources:rotate-180 motion-reduce:transition-none" />
      </Collapsible.Trigger>
      <Collapsible.Content className="data-[state=open]:animate-collapsible-down data-[state=closed]:animate-collapsible-up overflow-hidden">
        <ul className="mt-2 flex flex-col gap-2">
          {groups.map((group) => (
            <li key={group.key} className="bg-card border-border flex items-start gap-3 rounded-xl border px-3 py-2.5 text-sm">
              <span className="bg-accent text-accent-foreground mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-lg">
                <SourceIcon type={group.sourceType} />
              </span>
              <span className="min-w-0 flex-1">
                {group.url ? (
                  <a
                    href={group.url}
                    target="_blank"
                    rel="noreferrer noopener"
                    className="text-foreground decoration-border hover:decoration-foreground font-medium underline underline-offset-2"
                  >
                    {group.title}
                  </a>
                ) : (
                  <span className="text-foreground font-medium">{group.title}</span>
                )}
                <span className="text-muted-foreground mt-0.5 flex flex-wrap items-center gap-x-2 text-xs">
                  <span>{kindLabel(group.sourceType)}</span>
                  {group.publisher && <span>· {group.publisher}</span>}
                  <span className="tabular-nums">
                    · {group.passages} {text("reviewedPassages")}
                  </span>
                  {group.markers.length > 0 && (
                    <span className="tabular-nums">· [{group.markers.join("، ")}]</span>
                  )}
                </span>
                {group.warnings.map((warning) => (
                  <span key={warning} className="text-warning-foreground mt-1 block text-xs">
                    {warning}
                  </span>
                ))}
              </span>
            </li>
          ))}
        </ul>
      </Collapsible.Content>
    </Collapsible.Root>
  );
}

export const SourcesUI = makeAssistantDataUI<{ citations: Citation[] }>({
  name: "raise-sources",
  render: ({ data }) => <SourcesDisclosure citations={data.citations} />
});

/* --------------------------------------------------------------- artifacts */

function ArtifactButtons({ ids }: { ids: string[] }) {
  const { text } = useAppState();
  const { downloadArtifact } = useChatState();
  return (
    <div className="mt-3 flex flex-wrap gap-2">
      {ids.map((id, index) => (
        <Button key={id} variant="outline" size="sm" onClick={() => void downloadArtifact(id)}>
          <DownloadIcon />
          {text("download")}
          {ids.length > 1 ? ` ${index + 1}` : ""}
        </Button>
      ))}
    </div>
  );
}

export const ArtifactsUI = makeAssistantDataUI<{ ids: string[] }>({
  name: "raise-artifacts",
  render: ({ data }) => <ArtifactButtons ids={data.ids} />
});

/* --------------------------------------------------------- warning, notice */

export const WarningUI = makeAssistantDataUI<{ message: string }>({
  name: "raise-warning",
  render: ({ data }) => (
    <div className="bg-warning/40 text-warning-foreground border-warning-border mt-3 flex gap-2 rounded-xl border px-3 py-2.5 text-sm">
      <AlertTriangleIcon className="mt-0.5 size-4 shrink-0" />
      <span>{data.message}</span>
    </div>
  )
});

function NoticeLine({ status }: { status: string }) {
  const { text } = useAppState();
  return (
    <p className="text-muted-foreground mt-2 flex items-center gap-1.5 text-xs">
      <PauseCircleIcon className="size-3.5" />
      {status === "cancelled" ? text("cancelled") : text("interrupted")}
    </p>
  );
}

export const NoticeUI = makeAssistantDataUI<{ status: string }>({
  name: "raise-notice",
  render: ({ data }) => <NoticeLine status={data.status} />
});

/** Mount once inside the runtime provider to register every RAISE part. */
export function RaiseMessageParts() {
  return (
    <>
      <ProgressUI />
      <ClarificationUI />
      <SourcesUI />
      <ArtifactsUI />
      <WarningUI />
      <NoticeUI />
    </>
  );
}
