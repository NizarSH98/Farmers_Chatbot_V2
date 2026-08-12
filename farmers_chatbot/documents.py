"""Validated project-document ingestion and scoped retrieval."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import mimetypes
import os
import re
import subprocess
import sys
import uuid
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion
from sklearn.preprocessing import normalize

from .config import MAX_PROJECT_FILE_BYTES, MAX_PROJECT_FILES
from .graph_ingestion import ProjectChunkRecord, normalize_search_text
from .graph_repository import GraphRepository
from .language import detect_language
from .pilot_store import PilotStore
from .storage_backends import PrivateFileStorage

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".csv", ".xlsx"}
ALLOWED_MIME_TYPES = {
    ".pdf": {"application/pdf"},
    ".docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    },
    ".txt": {"text/plain", "application/octet-stream"},
    ".csv": {"text/csv", "application/vnd.ms-excel", "text/plain"},
    ".xlsx": {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    },
}
MAX_EXTRACTED_CHARACTERS = 250_000
MAX_ARCHIVE_FILES = 1000
MAX_ARCHIVE_UNCOMPRESSED = 50 * 1024 * 1024
MAX_ARCHIVE_ENTRY_BYTES = 20 * 1024 * 1024
MAX_ARCHIVE_COMPRESSION_RATIO = 200
MAX_PDF_PAGES = 200
DOCUMENT_PARSE_TIMEOUT_SECONDS = 12.0
DOCUMENT_PARSER_MEMORY_BYTES = 512 * 1024 * 1024
DOCUMENT_PARSER_CPU_SECONDS = 10
MAX_WORKER_RESPONSE_BYTES = (MAX_EXTRACTED_CHARACTERS * 4) + 65_536


@dataclass(frozen=True)
class ProjectSearchResult:
    chunk_id: str
    document_id: str
    filename: str
    text: str
    score: float
    source_type: str = "user_project_document"

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "filename": self.filename,
            "text": self.text,
            "score": self.score,
            "source_type": self.source_type,
        }


def _clean_filename(filename: str) -> str:
    name = Path(filename).name
    cleaned = re.sub(r"[^A-Za-z0-9._\-\u0600-\u06ff ]+", "_", name).strip()
    return cleaned[:180] or "document"


def _validate_zip(data: bytes) -> None:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            infos = archive.infolist()
            if len(infos) > MAX_ARCHIVE_FILES:
                raise ValueError("Office file contains too many embedded files")
            total = sum(info.file_size for info in infos)
            if total > MAX_ARCHIVE_UNCOMPRESSED:
                raise ValueError("Office file expands beyond the pilot safety limit")
            for info in infos:
                normalized_name = info.filename.replace("\\", "/")
                candidate = PurePosixPath(normalized_name)
                if (
                    candidate.is_absolute()
                    or ".." in candidate.parts
                    or normalized_name.startswith("//")
                    or re.match(r"^[A-Za-z]:/", normalized_name)
                ):
                    raise ValueError("Office file contains an unsafe path")
                unix_mode = (info.external_attr >> 16) & 0xFFFF
                if unix_mode & 0o170000 == 0o120000:
                    raise ValueError("Office file contains an unsafe symbolic link")
                if info.flag_bits & 0x1:
                    raise ValueError("Encrypted Office files are not accepted")
                if info.file_size > MAX_ARCHIVE_ENTRY_BYTES:
                    raise ValueError("Office file contains an oversized embedded file")
                if info.file_size and info.compress_size == 0:
                    raise ValueError("Office file contains an invalid compressed entry")
                if (
                    info.compress_size
                    and info.file_size / info.compress_size
                    > MAX_ARCHIVE_COMPRESSION_RATIO
                ):
                    raise ValueError("Office file contains a suspicious compression ratio")
    except zipfile.BadZipFile as exc:
        raise ValueError("Office document is not a valid ZIP-based file") from exc


def _decode_text(data: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1256", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("Text encoding is not supported")


def _run_isolated_extraction(extension: str, data: bytes) -> str:
    worker = Path(__file__).with_name("document_parser_worker.py")
    command = [
        sys.executable,
        str(worker),
        extension,
        str(MAX_EXTRACTED_CHARACTERS),
        str(MAX_PDF_PAGES),
        str(MAX_PROJECT_FILE_BYTES),
        str(DOCUMENT_PARSER_MEMORY_BYTES),
        str(DOCUMENT_PARSER_CPU_SECONDS),
    ]
    creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        creationflags=creation_flags,
    )
    try:
        output, _stderr = process.communicate(
            data,
            timeout=DOCUMENT_PARSE_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        process.kill()
        process.communicate()
        raise ValueError("Document parsing exceeded the safety time limit") from exc

    if len(output) > MAX_WORKER_RESPONSE_BYTES:
        raise ValueError("Document parser output exceeded the safety limit")
    try:
        response = json.loads(output.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Document parser failed safely") from exc
    if process.returncode != 0 or not response.get("ok"):
        message = response.get("error")
        if not isinstance(message, str) or not message:
            message = "Document parser failed safely"
        raise ValueError(message)
    text = response.get("text")
    if not isinstance(text, str):
        raise ValueError(  # noqa: TRY004 - upload API exposes safe ValueError failures
            "Document parser returned an invalid response"
        )
    return text


def extract_document_text(filename: str, data: bytes) -> str:
    extension = Path(filename).suffix.lower()
    if not data or len(data) > MAX_PROJECT_FILE_BYTES:
        raise ValueError("File must be non-empty and no larger than 10 MB")
    if extension == ".pdf":
        if not data.startswith(b"%PDF-"):
            raise ValueError("PDF signature is invalid")
        return _run_isolated_extraction(extension, data)
    elif extension in {".docx", ".xlsx"}:
        _validate_zip(data)
        return _run_isolated_extraction(extension, data)
    elif extension == ".csv":
        decoded = _decode_text(data)
        rows = csv.reader(io.StringIO(decoded))
        text = "\n".join(" | ".join(row) for _, row in zip(range(5001), rows))
    elif extension == ".txt":
        text = _decode_text(data)
    else:
        raise ValueError("Unsupported document type")

    cleaned = re.sub(r"\x00", "", text)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    if not cleaned:
        raise ValueError("No readable text was found in the document")
    return cleaned[:MAX_EXTRACTED_CHARACTERS]


def chunk_text(text: str, size: int = 1400, overlap: int = 180) -> list[str]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if len(current) + len(paragraph) + 2 <= size:
            current = f"{current}\n\n{paragraph}".strip()
            continue
        if current:
            chunks.append(current)
        if len(paragraph) <= size:
            current = paragraph
            continue
        start = 0
        while start < len(paragraph):
            end = min(len(paragraph), start + size)
            chunks.append(paragraph[start:end])
            if end == len(paragraph):
                break
            start = max(start + 1, end - overlap)
        current = ""
    if current:
        chunks.append(current)
    return chunks[:250]


class DocumentService:
    def __init__(self, store: PilotStore, storage: PrivateFileStorage) -> None:
        self.store = store
        self.storage = storage

    def ingest(
        self,
        owner_user_id: str,
        project_id: str,
        *,
        filename: str,
        data: bytes,
        mime_type: str | None = None,
    ) -> str:
        if not data or len(data) > MAX_PROJECT_FILE_BYTES:
            raise ValueError("File must be non-empty and no larger than 10 MB")

        cleaned_name = _clean_filename(filename)
        extension = Path(cleaned_name).suffix.lower()
        if extension not in ALLOWED_EXTENSIONS:
            raise ValueError("Allowed files: PDF, DOCX, TXT, CSV, and XLSX")
        supplied_mime = (mime_type or "").split(";", 1)[0].lower()
        if supplied_mime and supplied_mime not in ALLOWED_MIME_TYPES[extension]:
            raise ValueError("File extension and media type do not match")

        digest = hashlib.sha256(data).hexdigest()
        existing = next(
            (
                item
                for item in self.store.list_documents(owner_user_id, project_id)
                if item.get("sha256") == digest
            ),
            None,
        )
        if existing:
            return str(existing["id"])
        if self.store.document_count(owner_user_id, project_id) >= MAX_PROJECT_FILES:
            raise ValueError(f"A project can contain at most {MAX_PROJECT_FILES} files")

        text = extract_document_text(cleaned_name, data)
        chunks = chunk_text(text)
        storage_path = (
            f"users/{owner_user_id}/projects/{project_id}/documents/"
            f"{uuid.uuid4()}-{cleaned_name}"
        )
        detected_mime = (
            supplied_mime
            or mimetypes.guess_type(cleaned_name)[0]
            or "application/octet-stream"
        )
        self.storage.put(storage_path, data, detected_mime)
        try:
            document_id = self.store.add_document(
                owner_user_id,
                project_id,
                filename=cleaned_name,
                mime_type=detected_mime,
                storage_path=storage_path,
                sha256=digest,
                size_bytes=len(data),
                chunks=chunks,
            )
            if self.store.is_postgres:
                records = tuple(
                    ProjectChunkRecord(
                        id=str(item["id"]),
                        owner_user_id=owner_user_id,
                        project_id=project_id,
                        document_id=document_id,
                        chunk_index=int(item["chunk_index"]),
                        content=str(item["text_content"]),
                        normalized_content=normalize_search_text(
                            str(item["text_content"])
                        ),
                        contextualized_content=(
                            f"{cleaned_name}\n\n{item['text_content']}"
                        ),
                        content_hash=hashlib.sha256(
                            str(item["text_content"]).encode("utf-8")
                        ).hexdigest(),
                        language=detect_language(str(item["text_content"])),
                        metadata={"filename": cleaned_name},
                    )
                    for item in self.store.list_project_chunks(
                        owner_user_id, project_id
                    )
                    if str(item["document_id"]) == document_id
                )
                GraphRepository(self.store._connect).upsert_project_chunks(records)
            return document_id
        except Exception:
            self.storage.delete(storage_path)
            if "document_id" in locals():
                try:
                    self.store.delete_document(
                        owner_user_id, project_id, document_id
                    )
                except ValueError:
                    pass
            raise

    def delete(
        self,
        owner_user_id: str,
        project_id: str,
        document_id: str,
    ) -> None:
        documents = self.store.list_documents(owner_user_id, project_id)
        document = next(
            (item for item in documents if item["id"] == document_id),
            None,
        )
        if not document:
            raise ValueError("Document not found")
        path = str(document["storage_path"])
        self.storage.delete(path)
        self.store.delete_document(owner_user_id, project_id, document_id)


def search_project_chunks(
    chunks: list[dict[str, Any]],
    query: str,
    *,
    top_k: int = 5,
    min_score: float = 0.01,
) -> list[ProjectSearchResult]:
    if not chunks or not query.strip():
        return []
    vectorizer = FeatureUnion(
        [
            (
                "words",
                TfidfVectorizer(
                    ngram_range=(1, 2),
                    sublinear_tf=True,
                    token_pattern=r"(?u)\b\w[\w'-]+\b",
                ),
            ),
            (
                "characters",
                TfidfVectorizer(
                    analyzer="char_wb",
                    ngram_range=(3, 5),
                    sublinear_tf=True,
                    max_features=20000,
                ),
            ),
        ]
    )
    texts = [f"{chunk['filename']} {chunk['text_content']}" for chunk in chunks]
    try:
        vectors = normalize(vectorizer.fit_transform(texts))
        query_vector = normalize(vectorizer.transform([query]))
    except ValueError:
        return []
    scores = (query_vector @ vectors.T).toarray().ravel()
    ranked = np.argsort(scores)[::-1]
    results = []
    for index in ranked[: max(1, min(int(top_k), 10))]:
        score = float(scores[int(index)])
        if score < min_score:
            continue
        chunk = chunks[int(index)]
        results.append(
            ProjectSearchResult(
                chunk_id=str(chunk["id"]),
                document_id=str(chunk["document_id"]),
                filename=str(chunk["filename"]),
                text=str(chunk["text_content"]),
                score=score,
            )
        )
    return results
