# RAISE Akkar Farmer Assistant

Arabic-first, bilingual agricultural decision support for farmers and agri-food stakeholders in Akkar and rural Lebanon.

The project combines:

- a source-traceable Akkar and ESDU knowledge base;
- a modern Arabic-first Next.js workspace with persistent chats and projects;
- Supabase authentication, PostgreSQL/pgvector, and private storage;
- Quick, Standard, Deep, and Source-only answer modes;
- risk-based internal retrieval, authorized direct live-source connectors, and
  bounded tool calling;
- a local MCP server;
- a mounted but disabled Meta WhatsApp router for post-soak activation;
- optional local Whisper speech-to-text;
- consent-aware feedback and performance evidence;
- direct traceability to `RAISE_Logframe_final.xlsx`.

> **Pilot status:** The software and strengthened knowledge base are under internal review. The knowledge base is not an official ESDU publication until ESDU approves its content, Arabic field language, title, and publication status.

## Why this exists

The goal is to make useful agricultural knowledge easier to access for Lebanese farmers, starting with Akkar. A strong answer must be more than fluent: it should fit the farmer's locality and production system, expose its sources and limitations, support Arabic use, learn from field feedback, and avoid pretending that fast-changing prices, weather, alerts, or regulations are static facts.

## Current architecture and capabilities

- One canonical asynchronous assistant engine and provider client shared by web,
  frozen Streamlit compatibility, mounted-but-disabled WhatsApp, and MCP.
- Atomic, idempotent turn reservation/finalization with provider usage, cost,
  latency, tool, retrieval, citation, and terminal-state records.
- Versioned PostgreSQL GraphRAG schema for releases, passages, bilingual aliases,
  claims, evidence-backed relations, project chunks, and atomic activation/
  rollback.
- A provider-independent bilingual ontology with 162 entities across all 21
  domain types, 352 aliases, and 183 passage-evidenced relations. Graph lookup
  is word-boundary safe, bidirectional, cycle-safe, and bounded to two hops.
- Lexical plus graph retrieval remains active while vector cutover is blocked on
  the hidden bilingual embedding benchmark.
- The DOCX-derived canonical and Arabic Markdown drafts are generated locally
  and validated; all 21 legacy JSON items have one merge owner or an explicit
  exclusion so JSON and Markdown cannot be double-indexed.
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
- Disabled FastAPI WhatsApp router with signature/phone-ID
  verification, HMAC identities, coordinator-owned quotas/idempotency, and
  persisted-turn delivery retry.
- Online Edge TTS with explicit disclosure.
- Optional local Whisper input when the voice dependencies are installed.

## Knowledge structure

The editable knowledge source is:

```text
knowledge_base/
├── agrifood_knowledge_draft_v0.2.md     # canonical bilingual GraphRAG draft
├── agrifood_knowledge_draft_v0.2_ar.md  # Arabic review companion
├── guide.json                           # legacy bilingual candidates
├── sources.json                         # source register
└── README.md                            # review and regeneration rules
```

`scripts/convert_agrifood_docx.py` deterministically rebuilds both v0.2
Markdown files without an external translation service. The legacy
`scripts/build_guide.py` path remains available only for comparison during the
one-release migration.

The legacy `Agricultural Guide for Lebanon.pdf` remains for migration and comparison. The application now retrieves from the structured knowledge base so claims can be reviewed, versioned, and retired individually.

The draft expansion covers:

- Akkar plain versus upland/terraced contexts;
- dated Ministry of Agriculture production signals;
- potato, greenhouse, orchard, water, soil, livestock, post-harvest, and market decision checklists;
- crop/livestock, soil/water, IPM, greenhouse, post-harvest, food-safety,
  business, troubleshooting, referral, and dynamic-evidence decision paths;
- safety boundaries and expert escalation;
- dynamic information that must come from a timestamped tool.

All knowledge items are currently `draft`. Technical and field-language approval is still required.

## Local setup

Use Python 3.12:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
alembic upgrade head
uvicorn farmers_chatbot.web_api:app --reload --port 8000
```

Run the canonical frontend in a second terminal with Node.js 22.12 or newer:

```powershell
Set-Location apps/web
Copy-Item .env.example .env.local
npm ci
npm run dev
```

Add a deployment-specific OpenRouter key to `.env` if connected generation is required:

```env
OPENROUTER_API_KEY=your_key_here
```

The local development profile may be used for offline retrieval tests. Pilot and
production startup fail closed when connected database, storage, migration,
origin, provider, consent, retention, or model settings are invalid.

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
- `docs/UI_UX.md`
- `docs/FIELD_SESSION_TEMPLATE.md`
- `docs/ESDU_INTERNAL_KNOWLEDGE_INTAKE.md`
- `docs/STAKEHOLDER_TRACKER_SCHEMA.md`
- `docs/RRO.md`
- `docs/DEPLOYMENT.md`
- `docs/PILOT_DEPLOYMENT_RUNBOOK.md`
- `docs/PILOT_PROVIDER_SETUP_CHECKLIST.md`
- `docs/DATA_PORTABILITY.md`
- `docs/POLICY_APPROVAL_CHECKLIST.md`
- `docs/PILOT_READINESS_2026-07-29.md`
- `docs/PILOT_READINESS_2026-08-01.md`
- `docs/SOURCE_DOCUMENT_INTAKE.md`

Software metrics and contractual achievement are reported separately. Code cannot substitute for 40–50 stakeholder records, four feedback sessions, or approval of the final RRO.

## Deployment

The locked pilot topology is Next.js on Vercel, one FastAPI backend on Render,
and Supabase-managed PostgreSQL/auth/private storage. Streamlit is a frozen
one-release compatibility client and must not receive a new hosted deployment.
WhatsApp remains disabled until the canonical web app completes a clean
seven-day soak; its thin router is already mounted in the same FastAPI
deployment. Use `docs/CANONICAL_PILOT_RUNBOOK.md` for backup/restore, live
migration, release gates, soak, rollback, and canary requirements.

## Safety and privacy

The assistant is decision support, not a substitute for an agronomist, veterinarian, laboratory, engineer, food-safety professional, or competent authority. It must not invent pesticide/veterinary instructions, current alerts, market prices, or regulations.

Connected generation sends the farmer's text, recent conversation context, and retrieved passages to the configured model provider. Online TTS sends answer text to its provider. Do not collect names, phone numbers, precise personal location, or other personal data unless an approved pilot process requires it and obtains informed consent.

The web and WhatsApp channels enforce a versioned lifecycle-wide user agreement
and privacy policy before normal use. Both documents are also readable before web
sign-in.
Users can export active workspace data and delete their account/private content.
The agreement is an operational template and still requires institutional
privacy/legal approval before public or production use.

## License

The software is available under the MIT License. Knowledge-source copyrights and the right to use ESDU/AUB names or branding remain separate and must be reviewed before publication.
