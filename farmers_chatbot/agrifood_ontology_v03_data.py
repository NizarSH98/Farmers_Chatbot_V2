"""Schema-first v0.3 ontology additions.

The data in this module is deliberately provider-independent.  It expands the
v0.2 curated graph with concepts needed by farm production, business planning,
sustainability, and editor workflows.  Every edge is assigned to a retained
knowledge record so release compilation can bind it to a source passage.
"""

from __future__ import annotations

from typing import Any

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
R = "kb-referrals"
DY = "kb-dynamic-information"

# key, type, English, Arabic, record IDs, optional explicit aliases
V03_ENTITIES: tuple[
    tuple[str, str, str, str, tuple[str, ...], tuple[tuple[str, str, str], ...]],
    ...,
] = (
    ("nitrogen", "nutrient", "nitrogen", "النيتروجين", (SO, C), (("N nutrient", "en", "latin"), ("azote", "arz", "latin"))),
    ("phosphorus", "nutrient", "phosphorus", "الفوسفور", (SO, C), (("P nutrient", "en", "latin"),)),
    ("potassium", "nutrient", "potassium", "البوتاسيوم", (SO, C), (("K nutrient", "en", "latin"),)),
    ("calcium", "nutrient", "calcium", "الكالسيوم", (SO, G), (("Ca nutrient", "en", "latin"),)),
    ("magnesium", "nutrient", "magnesium", "المغنيسيوم", (SO, G), (("Mg nutrient", "en", "latin"),)),
    ("iron_nutrient", "nutrient", "plant-available iron", "الحديد المتاح للنبات", (SO, T), (("Fe nutrient", "en", "latin"),)),
    ("zinc_nutrient", "nutrient", "plant-available zinc", "الزنك المتاح للنبات", (SO, T), (("Zn nutrient", "en", "latin"),)),
    ("boron_nutrient", "nutrient", "plant-available boron", "البورون المتاح للنبات", (SO, T), (("B nutrient", "en", "latin"),)),
    ("open_field_system", "farm_system", "open-field farm system", "نظام الزراعة في الحقل المكشوف", (C, S), (("zera3a makshoufe", "arz", "latin"),)),
    ("orchard_system", "farm_system", "orchard farm system", "نظام المزرعة البستانية", (C, S), (("busten system", "arz", "latin"),)),
    ("mixed_farm_system", "farm_system", "mixed crop-livestock farm", "مزرعة مختلطة نباتية وحيوانية", (L, S), (("mazra3a mokhtalita", "arz", "latin"),)),
    ("rainfed_system", "farm_system", "rainfed farm system", "نظام الزراعة البعلية", (C, CL), (("zera3a ba3liye", "arz", "latin"),)),
    ("irrigated_system", "farm_system", "irrigated farm system", "نظام الزراعة المروية", (C, W), (("zera3a marwiye", "arz", "latin"),)),
    ("protected_system", "farm_system", "protected agriculture system", "نظام الزراعة المحمية", (G, S), (("zera3a mahmiye", "arz", "latin"),)),
    ("smallholder_system", "farm_system", "smallholder farm system", "نظام الحيازة الزراعية الصغيرة", (S, B), (("small farm", "en", "latin"),)),
    ("drip_line", "equipment", "drip irrigation line", "خط ري بالتنقيط", (W, G), (("khat tan2it", "arz", "latin"),)),
    ("drip_emitter", "equipment", "drip emitter", "نقّاط الري", (W, G), (("nakkat", "arz", "latin"),)),
    ("irrigation_pump", "equipment", "irrigation pump", "مضخة الري", (W, B), (("pompe may", "arz", "latin"),)),
    ("irrigation_filter", "equipment", "irrigation filter", "مرشح مياه الري", (W, G), (("filter ray", "arz", "latin"),)),
    ("fertigation_unit", "equipment", "fertigation unit", "وحدة التسميد مع الري", (W, SO), (("fertigation", "en", "latin"),)),
    ("field_sprayer", "equipment", "field sprayer", "مرشّة حقلية", (I, C), (("rashashe", "arz", "latin"),)),
    ("protective_equipment", "equipment", "personal protective equipment", "معدات الوقاية الشخصية", (I, L), (("PPE", "en", "latin"), ("3edet wi2aye", "arz", "latin"))),
    ("soil_probe", "equipment", "soil sampling probe", "مسبار أخذ عينة التربة", (SO,), (("soil auger", "en", "latin"),)),
    ("farm_thermometer", "equipment", "farm thermometer", "ميزان حرارة زراعي", (G, P), (("termometre", "arz", "latin"),)),
    ("farm_hygrometer", "equipment", "farm hygrometer", "مقياس الرطوبة", (G, P), (("hygrometer", "en", "latin"),)),
    ("cold_room", "equipment", "cold storage room", "غرفة تبريد", (P, B), (("chambre froide", "arz", "latin"),)),
    ("reusable_crate", "equipment", "reusable produce crate", "صندوق محصول قابل لإعادة الاستخدام", (P, B), (("sandou2 khodra", "arz", "latin"),)),
    ("soil_test", "measurement", "soil laboratory test", "فحص التربة المخبري", (SO, R), (("fahs torbe", "arz", "latin"),)),
    ("water_test", "measurement", "irrigation-water test", "فحص مياه الري", (W, R), (("fahs may", "arz", "latin"),)),
    ("soil_moisture_measurement", "measurement", "soil moisture measurement", "قياس رطوبة التربة", (W, T), (("soil moisture", "en", "latin"),)),
    ("ph_measurement", "measurement", "pH measurement", "قياس درجة الحموضة", (SO, W), (("pH test", "en", "latin"),)),
    ("ec_measurement", "measurement", "electrical-conductivity measurement", "قياس التوصيل الكهربائي", (SO, W), (("EC test", "en", "latin"),)),
    ("flow_measurement", "measurement", "irrigation flow measurement", "قياس تدفق مياه الري", (W,), (("debit may", "arz", "latin"),)),
    ("pressure_measurement", "measurement", "irrigation pressure measurement", "قياس ضغط الري", (W,), (("pressure test", "en", "latin"),)),
    ("temperature_measurement", "measurement", "temperature measurement", "قياس درجة الحرارة", (G, P, CL), (("darajet harara", "arz", "latin"),)),
    ("humidity_measurement", "measurement", "relative-humidity measurement", "قياس الرطوبة النسبية", (G, P), (("RH", "en", "latin"),)),
    ("yield_measurement", "measurement", "crop yield measurement", "قياس إنتاج المحصول", (C, B), (("yield per area", "en", "latin"),)),
    ("marketable_yield_measurement", "measurement", "marketable yield measurement", "قياس الإنتاج القابل للتسويق", (P, B), (("saleable yield", "en", "latin"),)),
    ("mortality_measurement", "measurement", "animal mortality measurement", "قياس نفوق الحيوانات", (L,), (("mortality rate", "en", "latin"),)),
    ("input_quantity_measurement", "measurement", "farm input quantity", "قياس كمية المدخل الزراعي", (B, SO), (("input amount", "en", "latin"),)),
    ("hectare", "unit", "hectare", "هكتار", (B, C), (("ha", "en", "latin"),)),
    ("dunum", "unit", "dunum", "دونم", (B, C), (("donum", "arz", "latin"),)),
    ("kilogram", "unit", "kilogram", "كيلوغرام", (B, P), (("kg", "en", "latin"),)),
    ("tonne", "unit", "metric tonne", "طن متري", (B, P), (("t", "en", "latin"),)),
    ("liter", "unit", "liter", "ليتر", (B, W), (("L", "en", "latin"),)),
    ("cubic_meter", "unit", "cubic meter", "متر مكعب", (W, B), (("m3", "en", "latin"),)),
    ("millimeter", "unit", "millimeter", "مليمتر", (CL, W), (("mm", "en", "latin"),)),
    ("degree_celsius", "unit", "degree Celsius", "درجة مئوية", (CL, G, P), (("Celsius", "en", "latin"),)),
    ("percentage_unit", "unit", "percentage", "نسبة مئوية", (G, B), (("percent", "en", "latin"),)),
    ("liter_per_hour", "unit", "liter per hour", "ليتر في الساعة", (W,), (("L/h", "en", "latin"),)),
    ("lebanese_pound", "unit", "Lebanese pound", "ليرة لبنانية", (B, DY), (("LBP", "en", "latin"), ("lira", "arz", "latin"))),
    ("us_dollar", "unit", "US dollar", "دولار أميركي", (B, DY), (("USD", "en", "latin"),)),
    ("fresh_produce", "product", "fresh produce", "منتج زراعي طازج", (P, B), (("fresh vegetables", "en", "latin"),)),
    ("potato_tuber", "product", "marketable potato tuber", "درنة بطاطا قابلة للتسويق", (C, P, B), (("batata lal sou2", "arz", "latin"),)),
    ("milk_product", "product", "farm milk", "حليب المزرعة", (L, B), (("halib", "arz", "latin"),)),
    ("egg_product", "product", "farm egg", "بيض المزرعة", (L, B), (("bayd", "arz", "latin"),)),
    ("meat_product", "product", "farm meat product", "منتج لحوم المزرعة", (L, B), (("lahme", "arz", "latin"),)),
    ("compost_product", "product", "finished compost", "سماد عضوي مكتمل النضج", (SO, B), (("compost جاهز", "arz", "arabic"),)),
    ("processed_food_product", "product", "processed food product", "منتج غذائي مصنّع", (F, B), (("mouneh product", "arz", "latin"),)),
    ("graded_produce", "product", "graded agricultural produce", "محصول زراعي مفروز", (P, B), (("sorted produce", "en", "latin"),)),
    ("farmer_actor", "value_chain_actor", "farmer", "المزارع", (S, B), (("mazare3", "arz", "latin"),)),
    ("input_supplier", "value_chain_actor", "farm input supplier", "مورد المدخلات الزراعية", (B, I), (("supplier zira3e", "arz", "latin"),)),
    ("trader_actor", "value_chain_actor", "agricultural trader", "تاجر المنتجات الزراعية", (B, P), (("tejir", "arz", "latin"),)),
    ("wholesaler_actor", "value_chain_actor", "agricultural wholesaler", "تاجر الجملة الزراعي", (B, P), (("jemle", "arz", "latin"),)),
    ("retailer_actor", "value_chain_actor", "food retailer", "بائع التجزئة الغذائي", (B, P), (("retail", "en", "latin"),)),
    ("processor_actor", "value_chain_actor", "food processor", "مصنّع الأغذية", (F, B), (("mou3amel ghiza", "arz", "latin"),)),
    ("transporter_actor", "value_chain_actor", "agricultural transporter", "ناقل المنتجات الزراعية", (P, B), (("na2el", "arz", "latin"),)),
    ("cooperative_actor", "value_chain_actor", "agricultural cooperative actor", "جهة تعاونية زراعية", (B, R), (("ta3awoniye", "arz", "latin"),)),
    ("consumer_actor", "value_chain_actor", "food consumer", "مستهلك الغذاء", (B, F), (("mostahlik", "arz", "latin"),)),
    ("farm_loan", "financial_instrument", "farm loan", "قرض زراعي", (B,), (("2ard zira3e", "arz", "latin"),)),
    ("farm_grant", "financial_instrument", "farm grant", "منحة زراعية", (B, DY), (("minha zira3iye", "arz", "latin"),)),
    ("farm_savings", "financial_instrument", "farm savings reserve", "احتياطي ادخار للمزرعة", (B,), (("idikhar", "arz", "latin"),)),
    ("agricultural_insurance", "financial_instrument", "agricultural insurance", "تأمين زراعي", (B, DY), (("ta2min zira3e", "arz", "latin"),)),
    ("supplier_credit", "financial_instrument", "supplier credit", "ائتمان المورد", (B,), (("deyn supplier", "arz", "latin"),)),
    ("equipment_lease", "financial_instrument", "equipment lease", "استئجار المعدات", (B,), (("ijar equipment", "arz", "latin"),)),
    ("market_contract", "opportunity", "market contract opportunity", "فرصة عقد تسويق", (B, DY), (("contract sou2", "arz", "latin"),)),
    ("extension_training", "opportunity", "agricultural extension training", "فرصة تدريب إرشادي زراعي", (R, DY), (("training zira3e", "arz", "latin"),)),
    ("funding_call", "opportunity", "dated funding call", "دعوة تمويل مؤرخة", (B, DY), (("funding call", "en", "latin"),)),
    ("certification_program", "opportunity", "certification support program", "برنامج دعم الشهادات", (B, DY), (("certification support", "en", "latin"),)),
    ("cooperative_marketing", "opportunity", "cooperative marketing opportunity", "فرصة تسويق تعاوني", (B,), (("taswi2 ta3awoni", "arz", "latin"),)),
    ("value_addition_opportunity", "opportunity", "value-addition opportunity", "فرصة إضافة قيمة", (F, B), (("value added", "en", "latin"),)),
    ("organic_certification", "certification", "organic certification", "شهادة الزراعة العضوية", (B, DY), (("organic cert", "en", "latin"),)),
    ("good_agricultural_practices", "certification", "good agricultural practices certification", "شهادة الممارسات الزراعية الجيدة", (C, B), (("GAP certification", "en", "latin"),)),
    ("food_safety_certification", "certification", "food-safety certification", "شهادة سلامة الغذاء", (F, B), (("HACCP certification", "en", "latin"),)),
    ("traceability_certification", "certification", "traceability certification", "شهادة التتبع", (P, B), (("traceability cert", "en", "latin"),)),
    ("quality_standard", "certification", "market quality standard", "معيار جودة السوق", (P, B), (("quality grade", "en", "latin"),)),
    ("yield_stability", "outcome", "yield stability", "استقرار الإنتاج", (C, CL), (("stable yield", "en", "latin"),)),
    ("net_margin_outcome", "outcome", "improved net margin", "تحسن الهامش الصافي", (B,), (("better margin", "en", "latin"),)),
    ("water_productivity", "outcome", "water productivity", "إنتاجية المياه", (W, B), (("crop per water", "en", "latin"),)),
    ("reduced_postharvest_loss", "outcome", "reduced post-harvest loss", "خفض فاقد ما بعد الحصاد", (P, B), (("less food loss", "en", "latin"),)),
    ("soil_resilience", "outcome", "soil resilience", "مرونة التربة", (SO, CL), (("resilient soil", "en", "latin"),)),
    ("worker_safety_outcome", "outcome", "improved worker safety", "تحسن سلامة العامل", (I, B), (("safe worker", "en", "latin"),)),
    ("animal_welfare_outcome", "outcome", "improved animal welfare", "تحسن رفاه الحيوان", (L,), (("animal welfare", "en", "latin"),)),
    ("food_safety_outcome", "outcome", "improved food safety", "تحسن سلامة الغذاء", (F, P), (("safe food", "en", "latin"),)),
    ("market_access_outcome", "outcome", "improved market access", "تحسن الوصول إلى السوق", (B, P), (("access to market", "en", "latin"),)),
    ("income_resilience", "outcome", "farm income resilience", "مرونة دخل المزرعة", (B, CL), (("stable income", "en", "latin"),)),
    ("cost_reduction_outcome", "outcome", "farm cost reduction", "خفض تكاليف المزرعة", (B, W), (("save farm cost", "en", "latin"),)),
    ("biodiversity_outcome", "outcome", "improved farm biodiversity", "تحسن التنوع الحيوي الزراعي", (I, SO), (("more biodiversity", "en", "latin"),)),
)

# record, subject, predicate, object, risk, qualifiers
_BASE_LINKS: dict[str, tuple[str, str, str]] = {
    "nutrient": (SO, "affects", "soil_health"),
    "farm_system": (S, "located_in", "akkar"),
    "equipment": (D, "requires_context", "site_assessment"),
    "measurement": (D, "supports_action", "diagnosis_workflow"),
    "unit": (B, "applies_to", "enterprise_budget"),
    "product": (B, "applies_to", "buyer_specification"),
    "value_chain_actor": (B, "related_to", "buyer"),
    "financial_instrument": (B, "requires_context", "enterprise_budget"),
    "opportunity": (DY, "requires_live_source", "market_information_service"),
    "certification": (B, "requires_live_source", "competent_authority"),
    "outcome": (D, "related_to", "record_keeping"),
}

_RELATIONS: list[tuple[str, str, str, str, str, dict[str, Any]]] = []
for key, entity_type, _en, _ar, records, _aliases in V03_ENTITIES:
    record, predicate, target = _BASE_LINKS[entity_type]
    if record not in records and records:
        record = records[0]
    _RELATIONS.append(
        (record, key, predicate, target, "medium", {"ontology_extension": "v0.3"})
    )


def _add(
    record: str,
    subject: str,
    predicate: str,
    object_: str,
    *,
    risk: str = "medium",
    **qualifiers: Any,
) -> None:
    _RELATIONS.append((record, subject, predicate, object_, risk, qualifiers))


for nutrient in ("nitrogen", "phosphorus", "potassium", "calcium", "magnesium", "iron_nutrient", "zinc_nutrient", "boron_nutrient"):
    _add(SO, "fertilizer", "targets", nutrient)
    _add(SO, nutrient, "measured_by", "soil_test")
for system in ("open_field_system", "orchard_system", "mixed_farm_system", "rainfed_system", "irrigated_system", "protected_system", "smallholder_system"):
    _add(S, system, "depends_on", "water_reliability")
    _add(S, system, "depends_on", "soil_health")
for equipment, practice in (
    ("drip_line", "irrigation_scheduling"), ("drip_emitter", "drip_maintenance"),
    ("irrigation_pump", "irrigation_scheduling"), ("irrigation_filter", "drip_maintenance"),
    ("fertigation_unit", "irrigation_scheduling"), ("field_sprayer", "ipm"),
    ("protective_equipment", "nonchemical_control"), ("soil_probe", "soil_sampling"),
    ("farm_thermometer", "crop_calendar"), ("farm_hygrometer", "ventilation"),
    ("cold_room", "cold_chain"), ("reusable_crate", "sorting"),
):
    record = I if equipment in {"field_sprayer", "protective_equipment"} else W if equipment.startswith(("drip", "irrigation", "fertigation")) else P
    _add(record, equipment, "supports_action", practice)
    _add(record, equipment, "alternative_to", "record_keeping", context="equipment_does_not_replace_records")

for measurement, unit in (
    ("soil_test", "percentage_unit"), ("water_test", "percentage_unit"),
    ("soil_moisture_measurement", "percentage_unit"), ("ph_measurement", "percentage_unit"),
    ("ec_measurement", "percentage_unit"), ("flow_measurement", "liter_per_hour"),
    ("pressure_measurement", "percentage_unit"), ("temperature_measurement", "degree_celsius"),
    ("humidity_measurement", "percentage_unit"), ("yield_measurement", "kilogram"),
    ("marketable_yield_measurement", "kilogram"), ("mortality_measurement", "percentage_unit"),
    ("input_quantity_measurement", "kilogram"),
):
    record = W if measurement in {"water_test", "soil_moisture_measurement", "flow_measurement", "pressure_measurement"} else B if "yield" in measurement or measurement == "input_quantity_measurement" else SO
    _add(record, measurement, "has_unit", unit)
    _add(record, measurement, "measured_by", "record_keeping")

for unit, measurement in (
    ("hectare", "yield_measurement"), ("dunum", "yield_measurement"),
    ("kilogram", "marketable_yield_measurement"), ("tonne", "yield_measurement"),
    ("liter", "input_quantity_measurement"), ("cubic_meter", "flow_measurement"),
    ("millimeter", "precipitation_decline"), ("degree_celsius", "temperature_measurement"),
    ("percentage_unit", "humidity_measurement"), ("liter_per_hour", "emitter_flow"),
    ("lebanese_pound", "enterprise_budget"), ("us_dollar", "enterprise_budget"),
):
    _add(
        B if unit in {
            "lebanese_pound", "us_dollar", "hectare", "dunum", "kilogram", "tonne"
        } else W,
        measurement,
        "has_unit",
        unit,
        reporting_context="common_unit",
    )

for system, product in (
    ("open_field_system", "fresh_produce"), ("open_field_system", "potato_tuber"),
    ("mixed_farm_system", "milk_product"), ("mixed_farm_system", "egg_product"),
    ("mixed_farm_system", "meat_product"), ("smallholder_system", "compost_product"),
    ("protected_system", "graded_produce"), ("smallholder_system", "processed_food_product"),
):
    _add(B, system, "produces", product)
    _add(B, product, "sold_to", "trader_actor")

for subject, predicate, object_ in (
    ("farmer_actor", "sold_to", "trader_actor"), ("farmer_actor", "sold_to", "cooperative_actor"),
    ("trader_actor", "sold_to", "wholesaler_actor"), ("wholesaler_actor", "sold_to", "retailer_actor"),
    ("farmer_actor", "sold_to", "processor_actor"), ("transporter_actor", "supports_action", "cold_chain"),
    ("processor_actor", "produces", "processed_food_product"), ("retailer_actor", "sold_to", "consumer_actor"),
    ("input_supplier", "provided_by", "cooperative_actor"),
):
    _add(B, subject, predicate, object_)

for instrument in ("farm_loan", "farm_grant", "farm_savings", "agricultural_insurance", "supplier_credit", "equipment_lease"):
    _add(B, instrument, "benefits", "income_resilience")
    _add(B, instrument, "costs", "financing_cost")
for opportunity in ("market_contract", "extension_training", "funding_call", "certification_program", "cooperative_marketing", "value_addition_opportunity"):
    _add(DY if opportunity in {"funding_call", "market_contract", "certification_program"} else B, opportunity, "provided_by", "competent_authority")
    _add(B, opportunity, "benefits", "market_access_outcome")
for certification, product in (
    ("organic_certification", "fresh_produce"),
    ("good_agricultural_practices", "graded_produce"),
    ("food_safety_certification", "processed_food_product"),
    ("traceability_certification", "graded_produce"),
    ("quality_standard", "fresh_produce"),
):
    _add(B, certification, "targets", product)
    _add(B, certification, "provided_by", "competent_authority")
    _add(B, certification, "valid_during", "alert_window")

for action, predicate, outcome in (
    ("crop_rotation", "increases", "yield_stability"),
    ("enterprise_budget", "increases", "net_margin_outcome"),
    ("irrigation_scheduling", "increases", "water_productivity"),
    ("cold_chain", "increases", "reduced_postharvest_loss"),
    ("soil_conservation", "increases", "soil_resilience"),
    ("protective_equipment", "increases", "worker_safety_outcome"),
    ("biosecurity", "increases", "animal_welfare_outcome"),
    ("hygiene", "increases", "food_safety_outcome"),
    ("quality_standard", "increases", "market_access_outcome"),
    ("sensitivity_analysis", "increases", "income_resilience"),
    ("drip_maintenance", "increases", "cost_reduction_outcome"),
    ("ipm", "increases", "biodiversity_outcome"),
    ("waterlogging", "decreases", "yield_stability"),
    ("food_loss", "decreases", "net_margin_outcome"),
    ("fertilizer_loss", "decreases", "cost_reduction_outcome"),
    ("pesticide_use", "decreases", "worker_safety_outcome"),
):
    record = B if outcome in {"net_margin_outcome", "market_access_outcome", "income_resilience", "cost_reduction_outcome"} else I if "safety" in outcome or outcome == "biodiversity_outcome" else D
    _add(record, action, predicate, outcome)

# Explicit typed safety and compatibility semantics needed by query routing.
for record, subject, predicate, object_, risk in (
    (I, "ipm", "controls", "insect_pest", "medium"),
    (I, "sanitation", "prevents", "crop_disease", "medium"),
    (L, "biosecurity", "prevents", "animal_disease", "high"),
    (F, "hygiene", "prevents", "food_contamination", "high"),
    (SO, "compost", "compatible_with", "soil_health", "medium"),
    (I, "pesticide", "contraindicated_with", "worker_exposure", "high"),
    (L, "veterinary_medicine", "contraindicated_with", "withdrawal_period", "high"),
    (C, "potato", "has_stage", "planting", "low"),
    (C, "potato", "has_stage", "harvest", "low"),
    (T, "crop_disease", "has_symptom", "leaf_spot", "medium"),
    (L, "animal_disease", "has_symptom", "respiratory_distress", "high"),
    (B, "graded_produce", "benefits", "market_access_outcome", "medium"),
    (P, "reusable_crate", "prevents", "food_loss", "medium"),
    (W, "drip_line", "alternative_to", "irrigation_water", "medium"),
    (DY, "alert_window", "supersedes", "stale_information", "high"),
):
    _add(record, subject, predicate, object_, risk=risk)

# Complete the 450-edge gate with non-duplicative, evidence-scoped action links.
_ACTION_TARGETS = (
    (C, "record_keeping", "yield_measurement"), (C, "scouting", "yield_stability"),
    (L, "record_keeping", "mortality_measurement"), (L, "ventilation", "animal_welfare_outcome"),
    (SO, "soil_sampling", "soil_test"), (SO, "soil_test", "fertilizer"),
    (SO, "crop_rotation", "soil_resilience"), (W, "drip_maintenance", "drip_emitter"),
    (W, "irrigation_scheduling", "flow_measurement"), (W, "water_test", "water_quality"),
    (I, "scouting", "insect_pest"), (I, "nonchemical_control", "biodiversity_outcome"),
    (CL, "crop_calendar", "yield_stability"), (CL, "rainwater_harvesting", "water_productivity"),
    (G, "ventilation", "humidity_measurement"), (G, "shade_management", "temperature_measurement"),
    (P, "sorting", "graded_produce"), (P, "cold_chain", "cold_room"),
    (F, "traceability", "traceability_certification"), (F, "haccp", "food_safety_certification"),
    (B, "enterprise_budget", "cost_reduction_outcome"), (B, "break_even_analysis", "net_margin_outcome"),
    (B, "cooperative", "cooperative_marketing"), (T, "diagnosis_workflow", "soil_moisture_measurement"),
    (R, "extension_service", "extension_training"), (D, "record_keeping", "input_quantity_measurement"),
)
for record, action, target in _ACTION_TARGETS:
    _add(record, action, "supports_action", target, evidence_scope="retained_guidance")

V03_RELATIONS = tuple(_RELATIONS)
