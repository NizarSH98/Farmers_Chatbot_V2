"""Review and update pilot feedback without exposing a generic database console."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from farmers_chatbot.storage import EvidenceStore


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--database",
        default=os.getenv("RUNTIME_DB_PATH", "data/runtime.sqlite3"),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--status")

    update_parser = subparsers.add_parser("update")
    update_parser.add_argument("--id", type=int, required=True)
    update_parser.add_argument(
        "--status",
        required=True,
        choices=["new", "validated", "planned", "resolved", "verified", "rejected"],
    )
    update_parser.add_argument(
        "--priority",
        choices=["low", "medium", "high"],
    )
    update_parser.add_argument("--release-version")
    update_parser.add_argument("--verification-note")

    subparsers.add_parser("summary")
    args = parser.parse_args()
    store = EvidenceStore(args.database)
    if args.command == "list":
        print(
            json.dumps(
                store.list_feedback(args.status),
                ensure_ascii=False,
                indent=2,
            )
        )
    elif args.command == "update":
        store.update_feedback(
            args.id,
            status=args.status,
            priority=args.priority,
            release_version=args.release_version,
            verification_note=args.verification_note,
        )
        print(f"Updated feedback #{args.id}")
    else:
        print(json.dumps(store.feedback_summary(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

