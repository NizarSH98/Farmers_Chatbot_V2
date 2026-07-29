"""Measure local service latency without spending provider credits by default."""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from farmers_chatbot.knowledge import KnowledgeIndex
from farmers_chatbot.llm import AssistantService
from farmers_chatbot.storage import EvidenceStore
from farmers_chatbot.tools import ToolRegistry

QUESTIONS = [
    "What should I check before planting potatoes in Akkar?",
    "How should I assess irrigation needs for my field?",
    "What has ESDU tested with livestock farmers in Akkar?",
    "الخيار في البيت البلاستيكي يذبل، ماذا أفحص أولاً؟",
    "كيف أحدد موعد الري وكمية المياه؟",
    "ما الذي يميّز مقاربة ESDU في التنمية الريفية؟",
]


def percentile(values: list[int], fraction: float) -> int:
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * fraction)))
    return ordered[index]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=30)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--mode", default="standard")
    parser.add_argument(
        "--connected",
        action="store_true",
        help="Use OPENROUTER_API_KEY and incur provider usage.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/generated/service_latency_latest.json"),
    )
    args = parser.parse_args()

    key = os.getenv("OPENROUTER_API_KEY") if args.connected else ""
    if args.connected and not key:
        raise SystemExit("--connected requires OPENROUTER_API_KEY")
    with tempfile.TemporaryDirectory(prefix="raise-benchmark-") as temp_dir:
        knowledge = KnowledgeIndex.from_directory()
        evidence = EvidenceStore(Path(temp_dir) / "runtime.sqlite3")
        tools = ToolRegistry(knowledge, evidence)
        service = AssistantService(knowledge, tools, api_key=key)

        def run(index: int) -> dict:
            question = QUESTIONS[index % len(QUESTIONS)]
            started = time.perf_counter()
            response = service.answer(question, mode_key=args.mode)
            return {
                "duration_ms": int((time.perf_counter() - started) * 1000),
                "success": response.success,
                "language": response.language,
            }

        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
            results = list(pool.map(run, range(max(1, args.iterations))))
    durations = [result["duration_ms"] for result in results]
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "profile": "connected-model" if args.connected else "local-retrieval-fallback",
        "iterations": len(results),
        "workers": args.workers,
        "mode": args.mode,
        "median_ms": int(statistics.median(durations)),
        "p95_ms": percentile(durations, 0.95),
        "max_ms": max(durations),
        "success_percent": round(
            sum(result["success"] for result in results) / len(results) * 100,
            1,
        ),
        "contractual_warning": (
            "This local fallback benchmark is not the connected-model pilot-load "
            "measurement required by the logframe."
            if not args.connected
            else "Use only after the team approves load, cost, and measurement method."
        ),
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        f"{report['profile']}: median={report['median_ms']}ms, "
        f"p95={report['p95_ms']}ms, success={report['success_percent']}%"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
