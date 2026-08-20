# CLAUDE.md

Guidance for Claude Code (claude.ai/code) working in this repository.

## Project overview

RAISE Akkar Farmer Assistant: an Arabic-first, bilingual agricultural
decision-support assistant for farmers in Akkar, Lebanon. It routes every answer
through local retrieval, an evidence-backed knowledge graph, bounded tools,
citations, risk rules, and verification.

The defining constraint is not "build a chatbot" — it is **source traceability
under safety pressure**. Three rules follow from that and should survive any
refactor:

1. Every claim is attributable to a reviewed passage carrying geography,
   validity, risk, and review state.
2. The system fails closed rather than degrading silently — on missing config,
   auth, an unapproved model or embedding, an unauthorised live source, or a
   database that is not at the Alembic head.
3. Software readiness is not deployment readiness. Passing tests is never
   evidence that a field, legal, or hosted gate passed.

Static pilot approval does not authorise exact chemical doses, veterinary
prescriptions, definitive diagnoses, food-processing safety parameters, or
unstamped legal/market claims.

## Commands

### Local stack — the only local mode

PostgreSQL is required. There is no SQLite fallback and no bare-uvicorn path.

```powershell
Copy-Item .env.example .env
.\scripts\raise.ps1 start -Rebuild
.\scripts\raise.ps1 smoke
```

Web 3000, API 8000, PostgreSQL 55432, Qdrant 6433, all bound to localhost.

Data commands run **inside the API container**, so they use the same
interpreter, dependencies, and network as the deployed service:

- `.\scripts\raise.ps1 build-graph` — build and activate a release
- `.\scripts\raise.ps1 evaluate` — score retrieval, gated on the Arabic gap
- `.\scripts\raise.ps1 ablate` — run the ablation ladder
- `.\scripts\raise.ps1 graph-profile` — describe the graph's structure
- `.\scripts\raise.ps1 export` / `restore -Path ...` — portable backups
- `.\scripts\raise.ps1 archive -Path ...` — v2 rollout archive

If the published PostgreSQL port stops accepting connections on Windows,
`docker compose restart postgres` re-establishes the Docker port proxy.

### Backend tests

Tests need the stack running. They create and migrate a separate `raise_test`
database beside it, so local release data is never touched. Override with
`TEST_DATABASE_URL`.

```powershell
python -m pytest -q -m "not arabic"   # inner loop
python -m pytest -q -m arabic         # required before merge
python -m ruff check farmers_chatbot tests scripts mcp_server.py
python scripts/release_preflight.py
```

### Frontend (`apps/web`)

```powershell
cd apps/web
npm ci; npx tsc --noEmit; npm run lint; npx vitest run; npm run build
```

### CI parity

`.github/workflows/ci.yml` is the source of truth: `python` (with a pgvector
service), `frontend`, `migration`, and `security` jobs.

## Architecture

### Surfaces

`farmers_chatbot/` is the shared core. Three entry points must stay
behaviourally consistent:

- `farmers_chatbot/web_api.py` → FastAPI backing the Next.js app in `apps/web/`.
  This is the pilot surface.
- `farmers_chatbot/whatsapp_router.py` → mounted in the same FastAPI app,
  fail-closed behind `WHATSAPP_ENABLED=false`. Retained deliberately: it holds
  Meta protocol work (signature verification, the webhook handshake, message-ID
  dedup, retry reusing the persisted turn) that is expensive to re-derive. It is
  blocked on API access, not on code.
- `mcp_server.py` → the bounded tool set over MCP stdio. Requires PostgreSQL
  because it serves the activated release.

Streamlit was removed. `assistant_compat.UnifiedAssistantFacade` is not a legacy
shim — it is the synchronous bridge MCP and the benchmark script need to reach
the async engine.

### Request flow

`TurnCoordinator` owns idempotency, atomic quota/cost reservation, persistence,
exactly one terminal result, and stream recovery. `AssistantEngine`
(`assistant_pipeline.py`) analyses the request, may pause for clarification,
retrieves, runs bounded tools, streams generation, and verifies. `ProviderClient`
is the only path to OpenRouter. `ToolExecutor` owns schemas, budgets, timeouts.

### Knowledge is a versioned release, not a folder of files

PostgreSQL is authoritative for immutable releases; Qdrant is a **rebuildable
projection** activated by atomic alias swap. Never activate them independently.

`knowledge_base/agrifood_knowledge_v0.3.{en,ar}.md` is the canonical corpus,
with shared knowledge, claim, entity, relation, and source IDs across languages.
`knowledge_base/legacy/` holds `guide.json` and `sources.json`, which are
**build inputs** to `scripts/convert_agrifood_docx.py` for supersedes lineage
and Arabic drafts. They are never served at runtime — that was a real safety bug
and the reason `ReleaseKnowledgeGateway` exists.

`ReleaseKnowledgeGateway` (`release_knowledge.py`) is the only release-scoped
lookup for the tool layer. It raises `ReleaseUnavailable` when nothing is
activated, and the tools then tell the model not to answer from unreviewed
material. The terminal retrieval fallback (`ProjectOnlyFallbackRetrieval`)
serves tenant project documents but never reviewed claims.

### Retrieval

`RAG_BACKEND` selects `postgres` or `qdrant`, layered as fallbacks. Routes:
`vector` (dense + BM25 fusion), `contextual` (contextual hybrid), `lazy_graph`
(two-hop expansion with Personalized PageRank). `route_override` and
`graph_hops` on `RetrievalRequest` let the ablation runner isolate each.

### Persistence

`PilotStore` is the single store — PostgreSQL only, schema versioned solely by
Alembic. It refuses any non-PostgreSQL URL. Quota, telemetry, and feedback live
here too; the separate `EvidenceStore` SQLite database was removed.

### Config

`farmers_chatbot/config.py` centralises environment settings; see `.env.example`.
`APP_ENV` is the main branch point and triggers `hosted_runtime` validation.
Client-supplied model IDs always go through `resolve_model_id()` against
`OPENROUTER_ALLOWED_MODELS`.

### Frontend

Next.js App Router + React 19 + Supabase. `lib/api.ts` wraps the backend with
SSE streaming; `components/ChatWorkspace.tsx` is the main UI and is the largest
maintenance hotspot in the repo.

## Working agreements

- **English first, Arabic gated.** Iterate with `-m "not arabic"`, then run
  `-m arabic` before merge. The `arabic_english_gap` metric is a hard gate
  (`--max-language-gap-points`, default 2.0) so English-first cannot become
  English-only.
- **Test database-dependent code against the database.** Doubles are fine for
  logic; anything whose job is talking to PostgreSQL uses the real test
  database. A gateway verified against a fake shipped two live bugs.
- **Backward compatibility is not a constraint.** v2 keeps accounts registered
  and archives prior workspace content (`scripts/archive_user_data.py`); it does
  not migrate it. Changing the data lifecycle also needs new bilingual legal
  text and a `CONSENT_VERSION` bump, because `hosted_runtime` refuses to start
  unless consent matches the deployed text.
- Active work happens on `master` and short-lived branches from it.

## Current state

See `docs/CLEANUP_PLAN_2026-08.md` for the v2 cleanup, the standing decisions,
and what each stage delivered.

The graph is well formed (mean degree 3.8, 5% orphans, 33 relation types in use,
no ambiguous aliases) and its path retrieval is real — a shuffled-path negative
control collapses accuracy from 0.891 to 0.018. But it adds no measurable
evidence-retrieval benefit on the current 240-case set, because dense and sparse
fusion alone already reaches 99.4% recall@10. There is no headroom, so the
evaluation cannot yet demonstrate the graph's value either way. Answer-level
safety, citation entailment, and frontier comparisons remain unmeasured.

`RAISE_Logframe_final.xlsx`, `.env`, and the source DOCX must never be
committed; `scripts/release_preflight.py` and the CI `security` job check.
