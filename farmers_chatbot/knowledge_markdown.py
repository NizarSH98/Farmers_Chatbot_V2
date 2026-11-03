"""Strict parser and validator for the canonical RAISE Markdown corpus."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .agrifood_ontology import ONTOLOGY_VERSION, ontology_for_record
from .graph_ingestion import RELATION_TYPES

REQUIRED_METADATA = {
    "id", "title_en", "title_ar", "languages", "content_kind", "geography",
    "topics", "entities", "graph_relations", "risk", "evidence_class",
    "claim_ids", "source_ids", "review_status", "translation_status",
    "dynamicity", "effective_from", "expires_at", "review_by", "owner_role",
    "reviewer_roles", "retrieval_enabled", "publication_scope",
    "production_eligible", "supersedes_legacy_items",
    "ontology_version", "ontology_entities", "ontology_relations",
}
REQUIRED_SECTIONS = {
    "English guidance", "Arabic guidance — machine draft", "Decision logic",
    "منطق القرار — مسودة آلية", "Safe next action",
    "الخطوة التالية الآمنة — مسودة آلية", "Avoid or escalate",
    "ما يجب تجنبه أو تصعيده — مسودة آلية",
    "Evidence and applicability limits", "Claim-level sources",
    "حدود الأدلة وقابلية التطبيق — مسودة آلية",
}
ARABIC_RE = re.compile(r"[\u0600-\u06ff]")


class KnowledgeMarkdownError(ValueError):
    """Raised when the Markdown contract or its graph references are invalid."""


@dataclass(frozen=True)
class MarkdownRecord:
    heading: str
    metadata: dict[str, Any]
    sections: dict[str, str]


@dataclass(frozen=True)
class MarkdownCorpus:
    front_matter: dict[str, Any]
    records: tuple[MarkdownRecord, ...]
    sources: dict[str, dict[str, Any]]


def _front_matter(text: str) -> dict[str, Any]:
    match = re.match(r"\A---\r?\n(.*?)\r?\n---\r?\n", text, flags=re.DOTALL)
    if not match:
        raise KnowledgeMarkdownError("global YAML front matter is missing")
    result: dict[str, Any] = {}
    for line in match.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip().strip('"')
        if value in {"true", "false"}:
            parsed: Any = value == "true"
        elif value.startswith("["):
            parsed = [item.strip() for item in value[1:-1].split(",") if item.strip()]
        else:
            parsed = value
        result[key.strip()] = parsed
    required = {
        "document_id", "version", "status", "publication_scope",
        "production_eligible", "source_doc_sha256", "generated_at",
        "languages", "scope", "ontology_version",
    }
    missing = sorted(required - set(result))
    if missing:
        raise KnowledgeMarkdownError(f"front matter is missing: {', '.join(missing)}")
    return result


def _record_blocks(text: str) -> list[tuple[str, str]]:
    headings = list(re.finditer(r"(?m)^## (.+?)\r?$", text))
    appendix = re.search(r"(?m)^# Non-retrievable source and validation appendix\r?$", text)
    result = []
    for index, match in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        if appendix and appendix.start() > match.start():
            end = min(end, appendix.start())
        result.append((match.group(1).strip(), text[match.end() : end]))
    return result


def _sections(body: str) -> dict[str, str]:
    matches = list(re.finditer(r"(?m)^### (.+?)\r?$", body))
    result = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        result[match.group(1).strip()] = body[match.end() : end].strip()
    return result


def parse_knowledge_markdown(path: str | Path) -> MarkdownCorpus:
    text = Path(path).read_text(encoding="utf-8")
    if "\ufffd" in text:
        raise KnowledgeMarkdownError("corpus contains a Unicode replacement character")
    front = _front_matter(text)
    records = []
    for heading, body in _record_blocks(text):
        match = re.match(r"\s*```yaml\r?\n(.*?)\r?\n```", body, flags=re.DOTALL)
        if not match:
            raise KnowledgeMarkdownError(f"metadata must immediately follow: {heading}")
        try:
            metadata = json.loads(match.group(1))
        except json.JSONDecodeError as exc:
            raise KnowledgeMarkdownError(f"metadata is not JSON-compatible YAML: {heading}") from exc
        missing = sorted(REQUIRED_METADATA - set(metadata))
        if missing:
            raise KnowledgeMarkdownError(f"{metadata.get('id', heading)} metadata missing: {', '.join(missing)}")
        sections = _sections(body[match.end() :])
        missing_sections = sorted(REQUIRED_SECTIONS - set(sections))
        if missing_sections:
            raise KnowledgeMarkdownError(f"{metadata['id']} sections missing: {', '.join(missing_sections)}")
        records.append(MarkdownRecord(heading, metadata, sections))

    source_match = re.search(r"(?ms)^### Source register\r?$.*?^```json\r?\n(.*?)\r?\n```", text)
    if not source_match:
        raise KnowledgeMarkdownError("non-retrievable source register is missing")
    source_items = json.loads(source_match.group(1))
    sources = {str(item["id"]): item for item in source_items}
    corpus = MarkdownCorpus(front, tuple(records), sources)
    validate_corpus(corpus)
    return corpus


def validate_corpus(corpus: MarkdownCorpus) -> None:
    version = str(corpus.front_matter["version"])
    if version not in {"0.2", "0.3"}:
        raise KnowledgeMarkdownError("corpus version is not supported")
    is_v03 = version == "0.3"
    if is_v03 and corpus.front_matter["ontology_version"] != ONTOLOGY_VERSION:
        raise KnowledgeMarkdownError("v0.3 corpus ontology version is not supported")
    if not is_v03 and not str(corpus.front_matter["ontology_version"]).startswith("raise-agrifood-ontology-v0.2"):
        raise KnowledgeMarkdownError("historical v0.2 ontology version is not supported")
    ids = [str(record.metadata["id"]) for record in corpus.records]
    if not ids or len(ids) != len(set(ids)):
        raise KnowledgeMarkdownError("record IDs must be non-empty and unique")
    id_set = set(ids)
    superseded: set[str] = set()
    normalized_blocks: set[str] = set()
    duplicates = 0
    for record in corpus.records:
        meta = record.metadata
        if is_v03:
            expected_ontology = ontology_for_record(str(meta["id"]))
            for key in ("ontology_version", "ontology_entities", "ontology_relations"):
                if meta[key] != expected_ontology[key]:
                    raise KnowledgeMarkdownError(
                        f"{meta['id']} embedded ontology differs from the versioned spec"
                    )
            if meta["review_status"] != "approved":
                raise KnowledgeMarkdownError(f"{meta['id']} is not pilot-approved")
            if meta.get("approval_authority") != "project_owner":
                raise KnowledgeMarkdownError(f"{meta['id']} lacks project-owner approval")
            if meta.get("expert_verification_status") != "pending":
                raise KnowledgeMarkdownError(f"{meta['id']} expert status is invalid")
        elif meta["review_status"] != "ai_draft":
            raise KnowledgeMarkdownError(f"{meta['id']} historical review status is invalid")
        if meta["translation_status"] != "machine_draft":
            raise KnowledgeMarkdownError(f"{meta['id']} translation status is invalid")
        if meta["production_eligible"] is not False or meta["publication_scope"] != "pilot":
            raise KnowledgeMarkdownError(f"{meta['id']} violates the pilot publication policy")
        if not meta["retrieval_enabled"]:
            raise KnowledgeMarkdownError(f"{meta['id']} is unexpectedly excluded from retrieval")
        if not ARABIC_RE.search(record.sections["Arabic guidance — machine draft"]):
            raise KnowledgeMarkdownError(f"{meta['id']} has no Arabic guidance")
        source_ids = {str(item) for item in meta["source_ids"]}
        missing_sources = sorted(source_ids - set(corpus.sources))
        if missing_sources:
            raise KnowledgeMarkdownError(f"{meta['id']} has unresolved sources: {missing_sources}")
        for relation in meta["graph_relations"]:
            if relation.get("type") not in RELATION_TYPES:
                raise KnowledgeMarkdownError(f"{meta['id']} has an unsupported relation")
            if relation.get("target") not in id_set:
                raise KnowledgeMarkdownError(f"{meta['id']} has an unresolved graph target")
        current = {str(item) for item in meta["supersedes_legacy_items"]}
        if superseded & current:
            raise KnowledgeMarkdownError("legacy JSON items are superseded more than once")
        superseded |= current
        for section_name in REQUIRED_SECTIONS - {"Claim-level sources"}:
            block = re.sub(r"\W+", " ", record.sections[section_name].casefold()).strip()
            if block in normalized_blocks:
                duplicates += 1
            normalized_blocks.add(block)
    if duplicates:
        raise KnowledgeMarkdownError(f"normalized duplicate content blocks remain: {duplicates}")
    if any(item.get("retrieval_enabled") is not False for item in corpus.sources.values()):
        raise KnowledgeMarkdownError("source-register appendix must be non-retrievable")
