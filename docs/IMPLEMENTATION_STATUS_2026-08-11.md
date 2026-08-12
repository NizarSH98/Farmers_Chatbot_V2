# RAISE Rebuild Implementation Status

Snapshot date: 2026-08-11

This file separates implemented repository work from gates that require hosted
systems, elapsed soak time, private credentials, or human evaluation. Passing
local tests is not evidence that an external gate passed.

## Implemented locally

- Alembic adoption and reversible revisions through `20260811_0003`; hosted
  startup checks the exact head and refuses SQLite/local-storage fallback.
- Isolated PDF parsing with current `pypdf`, bounded time/pages/bytes/memory,
  malformed/encrypted/decompression defenses, and document-security tests.
- Web, frozen Streamlit compatibility, disabled WhatsApp, and MCP paths route
  through the canonical `AssistantEngine`/`TurnCoordinator`, one
  `ProviderClient`, and bounded `ToolExecutor`. The former synchronous
  `AssistantService` contains no provider/retrieval/tool loop and is only a
  one-release facade.
- Atomic quota/cost reservation, request-payload conflict detection, exact turn
  finalization, provider accounting, one terminal result, and persisted turn
  recovery.
- Next.js parity for conversations, projects, project documents, artifacts,
  workspace export/data controls, Arabic/RTL, draft warning, source state, and
  interrupted-SSE recovery.
- One Render backend in `render.yaml`; Streamlit is frozen compatibility only.
- WhatsApp is a disabled-by-default router mounted in the canonical FastAPI app.
  It reuses the web service container, engine, provider, coordinator, storage,
  and tools. Meta message IDs are idempotency keys and delivery retries reuse
  the persisted answer. The root module is only an import wrapper.
- Versioned PostgreSQL hybrid/GraphRAG schema, evidence-backed claims and
  relations, bilingual aliases, tenant project chunks, immutable releases,
  ingestion idempotency, and atomic activation/rollback APIs.
- Parallel lexical/vector/alias/graph/project retrieval contract with controlled
  graph hops, RRF, scope filters, evidence IDs, and lexical/graph fallback.
  Vector cutover is disabled until the bilingual benchmark passes.
- Direct live-source connectors fetch only exact operator-authorized HTTPS
  endpoints from a versioned registry. Redirects, untrusted hosts, unsupported
  content types, oversized/decompressed bodies, and irrelevant passages fail
  closed. Retained passages, observation/expiry times, and immutable evidence
  IDs feed deterministic business/action artifacts.
- Versioned hidden-evaluation and embedding-benchmark harnesses with retrieval,
  citation, safety, language-gap, latency/cost, ablation, and pairwise-CI
  metrics.
- Body-order DOCX extractor, source reconciliation, record/graph metadata,
  Markdown validator, release builder, and draft-only ingestion/activation
  guard.
- Deterministic local-only corpus conversion with a canonical bilingual
  graph-ready Markdown file and a standalone Arabic review companion. The
  converter imports no model/provider client and makes zero translation network
  calls.
- Versioned bilingual ontology compiled into each release: 162 entities across
  all 21 planned entity types, 352 normalized English/Arabic/Lebanese/Arabizi
  aliases, and 183 typed, qualified, passage-evidenced relations. Alias lookup
  is word-boundary safe and local traversal is bidirectional, cycle-safe, and
  capped at two hops/50 paths.

## Latest local evidence

- Backend: compilation passed; Ruff passed; all 175 tests passed.
- Python production dependencies: `pip-audit -r requirements.txt` reported no
  known vulnerabilities.
- Alembic: offline PostgreSQL SQL rendered revisions `0001 -> 0002 -> 0003`.
- Release preflight passed.
- Frontend: production npm audit reported zero vulnerabilities; typecheck
  passed; 15 tests passed; lint passed with zero warnings/errors; the production
  Next.js build passed. The raw Google Fonts request was removed.
- Render blueprint parses to exactly one service.

## Remaining code-level work

No known implementation item from the approved pre-hosting scope is left
unowned. The root WhatsApp import wrapper and frozen Streamlit facade are
intentional one-release compatibility surfaces; deleting them is a post-soak
cutover action, not a second orchestration path. New connector entries remain
disabled until operators document source authorization and reliability.

## External gates not yet satisfied

- Export and restore of the real hosted PostgreSQL database and private storage
  into a disposable environment.
- Live PostgreSQL/pgvector execution of all migrations and rollback against that
  restored environment.
- Provider/model credentials, Supabase policies, Vercel/Render configuration,
  OAuth callbacks, two-account isolation, and live operational smoke tests.
- Seven uninterrupted days of canonical web soak telemetry.
- Authorization and reliability approval for exact live-source registry
  endpoints; live connectors remain off and current claims fail closed until
  that operational review is complete.
- Native hidden bilingual benchmark, embedding selection, graph extraction gold
  labels, matched frontier-model comparisons, and farmer/expert blind review.
- Shadow and 5%/50%/100% canary activation of a complete draft corpus.
- Expert, Arabic editorial, field, institutional, privacy/legal, and publication
  approvals.

## Corpus result

The supplied DOCX remains unchanged and uncommitted at SHA-256
`3C0BAF8145E4A2E287BA5783F8AB26A7CEAE1C5340322C1EE065887CC9B75B0E`.
The converter extracts 32 chapters into 18 deduplicated atomic draft records,
resolves 35 source entries, and writes:

- `knowledge_base/agrifood_knowledge_draft_v0.2.md`
- `knowledge_base/agrifood_knowledge_draft_v0.2_ar.md`

The official validate-only release path compiles the canonical file into 36
language documents, 190 semantic chunks and claims, 162 entities, 352 aliases,
183 typed relations, and 373 evidence links. Repeated conversion is
byte-for-byte stable.
All content remains `ai_draft`, pilot-only, and production-ineligible. The
Arabic is a local repository AI draft that still requires agricultural,
linguistic, and field review.
