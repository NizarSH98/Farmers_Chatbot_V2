"""Provider-neutral private storage contract tests."""

from __future__ import annotations

from io import BytesIO
from typing import ClassVar

import pytest

from farmers_chatbot.storage_backends import S3PrivateStorage, safe_storage_path


class MissingObject(Exception):
    response: ClassVar[dict[str, dict[str, str]]] = {
        "Error": {"Code": "NoSuchKey"}
    }


class FakeS3:
    def __init__(self) -> None:
        self.objects: dict[tuple[str, str], tuple[bytes, str]] = {}
        self.presign_expires = 0

    def head_object(self, *, Bucket: str, Key: str) -> None:
        if (Bucket, Key) not in self.objects:
            raise MissingObject()

    def put_object(
        self, *, Bucket: str, Key: str, Body: bytes, ContentType: str
    ) -> None:
        self.objects[(Bucket, Key)] = (Body, ContentType)

    def get_object(self, *, Bucket: str, Key: str) -> dict[str, BytesIO]:
        try:
            data, _ = self.objects[(Bucket, Key)]
        except KeyError as exc:
            raise MissingObject() from exc
        return {"Body": BytesIO(data)}

    def delete_object(self, *, Bucket: str, Key: str) -> None:
        self.objects.pop((Bucket, Key), None)

    def generate_presigned_url(
        self, operation: str, *, Params: dict[str, str], ExpiresIn: int
    ) -> str:
        assert operation == "get_object"
        self.presign_expires = ExpiresIn
        return f"https://objects.example.test/{Params['Bucket']}/{Params['Key']}"


def test_s3_storage_round_trip_is_private_and_refuses_overwrite() -> None:
    client = FakeS3()
    storage = S3PrivateStorage(bucket="raise-private", client=client)

    storage.put("users/u-1/report.pdf", b"private", "application/pdf")
    assert storage.get("users/u-1/report.pdf") == b"private"
    with pytest.raises(RuntimeError, match="overwrite"):
        storage.put("users/u-1/report.pdf", b"replacement")

    url = storage.signed_url("users/u-1/report.pdf", expires_seconds=99999)
    assert url == "https://objects.example.test/raise-private/users/u-1/report.pdf"
    assert client.presign_expires == 3600

    storage.delete("users/u-1/report.pdf")
    with pytest.raises(FileNotFoundError):
        storage.get("users/u-1/report.pdf")


@pytest.mark.parametrize("path", ["../secret", "/absolute", "safe/../../escape"])
def test_private_storage_rejects_unsafe_keys(path: str) -> None:
    with pytest.raises(ValueError, match="Unsafe"):
        safe_storage_path(path)
