#!/bin/sh
set -eu

: "${RESTIC_REPOSITORY:?RESTIC_REPOSITORY is required}"
: "${RESTIC_PASSWORD:?RESTIC_PASSWORD is required}"
: "${PGHOST:?PGHOST is required}"
: "${PGDATABASE:?PGDATABASE is required}"
: "${PGUSER:?PGUSER is required}"

interval="${BACKUP_INTERVAL_SECONDS:-86400}"
keep_daily="${BACKUP_KEEP_DAILY:-7}"
keep_weekly="${BACKUP_KEEP_WEEKLY:-4}"
keep_monthly="${BACKUP_KEEP_MONTHLY:-6}"
backup_host="${BACKUP_HOST:-raise-vps}"

case "$interval" in
  ''|*[!0-9]*) echo "BACKUP_INTERVAL_SECONDS must be a positive integer" >&2; exit 2 ;;
esac
if [ "$interval" -lt 300 ]; then
  echo "BACKUP_INTERVAL_SECONDS must be at least 300" >&2
  exit 2
fi

umask 077
trap 'exit 0' INT TERM

run_backup() {
  stamp="$(date -u +%Y%m%dT%H%M%SZ)"
  dump="/work/raise-${stamp}.dump"
  rm -f /work/raise-*.dump
  echo "Starting RAISE backup at ${stamp}"
  pg_dump --format=custom --no-owner --no-privileges --file="$dump"
  if ! restic snapshots >/dev/null 2>&1; then
    echo "Initializing the encrypted external restic repository"
    restic init
  fi
  restic backup \
    --host "$backup_host" \
    --tag raise \
    "$dump" /private-files
  restic forget \
    --host "$backup_host" \
    --tag raise \
    --keep-daily "$keep_daily" \
    --keep-weekly "$keep_weekly" \
    --keep-monthly "$keep_monthly" \
    --prune
  date -u +%Y-%m-%dT%H:%M:%SZ > /work/last-success
  rm -f "$dump"
  echo "RAISE backup completed successfully"
}

run_backup
while :; do
  sleep "$interval" &
  wait $!
  run_backup
done
