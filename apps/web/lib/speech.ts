import type { SpeechSynthesisAdapter } from "@assistant-ui/react";
import type { Language } from "./types";

/** BCP-47 tags used for both dictation and read-aloud. */
export const speechLocale = (language: Language): string =>
  language === "ar" ? "ar-LB" : "en-US";

/** Turn answer markdown into text that sounds natural when spoken. */
export function speakableText(markdown: string): string {
  return markdown
    .replace(/```[\s\S]*?```/g, " ")
    .replace(/\[(\d{1,2})\]\(#cite-\d{1,2}\)/g, "")
    .replace(/\[(\d{1,2})\]/g, "")
    .replace(/!\[[^\]]*\]\([^)]*\)/g, "")
    .replace(/\[([^\]]+)\]\([^)]*\)/g, "$1")
    .replace(/[*_`#>|]/g, "")
    .replace(/^\s*[-•]\s+/gm, "")
    .replace(/\s+/g, " ")
    .trim();
}

function pickVoice(locale: string): SpeechSynthesisVoice | undefined {
  const voices = window.speechSynthesis.getVoices();
  const base = locale.split("-")[0];
  return (
    voices.find((voice) => voice.lang === locale) ??
    voices.find((voice) => voice.lang.toLowerCase().startsWith(base))
  );
}

/**
 * Browser read-aloud that, unlike the stock adapter, speaks Arabic answers with
 * an Arabic voice (preferring Lebanese when the device has one).
 */
export class LocaleSpeechSynthesisAdapter implements SpeechSynthesisAdapter {
  constructor(private readonly language: Language) {}

  static isSupported(): boolean {
    return typeof window !== "undefined" && "speechSynthesis" in window;
  }

  speak(text: string): SpeechSynthesisAdapter.Utterance {
    const locale = speechLocale(this.language);
    const utterance = new SpeechSynthesisUtterance(speakableText(text));
    utterance.lang = locale;
    const voice = pickVoice(locale);
    if (voice) utterance.voice = voice;

    const subscribers = new Set<() => void>();
    const notify = () => subscribers.forEach((callback) => callback());
    const handle: SpeechSynthesisAdapter.Utterance = {
      status: { type: "starting" },
      cancel: () => {
        if (handle.status.type === "ended") return;
        handle.status = { type: "ended", reason: "cancelled" };
        window.speechSynthesis.cancel();
        notify();
      },
      subscribe: (callback) => {
        subscribers.add(callback);
        return () => subscribers.delete(callback);
      }
    };
    utterance.onstart = () => {
      handle.status = { type: "running" };
      notify();
    };
    utterance.onend = () => {
      if (handle.status.type === "ended") return;
      handle.status = { type: "ended", reason: "finished" };
      notify();
    };
    utterance.onerror = (event) => {
      if (handle.status.type === "ended") return;
      handle.status = { type: "ended", reason: "error", error: event.error };
      notify();
    };
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
    return handle;
  }
}
