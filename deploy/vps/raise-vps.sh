#!/usr/bin/env bash
# Operator commands for the single-VPS deployment. Run from /opt/raise.
#   bash deploy/vps/raise-vps.sh <command>
set -euo pipefail
cd "$(dirname "$0")/../.."

[[ -f .env ]] || { echo "Missing .env; run deploy/vps/make-env.sh first." >&2; exit 1; }
COMPOSE=(docker compose -f compose.yaml -f compose.vps.yaml)
DOMAIN="$(grep -E '^APP_DOMAIN=' .env | cut -d= -f2-)"

preflight() {
  if grep -q 'REPLACE_ME' .env; then
    echo "Unfilled values in .env:" >&2
    grep -n 'REPLACE_ME' .env >&2
    exit 1
  fi
  if grep -qE '^APP_ENV=development' .env; then
    echo "APP_ENV is development; refusing to start a public deployment." >&2
    exit 1
  fi
  "${COMPOSE[@]}" config --quiet
}

case "${1:-help}" in
  up)
    preflight
    "${COMPOSE[@]}" pull
    "${COMPOSE[@]}" up -d --remove-orphans
    "${COMPOSE[@]}" ps
    ;;
  bootstrap)
    # Build and activate the knowledge release (first deploy, or after the
    # knowledge base changes). Downloads the embedding model once.
    "${COMPOSE[@]}" --profile tools run --rm bootstrap
    ;;
  status)
    "${COMPOSE[@]}" ps
    echo
    curl -fsS "https://${DOMAIN}/api/healthz" && echo
    echo
    free -h; df -h /
    ;;
  logs)
    shift
    "${COMPOSE[@]}" logs -f --tail 200 "$@"
    ;;
  update)
    # Pull the newest images CI published from master and restart.
    preflight
    "${COMPOSE[@]}" pull
    "${COMPOSE[@]}" up -d --remove-orphans
    docker image prune -f
    ;;
  pin)
    # Pin all three images to one commit: raise-vps.sh pin <full-40-char-sha>
    sha="${2:?usage: pin <full git sha>}"
    for svc in api web backup; do
      key="$(echo "$svc" | tr a-z A-Z)_IMAGE"
      sed -i "s|^${key}=.*|${key}=ghcr.io/nizarsh98/farmers_chatbot_v2-${svc}:sha-${sha}|" .env
    done
    grep -E '^(API|WEB|BACKUP)_IMAGE=' .env
    echo "Now run: bash deploy/vps/raise-vps.sh up"
    ;;
  research-export)
    # Pseudonymous pilot interaction dataset (participant codes only), copied
    # to ./pilot_exports/research-<stamp>. Download it with scp, then delete it
    # from the server.
    stamp="$(date -u +%Y%m%d-%H%M%S)"
    inside="/tmp/raise-research-${stamp}"
    "${COMPOSE[@]}" exec -T --workdir /app api python -m scripts.export_research_dataset --output "$inside"
    mkdir -p pilot_exports
    chmod 700 pilot_exports
    api="$("${COMPOSE[@]}" ps -q api)"
    docker cp "${api}:${inside}" "pilot_exports/research-${stamp}"
    "${COMPOSE[@]}" exec -T api rm -rf "$inside"
    echo "pilot_exports/research-${stamp}"
    ;;
  stop)
    "${COMPOSE[@]}" stop
    ;;
  *)
    echo "commands: up | bootstrap | status | logs [service] | update | pin <sha> | research-export | stop"
    ;;
esac
