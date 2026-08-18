"""Pinned, cached local English-to-Arabic translation with OPUS-MT."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MODEL_ID = "Helsinki-NLP/opus-mt-en-ar"
MODEL_REVISION = "03087980e8ce753d64b3248ed0a912444545b840"
TRANSLATOR_VERSION = "raise-opus-mt-en-ar-v1"


class LocalTranslationError(RuntimeError):
    """Raised when the pinned local translation model cannot safely run."""


@dataclass(frozen=True)
class LocalTranslationConfig:
    model_id: str = MODEL_ID
    revision: str = MODEL_REVISION
    model_cache: Path = Path("model-cache")
    result_cache: Path = Path("build-cache/opus-translation")
    batch_size: int = 12
    allow_download: bool = True

    @classmethod
    def from_env(cls) -> LocalTranslationConfig:
        return cls(
            model_cache=Path(os.getenv("RAG_MODEL_CACHE", "model-cache")),
            result_cache=Path(
                os.getenv("LOCAL_TRANSLATION_CACHE_DIR", "build-cache/opus-translation")
            ),
            batch_size=max(1, min(int(os.getenv("LOCAL_TRANSLATION_BATCH_SIZE", "12")), 32)),
            allow_download=os.getenv("LOCAL_TRANSLATION_OFFLINE", "false").lower()
            != "true",
        )


class LocalArabicTranslator:
    """Translate immutable text units in batches and cache by model/input hash."""

    def __init__(self, config: LocalTranslationConfig | None = None) -> None:
        self.config = config or LocalTranslationConfig.from_env()
        self.config.result_cache.mkdir(parents=True, exist_ok=True)
        self._tokenizer: Any = None
        self._model: Any = None
        self.inputs_translated = 0
        self.cache_hits = 0
        self.batches = 0

    def _load(self) -> tuple[Any, Any]:
        if self._tokenizer is not None and self._model is not None:
            return self._tokenizer, self._model
        try:
            import torch
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

            torch.set_num_threads(max(1, min((os.cpu_count() or 2) // 2, 8)))
            common = {
                "revision": self.config.revision,
                "cache_dir": str(self.config.model_cache),
                "local_files_only": not self.config.allow_download,
            }
            self._tokenizer = AutoTokenizer.from_pretrained(
                self.config.model_id, **common
            )
            self._model = AutoModelForSeq2SeqLM.from_pretrained(
                self.config.model_id, **common
            ).to("cpu")
            self._model.eval()
        except Exception as exc:
            raise LocalTranslationError(
                "the pinned OPUS-MT English-to-Arabic model is unavailable"
            ) from exc
        return self._tokenizer, self._model

    def _identity(self, text: str) -> str:
        payload = {
            "translator_version": TRANSLATOR_VERSION,
            "model": self.config.model_id,
            "revision": self.config.revision,
            "text": text,
            "num_beams": 4,
            "max_new_tokens": 512,
        }
        return hashlib.sha256(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

    def _cached(self, text: str) -> str | None:
        path = self.config.result_cache / f"{self._identity(text)}.json"
        if not path.is_file():
            return None
        value = json.loads(path.read_text(encoding="utf-8"))
        self.cache_hits += 1
        return str(value["translation"])

    def _store(self, text: str, translation: str) -> None:
        identity = self._identity(text)
        path = self.config.result_cache / f"{identity}.json"
        path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "identity_sha256": identity,
                    "model": self.config.model_id,
                    "revision": self.config.revision,
                    "translation": translation,
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

    def translate_many(self, texts: list[str]) -> list[str]:
        results: list[str | None] = [None] * len(texts)
        missing_texts: list[str] = []
        missing_indexes: list[int] = []
        for index, text in enumerate(texts):
            cached = self._cached(text)
            if cached is None:
                missing_texts.append(text)
                missing_indexes.append(index)
            else:
                results[index] = cached
        if missing_texts:
            tokenizer, model = self._load()
            import torch

            for start in range(0, len(missing_texts), self.config.batch_size):
                batch = missing_texts[start : start + self.config.batch_size]
                indexes = missing_indexes[start : start + self.config.batch_size]
                encoded = tokenizer(
                    batch,
                    return_tensors="pt",
                    padding=True,
                    truncation=False,
                )
                if int(encoded["input_ids"].shape[1]) > 512:
                    raise LocalTranslationError(
                        "translation unit exceeds the pinned model context"
                    )
                with torch.inference_mode():
                    generated = model.generate(
                        **encoded,
                        num_beams=4,
                        max_new_tokens=512,
                        early_stopping=True,
                    )
                decoded = tokenizer.batch_decode(generated, skip_special_tokens=True)
                if len(decoded) != len(batch):
                    raise LocalTranslationError("translation batch size mismatch")
                for index, source, translated in zip(indexes, batch, decoded, strict=True):
                    value = translated.strip()
                    if not value:
                        single = tokenizer(
                            [source],
                            return_tensors="pt",
                            padding=True,
                            truncation=False,
                        )
                        with torch.inference_mode():
                            fallback = model.generate(
                                **single,
                                num_beams=1,
                                max_new_tokens=512,
                            )
                        value = tokenizer.batch_decode(
                            fallback, skip_special_tokens=True
                        )[0].strip()
                    if not value and source.endswith(":"):
                        heading = tokenizer(
                            [source[:-1] + "."],
                            return_tensors="pt",
                            padding=True,
                            truncation=False,
                        )
                        with torch.inference_mode():
                            heading_output = model.generate(
                                **heading,
                                num_beams=1,
                                max_new_tokens=128,
                            )
                        value = tokenizer.batch_decode(
                            heading_output, skip_special_tokens=True
                        )[0].strip()
                        if value:
                            value = value.rstrip(" .:") + ":"
                    if not value:
                        raise LocalTranslationError(
                            f"local translator returned empty text: {self._identity(source)}"
                        )
                    self._store(source, value)
                    results[index] = value
                self.inputs_translated += len(batch)
                self.batches += 1
        if any(value is None for value in results):
            raise LocalTranslationError("local translation result set is incomplete")
        return [str(value) for value in results]
