"""Archive prior-version workspace data, then purge it from the hot database.

The v2 rollout keeps every registered account but does not carry its workspace
forward. Each user's conversations, projects, documents, artifacts, and feedback
are exported to a checksummed per-user JSON file, then removed from PostgreSQL.
Accounts, consent records, and quota counters are untouched.

Archiving is not "leave it in place": the published privacy policy promises a
retention window, so archived content must leave the live database.

    python -m scripts.archive_user_data --output /tmp/raise-archive
    python -m scripts.archive_user_data --output /tmp/raise-archive --purge
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from farmers_chatbot.pilot_store import PilotStore

SCHEMA_VERSION = "raise.user-archive.v1"

# Content tables only. users, consent, and quota history stay so that accounts
# remain registered and rate limits are not reset by the rollout.
CONTENT_TABLES = (
    "messages",
    "conversations",
    "document_chunks",
    "documents",
    "artifacts",
    "uploads",
    "projects",
    "provider_calls",
    "assistant_turns",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def archive(store: PilotStore, output_dir: Path, *, purge: bool) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    with store._connect() as connection:
        users = [
            dict(row)
            for row in connection.execute(
                "SELECT id, email, name FROM users ORDER BY id"
            ).fetchall()
        ]

    entries: list[dict[str, Any]] = []
    for user in users:
        user_id = str(user["id"])
        payload = store.export_user_data(user_id)
        target = output_dir / f"user-{user_id}.json"
        target.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=str),
            encoding="utf-8",
        )
        entries.append(
            {
                "user_id": user_id,
                "file": target.name,
                "bytes": target.stat().st_size,
                "sha256": _sha256(target),
            }
        )

    purged = False
    if purge:
        # Verify every export is readable before deleting anything.
        for entry in entries:
            candidate = output_dir / str(entry["file"])
            if _sha256(candidate) != entry["sha256"]:
                raise RuntimeError(f"archive checksum mismatch for {entry['file']}")
        with store._connect() as connection:
            connection.execute(
                f"TRUNCATE {', '.join(CONTENT_TABLES)} RESTART IDENTITY CASCADE"
            )
            connection.execute("UPDATE query_events SET user_id = NULL")
        purged = True

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(UTC).isoformat(),
        "user_count": len(entries),
        "purged": purged,
        "retained_tables": ["users", "user_consents", "query_events"],
        "purged_tables": list(CONTENT_TABLES) if purged else [],
        "users": entries,
    }
    manifest_path = output_dir / "archive-manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--purge",
        action="store_true",
        help="delete the archived content from PostgreSQL after verifying it",
    )
    args = parser.parse_args()

    store = PilotStore()
    try:
        manifest = archive(store, args.output, purge=args.purge)
    finally:
        store.close()
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
