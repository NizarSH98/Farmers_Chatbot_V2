#!/usr/bin/env bash
# Generate a production .env for a single-VPS pilot from .env.example.
#   bash deploy/vps/make-env.sh <domain> <operator-email>
# Generates every internal secret; leaves exactly the external values you must
# paste (OIDC client ID/secret, OpenRouter key) as REPLACE_ME. Refuses to
# overwrite an existing .env.
set -euo pipefail

DOMAIN="${1:-}"
EMAIL="${2:-}"
if [[ -z "$DOMAIN" || -z "$EMAIL" ]]; then
  echo "usage: bash deploy/vps/make-env.sh <domain> <operator-email>" >&2
  exit 1
fi
cd "$(dirname "$0")/../.."
if [[ -e .env ]]; then
  echo ".env already exists; refusing to overwrite (move it away first)." >&2
  exit 1
fi

# Hex secrets: POSTGRES_PASSWORD is interpolated into a URL, so avoid symbols.
secret() { openssl rand -hex 32; }

cp .env.example .env
chmod 600 .env

set_key() {
  local key="$1" value="$2"
  if grep -q "^${key}=" .env; then
    # '|' delimiter: values contain '/' and ':'; none of ours contain '|'.
    sed -i "s|^${key}=.*|${key}=${value}|" .env
  else
    printf '%s=%s\n' "$key" "$value" >> .env
  fi
}

# Application
set_key APP_ENV pilot
set_key APP_PUBLIC_URL "https://${DOMAIN}"
set_key PRIVACY_CONTACT_EMAIL "$EMAIL"
set_key FORWARDED_ALLOW_IPS 127.0.0.1

# Authentication (Google OIDC by default; change issuer for another provider)
set_key WEB_AUTH_MODE oidc
set_key APP_SESSION_SECRET "$(secret)"
set_key ACCESS_POLICY any_verified_email
set_key ADMIN_EMAILS "$EMAIL"
set_key OIDC_ISSUER_URL https://accounts.google.com
set_key OIDC_CLIENT_ID REPLACE_ME
set_key OIDC_CLIENT_SECRET REPLACE_ME
set_key OIDC_REDIRECT_URI "https://${DOMAIN}/api/auth/callback"
set_key AUTH_POST_LOGIN_REDIRECT_URL "https://${DOMAIN}"

# Database / vector store (Compose builds the internal URLs from these)
set_key POSTGRES_PASSWORD "$(secret)"
set_key DATABASE_URL ""
set_key CLARIFICATION_DATABASE_URL ""
set_key QDRANT_API_KEY "$(secret)"
set_key QDRANT_URL http://qdrant:6333

# Storage: local Docker volume (covered by Lightsail snapshots + restic backup)
set_key STORAGE_BACKEND local
set_key LOCAL_FILE_ROOT /app/data/private

# AI
set_key OPENROUTER_API_KEY REPLACE_ME

# Backups (restic). Fill these in, then set COMPOSE_PROFILES=backup.
set_key RESTIC_PASSWORD "$(secret)"
set_key BACKUP_HOST "$DOMAIN"

# Images published by CI from master
set_key API_IMAGE ghcr.io/nizarsh98/farmers_chatbot_v2-api:latest
set_key WEB_IMAGE ghcr.io/nizarsh98/farmers_chatbot_v2-web:latest
set_key BACKUP_IMAGE ghcr.io/nizarsh98/farmers_chatbot_v2-backup:latest
set_key NEXT_PUBLIC_LOCAL_AUTH false

# VPS overlay: makes a bare `docker compose` use production files only and
# never the local compose.override.yaml (which disables auth).
set_key COMPOSE_FILE compose.yaml:compose.vps.yaml
set_key COMPOSE_PROFILES ""
set_key APP_DOMAIN "$DOMAIN"
set_key ACME_EMAIL "$EMAIL"

echo "Wrote .env (mode 600). Still to fill in:"
grep -n 'REPLACE_ME' .env
echo
echo "IMPORTANT: copy RESTIC_PASSWORD into your password manager now."
echo "Losing it makes every encrypted backup unrecoverable."
