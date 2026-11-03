#!/bin/sh
set -eu

: "${RESTIC_REPOSITORY:?RESTIC_REPOSITORY is required}"
: "${RESTIC_PASSWORD:?RESTIC_PASSWORD is required}"

snapshot="${1:-latest}"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
target="/work/restore-${stamp}"
mkdir -p "$target"

echo "Restoring RAISE snapshot ${snapshot} into ${target}"
restic restore "$snapshot" --target "$target"
dump="$(find "$target" -type f -name 'raise-*.dump' -print -quit)"
if [ -z "$dump" ]; then
  echo "The restored snapshot does not contain a PostgreSQL dump" >&2
  exit 1
fi
pg_restore --list "$dump" >/dev/null
echo "PostgreSQL archive verified: ${dump}"
echo "Private files restored under: ${target}/private-files"
echo "Restore into a disposable PostgreSQL service before any production recovery."
