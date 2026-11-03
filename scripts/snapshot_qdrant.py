"""Create and download snapshots for the active release's Qdrant collections."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx
import psycopg
from psycopg.rows import dict_row
from qdrant_client import AsyncQdrantClient


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


async def run(output: Path, scope: str) -> dict[str, Any]:
    database_url = os.getenv("DATABASE_URL", "")
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6433").rstrip("/")
    api_key = os.getenv("QDRANT_API_KEY") or None
    with psycopg.connect(database_url, row_factory=dict_row) as connection:
        row = connection.execute(
            """
            SELECT projection.* FROM active_knowledge_releases active
            JOIN knowledge_release_projections projection
              ON projection.release_id=active.release_id AND projection.target='qdrant'
            WHERE active.deployment_scope=%s AND projection.state='ready'
            """,
            (scope,),
        ).fetchone()
    if not row:
        raise RuntimeError(f"no ready active Qdrant projection for {scope}")
    target = output.parent / "qdrant"
    target.mkdir(parents=True, exist_ok=True)
    client = AsyncQdrantClient(url=qdrant_url, api_key=api_key)
    headers = {"api-key": api_key} if api_key else {}
    entries: list[dict[str, Any]] = []
    try:
        async with httpx.AsyncClient(timeout=120, headers=headers) as http:
            for collection, expected in (
                (str(row["evidence_collection"]), int(row["evidence_points"])),
                (str(row["entity_collection"]), int(row["entity_points"])),
            ):
                snapshot = await client.create_snapshot(collection, wait=True)
                if snapshot is None:
                    raise RuntimeError(f"Qdrant did not create a snapshot for {collection}")
                name = str(snapshot.name)
                response = await http.get(
                    f"{qdrant_url}/collections/{quote(collection, safe='')}/snapshots/{quote(name, safe='')}"
                )
                response.raise_for_status()
                path = target / name
                path.write_bytes(response.content)
                count = (await client.count(collection, exact=True)).count
                if count != expected:
                    raise RuntimeError(f"snapshot source count mismatch for {collection}")
                entries.append(
                    {
                        "collection": collection,
                        "file": path.relative_to(output.parent).as_posix(),
                        "sha256": _sha256(path),
                        "size": path.stat().st_size,
                        "points": count,
                        "qdrant_checksum": snapshot.checksum,
                    }
                )
    finally:
        await client.close()
    manifest: dict[str, Any] = {
        "schema_version": "raise.qdrant.snapshots.v1",
        "release_id": str(row["release_id"]),
        "scope": scope,
        "projection_manifest_sha256": str(row["manifest_sha256"]),
        "collections": entries,
    }
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    manifest["manifest_sha256"] = hashlib.sha256(canonical).hexdigest()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--scope", choices=("internal", "pilot", "production"), default="pilot")
    args = parser.parse_args()
    print(json.dumps(asyncio.run(run(args.output, args.scope)), sort_keys=True))


if __name__ == "__main__":
    main()
