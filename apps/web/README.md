# Web application map

Purpose: explain where the Next.js user interface lives and which file owns
each frontend responsibility.

The chat UI is assembled from proven open-source modules: assistant-ui for the
conversation runtime and thread, shadcn/ui (Base UI) for primitives, and
Tailwind v4 with RAISE design tokens. RAISE-specific code adapts our backend to
those modules rather than re-implementing chat behavior.

## Entry points and ownership

| Path | Responsibility |
| --- | --- |
| app/page.tsx | Mounts the app shell |
| app/layout.tsx | Root HTML, IBM Plex Sans Arabic, theme, tooltips, toasts |
| app/globals.css | RAISE design tokens (light + dark) and base typography |
| app/admin/page.tsx | Knowledge-release and editor administration |
| app/api/[...path]/route.ts | Same-origin proxy from browser /api calls to FastAPI |
| components/raise/app-state.tsx | Session, consent, config, language, answer preferences |
| components/raise/chat-runtime.tsx | assistant-ui ExternalStoreRuntime over our SSE turns: edit, retry, stop, attachments, feedback, dictation, read-aloud, conversation list |
| components/raise/convert.ts | Message → assistant-ui parts (progress, clarification, sources, artifacts) |
| components/raise/message-parts.tsx | Renderers for those parts |
| components/raise/app-shell.tsx, app-sidebar.tsx, settings-dialog.tsx, workspace-sheet.tsx, gates.tsx | Layout, navigation, settings, projects, sign-in/consent screens |
| components/assistant-ui/, components/ui/, hooks/ | Vendored registry code (assistant-ui, shadcn); keep close to upstream |
| lib/api.ts | Session-aware HTTP, uploads, and SSE turn streaming |
| lib/speech.ts | Language-aware read-aloud (Arabic voice for Arabic answers) |
| lib/sources.ts | Groups per-passage citations into reader-facing sources |
| lib/i18n.ts | Arabic and English interface copy |

Tests sit next to the code they verify.

## Updating vendored components

Re-pull with `npx shadcn@latest add <registry url>`, then re-apply the RAISE
localisation hook (`useKitText`) and token classes. Keep behavior changes in
`components/raise/`.

## Commands

~~~powershell
npm ci
npx tsc --noEmit
npm run lint
npx vitest run
npm run build
~~~
