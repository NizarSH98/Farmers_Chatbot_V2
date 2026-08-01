# Controlled Stakeholder Tracker Schema

The contractual 40–50 stakeholder targets require a controlled project record. Do not store names, phone numbers, or raw external-platform identifiers in this public repository.

Recommended fields:

| Field | Purpose |
|---|---|
| stakeholder_id | Project pseudonym, unique and stable |
| consent_status/date/version | Evidence of informed participation |
| stakeholder_category | Farmer, cooperative, extension, supplier, processor, institution, other |
| geography | Approved locality granularity |
| production_system | Crop, greenhouse, orchard, livestock, dairy, herbs, mixed, other |
| plain/upland/terraced | Akkar context representation |
| language preference | Arabic, English, other |
| accessibility/connectivity needs | Pilot design, collected minimally |
| enrolled_date | A.1.1.3 evidence |
| tried_model_date/channel | A.1.2.1 evidence |
| session_ids | A.1.2.2 participation evidence |
| active/withdrawn | Consent and denominator control |
| notes | Non-sensitive operational notes only |

Internal reporting should show de-duplicated counts and representation categories. Do not infer enrollment from a website visit or count multiple devices as multiple stakeholders.

