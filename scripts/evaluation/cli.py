"""Command-line entry point for deterministic evaluation and leakage guards."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from .harness import EvaluationHarness
from .schema import (
    SchemaError,
    load_ablation_manifest,
    load_cases,
    load_pairwise_judgments,
    load_run_records,
)
from .separation import assert_hidden_not_tracked, assert_split_separation


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_report(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def score_command(args: argparse.Namespace) -> int:
    cases = load_cases(args.cases)
    splits = {case.split for case in cases}
    if len(splits) != 1:
        raise SchemaError("a scored dataset must contain exactly one split")
    records = load_run_records(args.runs)
    report = EvaluationHarness(cases, top_k=args.top_k).score(
        records, args.system_id
    )
    report["dataset"] = {
        "id": args.dataset_id,
        "version": args.dataset_version,
        "split": cases[0].split,
        "cases_sha256": file_digest(args.cases),
        "runs_sha256": file_digest(args.runs),
    }
    if args.ablations:
        manifest = load_ablation_manifest(args.ablations)
        report["ablation_manifest"] = {
            "schema_version": manifest["schema_version"],
            "sha256": file_digest(args.ablations),
        }
    if args.pairwise:
        judgments = load_pairwise_judgments(args.pairwise)
        unknown_pairwise = sorted(
            {item.case_id for item in judgments} - {case.case_id for case in cases}
        )
        if unknown_pairwise:
            raise SchemaError(
                "pairwise file contains unknown case IDs: "
                + ", ".join(unknown_pairwise)
            )
        report["pairwise"] = EvaluationHarness.score_pairwise(
            judgments,
            seed=args.bootstrap_seed,
            resamples=args.bootstrap_resamples,
        )
        report["dataset"]["pairwise_sha256"] = file_digest(args.pairwise)
    _write_report(args.output, report)
    print(
        f"Scored {report['coverage']['run_record_count']}/"
        f"{report['coverage']['case_count']} cases for {args.system_id}."
    )
    return 0


def guard_command(args: argparse.Namespace) -> int:
    assert_hidden_not_tracked(args.repo_root, args.hidden_root)
    result = assert_split_separation(
        load_cases(args.public_cases),
        load_cases(args.hidden_cases),
    )
    print(
        "Evaluation split guard passed: "
        f"{result['public_case_count']} public and "
        f"{result['hidden_case_count']} hidden cases."
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    score = commands.add_parser("score", help="Score one system run")
    score.add_argument("--cases", type=Path, required=True)
    score.add_argument("--runs", type=Path, required=True)
    score.add_argument("--system-id", required=True)
    score.add_argument("--dataset-id", required=True)
    score.add_argument("--dataset-version", required=True)
    score.add_argument("--top-k", type=int, default=10)
    score.add_argument("--pairwise", type=Path)
    score.add_argument("--ablations", type=Path)
    score.add_argument("--bootstrap-seed", type=int, default=1729)
    score.add_argument("--bootstrap-resamples", type=int, default=2000)
    score.add_argument("--output", type=Path, required=True)
    score.set_defaults(handler=score_command)

    guard = commands.add_parser("guard", help="Check public/hidden separation")
    guard.add_argument("--public-cases", type=Path, required=True)
    guard.add_argument("--hidden-cases", type=Path, required=True)
    guard.add_argument("--repo-root", type=Path, default=Path.cwd())
    guard.add_argument(
        "--hidden-root",
        type=Path,
        default=Path("evaluation/hidden"),
    )
    guard.set_defaults(handler=guard_command)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
