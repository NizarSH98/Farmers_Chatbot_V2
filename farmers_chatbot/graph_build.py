"""Resumable, schema-first local knowledge graph release builder."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import os
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypedDict

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from .agrifood_ontology import ONTOLOGY_VERSION, ontology_fingerprint
from .graph_repository import GraphRepository
from .knowledge_release import PARSER_VERSION, build_release_batch
from .qdrant_projection import (
    ProjectionConfig,
    QdrantProjectionRepository,
    QdrantProjector,
    manifest_as_dict,
)
from .retrieval_versions import PROJECTION_TEXT_VERSION

BUILD_SCHEMA_VERSION = "raise-graph-build-v1"
EXPECTED_SOURCE_DOC_SHA256 = (
    "3C0BAF8145E4A2E287BA5783F8AB26A7CEAE1C5340322C1EE065887CC9B75B0E"
)


class GraphBuildError(RuntimeError):
    """Raised when an integrity gate prevents release construction."""


@dataclass(frozen=True)
class GraphBuildCommand:
    release_version: str
    source_manifest_hash: str
    ontology_version: str
    local_model_revision: str
    embedding_candidate: str
    embedding_dimensions: int
    english_path: str
    arabic_path: str
    disposition_path: str
    source_doc_path: str
    translation_report_path: str
    deployment_scope: str = "pilot"
    activate: bool = True
    resume: bool = True
    created_by: str = "local-release-builder"

    @property
    def thread_id(self) -> str:
        payload = json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))
        return "graph-build-" + hashlib.sha256(payload.encode()).hexdigest()[:24]


@dataclass(frozen=True)
class GraphBuildStatus:
    build_id: str
    stage: str
    checkpoint: str
    release_id: str | None
    counts: dict[str, int]
    validation_results: dict[str, Any]
    projection_state: str
    failure_details: str | None = None


class BuildState(TypedDict, total=False):
    command: dict[str, Any]
    build_id: str
    stage: str
    checkpoint: str
    release_id: str
    counts: dict[str, int]
    validation_results: dict[str, Any]
    projection: dict[str, Any]
    activation: dict[str, Any]
    report_path: str
    report_sha256: str


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _command(value: dict[str, Any]) -> GraphBuildCommand:
    return GraphBuildCommand(**value)


def source_manifest_hash(
    *, english: Path, arabic: Path, disposition: Path, source_doc: Path
) -> str:
    values = {
        "english_sha256": _sha256(english),
        "arabic_sha256": _sha256(arabic),
        "disposition_sha256": _sha256(disposition),
        "source_doc_sha256": _sha256(source_doc).upper(),
        "ontology_sha256": ontology_fingerprint(),
        "parser_version": PARSER_VERSION,
        "projection_text_version": PROJECTION_TEXT_VERSION,
    }
    return hashlib.sha256(
        json.dumps(values, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


class GraphBuildRunner:
    """Execute the immutable release workflow with PostgreSQL checkpoints."""

    def __init__(
        self,
        database_url: str,
        *,
        projection_config: ProjectionConfig | None = None,
        report_dir: Path = Path("build-reports"),
    ) -> None:
        if not database_url.startswith(("postgres://", "postgresql://")):
            raise GraphBuildError("graph build requires PostgreSQL")
        self.database_url = database_url
        self.projection_config = projection_config or ProjectionConfig.from_env()
        self.report_dir = report_dir
        self.pool = ConnectionPool(
            database_url,
            min_size=1,
            max_size=4,
            kwargs={"row_factory": dict_row},
        )
        self.repository = GraphRepository(self.pool.connection)
        self.projection_repository = QdrantProjectionRepository(self.pool.connection)

    def close(self) -> None:
        self.pool.close()

    def _batch(self, command: GraphBuildCommand) -> Any:
        return build_release_batch(
            Path(command.english_path),
            embedding_model=command.embedding_candidate,
            embedding_dimensions=command.embedding_dimensions,
            created_by=command.created_by,
        )

    def _verify(self, state: BuildState) -> BuildState:
        command = _command(state["command"])
        paths = [
            Path(command.english_path),
            Path(command.arabic_path),
            Path(command.disposition_path),
            Path(command.source_doc_path),
            Path(command.translation_report_path),
        ]
        missing = [str(path) for path in paths if not path.is_file()]
        if missing:
            raise GraphBuildError(f"required graph-build inputs are missing: {missing}")
        source_hash = _sha256(Path(command.source_doc_path)).upper()
        if source_hash != EXPECTED_SOURCE_DOC_SHA256:
            raise GraphBuildError("source DOCX checksum changed")
        if command.ontology_version != ONTOLOGY_VERSION:
            raise GraphBuildError("graph-build ontology version is not installed")
        actual_manifest = source_manifest_hash(
            english=Path(command.english_path),
            arabic=Path(command.arabic_path),
            disposition=Path(command.disposition_path),
            source_doc=Path(command.source_doc_path),
        )
        if not hmac.compare_digest(actual_manifest, command.source_manifest_hash):
            raise GraphBuildError("source manifest differs from the requested build")
        translation = json.loads(
            Path(command.translation_report_path).read_text(encoding="utf-8")
        )
        if translation.get("failed") != 0 or translation.get("records") != 18:
            raise GraphBuildError("local bilingual validation has not passed all records")
        if translation.get("english_sha256") != _sha256(Path(command.english_path)):
            raise GraphBuildError("translation report does not match the English corpus")
        if translation.get("arabic_sha256") != _sha256(Path(command.arabic_path)):
            raise GraphBuildError("translation report does not match the Arabic corpus")
        disposition = json.loads(
            Path(command.disposition_path).read_text(encoding="utf-8")
        )
        chapters = disposition.get("chapters") or []
        if [item.get("chapter") for item in chapters] != list(range(1, 33)):
            raise GraphBuildError("source-chapter disposition is incomplete")
        return {
            "stage": "verified",
            "checkpoint": "inputs_verified",
            "validation_results": {
                "source_doc_sha256": source_hash,
                "source_manifest_sha256": actual_manifest,
                "translation_report_sha256": translation.get("report_sha256"),
                "translation_records": translation["records"],
                "chapters_accounted_for": len(chapters),
                "ontology_sha256": ontology_fingerprint(),
            },
        }

    def _compile(self, state: BuildState) -> BuildState:
        batch = self._batch(_command(state["command"]))
        counts = {
            "sources": len(batch.sources),
            "documents": len(batch.documents),
            "chunks": len(batch.chunks),
            "entities": len(batch.entities),
            "aliases": len(batch.aliases),
            "claims": len(batch.claims),
            "relations": len(batch.relations),
            "evidence": len(batch.evidence),
        }
        if counts["entities"] < 250 or counts["aliases"] < 600 or counts["relations"] < 450:
            raise GraphBuildError("ontology scale gate failed")
        return {
            "stage": "compiled",
            "checkpoint": "batch_compiled",
            "release_id": batch.release.id,
            "counts": counts,
        }

    def _ingest(self, state: BuildState) -> BuildState:
        command = _command(state["command"])
        batch = self._batch(command)
        self.repository.create_release(batch.release)
        input_hash = hashlib.sha256(Path(command.english_path).read_bytes()).hexdigest()
        run = self.repository.begin_ingestion(
            batch.release.id,
            input_hash,
            parser_version=PARSER_VERSION,
        )
        if run["state"] != "completed":
            try:
                stats = self.repository.ingest_batch(batch)
                self.repository.complete_ingestion(str(run["id"]), stats=stats)
            except Exception as exc:
                self.repository.complete_ingestion(
                    str(run["id"]), stats={}, error_type=type(exc).__name__
                )
                raise
        sealed = self.repository.seal_release(batch.release.id)
        return {
            "stage": "sealed",
            "checkpoint": "postgres_release_sealed",
            "release_id": batch.release.id,
            "validation_results": {
                **state.get("validation_results", {}),
                "postgres_integrity": sealed,
            },
        }

    def _project(self, state: BuildState) -> BuildState:
        projector = QdrantProjector(
            self.projection_repository,
            self.projection_config,
        )
        try:
            manifest = asyncio.run(projector.project(state["release_id"]))
        finally:
            asyncio.run(projector.close())
        return {
            "stage": "projected",
            "checkpoint": "qdrant_projection_ready",
            "projection": manifest_as_dict(manifest),
        }

    def _activate(self, state: BuildState) -> BuildState:
        command = _command(state["command"])
        if not command.activate:
            return {"stage": "ready", "checkpoint": "activation_skipped"}
        manifest = state["projection"]
        projector = QdrantProjector(
            self.projection_repository,
            self.projection_config,
        )
        try:
            # Alias switching happens before the authoritative pointer. Runtime
            # reads use the exact release collection, so an alias is never trusted
            # as the source of release identity.
            from .qdrant_projection import ProjectionManifest

            asyncio.run(projector.activate_aliases(ProjectionManifest(**manifest)))
        finally:
            asyncio.run(projector.close())
        activation = self.repository.activate_release(
            command.deployment_scope,
            state["release_id"],
            activated_by=command.created_by,
        )
        return {
            "stage": "activated",
            "checkpoint": "release_activated",
            "activation": asdict(activation),
        }

    def _report(self, state: BuildState) -> BuildState:
        report: dict[str, Any] = {
            "schema_version": BUILD_SCHEMA_VERSION,
            "build_id": state["build_id"],
            "created_at": datetime.now(UTC).isoformat(),
            "command": state["command"],
            "release_id": state["release_id"],
            "counts": state.get("counts", {}),
            "validation_results": state.get("validation_results", {}),
            "projection": state.get("projection", {}),
            "activation": state.get("activation", {}),
            "external_model_calls": 0,
        }
        canonical = json.dumps(
            report, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        integrity = hashlib.sha256(canonical).hexdigest()
        signing_key = os.getenv("GRAPH_BUILD_SIGNING_KEY", "").encode()
        report["integrity_sha256"] = integrity
        report["signature_hmac_sha256"] = (
            hmac.new(signing_key, canonical, hashlib.sha256).hexdigest()
            if signing_key
            else None
        )
        self.report_dir.mkdir(parents=True, exist_ok=True)
        path = self.report_dir / f"graph-build-{state['release_id']}.json"
        path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return {
            "stage": "complete",
            "checkpoint": "build_report_written",
            "report_path": str(path),
            "report_sha256": _sha256(path),
        }

    def _workflow(self, checkpointer: PostgresSaver) -> Any:
        workflow = StateGraph(BuildState)
        workflow.add_node("verify", self._verify)
        workflow.add_node("compile", self._compile)
        workflow.add_node("ingest", self._ingest)
        workflow.add_node("project", self._project)
        workflow.add_node("activate", self._activate)
        workflow.add_node("report", self._report)
        workflow.add_edge(START, "verify")
        workflow.add_edge("verify", "compile")
        workflow.add_edge("compile", "ingest")
        workflow.add_edge("ingest", "project")
        workflow.add_edge("project", "activate")
        workflow.add_edge("activate", "report")
        workflow.add_edge("report", END)
        return workflow.compile(checkpointer=checkpointer)

    def run(self, command: GraphBuildCommand) -> GraphBuildStatus:
        config = {"configurable": {"thread_id": command.thread_id}}
        with PostgresSaver.from_conn_string(self.database_url) as checkpointer:
            checkpointer.setup()
            graph = self._workflow(checkpointer)
            snapshot = graph.get_state(config)
            if command.resume and snapshot.values and snapshot.next:
                result = graph.invoke(None, config=config)
            elif command.resume and snapshot.values and not snapshot.next:
                result = dict(snapshot.values)
            else:
                result = graph.invoke(
                    {
                        "command": asdict(command),
                        "build_id": command.thread_id,
                        "stage": "created",
                        "checkpoint": "created",
                        "counts": {},
                        "validation_results": {},
                    },
                    config=config,
                )
        return GraphBuildStatus(
            build_id=command.thread_id,
            stage=str(result.get("stage", "unknown")),
            checkpoint=str(result.get("checkpoint", "unknown")),
            release_id=result.get("release_id"),
            counts=dict(result.get("counts") or {}),
            validation_results=dict(result.get("validation_results") or {}),
            projection_state=(
                "ready" if result.get("projection") else "not_projected"
            ),
        )
