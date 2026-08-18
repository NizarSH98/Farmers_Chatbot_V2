"""Versioned bilingual agrifood ontology compiled into knowledge releases.

The ontology is deterministic and provider-independent. It models concepts and
evidence-qualified connections; it never changes the corpus review status.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from .agrifood_ontology_v03_data import V03_ENTITIES, V03_RELATIONS
from .graph_ingestion import (
    ENTITY_TYPES,
    RELATION_TYPES,
    canonical_json_sha256,
    normalize_search_text,
)

ONTOLOGY_VERSION = "raise-agrifood-ontology-v0.3.0"
ONTOLOGY_MIN_ENTITIES = 250
ONTOLOGY_MIN_RELATIONS = 450

S = "kb-scope-local-context"
C = "kb-crop-production"
L = "kb-livestock"
SO = "kb-soil-management"
W = "kb-water-irrigation"
I = "kb-ipm-safety"
CL = "kb-climate-season"
G = "kb-greenhouse"
P = "kb-postharvest"
F = "kb-food-processing-safety"
B = "kb-business-markets"
T = "kb-troubleshooting"
D = "kb-decision-rules"
Q = "kb-faq"
M = "kb-misconceptions"
R = "kb-referrals"
TE = "kb-terminology"
DY = "kb-dynamic-information"


@dataclass(frozen=True)
class OntologyAlias:
    text: str
    language: str
    script: str


@dataclass(frozen=True)
class OntologyEntity:
    key: str
    entity_type: str
    label_en: str
    label_ar: str
    aliases: tuple[OntologyAlias, ...] = ()
    record_ids: tuple[str, ...] = ()

    def metadata(self) -> dict[str, Any]:
        return {
            "id": self.key,
            "type": self.entity_type,
            "label_en": self.label_en,
            "label_ar": self.label_ar,
            "aliases": [
                {
                    "text": alias.text,
                    "language": alias.language,
                    "script": alias.script,
                }
                for alias in self.aliases
            ],
        }


@dataclass(frozen=True)
class OntologyRelation:
    record_id: str
    subject: str
    predicate: str
    object: str
    evidence_section: str = "English guidance"
    risk: str = "medium"
    polarity: str = "positive"
    qualifiers: dict[str, Any] = field(default_factory=dict)

    def metadata(self) -> dict[str, Any]:
        return {
            "subject": self.subject,
            "type": self.predicate,
            "object": self.object,
            "evidence_section": self.evidence_section,
            "risk": self.risk,
            "polarity": self.polarity,
            "qualifiers": self.qualifiers,
        }


def _a(*values: tuple[str, str, str]) -> tuple[OntologyAlias, ...]:
    return tuple(OntologyAlias(*value) for value in values)


def _e(
    key: str,
    entity_type: str,
    label_en: str,
    label_ar: str,
    records: tuple[str, ...],
    aliases: tuple[OntologyAlias, ...] = (),
) -> OntologyEntity:
    return OntologyEntity(key, entity_type, label_en, label_ar, aliases, records)


ENTITIES: tuple[OntologyEntity, ...] = (
    _e("akkar", "location", "Akkar", "عكار", (S, C, CL), _a(("3akkar", "arz", "latin"))),
    _e("akkar_plain", "location", "Akkar agricultural plain", "سهل عكار الزراعي", (S,)),
    _e("akkar_uplands", "location", "Akkar uplands and terraces", "مرتفعات عكار ومدرجاتها", (S,)),
    _e("rural_lebanon", "location", "rural Lebanon", "لبنان الريفي", (S, R)),
    _e("potato", "crop", "potato", "البطاطا", (C, T, Q), _a(("بطاطا", "arz", "arabic"), ("batata", "arz", "latin"))),
    _e("orchard_crop", "crop", "orchard crop", "محصول بستاني", (C, P)),
    _e("olive", "crop", "olive", "الزيتون", (C, P)),
    _e("apple", "crop", "apple", "التفاح", (C, P)),
    _e("citrus", "crop", "citrus", "الحمضيات", (C, P)),
    _e("avocado", "crop", "avocado", "الأفوكادو", (C, P)),
    _e("tomato", "crop", "tomato", "البندورة", (G,), _a(("بندورة", "arz", "arabic"), ("banadoura", "arz", "latin"))),
    _e("cucumber", "crop", "cucumber", "الخيار", (G,)),
    _e("leafy_herb", "crop", "leafy herb", "عشبة ورقية", (G, P)),
    _e("legume", "crop", "legume", "بقوليات", (C, SO)),
    _e("certified_seed_potato", "variety", "certified seed potato", "تقاوي بطاطا معتمدة", (C,)),
    _e("market_suited_variety", "variety", "market-suited variety", "صنف ملائم للسوق", (C, B)),
    _e("cattle", "animal", "cattle", "الأبقار", (L,)),
    _e("sheep", "animal", "sheep", "الأغنام", (L,)),
    _e("goat", "animal", "goat", "الماعز", (L,)),
    _e("poultry", "animal", "poultry", "الدواجن", (L,)),
    _e("planting", "production_stage", "planting stage", "مرحلة الزراعة", (C, CL)),
    _e("vegetative", "production_stage", "vegetative stage", "مرحلة النمو الخضري", (C, G)),
    _e("flowering", "production_stage", "flowering stage", "مرحلة الإزهار", (C, CL)),
    _e("harvest", "production_stage", "harvest stage", "مرحلة الحصاد", (P,)),
    _e("postharvest", "production_stage", "post-harvest stage", "مرحلة ما بعد الحصاد", (P, F)),
    _e("storage", "production_stage", "storage stage", "مرحلة التخزين", (P, F)),
    _e("young_animal", "production_stage", "young-animal stage", "مرحلة الحيوان الصغير", (L,)),
    _e("lactation", "production_stage", "lactation stage", "مرحلة الإدرار", (L,)),
    _e("wilting", "symptom", "crop wilting", "ذبول المحصول", (T, Q), _a(("ذبول", "ar", "arabic"), ("zouboul", "arz", "latin"))),
    _e("yellowing", "symptom", "leaf yellowing", "اصفرار الأوراق", (T, Q), _a(("اصفرار", "ar", "arabic"), ("isfirar", "arz", "latin"))),
    _e("stunting", "symptom", "stunting", "تقزم النمو", (T,)),
    _e("leaf_spot", "symptom", "leaf spot", "بقع الأوراق", (T, G)),
    _e("root_damage", "symptom", "root damage", "ضرر الجذور", (T, SO)),
    _e("diarrhea", "symptom", "animal diarrhea", "إسهال الحيوان", (L, T)),
    _e("respiratory_distress", "symptom", "respiratory distress", "ضيق التنفس", (L, T)),
    _e("lameness", "symptom", "lameness", "العرج", (L, T)),
    _e("sudden_mortality", "symptom", "sudden mortality", "نفوق مفاجئ", (L, R)),
    _e("package_swelling", "symptom", "package swelling", "انتفاخ العبوة", (P, F)),
    _e("off_odor", "symptom", "unusual odor", "رائحة غير طبيعية", (P, F)),
    _e("insect_pest", "pest", "insect pest", "آفة حشرية", (C, I, G)),
    _e("weed", "pest", "weed", "عشب ضار", (I, Q)),
    _e("rodent", "pest", "rodent", "قارض", (L, P)),
    _e("crop_disease", "disease", "crop disease", "مرض نباتي", (C, G, T)),
    _e("animal_disease", "disease", "animal disease", "مرض حيواني", (L, T)),
    _e("zoonotic_disease", "disease", "zoonotic disease", "مرض حيواني المنشأ", (L, R)),
    _e("foodborne_disease", "disease", "foodborne disease", "مرض منقول بالغذاء", (F, R)),
    _e("site_assessment", "practice", "site assessment", "تقييم الموقع", (S, C)),
    _e("field_history", "practice", "field history review", "مراجعة تاريخ الحقل", (C, SO, T)),
    _e("certified_seed_use", "practice", "certified seed use", "استخدام تقاوي معتمدة", (C,)),
    _e("crop_rotation", "practice", "crop rotation", "الدورة الزراعية", (C, I, SO)),
    _e("scouting", "practice", "field scouting", "الكشف الحقلي", (C, I, G)),
    _e("ipm", "practice", "integrated pest management", "الإدارة المتكاملة للآفات", (I, C), _a(("IPM", "en", "latin"), ("ادارة متكاملة", "arz", "arabic"))),
    _e("sanitation", "practice", "farm sanitation", "النظافة الزراعية", (I, L, G)),
    _e("biosecurity", "practice", "farm biosecurity", "الأمن الحيوي", (L,)),
    _e("soil_sampling", "practice", "representative soil sampling", "أخذ عينة تربة ممثلة", (SO,)),
    _e("irrigation_scheduling", "practice", "irrigation scheduling", "جدولة الري", (W, Q), _a(("jadwalet el ray", "arz", "latin"))),
    _e("drip_maintenance", "practice", "drip-system maintenance", "صيانة نظام التنقيط", (W, G)),
    _e("greenhouse_system", "practice", "greenhouse production system", "نظام إنتاج في الدفيئة", (G,)),
    _e("ventilation", "practice", "greenhouse ventilation", "تهوية الدفيئة", (G, L)),
    _e("shade_management", "practice", "shade management", "إدارة التظليل", (G, L)),
    _e("record_keeping", "practice", "farm record keeping", "حفظ سجلات المزرعة", (C, L, G, B)),
    _e("traceability", "practice", "traceability", "التتبع", (P, F)),
    _e("cold_chain", "practice", "cold-chain management", "إدارة سلسلة التبريد", (P, F)),
    _e("sorting", "practice", "produce sorting", "فرز المنتج", (P,)),
    _e("haccp", "practice", "HACCP system", "نظام تحليل المخاطر ونقاط التحكم الحرجة", (F,), _a(("HACCP", "en", "latin"), ("هاسب", "ar", "arabic"))),
    _e("hygiene", "practice", "good hygiene practice", "ممارسات النظافة الجيدة", (F, L)),
    _e("isolation", "practice", "risk isolation", "عزل الخطر", (L, R)),
    _e("diagnosis_workflow", "practice", "differential diagnosis workflow", "مسار التشخيص التفريقي", (T, D)),
    _e("enterprise_budget", "practice", "enterprise budgeting", "موازنة المشروع الزراعي", (B,)),
    _e("break_even_analysis", "practice", "break-even analysis", "تحليل نقطة التعادل", (B,)),
    _e("sensitivity_analysis", "practice", "sensitivity analysis", "تحليل الحساسية", (B,)),
    _e("crop_calendar", "practice", "adaptive crop calendar", "تقويم زراعي تكيفي", (CL,)),
    _e("professional_referral", "practice", "professional referral", "الإحالة المهنية", (R, D)),
    _e("nonchemical_control", "practice", "non-chemical risk reduction", "خفض الخطر من دون مواد كيميائية", (I,)),
    _e("waste_reduction", "practice", "waste reduction", "خفض الهدر", (P, B)),
    _e("irrigation_water", "input", "irrigation water", "مياه الري", (W, C, G), _a(("مي الري", "arz", "arabic"), ("mayy el ray", "arz", "latin"))),
    _e("fertilizer", "input", "fertilizer", "سماد", (SO, T, Q), _a(("smad", "arz", "latin"))),
    _e("manure", "input", "manure", "روث حيواني", (SO, F)),
    _e("compost", "input", "compost", "سماد عضوي معالج", (SO,)),
    _e("pesticide", "input", "agricultural pesticide", "مبيد زراعي", (I, C, DY), _a(("مبيد", "ar", "arabic"), ("mabid", "arz", "latin"))),
    _e("glyphosate", "input", "glyphosate", "غليفوسات", (I, Q)),
    _e("veterinary_medicine", "input", "veterinary medicine", "دواء بيطري", (L, DY)),
    _e("antimicrobial", "input", "antimicrobial", "مضاد ميكروبي", (L,)),
    _e("planting_material", "input", "planting material", "مواد الإكثار الزراعي", (C,)),
    _e("energy_input", "input", "energy input", "مدخلات الطاقة", (G, B)),
    _e("labor_input", "input", "labor input", "مدخلات العمل", (B,)),
    _e("soil_health", "soil", "soil health", "صحة التربة", (SO, M)),
    _e("salinity", "soil", "soil salinity", "ملوحة التربة", (SO, T)),
    _e("sodicity", "soil", "soil sodicity", "صودية التربة", (SO,)),
    _e("soil_ph", "soil", "soil pH", "درجة حموضة التربة", (SO, T)),
    _e("soil_ec", "soil", "soil electrical conductivity", "التوصيل الكهربائي للتربة", (SO, T), _a(("EC", "en", "latin"))),
    _e("compaction", "soil", "soil compaction", "انضغاط التربة", (SO, T)),
    _e("waterlogging", "soil", "waterlogging", "تغدق التربة", (SO, T)),
    _e("drainage", "soil", "soil drainage", "صرف التربة", (SO, W)),
    _e("organic_matter", "soil", "soil organic matter", "المادة العضوية في التربة", (SO,)),
    _e("water_quality", "water", "water quality", "نوعية المياه", (W, C, G)),
    _e("water_reliability", "water", "water-source reliability", "موثوقية مصدر المياه", (W, G, S)),
    _e("emitter_flow", "water", "emitter flow", "تصريف النقاط", (W, Q)),
    _e("pressure_uniformity", "water", "irrigation pressure uniformity", "تجانس ضغط الري", (W,)),
    _e("root_zone_moisture", "water", "root-zone moisture", "رطوبة منطقة الجذور", (W, T, Q)),
    _e("rainwater_harvesting", "water", "rainwater harvesting", "حصاد مياه الأمطار", (W, CL)),
    _e("heat", "climate", "heat stress", "إجهاد حراري", (CL, T, G)),
    _e("frost", "climate", "frost exposure", "التعرض للصقيع", (S, CL)),
    _e("drought", "climate", "drought", "الجفاف", (CL, W)),
    _e("extreme_weather", "climate", "extreme weather", "طقس متطرف", (CL, DY)),
    _e("humidity", "climate", "high humidity", "رطوبة مرتفعة", (G,)),
    _e("precipitation_decline", "climate", "declining precipitation", "تراجع الهطول", (CL,)),
    _e("planting_window", "season", "planting window", "نافذة الزراعة", (CL, C)),
    _e("harvest_window", "season", "harvest window", "نافذة الحصاد", (CL, P)),
    _e("alert_window", "season", "current alert window", "نافذة التنبيه الحالية", (CL, DY)),
    _e("moa_lebanon", "organization", "Lebanon Ministry of Agriculture", "وزارة الزراعة اللبنانية", (S, I, DY)),
    _e("lari", "organization", "Lebanese Agricultural Research Institute", "مصلحة الأبحاث العلمية الزراعية", (C, CL, DY), _a(("LARI", "en", "latin"), ("لاري", "arz", "arabic"))),
    _e("codex", "organization", "Codex Alimentarius", "الدستور الغذائي", (F,)),
    _e("who", "organization", "World Health Organization", "منظمة الصحة العالمية", (F,)),
    _e("competent_authority", "organization", "competent authority", "السلطة المختصة", (F, I, R)),
    _e("cooperative", "organization", "farmer cooperative", "تعاونية زراعية", (B, R)),
    _e("agronomist", "service", "qualified agronomist", "مهندس زراعي مؤهل", (C, I, R), _a(("مهندس زراعي", "arz", "arabic"), ("mhandes zira3e", "arz", "latin"))),
    _e("veterinarian", "service", "veterinarian", "طبيب بيطري", (L, R), _a(("دكتور بيطري", "arz", "arabic"), ("doctor baytari", "arz", "latin"))),
    _e("soil_water_lab", "service", "soil and water laboratory", "مختبر تربة ومياه", (SO, W, R)),
    _e("food_safety_specialist", "service", "food-safety specialist", "اختصاصي سلامة غذاء", (F, P, R)),
    _e("irrigation_engineer", "service", "irrigation engineer", "مهندس ري", (W, R)),
    _e("emergency_service", "service", "emergency service", "خدمة طوارئ", (R,)),
    _e("extension_service", "service", "agricultural extension service", "خدمة الإرشاد الزراعي", (R, S)),
    _e("market_information_service", "service", "dated market-information service", "خدمة معلومات سوق مؤرخة", (B, DY)),
    _e("buyer", "market", "buyer", "المشتري", (P, B)),
    _e("fresh_market", "market", "fresh produce market", "سوق المنتجات الطازجة", (P, B)),
    _e("processing_market", "market", "processing market", "سوق التصنيع", (P, B)),
    _e("buyer_specification", "market", "buyer specification", "مواصفة المشتري", (P, B)),
    _e("grant_opportunity", "market", "grant or opportunity call", "إعلان منحة أو فرصة", (B, DY)),
    _e("export_condition", "market", "export condition", "شرط تصدير", (B, DY)),
    _e("pesticide_register", "regulation", "current pesticide register", "سجل المبيدات الحالي", (I, DY)),
    _e("product_label", "regulation", "registered product label", "ملصق المنتج المسجل", (I, D)),
    _e("preharvest_interval", "regulation", "pre-harvest interval", "فترة ما قبل الحصاد", (I,), _a(("PHI", "en", "latin"))),
    _e("reentry_interval", "regulation", "re-entry interval", "فترة إعادة الدخول", (I,), _a(("REI", "en", "latin"))),
    _e("withdrawal_period", "regulation", "veterinary withdrawal period", "فترة سحب الدواء البيطري", (L,)),
    _e("food_licensing", "regulation", "food-business licensing", "ترخيص المنشأة الغذائية", (F, DY)),
    _e("organic_standard", "regulation", "organic production standard", "معيار الإنتاج العضوي", (M, DY)),
    _e("poisoning", "risk", "suspected poisoning", "اشتباه تسمم", (I, R)),
    _e("worker_exposure", "risk", "worker chemical exposure", "تعرض العامل لمادة كيميائية", (I, R)),
    _e("food_contamination", "risk", "food contamination", "تلوث الغذاء", (P, F, R)),
    _e("zoonotic_exposure", "risk", "zoonotic exposure", "تعرض لمرض حيواني المنشأ", (L, R)),
    _e("chemical_residue", "risk", "chemical residue risk", "خطر المتبقيات الكيميائية", (I, P)),
    _e("electrical_danger", "risk", "machinery or electrical danger", "خطر آلي أو كهربائي", (R,)),
    _e("false_diagnosis", "risk", "premature diagnosis", "تشخيص متسرع", (T, M)),
    _e("stale_information", "risk", "stale information", "معلومات قديمة", (DY, B)),
    _e("fixed_cost", "cost", "fixed cost", "تكلفة ثابتة", (B,)),
    _e("variable_cost", "cost", "variable cost", "تكلفة متغيرة", (B,)),
    _e("working_capital", "cost", "working capital", "رأس المال العامل", (B,)),
    _e("owner_labor", "cost", "owner labor", "عمل المالك", (B,)),
    _e("financing_cost", "cost", "financing cost", "تكلفة التمويل", (B,)),
    _e("depreciation", "cost", "depreciation", "الاستهلاك المحاسبي", (B,)),
    _e("contribution_margin", "cost", "contribution margin", "هامش المساهمة", (B,)),
    _e("break_even_price", "cost", "break-even price", "سعر التعادل", (B,)),
    _e("break_even_yield", "cost", "break-even yield", "إنتاج التعادل", (B,)),
    _e("water_use", "sustainability_impact", "water use", "استخدام المياه", (W, B, M)),
    _e("fertilizer_loss", "sustainability_impact", "fertilizer loss", "فقد الأسمدة", (SO, M, B)),
    _e("pesticide_use", "sustainability_impact", "pesticide use", "استخدام المبيدات", (I, B)),
    _e("energy_use", "sustainability_impact", "energy use", "استخدام الطاقة", (G, B)),
    _e("labor_impact", "sustainability_impact", "labor impact", "أثر العمل", (B,)),
    _e("soil_conservation", "sustainability_impact", "soil conservation", "حفظ التربة", (SO, CL)),
    _e("biodiversity", "sustainability_impact", "farm biodiversity", "التنوع الحيوي الزراعي", (I, M)),
    _e("food_loss", "sustainability_impact", "food loss", "فقد الغذاء", (P, B)),
)


ENTITIES += tuple(
    _e(
        key,
        entity_type,
        label_en,
        label_ar,
        record_ids,
        _a(*aliases),
    )
    for key, entity_type, label_en, label_ar, record_ids, aliases in V03_ENTITIES
)

def _r(
    record_id: str,
    subject: str,
    predicate: str,
    object_: str,
    *,
    section: str = "English guidance",
    risk: str = "medium",
    **qualifiers: Any,
) -> OntologyRelation:
    return OntologyRelation(
        record_id=record_id,
        subject=subject,
        predicate=predicate,
        object=object_,
        evidence_section=section,
        risk=risk,
        qualifiers=qualifiers,
    )


RELATIONS: tuple[OntologyRelation, ...] = (
    _r(S, "site_assessment", "applies_to", "akkar"),
    _r(S, "site_assessment", "requires_context", "akkar_plain", context="terrain"),
    _r(S, "site_assessment", "requires_context", "akkar_uplands", context="altitude_and_slope"),
    _r(S, "site_assessment", "requires_context", "water_reliability"),
    _r(S, "crop_calendar", "requires_context", "frost"),
    _r(S, "crop_calendar", "requires_context", "buyer"),
    _r(S, "professional_referral", "applies_to", "rural_lebanon"),
    _r(S, "extension_service", "related_to", "moa_lebanon"),
    _r(C, "field_history", "applies_to", "potato"),
    _r(C, "certified_seed_use", "applies_to", "certified_seed_potato"),
    _r(C, "potato", "requires_context", "market_suited_variety"),
    _r(C, "potato", "requires_context", "water_quality"),
    _r(C, "potato", "requires_context", "soil_health"),
    _r(C, "crop_rotation", "supports_action", "soil_health"),
    _r(C, "scouting", "supports_action", "ipm"),
    _r(C, "pesticide", "requires_context", "crop_disease", risk="high"),
    _r(C, "pesticide", "requires_live_source", "pesticide_register", risk="high"),
    _r(C, "crop_disease", "escalates_to", "agronomist", risk="high"),
    _r(C, "planting_material", "requires_context", "planting"),
    _r(C, "orchard_crop", "requires_context", "harvest_window"),
    _r(L, "biosecurity", "applies_to", "cattle"),
    _r(L, "biosecurity", "applies_to", "sheep"),
    _r(L, "biosecurity", "applies_to", "goat"),
    _r(L, "biosecurity", "applies_to", "poultry"),
    _r(L, "biosecurity", "supports_action", "zoonotic_exposure", risk="high"),
    _r(L, "isolation", "supports_action", "animal_disease", risk="high"),
    _r(L, "sudden_mortality", "escalates_to", "veterinarian", risk="critical"),
    _r(L, "respiratory_distress", "escalates_to", "veterinarian", risk="critical"),
    _r(L, "diarrhea", "requires_context", "young_animal", risk="high"),
    _r(L, "veterinary_medicine", "requires_context", "animal_disease", risk="high"),
    _r(L, "veterinary_medicine", "requires_context", "withdrawal_period", risk="high"),
    _r(L, "antimicrobial", "requires_context", "veterinarian", risk="high"),
    _r(L, "hygiene", "supports_action", "biosecurity"),
    _r(L, "ventilation", "applies_to", "poultry"),
    _r(SO, "soil_sampling", "supports_action", "soil_health"),
    _r(SO, "soil_sampling", "requires_context", "field_history"),
    _r(SO, "fertilizer", "requires_context", "soil_ph"),
    _r(SO, "fertilizer", "requires_context", "soil_ec"),
    _r(SO, "fertilizer", "requires_context", "organic_matter"),
    _r(SO, "salinity", "may_cause", "stunting"),
    _r(SO, "waterlogging", "may_cause", "root_damage"),
    _r(SO, "compaction", "may_cause", "root_damage"),
    _r(SO, "drainage", "supports_action", "waterlogging"),
    _r(SO, "compost", "requires_context", "soil_health"),
    _r(SO, "manure", "requires_context", "food_contamination", risk="high"),
    _r(SO, "crop_rotation", "supports_action", "soil_conservation"),
    _r(W, "irrigation_scheduling", "requires_context", "emitter_flow"),
    _r(W, "irrigation_scheduling", "requires_context", "root_zone_moisture"),
    _r(W, "irrigation_scheduling", "requires_context", "water_quality"),
    _r(W, "irrigation_scheduling", "requires_context", "heat"),
    _r(W, "drip_maintenance", "supports_action", "pressure_uniformity"),
    _r(W, "drainage", "requires_context", "soil_health"),
    _r(W, "rainwater_harvesting", "supports_action", "water_reliability"),
    _r(W, "water_reliability", "supports_action", "crop_calendar"),
    _r(W, "irrigation_water", "requires_context", "water_quality"),
    _r(W, "irrigation_scheduling", "supports_action", "water_use"),
    _r(I, "ipm", "depends_on", "scouting"),
    _r(I, "ipm", "depends_on", "sanitation"),
    _r(I, "ipm", "depends_on", "nonchemical_control"),
    _r(I, "pesticide", "requires_live_source", "pesticide_register", risk="high"),
    _r(I, "pesticide", "requires_context", "product_label", risk="high"),
    _r(I, "product_label", "requires_context", "preharvest_interval", risk="high"),
    _r(I, "product_label", "requires_context", "reentry_interval", risk="high"),
    _r(I, "pesticide", "may_cause", "worker_exposure", risk="high"),
    _r(I, "pesticide", "may_cause", "chemical_residue", risk="high"),
    _r(I, "poisoning", "escalates_to", "emergency_service", risk="critical"),
    _r(I, "worker_exposure", "escalates_to", "emergency_service", risk="critical"),
    _r(I, "glyphosate", "prohibits", "professional_referral", risk="high", basis="RAISE_product_policy"),
    _r(I, "moa_lebanon", "supported_by", "pesticide_register", risk="high"),
    _r(I, "insect_pest", "may_be_confused_with", "crop_disease"),
    _r(I, "nonchemical_control", "supports_action", "pesticide_use"),
    _r(CL, "crop_calendar", "requires_context", "akkar"),
    _r(CL, "crop_calendar", "requires_context", "planting_window"),
    _r(CL, "crop_calendar", "requires_context", "harvest_window"),
    _r(CL, "crop_calendar", "requires_context", "water_reliability"),
    _r(CL, "crop_calendar", "requires_live_source", "alert_window"),
    _r(CL, "heat", "may_cause", "wilting"),
    _r(CL, "drought", "may_cause", "water_reliability"),
    _r(CL, "precipitation_decline", "may_cause", "drought"),
    _r(CL, "extreme_weather", "requires_live_source", "lari", risk="high"),
    _r(CL, "frost", "requires_context", "planting_window"),
    _r(CL, "soil_conservation", "supports_action", "drought"),
    _r(G, "greenhouse_system", "requires_context", "ventilation"),
    _r(G, "greenhouse_system", "requires_context", "humidity"),
    _r(G, "greenhouse_system", "requires_context", "water_reliability"),
    _r(G, "ventilation", "applies_to", "tomato"),
    _r(G, "ventilation", "applies_to", "cucumber"),
    _r(G, "humidity", "may_cause", "crop_disease"),
    _r(G, "drip_maintenance", "applies_to", "greenhouse_system"),
    _r(G, "irrigation_scheduling", "requires_context", "vegetative"),
    _r(G, "shade_management", "supports_action", "heat"),
    _r(G, "energy_input", "requires_context", "water_reliability"),
    _r(G, "scouting", "supports_action", "crop_disease"),
    _r(G, "record_keeping", "supports_action", "diagnosis_workflow"),
    _r(P, "harvest", "requires_context", "buyer_specification"),
    _r(P, "sorting", "applies_to", "postharvest"),
    _r(P, "cold_chain", "applies_to", "storage"),
    _r(P, "traceability", "supports_action", "food_contamination", risk="high"),
    _r(P, "package_swelling", "escalates_to", "food_safety_specialist", risk="high"),
    _r(P, "off_odor", "escalates_to", "food_safety_specialist", risk="high"),
    _r(P, "food_contamination", "prohibits", "buyer", risk="high"),
    _r(P, "waste_reduction", "supports_action", "food_loss"),
    _r(P, "fresh_market", "requires_context", "buyer_specification"),
    _r(P, "processing_market", "requires_context", "buyer_specification"),
    _r(P, "orchard_crop", "requires_context", "cold_chain"),
    _r(F, "hygiene", "supports_action", "food_contamination", risk="high"),
    _r(F, "haccp", "depends_on", "hygiene", risk="high"),
    _r(F, "haccp", "supported_by", "codex", risk="high"),
    _r(F, "hygiene", "supported_by", "who", risk="high"),
    _r(F, "postharvest", "requires_context", "food_licensing", risk="high"),
    _r(F, "foodborne_disease", "escalates_to", "emergency_service", risk="critical"),
    _r(F, "package_swelling", "may_cause", "foodborne_disease", risk="high"),
    _r(F, "food_contamination", "escalates_to", "competent_authority", risk="high"),
    _r(F, "traceability", "supports_action", "haccp", risk="high"),
    _r(B, "enterprise_budget", "depends_on", "fixed_cost"),
    _r(B, "enterprise_budget", "depends_on", "variable_cost"),
    _r(B, "enterprise_budget", "depends_on", "working_capital"),
    _r(B, "enterprise_budget", "depends_on", "owner_labor"),
    _r(B, "enterprise_budget", "depends_on", "financing_cost"),
    _r(B, "enterprise_budget", "depends_on", "depreciation"),
    _r(B, "break_even_analysis", "depends_on", "contribution_margin"),
    _r(B, "break_even_analysis", "supports_action", "break_even_price"),
    _r(B, "break_even_analysis", "supports_action", "break_even_yield"),
    _r(B, "sensitivity_analysis", "supports_action", "enterprise_budget"),
    _r(B, "buyer", "requires_context", "market_suited_variety"),
    _r(B, "grant_opportunity", "requires_live_source", "market_information_service"),
    _r(B, "export_condition", "requires_live_source", "competent_authority"),
    _r(B, "enterprise_budget", "requires_context", "water_use"),
    _r(B, "enterprise_budget", "requires_context", "labor_impact"),
    _r(B, "enterprise_budget", "requires_context", "energy_use"),
    _r(B, "enterprise_budget", "requires_context", "pesticide_use"),
    _r(B, "enterprise_budget", "requires_context", "fertilizer_loss"),
    _r(B, "cooperative", "supports_action", "buyer"),
    _r(T, "wilting", "may_be_confused_with", "waterlogging"),
    _r(T, "wilting", "may_be_confused_with", "salinity"),
    _r(T, "wilting", "may_be_confused_with", "heat"),
    _r(T, "wilting", "may_be_confused_with", "crop_disease"),
    _r(T, "yellowing", "may_be_confused_with", "salinity"),
    _r(T, "yellowing", "may_be_confused_with", "root_damage"),
    _r(T, "yellowing", "may_be_confused_with", "crop_disease"),
    _r(T, "stunting", "may_be_confused_with", "compaction"),
    _r(T, "leaf_spot", "may_be_confused_with", "insect_pest"),
    _r(T, "diagnosis_workflow", "requires_context", "field_history"),
    _r(T, "diagnosis_workflow", "requires_context", "root_zone_moisture"),
    _r(T, "false_diagnosis", "prohibits", "pesticide", risk="high"),
    _r(T, "diarrhea", "may_be_confused_with", "animal_disease", risk="high"),
    _r(T, "lameness", "may_be_confused_with", "animal_disease", risk="high"),
    _r(D, "diagnosis_workflow", "depends_on", "site_assessment"),
    _r(D, "pesticide", "requires_context", "product_label", risk="high"),
    _r(D, "professional_referral", "supports_action", "false_diagnosis"),
    _r(D, "stale_information", "requires_live_source", "market_information_service"),
    _r(D, "diagnosis_workflow", "requires_context", "agronomist"),
    _r(Q, "irrigation_scheduling", "requires_context", "emitter_flow"),
    _r(Q, "yellowing", "prohibits", "fertilizer", risk="high"),
    _r(Q, "glyphosate", "prohibits", "pesticide_use", risk="high", basis="RAISE_product_policy"),
    _r(Q, "wilting", "requires_context", "root_zone_moisture"),
    _r(M, "irrigation_water", "may_cause", "fertilizer_loss"),
    _r(M, "fertilizer", "may_cause", "fertilizer_loss"),
    _r(M, "false_diagnosis", "may_cause", "pesticide_use", risk="high"),
    _r(M, "organic_standard", "requires_live_source", "competent_authority"),
    _r(M, "ipm", "supports_action", "biodiversity"),
    _r(M, "waterlogging", "may_cause", "root_damage"),
    _r(R, "poisoning", "escalates_to", "emergency_service", risk="critical"),
    _r(R, "zoonotic_exposure", "escalates_to", "veterinarian", risk="critical"),
    _r(R, "sudden_mortality", "escalates_to", "competent_authority", risk="critical"),
    _r(R, "food_contamination", "escalates_to", "food_safety_specialist", risk="high"),
    _r(R, "root_damage", "escalates_to", "agronomist"),
    _r(R, "salinity", "escalates_to", "soil_water_lab"),
    _r(R, "water_quality", "escalates_to", "soil_water_lab"),
    _r(R, "irrigation_scheduling", "escalates_to", "irrigation_engineer"),
    _r(R, "electrical_danger", "escalates_to", "emergency_service", risk="critical"),
    _r(R, "professional_referral", "requires_context", "extension_service"),
    _r(TE, "diagnosis_workflow", "requires_context", "crop_disease", context="local_and_scientific_name"),
    _r(TE, "insect_pest", "may_be_confused_with", "crop_disease"),
    _r(TE, "professional_referral", "requires_context", "extension_service"),
    _r(DY, "extreme_weather", "requires_live_source", "lari", risk="high"),
    _r(DY, "grant_opportunity", "requires_live_source", "market_information_service"),
    _r(DY, "pesticide_register", "requires_live_source", "moa_lebanon", risk="high"),
    _r(DY, "veterinary_medicine", "requires_live_source", "competent_authority", risk="high"),
    _r(DY, "export_condition", "requires_live_source", "competent_authority"),
    _r(DY, "food_licensing", "requires_live_source", "competent_authority", risk="high"),
    _r(DY, "stale_information", "conflicts_with", "alert_window"),
    _r(DY, "organic_standard", "requires_live_source", "competent_authority"),
)


RELATIONS += tuple(
    OntologyRelation(
        record_id=record_id,
        subject=subject,
        predicate=predicate,
        object=object_,
        risk=risk,
        qualifiers=qualifiers,
    )
    for record_id, subject, predicate, object_, risk, qualifiers in V03_RELATIONS
)


def validate_ontology(record_ids: set[str] | None = None) -> None:
    entity_keys = [item.key for item in ENTITIES]
    if len(ENTITIES) < ONTOLOGY_MIN_ENTITIES:
        raise ValueError("Agrifood ontology is below the entity coverage gate")
    if len(RELATIONS) < ONTOLOGY_MIN_RELATIONS:
        raise ValueError("Agrifood ontology is below the relation coverage gate")
    if len(entity_keys) != len(set(entity_keys)):
        raise ValueError("Agrifood ontology contains duplicate entity keys")
    if {item.entity_type for item in ENTITIES} != set(ENTITY_TYPES):
        raise ValueError("Agrifood ontology does not cover every entity type")
    entity_set = set(entity_keys)
    seen: set[tuple[str, str, str, str, str]] = set()
    for entity in ENTITIES:
        if not entity.label_en or not entity.label_ar:
            raise ValueError(f"Ontology entity lacks bilingual labels: {entity.key}")
    for relation in RELATIONS:
        if relation.predicate not in RELATION_TYPES:
            raise ValueError(f"Unsupported ontology relation: {relation.predicate}")
        if relation.subject not in entity_set or relation.object not in entity_set:
            raise ValueError("Ontology relation references an unknown entity")
        if record_ids is not None and relation.record_id not in record_ids:
            raise ValueError("Ontology relation references an unknown corpus record")
        key = (
            relation.record_id,
            relation.subject,
            relation.predicate,
            relation.object,
            json.dumps(relation.qualifiers, sort_keys=True),
        )
        if key in seen:
            raise ValueError("Agrifood ontology contains duplicate relations")
        seen.add(key)
    alias_targets: dict[str, set[str]] = {}
    for entity in ENTITIES:
        aliases = (
            OntologyAlias(entity.label_en, "en", "latin"),
            OntologyAlias(entity.label_ar, "ar", "arabic"),
            *entity.aliases,
        )
        for alias in aliases:
            normalized = normalize_search_text(alias.text)
            if not normalized:
                raise ValueError(f"Empty ontology alias: {entity.key}")
            alias_targets.setdefault(normalized, set()).add(entity.key)
    ambiguous = {key: value for key, value in alias_targets.items() if len(value) > 1}
    if ambiguous:
        raise ValueError(f"Ambiguous ontology aliases: {sorted(ambiguous)[:5]}")


def ontology_for_record(record_id: str) -> dict[str, Any]:
    return {
        "ontology_version": ONTOLOGY_VERSION,
        "ontology_entities": [
            entity.metadata() for entity in ENTITIES if record_id in entity.record_ids
        ],
        "ontology_relations": [
            relation.metadata() for relation in RELATIONS if relation.record_id == record_id
        ],
    }


def resolve_ontology_entity(value: str) -> str | None:
    normalized = normalize_search_text(value)
    matches: set[str] = set()
    for entity in ENTITIES:
        aliases = (
            entity.label_en,
            entity.label_ar,
            *(alias.text for alias in entity.aliases),
        )
        if normalized in {normalize_search_text(alias) for alias in aliases}:
            matches.add(entity.key)
    return next(iter(matches)) if len(matches) == 1 else None


def ontology_fingerprint() -> str:
    return canonical_json_sha256(
        {
            "version": ONTOLOGY_VERSION,
            "entities": [entity.metadata() for entity in ENTITIES],
            "relations": [
                relation.metadata() | {"record_id": relation.record_id}
                for relation in RELATIONS
            ],
        }
    )


validate_ontology()
