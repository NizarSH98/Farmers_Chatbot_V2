# Canonical pilot runbook

> **ARCHIVED.** This short checklist was superseded by the complete operator
> guide.

The canonical operator procedure is [DEPLOYMENT.md](../../DEPLOYMENT.md). It applies
to local Docker, a Dokploy-managed VPS, or any Linux host with Docker Compose.

Pilot deployments must use:

- `APP_ENV=pilot`, HTTPS, and `WEB_AUTH_MODE=oidc`;
- immutable GHCR `sha-<commit>` tags;
- strong PostgreSQL/session/Qdrant secrets;
- private local storage with tested off-VPS backup, or private S3 storage;
- the backup profile with an encrypted repository outside the VPS;
- only the `web` service routed publicly.

Do not enable WhatsApp until the canonical web deployment has completed its
approved soak and protocol/security review.
