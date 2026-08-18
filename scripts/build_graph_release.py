"""Build, project, and optionally activate the local v0.3 graph release."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict
from pathlib import Path

from farmers_chatbot.agrifood_ontology import ONTOLOGY_VERSION
from farmers_chatbot.graph_build import (
    GraphBuildCommand,
    GraphBuildRunner,
    source_manifest_hash,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--english", type=Path, default=Path("knowledge_base/agrifood_knowledge_v0.3.en.md"))
    parser.add_argument("--arabic", type=Path, default=Path("knowledge_base/agrifood_knowledge_v0.3.ar.md"))
    parser.add_argument("--disposition", type=Path, default=Path("knowledge_base/agrifood_knowledge_v0.3.disposition.json"))
    parser.add_argument("--source-doc", type=Path, default=Path("knowledge_base/ESDU_Agrifood_Knowledge_Base_v0.1.docx"))
    parser.add_argument("--translation-report", type=Path, default=Path("build-reports/translation-validation.v0.3.json"))
    parser.add_argument("--embedding-model", default=os.getenv("RAG_LOCAL_EMBEDDING_MODEL", "intfloat/multilingual-e5-small"))
    parser.add_argument("--embedding-dimensions", type=int, default=int(os.getenv("RAG_LOCAL_EMBEDDING_DIMENSIONS", "384")))
    parser.add_argument("--deployment-scope", choices=("internal", "pilot"), default="pilot")
    parser.add_argument("--activate", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--resume", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--created-by", default="local-release-builder")
    args = parser.parse_args()
    database_url = os.getenv("DATABASE_URL", "").strip()
    command = GraphBuildCommand(
        release_version="0.3",
        source_manifest_hash=source_manifest_hash(
            english=args.english,
            arabic=args.arabic,
            disposition=args.disposition,
            source_doc=args.source_doc,
        ),
        ontology_version=ONTOLOGY_VERSION,
        local_model_revision=os.getenv("OLLAMA_GRAPH_MODEL", "qwen3:4b-q4_K_M"),
        embedding_candidate=args.embedding_model,
        embedding_dimensions=args.embedding_dimensions,
        english_path=str(args.english),
        arabic_path=str(args.arabic),
        disposition_path=str(args.disposition),
        source_doc_path=str(args.source_doc),
        translation_report_path=str(args.translation_report),
        deployment_scope=args.deployment_scope,
        activate=args.activate,
        resume=args.resume,
        created_by=args.created_by,
    )
    runner = GraphBuildRunner(database_url)
    try:
        status = runner.run(command)
    finally:
        runner.close()
    print(json.dumps(asdict(status), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
