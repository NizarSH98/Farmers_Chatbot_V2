# Infrastructure migration report

Date: 2026-09-01

## 1. Original architecture

The product used a Next.js frontend intended for Vercel, one FastAPI service
described by a Render blueprint, and Supabase for browser authentication and
private objects. Application data was
already standard PostgreSQL/Alembic with pgvector. Qdrant was a rebuildable
projection. Local Compose existed, but API startup applied migrations implicitly
and production image publication/deployment was absent.

## 2. Final architecture

GitHub Actions validates and builds three images, GHCR stores SHA-tagged images,
and production Compose runs Next.js, FastAPI, PostgreSQL/pgvector, Qdrant, a
one-shot migration job, an opt-in bootstrap job, and encrypted off-VPS backups.
Dokploy supplies deployment, Traefik routing, TLS, logs, and metrics but is not
required by the runtime.

## 3. Provider dependencies removed

- Vercel hosting assumptions became a multi-stage Next.js standalone image.
- The Render blueprint became the FastAPI image, healthcheck, graceful
  ASGI process, Compose gates, and GHCR flow.
- Supabase browser SDK auth became OIDC authorization code with PKCE, signed
  application sessions, CSRF defense, and issuer/subject identity.
- Managed private storage calls became local-volume and S3-compatible backends.
- Standard PostgreSQL, Alembic SQL, pgvector behavior, and issuer/subject data
  were preserved. Realtime, edge functions, and RLS were not used.

## 4. Files changed

- Runtime: auth, OIDC, settings/guard, API session routes, generic identity,
  storage backends.
- Database: revision `20260901_0007` and expected-head checks.
- Frontend: same-origin proxy/session and CSRF client, standalone image, provider
  SDK removal.
- Containers: API, web, backup Dockerfiles; production/local/restore Compose.
- CI/CD: tests, security, Buildx, GHCR metadata/publish, optional webhook.
- Operations: restic scripts, environment template, and operator documentation.

## 5. Database migration status

The Alembic graph is linear at `20260901_0007`. The revision removes only the
obsolete vendor-auth ID column/index. This release is an authorized fresh user
reset; no identity migration is needed. PostgreSQL/pgvector remain authoritative
and Qdrant remains rebuildable.

## 6. Container architecture

`web` is public; `api`, `postgres`, and `qdrant` are private. `migrate`
is a required one-shot gate. `bootstrap` is an operator tool. `backup` sends
database dumps/local files to external encrypted storage. No Redis or separate
worker is justified by current workloads.

## 7. CI/CD pipeline

Pull requests run Python, frontend, migration, security, and container builds.
Successful default-branch pushes publish API/web/backup as immutable
`sha-<full-commit>` plus `latest`. A Dokploy webhook can deploy after
publication; controlled production promotion uses exact SHA tags.

## 8. VPS deployment procedure

Prepare Linux/Docker/Dokploy, connect repository and GHCR, create Compose from
`compose.yaml`, configure secrets/exact image tags, route only `web:3000`,
deploy, bootstrap knowledge, and run health/auth/query/file checks. Exact steps
are in `docs/DEPLOYMENT.md`.

## 9. Environment variables

Production requires application URL/metadata, OIDC/session secrets, access
policy, PostgreSQL/Qdrant secrets, storage choice, restic credentials, RAG
approvals, optional OpenRouter values, and three image tags. The template has
names and safe local defaults only.

## 10. Backup and restore

The backup profile makes custom PostgreSQL dumps and backs up the local
private-file volume through encrypted restic to S3-compatible storage outside
the VPS, with daily/weekly/monthly retention. The restore helper decrypts and
validates the archive. A full rehearsal uses a disposable database and rebuilt
Qdrant.

## 11. Security changes

Only the frontend is public. Production has no host database/Qdrant/API ports,
permissive CORS bridge, browser service key, privileged container, Docker
socket, or development server. Hosted sessions are HttpOnly, Secure, SameSite,
short-lived, and CSRF protected. Configuration fails closed.

## 12. Test results

Local validation completed on 2026-09-01:

- Python: 212 passed and 2 skipped in the non-Arabic gate; 6 passed in the
  separate Arabic gate. Ruff, compileall, pip consistency, release preflight,
  Alembic graph/offline SQL, and PowerShell parsing passed.
- Frontend: typecheck and lint passed; 4 test files/15 tests passed; the Next.js
  production build passed with `/`, `/admin`, and `/api/[...path]`; production
  `npm audit` reported 0 vulnerabilities.
- Security/dependencies: both Python dependency audits reported no known
  vulnerabilities; tracked and untracked source secret-pattern scans passed.
- Fresh database: migration head is `20260901_0007`, pgvector is `0.8.1`, and a
  transactional vector insert/read/distance check passed.
- Knowledge bootstrap: 36 sources/documents, 192 chunks/claims, 260 entities,
  494 relations, and 686 evidence links. Qdrant contains 384 evidence points and
  260 entity points; vector, contextual, and lazy-graph smoke routes passed.
- Application flow: consent, project creation, private upload/download, and
  account deletion passed through the Next.js proxy. The 47-byte persistence
  probe matched SHA-256
  `a202db412e7da09c504ea1e1082ee337b4424ac0ffb7ee664b1776b60edc31d3`.
- Persistence: a normal dependency-gated restart preserved migration state,
  the active release, Qdrant projection, private file, and model cache. The
  synthetic account/file was then deleted, leaving 0 users and 0 projects.
- Recovery: encrypted restic snapshot `35f48dbd` was decrypted and validated,
  then restored into a separate PostgreSQL 16/pgvector Compose project. Its
  revision and database/graph counts matched the source; the restored private
  file checksum matched exactly. Disposable restore/test volumes were removed.
- Images/runtime: API, web, and backup images built; application images run as
  non-root users; all live services are healthy, migration exited 0, Qdrant
  telemetry is disabled, and public checks go through the web proxy.

External account integrations are intentionally not reported as locally
tested.

## 13. Remaining risks

Live OIDC, external S3/restic, DNS/TLS, GHCR publication, GitHub-hosted Actions,
and Dokploy require real accounts and cannot be proven locally. External AI
behavior and operational soak remain separate approvals. Repeat a real restore
rehearsal against the selected backup target.

## 14. Manual actions required

Authorize OIDC; create private storage/backup buckets and credentials; set
GitHub/Dokploy secrets; point DNS; select image SHAs; perform the first Dokploy
deploy/bootstrap; verify external backups; and run production acceptance/soak.

## 15. Rollback procedure

For application-only changes, select the prior three SHA tags and redeploy. For
incompatible schema change, restore the pre-release database/files into new
state, deploy matching prior SHAs, rebuild Qdrant, validate, then switch traffic.
Never guess at a destructive live downgrade.

## 16. Fresh-machine readiness

A clean host needs Linux, Docker Compose, optional Dokploy, registry access,
environment secrets, and backup custody. Python, Node, PostgreSQL clients,
pgvector, and restic are in images. Final readiness is conditional only on the
external manual integrations and acceptance checks above.
