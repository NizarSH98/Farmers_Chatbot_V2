"""Local-only structured Ollama calls with content-addressed caching."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ollama import Client


class LocalModelError(RuntimeError):
    """Raised when a required local structured-model call is unavailable."""


TRANSLATION_REVIEW_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "faithful": {"type": "boolean"},
        "arabic_is_readable": {"type": "boolean"},
        "safety_meaning_preserved": {"type": "boolean"},
        "material_omissions": {
            "type": "array",
            "items": {"type": "string", "maxLength": 240},
            "maxItems": 8,
        },
    },
    "required": [
        "faithful",
        "arabic_is_readable",
        "safety_meaning_preserved",
        "material_omissions",
    ],
    "additionalProperties": False,
}

TRANSLATION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "translation": {
            "type": "string",
            "minLength": 1,
        }
    },
    "required": ["translation"],
    "additionalProperties": False,
}


@dataclass(frozen=True)
class LocalModelConfig:
    host: str = "http://localhost:11434"
    model: str = "qwen3:4b-q4_K_M"
    cache_dir: Path = Path("build-cache/local-model")
    timeout_seconds: int = 180

    @classmethod
    def from_env(cls) -> LocalModelConfig:
        return cls(
            host=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/"),
            model=os.getenv("OLLAMA_GRAPH_MODEL", "qwen3:4b-q4_K_M"),
            cache_dir=Path(
                os.getenv("LOCAL_MODEL_CACHE_DIR", "build-cache/local-model")
            ),
            timeout_seconds=int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "180")),
        )


class StructuredLocalModel:
    """Small wrapper around Ollama JSON-schema outputs.

    Cache identity includes every input that can change the result.  Repeating a
    graph build with the same source, prompt, schema, model and options therefore
    causes zero new local-model calls.
    """

    def __init__(self, config: LocalModelConfig | None = None) -> None:
        self.config = config or LocalModelConfig.from_env()
        self.client = Client(
            host=self.config.host,
            timeout=self.config.timeout_seconds,
        )
        self.config.cache_dir.mkdir(parents=True, exist_ok=True)
        self.calls = 0
        self.cache_hits = 0

    def available(self) -> bool:
        try:
            names = {
                str(item.model)
                for item in self.client.list().models
                if item.model
            }
        except (OSError, TimeoutError) as exc:
            raise LocalModelError("Ollama is not reachable") from exc
        return self.config.model in names

    def structured(
        self,
        *,
        stage: str,
        prompt_version: str,
        system: str,
        user: str,
        schema: dict[str, Any],
        source_hash: str,
        temperature: float = 0.0,
        seed: int = 37,
    ) -> dict[str, Any]:
        identity = {
            "stage": stage,
            "prompt_version": prompt_version,
            "model": self.config.model,
            "schema": schema,
            "source_hash": source_hash,
            "system": system,
            "user": user,
            "temperature": temperature,
            "seed": seed,
            "think": False,
        }
        digest = hashlib.sha256(
            json.dumps(
                identity,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        path = self.config.cache_dir / f"{digest}.json"
        if path.exists():
            self.cache_hits += 1
            return json.loads(path.read_text(encoding="utf-8"))["result"]
        if not self.available():
            raise LocalModelError(
                f"required local model is not installed: {self.config.model}"
            )
        try:
            response = self.client.chat(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                format=schema,
                think=False,
                keep_alive="30m",
                options={
                    "temperature": temperature,
                    "seed": seed,
                    "num_ctx": 8192,
                },
            )
            result = json.loads(response.message.content or "")
        except (OSError, TimeoutError, json.JSONDecodeError) as exc:
            raise LocalModelError(f"local model stage failed: {stage}") from exc
        self.calls += 1
        payload = {
            "cache_version": 1,
            "identity_sha256": digest,
            "result": result,
        }
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return result

    def translate_to_arabic(
        self,
        *,
        record_id: str,
        section: str,
        text: str,
        source_hash: str,
    ) -> str:
        result = self.structured(
            stage="translation_ar",
            prompt_version="agriculture-arabic-translation-v1",
            system=(
                "Translate the supplied authoritative English agricultural text "
                "into clear Modern Standard Arabic understandable in rural Lebanon. "
                "Translate every proposition. Preserve numbers, units, acronyms, "
                "proper names, uncertainty, conditions, prohibitions, escalation "
                "rules, list structure, and paragraph breaks. Do not summarize, "
                "omit, explain, correct, or add any fact or recommendation. Return "
                "only the JSON schema."
            ),
            user=f"Record: {record_id}\nSection: {section}\n\n{text}",
            schema=TRANSLATION_SCHEMA,
            source_hash=source_hash,
            seed=19,
        )
        translated = str(result["translation"]).strip()
        contaminated = (
            not any("\u0600" <= character <= "\u06ff" for character in translated)
            or "Record:" in translated
            or "Section:" in translated
            or any(
                "\u3400" <= character <= "\u9fff" or "\uac00" <= character <= "\ud7af"
                for character in translated
            )
        )
        if translated and contaminated:
            repaired = self.structured(
                stage="translation_ar_repair",
                prompt_version="agriculture-arabic-translation-repair-v1",
                system=(
                    "You are a strict English-to-Arabic translator. The output "
                    "translation must be written in Arabic script. Translate every "
                    "proposition exactly; preserve all numbers, units, uncertainty, "
                    "conditions, and safety meaning. Never repeat the instructions, "
                    "record ID, section name, or English source. Do not summarize or "
                    "add content. Return only the JSON schema."
                ),
                user=f"<source_text>\n{text}\n</source_text>",
                schema=TRANSLATION_SCHEMA,
                source_hash=source_hash,
                seed=23,
            )
            translated = str(repaired["translation"]).strip()
        if not translated:
            raise LocalModelError("local translation was empty")
        return translated

    def review_translation(
        self,
        *,
        record_id: str,
        english: str,
        arabic: str,
        source_hash: str,
        critic: bool = False,
    ) -> dict[str, Any]:
        role = "second independent critic" if critic else "bilingual reviewer"
        prompt = (
            f"Record ID: {record_id}\n\n"
            f"English authoritative text:\n{english[:2500]}\n\n"
            f"Arabic text:\n{arabic[:2500]}"
        )
        return self.structured(
            stage="translation_critic" if critic else "translation_review",
            prompt_version="translation-review-v2",
            system=(
                f"You are a {role} for Lebanese agricultural guidance. "
                "Assess semantic fidelity only. Do not add facts, doses, legal "
                "claims, diagnoses, or recommendations. A material omission must "
                "name one concrete proposition explicitly present in the supplied "
                "English and absent from the supplied Arabic. Never list a topic, "
                "warning category, or possible fact that is not in the supplied "
                "English. Return only the JSON schema."
            ),
            user=prompt,
            schema=TRANSLATION_REVIEW_SCHEMA,
            source_hash=source_hash,
            seed=71 if critic else 37,
        )
