# Canonical Pilot Deployment Runbook

Last updated: 2026-08-11

This is the authoritative deployment topology for the current RAISE pilot:

- Vercel: the only long-term user interface, from `apps/web`
- Render: one FastAPI service, `farmers_chatbot.web_api:app`
- Supabase: managed PostgreSQL, pgvector, authentication, and private storage
- OpenRouter: the single model and embedding gateway

`rag_chatbot.py` is a one-release compatibility client only. Do not create a
new hosted Streamlit deployment. The WhatsApp router is already mounted in the
canonical FastAPI app but is fail-closed behind `WHATSAPP_ENABLED=false`.
`whatsapp_api.py` is only an import wrapper; do not deploy a second service.

## Local development

Use Python 3.12 and Node.js 22.12 or newer.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
alembic upgrade head
uvicorn farmers_chatbot.web_api:app --reload --port 8000
```

In a second terminal:

```powershell
Set-Location apps/web
Copy-Item .env.example .env.local
npm ci
npm run dev
```

SQLite and local object storage are development-only. Pilot and production
startup fail closed unless PostgreSQL, the exact Alembic head, Supabase private
storage, authentication, origins, consent/retention settings, provider
credentials, and model allowlists are valid.

## Required pre-deployment gates

1. Export the hosted database and every private storage object with
   `scripts/pilot_data_portability.py`.
2. Restore the export into a disposable PostgreSQL/Supabase environment and
   verify users, consent, conversations, projects, documents, artifacts,
   feedback, usage events, and object hashes.
3. Run `alembic upgrade head` against that disposable database and exercise
   activation/rollback of a knowledge release.
4. Run the repository gates:

   ```powershell
   python -m compileall -q farmers_chatbot scripts mcp_server.py whatsapp_api.py
   python -m ruff check .
   python -m pytest -q
   python -m pip_audit -r requirements.txt
   Set-Location apps/web
   npm ci
   npm audit --omit=dev
   npm run typecheck
   npm test
   npm run lint
   npm run build
   ```

5. Keep `RAG_VECTOR_BENCHMARK_APPROVED=false` until a hidden bilingual
   benchmark selects a model and dimension. Lexical and graph retrieval remain
   the fallback.
6. Keep `WHATSAPP_ENABLED=false` until the web soak is complete.
7. Keep `ENABLE_TRUSTED_WEB_SEARCH=false` until
   `config/live_sources.v1.json` contains reviewed, exact, authorized
   endpoints. Hosted startup rejects an enabled empty/invalid registry.

## Supabase

- Use a dedicated pilot project in an approved region.
- Keep the storage bucket private and grant no anonymous object policy.
- Give migrations a direct database connection; use an appropriate pooler for
  application traffic.
- Install/enable the extensions required by migration `20260811_0003`,
  including pgvector, and verify the live DDL on the disposable restore before
  touching pilot data.
- Preserve tenant filters in application queries and test two-account isolation
  for projects, conversations, files, artifacts, and project chunks.

## Render backend

Deploy only `raise-esdu-web-api` from `render.yaml`. Automatic deployment is
disabled and `preDeployCommand` applies Alembic migrations.

Set managed secrets for the PostgreSQL URL, OpenRouter, Supabase, allowed Vercel
origin, public URL, and privacy contact. Do not set local SQLite/storage paths as
hosted fallbacks. Verify `GET /healthz`, authentication, consent, data export,
account deletion, SSE interruption recovery, and exact terminal turn state.

## Vercel frontend

Deploy `apps/web` and configure:

- `NEXT_PUBLIC_API_URL`: exact HTTPS origin of the Render API
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`

Register the exact Vercel callback/origin with Supabase. Validate Arabic/RTL,
low-bandwidth operation, projects, document upload, artifacts, exports, source
review badges, the session-level draft warning, and interrupted-stream recovery.

## Soak and channel cutover

Run an internal seven-day web soak with telemetry for terminal events,
retrieval channels, graph paths, citations, tools, abstentions, provider usage,
latency, and cost. Any critical error, missing terminal event, cross-tenant
evidence, or data-loss incident resets the soak.

After the soak, WhatsApp may be enabled only on the already-mounted canonical
FastAPI router. Meta message IDs are idempotency keys; outbound retries reuse
the persisted turn; raw phone numbers are never stored. Remove the root import
wrapper after one compatibility release.

## Corpus rollout

The draft Markdown corpus must be validated and ingested as a new immutable
release. It cannot be activated for production. Shadow it first, then canary the
pilot pointer at 5%, 50%, and 100%, recording evaluation and safety telemetry at
each stage. Rollback changes the active-release pointer atomically. Expert
approval creates a separate approved release; it never mutates or silently
promotes draft records.

## Stop conditions

Stop or roll back for a critical unsafe recommendation, failed migration,
unrestorable data, tenant isolation failure, unsupported high-risk claim,
missing terminal event, provider-policy violation, or material regression in
the hidden evaluation. Revoke exposed credentials and preserve incident
evidence when applicable.
