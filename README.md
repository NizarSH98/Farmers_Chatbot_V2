# RAISE Akkar Farmer Assistant

Arabic-first, bilingual agricultural decision support for farmers and agri-food stakeholders in Akkar and rural Lebanon.

The project combines:

- a source-traceable Akkar and ESDU knowledge base;
- an authenticated Streamlit workspace with persistent chats and projects;
- Google OIDC, Supabase Postgres/private storage, and local SQLite fallbacks;
- Quick, Standard, Deep, and Source-only answer modes;
- risk-based internal retrieval, trusted live search, and bounded tool calling;
- a local MCP server;
- a signed Meta WhatsApp test-number webhook service;
- optional local Whisper speech-to-text;
- consent-aware feedback and performance evidence;
- direct traceability to `RAISE_Logframe_final.xlsx`.

> **Pilot status:** The software and strengthened knowledge base are under internal review. The knowledge base is not an official ESDU publication until ESDU approves its content, Arabic field language, title, and publication status.

## Why this exists

The goal is to make useful agricultural knowledge easier to access for Lebanese farmers, starting with Akkar. A strong answer must be more than fluent: it should fit the farmer's locality and production system, expose its sources and limitations, support Arabic use, learn from field feedback, and avoid pretending that fast-changing prices, weather, alerts, or regulations are static facts.

## Current capabilities

- 21 bilingual Akkar-focused knowledge items with stable IDs and institutional sources.
- Hybrid word/character retrieval in English and Arabic.
- Source cards showing knowledge ID, evidence class, review status, risk class, and source links.
- Current mode profiles:
  - **Quick:** low-cost, short response.
  - **Standard:** default balance.
  - **Deep:** more retrieval, reasoning effort, and tool rounds.
  - **Source only:** no general model knowledge.
- Persistent, ownership-checked conversations, projects, uploads, artifacts,
  feedback, quotas, and 30-day retention.
- Safe internal tools include:
  - `search_knowledge`
  - `search_project_knowledge`
  - `search_trusted_sources`
  - `get_verified_source`
  - `calculate_enterprise_budget`
  - `convert_agricultural_units`
  - deterministic action plan, checklist, crop calendar, and referral artifacts
  - `get_source`
  - `get_logframe_status`
  - `record_feedback` with explicit consent
- Local-stdio MCP server exposing bounded knowledge, source, conversion, artifact,
  logframe, and feedback tools without shell or arbitrary URL access.
- FastAPI WhatsApp pilot adapter with signature/phone-ID verification,
  deduplication, HMAC identities, commands, and shared quotas.
- Online Edge TTS with explicit disclosure.
- Optional local Whisper input when the voice dependencies are installed.

## Knowledge structure

The editable knowledge source is:

```text
knowledge_base/
├── guide.json       # bilingual reviewed-item candidates
├── sources.json     # source register
└── README.md        # review rules
```

`scripts/build_guide.py` renders the structured source into
`knowledge_base/RAISE_Akkar_Agricultural_Guide.md` for internal review.

The legacy `Agricultural Guide for Lebanon.pdf` remains for migration and comparison. The application now retrieves from the structured knowledge base so claims can be reviewed, versioned, and retired individually.

The initial expansion covers:

- Akkar plain versus upland/terraced contexts;
- dated Ministry of Agriculture production signals;
- potato, greenhouse, orchard, water, soil, livestock, post-harvest, and market decision checklists;
- ESDU's participatory-development and living-lab approach;
- ESDU work on livestock resilience, sprouting units, composting, rainwater harvesting, zaatar/coriander, dairy, rural women, community-market links, and legumes;
- safety boundaries and expert escalation;
- dynamic information that must come from a timestamped tool.

All knowledge items are currently `draft`. Technical and field-language approval is still required.

## Local setup

Use Python 3.12:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
streamlit run rag_chatbot.py
```

Add a deployment-specific OpenRouter key to `.env` if connected generation is required:

```env
OPENROUTER_API_KEY=your_key_here
```

Without a key, the app remains usable as a retrieval interface and clearly labels that fallback.

## Voice options

Voice boundaries are explicit:

- Browser recording plus Whisper can run locally after installing `requirements-voice.txt`.
- Edge TTS is an **online** service and sends answer text to Microsoft to generate audio.
- The app does not claim that Edge TTS is offline.

Install optional local transcription:

```powershell
python -m pip install -r requirements-voice.txt
```

The first Whisper use downloads the selected model. Configure `WHISPER_MODEL` in `.env`.

## MCP

The official MCP Python SDK is constrained to the current stable v1 line:

```powershell
python mcp_server.py
```

The default transport is `stdio`. Available tools:

- `search_knowledge`
- `get_source`
- `get_verified_source`
- `search_project_knowledge`
- `search_trusted_sources`
- `convert_agricultural_units`
- `generate_farm_action_plan`
- `generate_inspection_checklist`
- `generate_crop_calendar`
- `generate_expert_referral_brief`
- `get_logframe_status`
- `record_feedback`

The server deliberately does not expose shell execution, arbitrary filesystem access, unrestricted URL fetching, or generic database queries. Do not publish an unauthenticated HTTP transport.

## Tests and logframe retrieval gate

Install development dependencies and run:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
python scripts/evaluate_retrieval.py
```

The retrieval evaluator writes a generated report under `reports/generated/`. The included 30-question bilingual set is a candidate benchmark. Its results do not become contractual evidence until the project team approves the questions and relevance labels.

## Logframe and governance documents

- `docs/LOGFRAME_TRACEABILITY.md`
- `docs/GOVERNANCE_AND_VALIDATION.md`
- `docs/INTERNAL_REVIEW.md`
- `docs/ARCHITECTURE.md`
- `docs/FIELD_SESSION_TEMPLATE.md`
- `docs/ESDU_INTERNAL_KNOWLEDGE_INTAKE.md`
- `docs/STAKEHOLDER_TRACKER_SCHEMA.md`
- `docs/RRO.md`
- `docs/DEPLOYMENT.md`
- `docs/PILOT_DEPLOYMENT_RUNBOOK.md`
- `docs/PILOT_READINESS_2026-07-29.md`

Software metrics and contractual achievement are reported separately. Code cannot substitute for 40–50 stakeholder records, four feedback sessions, or approval of the final RRO.

## Deployment

The internal pilot target is Streamlit Community Cloud with Google OIDC and
Supabase, followed by the optional Render/Meta test-number service only after web
gates pass. Use `docs/PILOT_DEPLOYMENT_RUNBOOK.md` for owner setup, managed secrets,
privacy/load gates, freeze, rollback, and WhatsApp verification. The contractual
workbook is local evidence and is deliberately excluded from deployed runtime source.

## Safety and privacy

The assistant is decision support, not a substitute for an agronomist, veterinarian, laboratory, engineer, food-safety professional, or competent authority. It must not invent pesticide/veterinary instructions, current alerts, market prices, or regulations.

Connected generation sends the farmer's text, recent conversation context, and retrieved passages to the configured model provider. Online TTS sends answer text to its provider. Do not collect names, phone numbers, precise personal location, or other personal data unless an approved pilot process requires it and obtains informed consent.

## License

The software is available under the MIT License. Knowledge-source copyrights and the right to use ESDU/AUB names or branding remain separate and must be reviewed before publication.
