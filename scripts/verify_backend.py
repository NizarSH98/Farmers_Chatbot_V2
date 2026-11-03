"""Run backend checks with a release gate that rejects skipped tests.

Plain pytest remains available for development. ProjectGraph/CI evidence must
not pass when PostgreSQL, migrations, or backup client tools are untested.
"""

from __future__ import annotations

import subprocess
import sys
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def result_counts(report: Path) -> dict[str, int]:
    root = ET.parse(report).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    return {
        key: sum(int(suite.get(key, "0")) for suite in suites)
        for key in ("tests", "failures", "errors", "skipped")
    }


def main() -> int:
    directory = ROOT / "reports" / "generated" / "verification"
    directory.mkdir(parents=True, exist_ok=True)
    report = directory / f"backend-{uuid.uuid4().hex}.xml"
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", *sys.argv[1:], f"--junitxml={report}"],
        cwd=ROOT,
        check=False,
    )
    if result.returncode:
        return result.returncode
    if not report.is_file():
        print("Backend verification failed: no machine-readable test report.")
        return 1
    counts = result_counts(report)
    print(f"Backend verification: {counts}; evidence: {report.relative_to(ROOT)}")
    if not counts["tests"] or any(counts[key] for key in ("failures", "errors", "skipped")):
        print("Backend verification failed: every selected check must execute and pass.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
