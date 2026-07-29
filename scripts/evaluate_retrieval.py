"""Score bilingual retrieval against the approved-candidate benchmark."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from farmers_chatbot.knowledge import KnowledgeIndex


def evaluate(benchmark_path: Path, top_k: int) -> dict:
    index = KnowledgeIndex.from_directory()
    cases = [
        json.loads(line)
        for line in benchmark_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    case_results = []
    for case in cases:
        hits = index.search(
            case["question"],
            language=case["language"],
            top_k=top_k,
        )
        retrieved = [hit.item_id for hit in hits]
        matched = sorted(set(retrieved) & set(case["relevant_ids"]))
        case_results.append(
            {
                "id": case["id"],
                "language": case["language"],
                "question": case["question"],
                "relevant_ids": case["relevant_ids"],
                "retrieved_ids": retrieved,
                "matched_ids": matched,
                "passed": bool(matched),
            }
        )

    languages = sorted({case["language"] for case in cases})
    by_language = {}
    for language in languages:
        group = [case for case in case_results if case["language"] == language]
        passed = sum(case["passed"] for case in group)
        by_language[language] = {
            "passed": passed,
            "total": len(group),
            "relevance_percent": round(passed / len(group) * 100, 1),
        }
    passed = sum(case["passed"] for case in case_results)
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "benchmark": str(benchmark_path),
        "top_k": top_k,
        "metric": "hit rate: at least one approved relevant item in top-k",
        "target_percent": 80,
        "passed": passed,
        "total": len(case_results),
        "relevance_percent": round(passed / len(case_results) * 100, 1),
        "target_met": passed / len(case_results) >= 0.8,
        "by_language": by_language,
        "cases": case_results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--benchmark",
        type=Path,
        default=Path("evaluation/benchmark_questions.jsonl"),
    )
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/generated/retrieval_latest.json"),
    )
    args = parser.parse_args()
    report = evaluate(args.benchmark, args.top_k)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(
        f"Retrieval relevance: {report['relevance_percent']}% "
        f"({report['passed']}/{report['total']}); target met={report['target_met']}"
    )
    for language, summary in report["by_language"].items():
        print(
            f"  {language}: {summary['relevance_percent']}% "
            f"({summary['passed']}/{summary['total']})"
        )
    return 0 if report["target_met"] else 1


if __name__ == "__main__":
    sys.exit(main())
