"""Restore checksum-verified Qdrant collection snapshots into an empty target."""

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
from qdrant_client import AsyncQdrantClient, models


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


async def run(manifest_path: Path, *, replace: bool) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != "raise.qdrant.snapshots.v1":
        raise RuntimeError("unsupported Qdrant snapshot manifest")
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6433").rstrip("/")
    api_key = os.getenv("QDRANT_API_KEY") or None
    headers = {"api-key": api_key} if api_key else {}
    client = AsyncQdrantClient(url=qdrant_url, api_key=api_key)
    restored: list[dict[str, Any]] = []
    try:
        async with httpx.AsyncClient(timeout=300, headers=headers) as http:
            for entry in manifest.get("collections") or []:
                collection = str(entry["collection"])
                path = (manifest_path.parent / str(entry["file"])).resolve()
                if not path.is_file() or _sha256(path) != entry["sha256"]:
                    raise RuntimeError(f"snapshot checksum mismatch: {path}")
                exists = await client.collection_exists(collection)
                if exists and not replace:
                    raise RuntimeError(
                        f"target collection exists: {collection}; use --replace only for a disposable restore target"
                    )
                if exists:
                    await client.delete_collection(collection)
                with path.open("rb") as handle:
                    response = await http.post(
                        f"{qdrant_url}/collections/{quote(collection, safe='')}/snapshots/upload",
                        params={"wait": "true", "priority": "snapshot"},
                        files={"snapshot": (path.name, handle, "application/octet-stream")},
                    )
                response.raise_for_status()
                count = (await client.count(collection, exact=True)).count
                if count != int(entry["points"]):
                    raise RuntimeError(f"restored count mismatch for {collection}")
                restored.append({"collection": collection, "points": count})

        collections = [str(entry["collection"]) for entry in manifest.get("collections") or []]
        evidence = next((name for name in collections if name.startswith("raise_evidence__")), "")
        entities = next((name for name in collections if name.startswith("raise_entities__")), "")
        if not evidence or not entities:
            raise RuntimeError("snapshot manifest does not contain both RAISE collections")
        existing_aliases = {item.alias_name for item in (await client.get_aliases()).aliases}
        operations: list[Any] = []
        for alias, collection in (
            ("raise_evidence_active", evidence),
            ("raise_entities_active", entities),
        ):
            if alias in existing_aliases:
                operations.append(
                    models.DeleteAliasOperation(
                        delete_alias=models.DeleteAlias(alias_name=alias)
                    )
                )
            operations.append(
                models.CreateAliasOperation(
                    create_alias=models.CreateAlias(
                        collection_name=collection,
                        alias_name=alias,
                    )
                )
            )
        await client.update_collection_aliases(operations)
    finally:
        await client.close()
    return {"release_id": manifest["release_id"], "restored": restored}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    print(json.dumps(asyncio.run(run(args.manifest, replace=args.replace)), sort_keys=True))


if __name__ == "__main__":
    main()
