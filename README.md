# RAISE Akkar Farmer Assistant

RAISE is an Arabic-first, bilingual agricultural decision-support application.
It combines a Next.js workspace, a FastAPI assistant engine, versioned local
knowledge, PostgreSQL/pgvector, and a rebuildable Qdrant search projection.

## Product direction

The exact experience to build is defined in the
[product experience specification](docs/product/PRODUCT_EXPERIENCE_SPEC.md).
It specifies novice-facing chat behavior, answer structure, reliability labels,
projects, frontend/backend boundaries, delivery phases, and acceptance tests.
Approve that contract before beginning the UI/backend redesign.

## Repository map

| Path | Purpose |
| --- | --- |
| apps/web | Next.js browser application and same-origin API proxy |
| farmers_chatbot | FastAPI, assistant pipeline, persistence, retrieval, auth, and storage package |
| migrations | Ordered Alembic PostgreSQL schema revisions |
| knowledge_base | Reviewed bilingual knowledge and deterministic build inputs |
| evaluation | Versioned evaluation datasets and reports |
| scripts | Operator, bootstrap, evaluation, and maintenance commands |
| deploy | Backup and restore container scripts |
| docs | Active product, architecture, operations, governance, and template index |
| legal | Bilingual user agreement and privacy text rendered by the API |
| config | Versioned non-secret source/model registries |
| tests | Backend, integration, migration, storage, and policy tests |

Start with [the documentation map](docs/README.md), the
[frontend map](apps/web/README.md), or the
[backend map](farmers_chatbot/README.md) instead of browsing filenames.

## Runtime architecture

```text
Internet
  -> Dokploy / Traefik (TLS)
  -> Next.js web :3000
       -> same-origin /api proxy
       -> FastAPI :8000
            -> PostgreSQL + pgvector :5432 (authoritative)
            -> Qdrant :6333 (rebuildable projection)
            -> private local volume or S3-compatible storage
            -> OpenRouter when connected generation is enabled

GitHub Actions -> GHCR SHA-tagged images -> Dokploy Compose deployment
PostgreSQL dump + local private files -> encrypted off-VPS restic repository
```

Only the Next.js service is publicly routed. The API, database, and Qdrant use
Docker networks. There is no Redis or always-on worker because the current
application has no durable queue workload that justifies either service.

## Local start

Prerequisites are Docker Desktop and PowerShell. Host Python and Node are only
needed for development checks, not to run the stack.

```powershell
Copy-Item .env.example .env
.\scripts\raise.ps1 start -Rebuild
.\scripts\raise.ps1 build-graph
.\scripts\raise.ps1 smoke
.\scripts\raise.ps1 status
```

The local overlay binds only to loopback: web 3000, API 8000, PostgreSQL 55432,
and Qdrant 6433. Local Compose explicitly disables login. Pilot and production
startup fail closed unless OIDC, HTTPS, secrets, migrations, and storage are
configured correctly.

Useful commands:

```powershell
.\scripts\raise.ps1 logs
.\scripts\raise.ps1 evaluate
.\scripts\raise.ps1 ablate
.\scripts\raise.ps1 graph-profile
.\scripts\raise.ps1 export
.\scripts\raise.ps1 stop
```

## Development gates

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe scripts\release_preflight.py
.\.venv\Scripts\python.exe -m ruff check farmers_chatbot scripts tests mcp_server.py
.\.venv\Scripts\python.exe -m pytest -q -m "not arabic"
.\.venv\Scripts\python.exe -m pytest -q -m arabic
npm ci --prefix apps/web
npm run typecheck --prefix apps/web
npm run lint --prefix apps/web
npm run test --prefix apps/web
npm run build --prefix apps/web
docker compose -f compose.yaml config --quiet
docker compose -f compose.yaml -f compose.override.yaml config --quiet
```

## Operations

The [documentation map](docs/README.md) identifies the authoritative file for
each kind of work. The operating source of truth is
[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md). It covers GHCR,
fresh VPS setup, Dokploy, environment, migrations, bootstrap, backups, restores,
updates, rollback, monitoring, troubleshooting, and disaster recovery.

See also [architecture](docs/ARCHITECTURE.md), [database
migrations](docs/DATABASE_MIGRATIONS.md), and the [migration
report](docs/MIGRATION_REPORT.md).

## Safety and license

RAISE is decision support, not a substitute for an agronomist, veterinarian,
laboratory, engineer, food-safety professional, or competent authority.
Software is MIT-licensed. Knowledge-source copyrights and institutional naming
rights remain separate.
