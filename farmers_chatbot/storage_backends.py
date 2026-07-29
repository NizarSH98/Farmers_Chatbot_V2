"""Private file storage for local development and Supabase Storage."""

from __future__ import annotations

import mimetypes
from pathlib import Path, PurePosixPath
from typing import Protocol
from urllib.parse import quote

import requests

from .config import (
    LOCAL_FILE_ROOT,
    SUPABASE_SERVICE_ROLE_KEY,
    SUPABASE_STORAGE_BUCKET,
    SUPABASE_URL,
)


class PrivateFileStorage(Protocol):
    def put(self, path: str, data: bytes, content_type: str | None = None) -> None: ...

    def get(self, path: str) -> bytes: ...

    def delete(self, path: str) -> None: ...

    def signed_url(self, path: str, expires_seconds: int = 600) -> str | None: ...


def safe_storage_path(path: str) -> str:
    candidate = PurePosixPath(path.replace("\\", "/"))
    if candidate.is_absolute() or ".." in candidate.parts or not candidate.parts:
        raise ValueError("Unsafe storage path")
    return candidate.as_posix()


class LocalPrivateStorage:
    def __init__(self, root: str | Path = LOCAL_FILE_ROOT) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _resolve(self, path: str) -> Path:
        relative = safe_storage_path(path)
        target = (self.root / Path(relative)).resolve()
        if target != self.root and self.root not in target.parents:
            raise ValueError("Unsafe storage target")
        return target

    def put(self, path: str, data: bytes, content_type: str | None = None) -> None:
        del content_type
        target = self._resolve(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

    def get(self, path: str) -> bytes:
        return self._resolve(path).read_bytes()

    def delete(self, path: str) -> None:
        target = self._resolve(path)
        if target.exists() and target.is_file():
            target.unlink()

    def signed_url(self, path: str, expires_seconds: int = 600) -> str | None:
        del path, expires_seconds
        return None


class SupabasePrivateStorage:
    def __init__(
        self,
        url: str = SUPABASE_URL,
        service_role_key: str = SUPABASE_SERVICE_ROLE_KEY,
        bucket: str = SUPABASE_STORAGE_BUCKET,
        timeout_seconds: float = 30,
    ) -> None:
        if not url or not service_role_key:
            raise ValueError("Supabase Storage is not configured")
        self.url = url.rstrip("/")
        self.key = service_role_key
        self.bucket = bucket
        self.timeout_seconds = timeout_seconds

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.key}",
            "apikey": self.key,
        }

    def _object_url(self, path: str, operation: str = "object") -> str:
        safe = safe_storage_path(path)
        encoded = "/".join(quote(part, safe="") for part in safe.split("/"))
        return f"{self.url}/storage/v1/{operation}/{quote(self.bucket)}/{encoded}"

    def put(self, path: str, data: bytes, content_type: str | None = None) -> None:
        mime = content_type or mimetypes.guess_type(path)[0] or "application/octet-stream"
        response = requests.post(
            self._object_url(path),
            headers={**self._headers(), "Content-Type": mime, "x-upsert": "false"},
            data=data,
            timeout=self.timeout_seconds,
        )
        if response.status_code not in {200, 201}:
            raise RuntimeError("Private file upload failed")

    def get(self, path: str) -> bytes:
        response = requests.get(
            self._object_url(path, "object/authenticated"),
            headers=self._headers(),
            timeout=self.timeout_seconds,
        )
        if response.status_code != 200:
            raise FileNotFoundError("Private file is unavailable")
        return response.content

    def delete(self, path: str) -> None:
        response = requests.delete(
            f"{self.url}/storage/v1/object/{quote(self.bucket)}",
            headers={**self._headers(), "Content-Type": "application/json"},
            json={"prefixes": [safe_storage_path(path)]},
            timeout=self.timeout_seconds,
        )
        if response.status_code not in {200, 204}:
            raise RuntimeError("Private file deletion failed")

    def signed_url(self, path: str, expires_seconds: int = 600) -> str | None:
        response = requests.post(
            self._object_url(path, "object/sign"),
            headers={**self._headers(), "Content-Type": "application/json"},
            json={"expiresIn": max(60, min(int(expires_seconds), 3600))},
            timeout=self.timeout_seconds,
        )
        if response.status_code != 200:
            return None
        signed = response.json().get("signedURL") or response.json().get("signedUrl")
        if not signed:
            return None
        return signed if signed.startswith("http") else f"{self.url}{signed}"


def configured_file_storage() -> PrivateFileStorage:
    if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
        return SupabasePrivateStorage()
    return LocalPrivateStorage()
