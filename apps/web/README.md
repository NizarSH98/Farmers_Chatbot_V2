# Web application map

Purpose: explain where the Next.js user interface lives and which file owns
each frontend responsibility.

## Current entry points

| Path | Responsibility |
| --- | --- |
| app/page.tsx | Loads the main chat workspace |
| app/admin/page.tsx | Separate knowledge-release and editor administration |
| app/api/[...path]/route.ts | Same-origin server proxy from browser /api calls to the private FastAPI service |
| app/layout.tsx | Root HTML, metadata, language, and global styles |
| app/globals.css | Shared visual tokens, layout, responsive, RTL, and component styles |
| components/ChatWorkspace.tsx | Current chat/conversation/project/settings UI; planned Phase 0 split |
| lib/api.ts | Session-aware HTTP, uploads, and SSE turn streaming |
| lib/auth.ts | Browser session/login helpers |
| lib/types.ts | API and UI TypeScript contracts |
| lib/i18n.ts | Central Arabic and English interface copy |
| lib/messages.ts | Message merging that preserves client-only state |

Tests sit next to the component or library they verify.

## Change boundary

The approved target structure and behavior are defined in
[the product experience specification](../../docs/product/PRODUCT_EXPERIENCE_SPEC.md).
Do not redesign individual screens independently of that contract.

Phase 0 splits ChatWorkspace by feature without changing behavior. Visual
implementation starts in Phase 1 only after the product contract is approved.

## Commands

~~~powershell
npm ci
npm run typecheck
npm run lint
npm test -- --run
npm run build
~~~
