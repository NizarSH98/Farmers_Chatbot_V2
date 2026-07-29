"""Deterministic, bounded farmer artifact builders."""

from __future__ import annotations

import io
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

from .config import MAX_ARTIFACTS_PER_USER_DAY
from .pilot_store import PilotStore
from .storage_backends import PrivateFileStorage

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@dataclass(frozen=True)
class ArtifactReference:
    artifact_id: str
    artifact_type: str
    filename: str
    mime_type: str

    def to_dict(self) -> dict[str, str]:
        return {
            "artifact_id": self.artifact_id,
            "artifact_type": self.artifact_type,
            "filename": self.filename,
            "mime_type": self.mime_type,
        }


def _safe_filename(value: str, extension: str) -> str:
    base = re.sub(r"[^A-Za-z0-9_\-\u0600-\u06ff ]+", "_", value).strip()
    base = re.sub(r"\s+", "_", base)[:80] or "RAISE_artifact"
    return f"{base}{extension}"


def _safe_cell(value: Any) -> Any:
    if isinstance(value, str) and value.startswith(("=", "+", "-", "@")):
        return f"'{value}"
    return value


def _limited_text(value: str, maximum: int = 5000) -> str:
    cleaned = " ".join((value or "").split()).strip()
    if not cleaned:
        raise ValueError("Artifact text cannot be empty")
    return cleaned[:maximum]


def _limited_items(items: list[Any], maximum: int = 50) -> list[Any]:
    if not items:
        raise ValueError("Artifact requires at least one item")
    return items[:maximum]


def _set_paragraph_direction(paragraph: Any, arabic: bool) -> None:
    if not arabic:
        return
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    properties = paragraph._p.get_or_add_pPr()  # noqa: SLF001
    bidi = OxmlElement("w:bidi")
    bidi.set(qn("w:val"), "1")
    properties.append(bidi)


def _docx_bytes(
    *,
    title: str,
    sections: list[tuple[str, str | list[str]]],
    language: str,
    sources: list[str],
    assumptions: list[str],
) -> bytes:
    arabic = language == "arabic"
    document = Document()
    heading = document.add_heading(_limited_text(title, 200), 0)
    _set_paragraph_direction(heading, arabic)
    generated = datetime.now(timezone.utc).date().isoformat()
    paragraph = document.add_paragraph(f"Generated / أُنشئ: {generated}")
    _set_paragraph_direction(paragraph, arabic)

    for heading_text, content in sections:
        section_heading = document.add_heading(_limited_text(heading_text, 200), 1)
        _set_paragraph_direction(section_heading, arabic)
        if isinstance(content, list):
            for item in _limited_items(content):
                item_paragraph = document.add_paragraph(
                    _limited_text(str(item)),
                    style="List Bullet",
                )
                _set_paragraph_direction(item_paragraph, arabic)
        else:
            item_paragraph = document.add_paragraph(_limited_text(content))
            _set_paragraph_direction(item_paragraph, arabic)

    if assumptions:
        assumptions_heading = document.add_heading("Assumptions / الافتراضات", 1)
        _set_paragraph_direction(assumptions_heading, arabic)
        for item in assumptions[:20]:
            item_paragraph = document.add_paragraph(
                _limited_text(str(item)),
                style="List Bullet",
            )
            _set_paragraph_direction(item_paragraph, arabic)
    if sources:
        sources_heading = document.add_heading("Sources / المصادر", 1)
        _set_paragraph_direction(sources_heading, arabic)
        for item in sources[:20]:
            item_paragraph = document.add_paragraph(
                _limited_text(str(item)),
                style="List Bullet",
            )
            _set_paragraph_direction(item_paragraph, arabic)

    warning = document.add_paragraph(
        "Pilot decision-support output. Verify high-risk agronomic, pesticide, "
        "veterinary, food-safety, financial, and regulatory decisions with a "
        "qualified local professional."
    )
    warning.runs[0].italic = True
    _set_paragraph_direction(warning, arabic)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


class ArtifactService:
    def __init__(
        self,
        store: PilotStore,
        storage: PrivateFileStorage,
        *,
        owner_user_id: str,
        project_id: str | None = None,
        conversation_id: str | None = None,
    ) -> None:
        self.store = store
        self.storage = storage
        self.owner_user_id = owner_user_id
        self.project_id = project_id
        self.conversation_id = conversation_id

    def _save(
        self,
        artifact_type: str,
        filename: str,
        mime_type: str,
        data: bytes,
        metadata: dict[str, Any],
    ) -> ArtifactReference:
        if self.store.artifacts_today(self.owner_user_id) >= MAX_ARTIFACTS_PER_USER_DAY:
            raise ValueError("Daily artifact generation limit reached")
        storage_path = (
            f"users/{self.owner_user_id}/artifacts/{uuid.uuid4()}-{filename}"
        )
        self.storage.put(storage_path, data, mime_type)
        try:
            artifact_id = self.store.add_artifact(
                self.owner_user_id,
                artifact_type=artifact_type,
                filename=filename,
                mime_type=mime_type,
                storage_path=storage_path,
                project_id=self.project_id,
                conversation_id=self.conversation_id,
                metadata=metadata,
            )
        except Exception:
            self.storage.delete(storage_path)
            raise
        return ArtifactReference(artifact_id, artifact_type, filename, mime_type)

    def generate_farm_action_plan(
        self,
        *,
        title: str,
        context: str,
        actions: list[str],
        assumptions: list[str] | None = None,
        sources: list[str] | None = None,
        language: str = "english",
    ) -> dict[str, Any]:
        data = _docx_bytes(
            title=title,
            sections=[
                ("Context / السياق", context),
                ("Action plan / خطة العمل", actions),
            ],
            language=language,
            sources=sources or [],
            assumptions=assumptions or [],
        )
        filename = _safe_filename(title, ".docx")
        return self._save(
            "farm_action_plan",
            filename,
            DOCX_MIME,
            data,
            {"language": language, "item_count": len(actions)},
        ).to_dict()

    def generate_inspection_checklist(
        self,
        *,
        title: str,
        context: str,
        checks: list[str],
        escalation_signs: list[str] | None = None,
        sources: list[str] | None = None,
        language: str = "english",
    ) -> dict[str, Any]:
        sections: list[tuple[str, str | list[str]]] = [
            ("Context / السياق", context),
            ("Inspection checks / نقاط الفحص", [f"☐ {item}" for item in checks]),
        ]
        if escalation_signs:
            sections.append(
                ("Escalate when / متى تجب الإحالة", escalation_signs)
            )
        data = _docx_bytes(
            title=title,
            sections=sections,
            language=language,
            sources=sources or [],
            assumptions=[],
        )
        filename = _safe_filename(title, ".docx")
        return self._save(
            "inspection_checklist",
            filename,
            DOCX_MIME,
            data,
            {"language": language, "item_count": len(checks)},
        ).to_dict()

    def generate_expert_referral_brief(
        self,
        *,
        title: str,
        situation: str,
        observations: list[str],
        question_for_expert: str,
        urgent_signs: list[str] | None = None,
        sources: list[str] | None = None,
        language: str = "english",
    ) -> dict[str, Any]:
        sections: list[tuple[str, str | list[str]]] = [
            ("Situation / الحالة", situation),
            ("Observed information / المعلومات المرصودة", observations),
            ("Decision needed / القرار المطلوب", question_for_expert),
        ]
        if urgent_signs:
            sections.append(("Urgent signs / مؤشرات عاجلة", urgent_signs))
        data = _docx_bytes(
            title=title,
            sections=sections,
            language=language,
            sources=sources or [],
            assumptions=[],
        )
        filename = _safe_filename(title, ".docx")
        return self._save(
            "expert_referral_brief",
            filename,
            DOCX_MIME,
            data,
            {"language": language},
        ).to_dict()

    def generate_crop_calendar(
        self,
        *,
        title: str,
        entries: list[dict[str, Any]],
        assumptions: list[str] | None = None,
        sources: list[str] | None = None,
        language: str = "english",
    ) -> dict[str, Any]:
        rows = _limited_items(entries, 60)
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Crop calendar"
        headers = ["Period", "Activity", "Decision trigger", "Risk / note", "Source"]
        sheet.append(headers)
        for cell in sheet[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="467A52")
            cell.alignment = Alignment(wrap_text=True)
        for entry in rows:
            sheet.append(
                [
                    _safe_cell(str(entry.get("period") or "")),
                    _safe_cell(str(entry.get("activity") or "")),
                    _safe_cell(str(entry.get("trigger") or "")),
                    _safe_cell(str(entry.get("risk") or "")),
                    _safe_cell(str(entry.get("source") or "")),
                ]
            )
        for column in "ABCDE":
            sheet.column_dimensions[column].width = 28
        meta = workbook.create_sheet("Assumptions and sources")
        meta.append(["Generated", datetime.now(timezone.utc).isoformat()])
        meta.append(["Language", language])
        meta.append(["Assumptions"])
        for item in (assumptions or [])[:20]:
            meta.append([_safe_cell(item)])
        meta.append(["Sources"])
        for item in (sources or [])[:20]:
            meta.append([_safe_cell(item)])
        buffer = io.BytesIO()
        workbook.save(buffer)
        filename = _safe_filename(title, ".xlsx")
        return self._save(
            "crop_calendar",
            filename,
            XLSX_MIME,
            buffer.getvalue(),
            {"language": language, "entry_count": len(rows)},
        ).to_dict()

    def calculate_enterprise_budget(
        self,
        *,
        title: str,
        currency: str,
        costs: list[dict[str, Any]],
        revenues: list[dict[str, Any]],
        assumptions: list[str] | None = None,
        sources: list[str] | None = None,
    ) -> dict[str, Any]:
        cost_rows = _limited_items(costs, 100)
        revenue_rows = _limited_items(revenues, 50)
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Enterprise budget"
        sheet.append([title])
        sheet.append(["Currency", _safe_cell(currency)])
        sheet.append([])
        sheet.append(["Costs"])
        sheet.append(["Item", "Quantity", "Unit", "Unit cost", "Total cost"])
        cost_start = 6
        for row in cost_rows:
            sheet.append(
                [
                    _safe_cell(str(row.get("item") or "")),
                    float(row.get("quantity") or 0),
                    _safe_cell(str(row.get("unit") or "")),
                    float(row.get("unit_cost") or 0),
                    None,
                ]
            )
            current = sheet.max_row
            sheet.cell(current, 5, f"=B{current}*D{current}")
        cost_end = sheet.max_row
        sheet.append(["Total costs", None, None, None, f"=SUM(E{cost_start}:E{cost_end})"])
        total_cost_row = sheet.max_row

        sheet.append([])
        sheet.append(["Revenue scenarios"])
        sheet.append(["Item", "Quantity", "Unit", "Unit price", "Total revenue"])
        revenue_start = sheet.max_row + 1
        for row in revenue_rows:
            sheet.append(
                [
                    _safe_cell(str(row.get("item") or "")),
                    float(row.get("quantity") or 0),
                    _safe_cell(str(row.get("unit") or "")),
                    float(row.get("unit_price") or 0),
                    None,
                ]
            )
            current = sheet.max_row
            sheet.cell(current, 5, f"=B{current}*D{current}")
        revenue_end = sheet.max_row
        sheet.append(
            [
                "Total revenue",
                None,
                None,
                None,
                f"=SUM(E{revenue_start}:E{revenue_end})",
            ]
        )
        total_revenue_row = sheet.max_row
        sheet.append(
            [
                "Net before financing/tax",
                None,
                None,
                None,
                f"=E{total_revenue_row}-E{total_cost_row}",
            ]
        )
        for column in "ABCDE":
            sheet.column_dimensions[column].width = 24
        for row_number in (1, 4, 5, total_cost_row, total_revenue_row):
            for cell in sheet[row_number]:
                cell.font = Font(bold=True)
        meta = workbook.create_sheet("Assumptions and sources")
        meta.append(["Generated", datetime.now(timezone.utc).isoformat()])
        meta.append(["Currency", _safe_cell(currency)])
        meta.append(["Assumptions"])
        for item in (assumptions or [])[:30]:
            meta.append([_safe_cell(item)])
        meta.append(["Sources"])
        for item in (sources or [])[:30]:
            meta.append([_safe_cell(item)])

        total_cost = sum(
            float(row.get("quantity") or 0) * float(row.get("unit_cost") or 0)
            for row in cost_rows
        )
        total_revenue = sum(
            float(row.get("quantity") or 0) * float(row.get("unit_price") or 0)
            for row in revenue_rows
        )
        buffer = io.BytesIO()
        workbook.save(buffer)
        filename = _safe_filename(title, ".xlsx")
        reference = self._save(
            "enterprise_budget",
            filename,
            XLSX_MIME,
            buffer.getvalue(),
            {
                "currency": currency[:20],
                "total_cost": total_cost,
                "total_revenue": total_revenue,
                "net_before_financing_tax": total_revenue - total_cost,
            },
        )
        return {
            **reference.to_dict(),
            "currency": currency[:20],
            "total_cost": round(total_cost, 2),
            "total_revenue": round(total_revenue, 2),
            "net_before_financing_tax": round(total_revenue - total_cost, 2),
            "warning": "Scenario estimate; not a profit guarantee.",
        }


def convert_agricultural_units(
    value: float,
    from_unit: str,
    to_unit: str,
) -> dict[str, Any]:
    units = {
        "m2": ("area", 1.0),
        "dunam": ("area", 1000.0),
        "hectare": ("area", 10000.0),
        "liter": ("volume", 1.0),
        "m3": ("volume", 1000.0),
        "kg": ("mass", 1.0),
        "tonne": ("mass", 1000.0),
    }
    source = from_unit.lower().strip()
    target = to_unit.lower().strip()
    if source not in units or target not in units:
        raise ValueError("Unsupported unit")
    source_dimension, source_factor = units[source]
    target_dimension, target_factor = units[target]
    if source_dimension != target_dimension:
        raise ValueError("Units measure different dimensions")
    result = float(value) * source_factor / target_factor
    return {
        "value": float(value),
        "from_unit": source,
        "result": round(result, 8),
        "to_unit": target,
    }
