"""Render the structured knowledge base as a human-reviewable Markdown guide."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def build(guide_path: Path, sources_path: Path) -> str:
    guide = json.loads(guide_path.read_text(encoding="utf-8"))
    sources = {
        source["id"]: source
        for source in json.loads(sources_path.read_text(encoding="utf-8"))
    }
    lines = [
        f"# {guide['title_en']}",
        "",
        f"# {guide['title_ar']}",
        "",
        f"Version: `{guide['version']}`  ",
        f"Updated: `{guide['updated']}`  ",
        f"Status: **{guide['publication_status']}**",
        "",
        (
            "> This guide is a project draft for technical and field-language review. "
            "It is not an official ESDU publication until formally approved."
        ),
        "",
        "## How to review this guide",
        "",
        (
            "Each section has a stable knowledge ID, geographic scope, topics, evidence "
            "class, risk class, status, and source register. Reviewers should use "
            "`docs/KNOWLEDGE_REVIEW_TEMPLATE.md` and record changes in version control."
        ),
        "",
    ]
    for item in guide["items"]:
        lines.extend(
            [
                f"## [{item['id']}] {item['title_en']}",
                "",
                f"### {item['title_ar']}",
                "",
                f"- Geography: {', '.join(item['geography'])}",
                f"- Topics: {', '.join(item['topics'])}",
                f"- Evidence class: `{item['evidence_class']}`",
                f"- Risk: `{item['risk']}`",
                f"- Review status: `{item['status']}`",
                "",
                "### English",
                "",
                item["text_en"],
                "",
                "### العربية",
                "",
                item["text_ar"],
                "",
                "### Sources",
                "",
            ]
        )
        if not item["source_ids"]:
            lines.append(
                "- Project governance rule requiring internal approval and field validation."
            )
        for source_id in item["source_ids"]:
            source = sources[source_id]
            lines.append(
                f"- [{source_id}] [{source['title']}]({source['url']}) — "
                f"{source['publisher']} (accessed {source['accessed']})"
            )
        lines.extend(
            [
                "",
                "### Review record",
                "",
                "- Technical reviewer: pending",
                "- Arabic/field-language reviewer: pending",
                "- Decision: pending",
                "- Next review date: pending",
                "",
                "---",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--guide",
        type=Path,
        default=Path("knowledge_base/guide.json"),
    )
    parser.add_argument(
        "--sources",
        type=Path,
        default=Path("knowledge_base/sources.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("knowledge_base/RAISE_Akkar_Agricultural_Guide.md"),
    )
    args = parser.parse_args()
    args.output.write_text(
        build(args.guide, args.sources),
        encoding="utf-8",
    )
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
