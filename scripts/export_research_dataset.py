"""Export the pseudonymous pilot interaction dataset as CSV files.

    python -m scripts.export_research_dataset --output /tmp/raise-research

Writes participants.csv, interactions.csv, query_events.csv, feedback.csv and a
manifest.json with row counts and SHA-256 checksums. Rows carry participant
codes only. CSVs are UTF-8 with a byte-order mark so Excel shows Arabic text
correctly. Review the free-text columns before sharing outside the project team.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from farmers_chatbot.pilot_store import PilotStore
from farmers_chatbot.research_export import SCHEMA_VERSION, build_research_dataset


def write_dataset(tables: dict[str, list[dict]], output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    files = []
    for name, rows in tables.items():
        path = output / f"{name}.csv"
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            if rows:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
        files.append(
            {
                "file": path.name,
                "rows": len(rows),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(UTC).isoformat(),
        "identifier": "participant_code",
        "notice": (
            "Pseudonymous research data. The code-to-person mapping is held only "
            "in the controlled stakeholder tracker. Review free text before "
            "sharing outside the project team."
        ),
        "files": files,
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--database", default=os.getenv("DATABASE_URL", ""))
    args = parser.parse_args()
    store = PilotStore(database_url=args.database or None)
    try:
        manifest = write_dataset(build_research_dataset(store), args.output)
    finally:
        store.close()
    for entry in manifest["files"]:
        print(f"{entry['file']}: {entry['rows']} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
