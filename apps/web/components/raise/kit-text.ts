"use client";

import type { CopyKey } from "@/lib/i18n";

import { useAppState } from "./app-state";

/**
 * Localised labels for the vendored assistant-ui elements, so their tooltips
 * and screen-reader names follow the user's language instead of English.
 */
export function useKitText(): (key: CopyKey) => string {
  return useAppState().text;
}
