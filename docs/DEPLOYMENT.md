# Deployment and operations

Last updated: 2026-09-01

ProjectGraph records the architecture and release acceptance gates. This document
is the operator guide; current evidence and open gaps are recorded in
[the delivery audit](../reports/DELIVERY_AUDIT.md).
Examples use `raise.example.org`; substitute the real domain. Never put real
secrets in Git, Compose YAML, shell history, or screenshots.

## 1. Architecture

```text
Git push
  -> GitHub Actions: Python, frontend, migration, security, image builds
  -> GHCR: API, web, and backup images tagged sha-<40-char commit> and latest
  -> Dokploy Compose on a VPS
       -> Traefik HTTPS -> web:3000
       -> web /api proxy -> api:8000
       -> api -> PostgreSQL/pgvector + Qdrant + private storage
       -> backup -> encrypted restic repository outside the VPS
```

`compose.yaml` is production and registry-pull oriented.
`compose.override.yaml` adds local builds and loopback ports. Do not load the
local override in Dokploy.

Single-VPS alternative without Dokploy: `compose.vps.yaml` adds one Caddy
container for automatic HTTPS in front of `web:3000`, and `deploy/vps/`
provides host setup, `.env` generation, and operator commands. The AWS
walkthrough is [AWS Lightsail deployment](DEPLOY_AWS_LIGHTSAIL.md).

## 2. Local development

Requirements: Docker Desktop with Compose v2 and enough memory/disk for the
local embedding model. Ollama and OpenRouter are optional unless the selected
operation needs connected generation.

```powershell
git clone <repository-url>
Set-Location Farmers_Chatbot_V2
Copy-Item .env.example .env
.\scripts\raise.ps1 start -Rebuild
.\scripts\raise.ps1 build-graph
.\scripts\raise.ps1 smoke
.\scripts\raise.ps1 status
```

Open `http://127.0.0.1:3000`. Local auth is deliberately disabled by the
overlay; these images must never be promoted to production. Stop without
deleting data using `.\scripts\raise.ps1 stop`. Follow logs using:

```powershell
docker compose -f compose.yaml -f compose.override.yaml logs -f --tail 200
```

### Local operator command card

Run these from the repository root. The two Compose files are intentional:
the base is the deployable stack and the override adds local builds and
loopback-only ports.

| Action | Command |
| --- | --- |
| START | `.\scripts\raise.ps1 start` (add `-Rebuild` after code/dependency changes) |
| STOP | `.\scripts\raise.ps1 stop` (named volumes survive) |
| RESTART | `.\scripts\raise.ps1 restart` |
| STATUS | `.\scripts\raise.ps1 status` |
| LOGS | `docker compose -f compose.yaml -f compose.override.yaml logs -f --tail 200` |
| MIGRATE/CHECK | `docker compose -f compose.yaml -f compose.override.yaml run --rm migrate python -m alembic current --check` |
| BOOTSTRAP | `.\scripts\raise.ps1 build-graph` |
| SMOKE TEST | `.\scripts\raise.ps1 smoke` |
| BACKUP STATUS | `docker compose -f compose.yaml -f compose.override.yaml --profile backup ps` |
| BACKUP LOGS | `docker compose -f compose.yaml -f compose.override.yaml --profile backup logs --tail 100 backup` |
| TEST RESTORE | `docker compose -f compose.yaml -f compose.override.yaml --profile backup run --rm --entrypoint /usr/local/bin/raise-restore backup latest` |

Local update cycle: fetch/review the intended Git change, rebuild with
`.\scripts\raise.ps1 start -Rebuild`, run migrations and bootstrap if their
inputs changed, then run smoke/manual checks. Production updates and rollbacks
select the same three immutable image SHA tags in Dokploy; see sections 10 and
11. Never mix API, web, and backup tags from different commits.

Fresh local reset (irreversibly deletes the local PostgreSQL, Qdrant, files,
model cache, and backup-work volumes):

```powershell
docker compose -f compose.yaml -f compose.override.yaml down --volumes --remove-orphans
.\scripts\raise.ps1 start -Rebuild
.\scripts\raise.ps1 build-graph
.\scripts\raise.ps1 smoke
```

Do not run that reset on a VPS. A production reset/restore requires an incident
plan, a verified external backup, and explicit approval.

## 3. Production images and GHCR

On pull requests, CI builds but does not publish. A successful push to the
default branch publishes:

```text
ghcr.io/<owner>/<repository>-api:sha-<full-git-sha>
ghcr.io/<owner>/<repository>-web:sha-<full-git-sha>
ghcr.io/<owner>/<repository>-backup:sha-<full-git-sha>
```

It also updates `:latest`. Production releases should select the three exact
`sha-...` tags. `:latest` is convenient for a continuous environment but is
not an adequate rollback record. OCI labels record the Git revision.

GitHub Actions uses `GITHUB_TOKEN` to publish packages. Set repository secret
`DOKPLOY_DEPLOY_WEBHOOK` only for optional latest-tracking deployment.

## 4. Fresh VPS preparation

Use any supported Linux VPS; no host-vendor API is required.

1. Apply OS updates and create a non-root sudo operator.
2. Use SSH keys, disable password login after verifying access, and restrict the
   management panel by firewall/VPN where practical.
3. Allow inbound 80/443 and required SSH sources. Do not allow 5432, 6333, 8000,
   or 3000 directly.
4. Install Docker Engine/Compose and Dokploy using maintained procedures.
5. Point the application DNS record at the VPS before requesting TLS.
6. Confirm free disk and memory for models, database, Qdrant, and images.
7. Prepare an S3-compatible bucket outside this VPS for backups. Enable
   versioning/object lock where available.

The VPS needs no global Python, Node, PostgreSQL client, or restic installation.

## 5. Dokploy configuration

1. Connect the GitHub repository or a read-only Git source.
2. Create a project/environment and a **Docker Compose** service.
3. Select the production branch and Compose path `./compose.yaml`.
4. Enable isolated deployments. Do not use Docker Stack mode.
5. Add registry `ghcr.io`, a GitHub username, and a minimally scoped token
   able to read private packages. Public packages need no credentials.
6. Add the production environment from section 6.
7. Set `API_IMAGE`, `WEB_IMAGE`, and `BACKUP_IMAGE` to the same release's
   exact `sha-...` tag. Set `COMPOSE_PROFILES=backup`.
8. Preview Compose. Confirm no host `ports:` and an internal data network.
9. In Domains, add only service `web`, container port `3000`, path `/`,
   HTTPS, and Let's Encrypt. Do not create an API/database domain.
10. Deploy. The migration service must exit 0 before API/web start.
11. Run the initial bootstrap from the Compose working directory/terminal:

```text
docker compose -f compose.yaml --profile tools run --rm bootstrap
```

12. Redeploy after a Compose domain change, then verify section 10.

Dokploy Environment values are stored in the deployment `.env`; Compose maps
required values into containers. Named volumes survive redeployments.

## 6. Production environment

Start from `.env.example`. Required production values:

### Application

- `APP_ENV=pilot` or `production`
- `APP_PUBLIC_URL=https://raise.example.org`
- real display, organization, privacy-contact, consent, and retention values
- `FORWARDED_ALLOW_IPS`: only trusted reverse-proxy addresses; never `*`

### Authentication

- `WEB_AUTH_MODE=oidc`
- `APP_SESSION_SECRET`: random 32+ character secret
- OIDC issuer, client ID/secret, scopes, and exact redirect URI
- redirect URI: `https://raise.example.org/api/auth/callback`
- post-login URL: `https://raise.example.org`
- access policy and any allowed/admin lists

Register the exact callback. The flow is authorization code with PKCE. The app
keeps a signed HttpOnly session, not provider tokens.

### Database and vector service

- strong unique `POSTGRES_PASSWORD`
- strong `QDRANT_API_KEY`
- unchanged approved RAG model/dimension/benchmark values

Compose constructs internal database/Qdrant URLs. Do not publish their ports.

### Private storage

- Small pilot: `STORAGE_BACKEND=local`; its volume must be externally backed
  up.
- S3: set endpoint, region, private bucket, access key, secret, and path style.
  Use a bucket-specific least-privilege identity.

### External backup

- `RESTIC_REPOSITORY=s3:https://<endpoint>/<bucket>/<prefix>`
- strong independent `RESTIC_PASSWORD` stored in the password vault
- backup-only S3 credentials, region, interval/retention/host
- `COMPOSE_PROFILES=backup`

Losing the restic password makes encrypted backups unrecoverable.

### AI and optional channels

Configure OpenRouter only when connected answers are required. Keep zero-data
retention enforcement and the model allowlist. WhatsApp remains false unless
separately approved and configured.

## 7. Database initialization and migrations

On every deploy PostgreSQL becomes healthy, `migrate` runs `alembic upgrade
head`, and API starts only on success. API readiness checks the exact revision.
For a fresh deployment, bootstrap knowledge after the first migration. For an
upgrade, verify a backup first. Never edit an applied revision or use
`alembic stamp` to bypass it.

```text
docker compose -f compose.yaml ps
docker compose -f compose.yaml run --rm migrate python -m alembic current --check
```

## 8. Backups

The backup container creates a custom-format `pg_dump`, then sends that dump
and local private files to encrypted off-VPS restic storage. It runs at startup
and on the configured interval. Defaults retain 7 daily, 4 weekly, and 6 monthly
snapshots with pruning.

Qdrant is excluded because it rebuilds from PostgreSQL. With S3 file storage,
configure independent bucket versioning/replication because the local file
volume is empty.

```text
docker compose -f compose.yaml --profile backup ps
docker compose -f compose.yaml --profile backup logs --tail 100 backup
docker compose -f compose.yaml --profile backup run --rm --entrypoint restic backup snapshots
docker compose -f compose.yaml --profile backup run --rm --entrypoint restic backup check
```

Alert on an unhealthy backup container, stale `last-success`, or failed check.

## 9. Test restore

Test restoration on a schedule and before risky schema releases. Never restore
over the active database.

1. Restore and structurally validate a snapshot:

```text
docker compose -f compose.yaml --profile backup run --rm \
  --entrypoint /usr/local/bin/raise-restore backup latest
```

2. From the printed work path, locate the verified `raise-*.dump`.
3. Start disposable PostgreSQL 16/pgvector on an isolated network.
4. Restore with:

```text
pg_restore --exit-on-error --no-owner --no-privileges \
  --dbname=<empty-disposable-database> <raise-dump>
```

5. Apply migrations, start disposable API/web/Qdrant, rebuild Qdrant, and run
   `python -m scripts.local_smoke_test`.
6. Verify revision, release ID, counts, file flows, and user isolation. Record
   snapshot ID, image SHAs, operator, date, and outcome.
7. Remove the disposable environment only after review.

The helper proves restic decryption/download and `pg_restore` archive parsing.
That is structural validation, not a complete business-data rehearsal.

## 10. Release and update procedure

Controlled production promotion:

1. Open a reviewed pull request and let every CI job pass.
2. Merge to the default branch.
3. Record the successful commit SHA and three published packages.
4. Verify a backup if the release has a migration.
5. In Dokploy, change all three image variables to
   `sha-<that-same-full-commit>`.
6. Preview Compose, deploy, and watch migration/application logs.
7. Run:

```text
curl --fail https://raise.example.org/
curl --fail https://raise.example.org/api/healthz
```

8. Sign in, create a conversation, run a source-backed query, upload/download a
   private test file, and verify admin restriction.
9. Record SHA, migration revision, active release ID, deployment ID, and backup
   snapshot in the release log.

Optional continuous deployment: set images to `:latest`, copy the Dokploy
Compose deploy webhook to GitHub secret `DOKPLOY_DEPLOY_WEBHOOK`, and keep
`pull_policy: always`. This is less controlled; retain the GitHub SHA and OCI
revision for each deployment.

## 11. Rollback

If no incompatible database migration was applied:

1. Select the previous release record.
2. Set all three image variables to its exact SHA tags.
3. Deploy, verify health/login/query/file flow, and record the rollback.

If schema changed incompatibly:

1. Stop writes.
2. Provision a new PostgreSQL volume/database.
3. Restore the pre-release restic snapshot into it.
4. Restore private files if required.
5. Deploy matching prior image SHAs against restored state.
6. Rebuild Qdrant, validate, then switch traffic.

Do not guess at an Alembic downgrade on the live database. Preserve failed
containers/logs until the incident record is complete.

## 12. Monitoring and routine checks

Dokploy provides deployment history, per-service logs, metrics, and container
state. Also use:

```text
docker compose -f compose.yaml ps
docker compose -f compose.yaml logs --since 30m api web migrate postgres qdrant backup
docker stats --no-stream
docker system df
df -h
free -h
curl --fail https://raise.example.org/api/healthz
```

Health should show `status=ok`, migration `20260901_0007`, an active release
after bootstrap, Qdrant reachable, and fallback ready. Monitor:

- HTTPS availability and latency;
- restart count and unhealthy containers;
- CPU, memory, disk, and inode pressure;
- PostgreSQL connections/locks and volume growth;
- API 5xx/auth failures and request IDs;
- Qdrant projection state;
- backup freshness and restic check;
- OpenRouter errors, budgets, and quota denials.

## 13. Troubleshooting

| Symptom | Check | Corrective action |
| --- | --- | --- |
| web 502/404 | Dokploy domain service/port and web health | route only `web:3000`; redeploy after domain changes |
| `/api` 502 | web/API logs, `API_INTERNAL_URL`, edge network | restore `http://api:8000`; verify API health |
| API will not start | migrate logs and `alembic_version` | fix migration/config; never bypass the gate |
| login loop | issuer metadata, exact callback, HTTPS, system clock | correct OIDC registration and time |
| POST returns 403 | browser session and CSRF header | sign in again; do not disable CSRF |
| database unavailable | health, password, volume, disk | correct secret; free disk safely; inspect logs |
| Qdrant unavailable | key, health, network, projection | repair then bootstrap; PostgreSQL fallback remains |
| backup unhealthy | logs, S3 reachability, password, credentials | correct repository access and rerun |
| image did not update | env tag, registry auth, pull logs | select exact new SHA and redeploy |
| container restarts | inspect, logs, memory/disk | fix the reported cause; do not just raise retries |

Use `X-Request-ID` to correlate user errors with API logs. Never paste
environment dumps or signed object URLs into tickets.

## 14. Disaster recovery on a clean VPS

Custody items: repository access, exact GHCR SHA tags, production secrets, OIDC
client control, DNS control, restic password/repository credentials, and latest
verified snapshot.

1. Prepare a new Linux VPS and install Docker/Dokploy.
2. Connect GHCR and create the Compose service from `compose.yaml`.
3. Restore PostgreSQL and local private files into new named volumes.
4. Configure exact prior image SHAs and production environment.
5. Deploy, migrate if necessary, and rebuild Qdrant.
6. Run health, auth, isolation, file, and representative query tests.
7. Change DNS and monitor closely.

No host Python/Node packages, developer cache, local database, or
provider-specific hosting service is required.
