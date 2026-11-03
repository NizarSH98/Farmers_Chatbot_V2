# Portable target architecture

Last updated: 2026-09-01

## Boundaries

The deployable unit is standard Docker Compose. GitHub stores source, GitHub
Actions tests/builds, GHCR stores immutable images, and Dokploy operates Compose
on a Linux VPS. Dokploy and the VPS vendor are replaceable: the same images and
`compose.yaml` run with ordinary Docker Compose.

## Services

| Service | Responsibility | Network/port | Persistence |
| --- | --- | --- | --- |
| `web` | Next.js standalone server and same-origin API proxy | public through Traefik, internal 3000 | none |
| `api` | FastAPI, auth session, assistant, uploads, REST/SSE | private 8000 | private-file and model-cache volumes |
| `migrate` | one-shot `alembic upgrade head` gate | data network | PostgreSQL |
| `postgres` | authoritative relational, graph, lexical, and pgvector data | internal 5432 | named volume |
| `qdrant` | exact-release dense/sparse search projection | internal 6333 | named volume; rebuildable |
| `bootstrap` | opt-in initial/rebuild graph release job | tools profile | PostgreSQL, Qdrant, model cache |
| `backup` | pg_dump plus private files to encrypted restic repository | backup profile, outbound only | work volume; repository is off-VPS |

There is no Redis or separate worker. Current background work is request-bound
or an explicit operator job. If future work requires retryable asynchronous
jobs, add a queue and worker as an independent architecture change.

## Request and identity flow

```text
browser -> HTTPS -> web
browser -> /api/* -> web runtime proxy -> api
api -> OIDC authorization-code + PKCE provider
api -> signed HttpOnly SameSite application session + CSRF token
api -> PostgreSQL / Qdrant / private storage
```

The browser never receives database, storage, OIDC client-secret, or backend
network credentials. The application stores issuer/subject identity claims, not
provider access or refresh tokens. Access allows any verified email, an email
allowlist, or a domain allowlist.

## Data authority

PostgreSQL is authoritative for users, consent, conversations, projects,
document metadata, feedback, usage, immutable knowledge releases, evidence,
claims, entities, relations, projection state, and activation history. Alembic
is the sole managed schema mechanism.

The pgvector extension, vector dimensions, embedding approvals, and similarity
behavior are preserved. Qdrant is a rebuildable projection of an activated
PostgreSQL release; it is not in the disaster-recovery backup set.

Private files use one interface:

- `STORAGE_BACKEND=local`: named volume included in restic backups.
- `STORAGE_BACKEND=s3`: private AWS S3 or S3-compatible bucket.

Objects use safe relative keys and cannot be silently overwritten.

## Deployment invariants

- Production images are prebuilt and selected by tag; the VPS does not compile.
- Only `web:3000` attaches to a public domain.
- Base Compose publishes no host ports and has an internal data network.
- The API waits for a successful migration and healthy Qdrant.
- Stateful services use named volumes.
- Containers have no Docker socket or privileged mode.
- Application containers run as non-root users.
- TLS terminates at Dokploy/Traefik.
- Logs go to stdout/stderr.

The reform does not alter approved embeddings, dimensions, retrieval routes,
evidence lineage, assistant modes, model allowlists, or safety rules.
PostgreSQL lexical/graph retrieval remains the Qdrant-outage fallback.
