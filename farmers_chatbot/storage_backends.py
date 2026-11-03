"""Provider-neutral private file storage for local volumes and S3 APIs."""

from __future__ import annotations

import mimetypes
from pathlib import Path, PurePosixPath
from typing import Any, Protocol

from .config import (
    LOCAL_FILE_ROOT,
    S3_ACCESS_KEY_ID,
    S3_BUCKET,
    S3_ENDPOINT_URL,
    S3_FORCE_PATH_STYLE,
    S3_REGION,
    S3_SECRET_ACCESS_KEY,
    STORAGE_BACKEND,
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


class S3PrivateStorage:
    """Private object storage compatible with AWS S3 and S3-like providers."""

    def __init__(
        self,
        *,
        bucket: str = S3_BUCKET,
        endpoint_url: str = S3_ENDPOINT_URL,
        region: str = S3_REGION,
        access_key_id: str = S3_ACCESS_KEY_ID,
        secret_access_key: str = S3_SECRET_ACCESS_KEY,
        force_path_style: bool = S3_FORCE_PATH_STYLE,
        client: Any | None = None,
    ) -> None:
        if not bucket:
            raise ValueError("S3 private storage requires S3_BUCKET")
        self.bucket = bucket
        if client is not None:
            self.client = client
            return
        import boto3
        from botocore.config import Config

        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint_url or None,
            region_name=region,
            aws_access_key_id=access_key_id or None,
            aws_secret_access_key=secret_access_key or None,
            config=Config(
                signature_version="s3v4",
                s3={
                    "addressing_style": "path" if force_path_style else "auto",
                },
            ),
        )

    @staticmethod
    def _not_found(exc: Exception) -> bool:
        response = getattr(exc, "response", {})
        error = response.get("Error", {}) if isinstance(response, dict) else {}
        return str(error.get("Code") or "") in {"404", "NoSuchKey", "NotFound"}

    def put(self, path: str, data: bytes, content_type: str | None = None) -> None:
        key = safe_storage_path(path)
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
        except Exception as exc:  # botocore is optional until S3 is selected
            if not self._not_found(exc):
                raise RuntimeError("Could not verify the private object target") from exc
        else:
            raise RuntimeError("Refusing to overwrite an existing private object")
        mime = content_type or mimetypes.guess_type(key)[0] or "application/octet-stream"
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType=mime,
        )

    def get(self, path: str) -> bytes:
        try:
            response = self.client.get_object(
                Bucket=self.bucket,
                Key=safe_storage_path(path),
            )
            return bytes(response["Body"].read())
        except Exception as exc:  # normalize provider-specific missing-key errors
            if self._not_found(exc):
                raise FileNotFoundError("Private file is unavailable") from exc
            raise

    def delete(self, path: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=safe_storage_path(path))

    def signed_url(self, path: str, expires_seconds: int = 600) -> str | None:
        return str(
            self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": safe_storage_path(path)},
                ExpiresIn=max(60, min(int(expires_seconds), 3600)),
            )
        )


def configured_file_storage() -> PrivateFileStorage:
    if STORAGE_BACKEND == "local":
        return LocalPrivateStorage()
    if STORAGE_BACKEND == "s3":
        return S3PrivateStorage()
    raise RuntimeError("STORAGE_BACKEND must be 'local' or 's3'")
