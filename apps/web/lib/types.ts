export type Language = "ar" | "en";

export interface AppConfig {
  app_name: string;
  agreement_version: string;
  default_language: Language;
  modes: Array<{
    id: string;
    label_en: string;
    label_ar: string;
    description: string;
  }>;
  models: Array<{
    id: string;
    label: string;
    description: string;
    supports_images: boolean;
  }>;
}

export interface CurrentUser {
  id: string;
  name: string;
  email: string;
  role: string;
  consent_current: boolean;
  default_mode: string;
}

export interface Conversation {
  id: string;
  title: string;
  archived: number | boolean;
  created_at: string;
  updated_at: string;
}

export interface Citation {
  source_type: string;
  title?: string;
  url?: string;
  item_id?: string;
  document_id?: string;
  status?: string;
  warning?: string;
  [key: string]: unknown;
}

export interface Message {
  id: string;
  clientKey?: string;
  role: "user" | "assistant" | "system";
  content: string;
  status: string;
  language?: string;
  model?: string;
  warning?: string;
  quickReplies?: string[];
  citations: Citation[];
  tools: string[];
  attachments: Array<{
    kind: string;
    mime_type?: string;
    storage_path?: string;
  }>;
  created_at: string;
  pending?: boolean;
  feedback?: "helpful" | "not_helpful";
  feedbackPending?: boolean;
}

export interface StreamEvent {
  event: string;
  data: Record<string, unknown>;
}

export interface TurnPayload {
  conversation_id: string;
  text: string;
  mode: string;
  model_id?: string;
  clarification_style: string;
  attachment_ids: string[];
}
