# RAISE Akkar Farmer Assistant

RAISE is an Arabic-first, bilingual agricultural decision-support product for
farmers and agri-food stakeholders in Akkar and rural Lebanon. It combines a
modern Next.js workspace, one FastAPI assistant engine, evidence-backed local
knowledge, farm/business tools, projects and documents, and guarded live-source
connectors. It is more than a general chatbot: answers are routed through local
retrieval, graph context, tools, citations, risk rules, and verification.

> **Pilot status:** The v0.3 corpus is project-owner approved for authenticated
> pilot use. Expert/editor verification remains pending metadata and does not
> create a recurring warning for farmers. Safety restrictions still apply. The
> corpus is not an official ESDU publication, and no frontier-model superiority
> claim has been established yet.

## Current architecture

- Next.js is the only user interface. Streamlit has been removed. WhatsApp is
  a disabled thin FastAPI router, retained for its Meta protocol handling.
- `TurnCoordinator`, `AssistantEngine`, `ProviderClient`, and `ToolExecutor`
  provide one idempotent orchestration path with exactly one terminal turn.
- PostgreSQL is the only persistence backend and is authoritative for immutable releases, evidence, claims,
  relations, review state, projects, quotas, and activation history.
- Qdrant 1.17.1 is a rebuildable exact-release projection with dense E5 vectors,
  BM25 sparse vectors, multilingual text fields, flat lineage payloads, scalar
  quantization, and atomic aliases.
- Retrieval routes simple questions through vector/BM25 fusion, normal guidance
  through contextual hybrid retrieval, and Deep questions through lazy two-hop
  graph expansion, Personalized PageRank, and path pruning. PostgreSQL
  lexical/graph retrieval is the Qdrant-outage fallback.
- OpenRouter is used only for connected answer generation/comparisons. DOCX
  extraction, corpus conversion, embeddings, graph construction, translation,
  and golden-set construction run locally.

The active local pilot release is
`release_4debc9a9de849675835bb255`: 36 sources, 36 documents, 192 chunks, 192
claims, 260 entities, 649 bilingual/local aliases, 494 passage-backed relations,
and 686 evidence links. Its two Qdrant collections contain 384 evidence points
and 260 entity points.

## Knowledge and ontology

Canonical source files:

```text
knowledge_base/
|-- agrifood_knowledge_v0.3.en.md
|-- agrifood_knowledge_v0.3.ar.md
|-- agrifood_knowledge_v0.3.disposition.json
|-- legacy/                            # build inputs only, never served
|   |-- guide.json
|   `-- sources.json
`-- README.md
```

The original `ESDU_Agrifood_Knowledge_Base_v0.1.docx` remains unchanged and
local/uncommitted. Its required SHA-256 is
`3C0BAF8145E4A2E287BA5783F8AB26A7CEAE1C5340322C1EE065887CC9B75B0E`.
All 32 source chapters have a recorded disposition. English and Arabic share
the same stable knowledge, claim, relation, entity, and source IDs.

The v0.3 schema defines 31 agricultural/business entity types and 34 relation
types. Every persisted edge requires a supporting passage and typed geography,
conditions, polarity, validity, risk, review state, and confidence.

## One-command local release candidate

Prerequisites: Docker Desktop, Python 3.12, Node 22.12+ (the container uses Node
24), and enough disk/RAM. Ollama is optional for future uncached graph ambiguity
resolution; the current checked release does not require OpenRouter to rebuild
its deterministic material.

```powershell
Copy-Item .env.example .env
.\scripts\raise.ps1 start -Rebuild
.\scripts\raise.ps1 status
.\scripts\raise.ps1 build-graph
.\scripts\raise.ps1 smoke
.\scripts\raise.ps1 evaluate
.\scripts\raise.ps1 ablate
.\scripts\raise.ps1 graph-profile
.\scripts\raise.ps1 export
```

PostgreSQL is required; there is no SQLite fallback and no bare-uvicorn
mode. Data commands run inside the API container, so they need no host
Python. If the published database port stops accepting connections on
Windows, `docker compose restart postgres` repairs the Docker port proxy.

Services bind only to localhost: web `3000`, API `8000`, PostgreSQL `55432`,
and Qdrant `6433`. `export` writes a portable PostgreSQL dump, both Qdrant
snapshots, and checksummed manifests under ignored `backups/`.

Restore a selected bundle into the local stack:

```powershell
.\scripts\raise.ps1 restore -Path .\backups\raise-YYYYMMDD-HHMMSS
```

Restore replaces the selected local databases, verifies snapshot hashes,
repairs Qdrant aliases, and runs the smoke test.

## Development gates

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q -m "not arabic"
python -m pytest -q -m arabic
python -m ruff check farmers_chatbot scripts tests mcp_server.py
pip-audit -r requirements.txt
npm ci --prefix apps/web
npm run typecheck --prefix apps/web
npm run test --prefix apps/web
npm run lint --prefix apps/web
npm run build --prefix apps/web
npm audit --prefix apps/web --omit=dev
```

The evaluation candidate contains 400 source-anchored cases: 240 tracked
development cases and 160 ignored/checksum-sealed acceptance cases. It covers
ten domains and English, MSA, Lebanese Arabic, Arabizi, and code-switching.
Local reports currently measure retrieval; answer-level safety/citation and
matched GPT/Claude comparisons require authorized provider access and human
review. The cases are never indexed as knowledge.

`scripts/run_ablations.py` runs the ablation ladder and reports what graph
expansion adds over contextual hybrid retrieval. On the current release that
delta is ~0 because dense and sparse fusion alone already reach 99.4%
recall@10, so the set has no headroom to demonstrate it either way. A
shuffled-path negative control confirms graph path retrieval is real
(0.891 -> 0.018). `scripts/profile_graph.py` describes the graph structurally.

## Interfaces and capabilities

- REST/SSE `/v1/turns` remains backward compatible and supports idempotency,
  persisted recovery, typed monotonic events, and exactly one terminal result.
- Projects, private documents, artifacts, workspace export, feedback, consent,
  data deletion, image input, Arabic/RTL, sources, and low-bandwidth recovery are
  supported in FastAPI/Next.js.
- Deterministic tools include enterprise budget/break-even/cash flow/sensitivity,
  unit conversion, action plans, checklists, crop calendars, referrals, source
  lookup, logframe status, and consented feedback.
- MCP exposes bounded application tools without shell, arbitrary filesystem,
  unrestricted URL, or generic database access. It serves the activated release
  and therefore requires PostgreSQL.
- Dynamic weather, prices, alerts, grants, contacts, and regulations must come
  from an authorized connector carrying its passage, publisher, observation
  time, expiry, and immutable evidence ID.

## Safety, privacy, and deployment

RAISE is decision support, not a substitute for an agronomist, veterinarian,
laboratory, engineer, food-safety professional, or competent authority. Static
pilot approval does not authorize exact chemical doses, veterinary
prescriptions, definitive diagnoses, food-processing safety parameters, or
unstamped legal/market claims.

Connected generation sends the farmer's input and selected evidence to the
configured provider. Do not collect phone numbers, precise personal location,
or other personal data without approved necessity and consent. Pilot/production
startup fails closed for invalid database, storage, migrations, origins,
provider settings, consent, retention, or model allowlists.

The locked hosted pilot topology remains Vercel + one Render FastAPI service +
Supabase, with Qdrant hosting to be selected. Hosting migration, real managed
restore, credentials, canary percentages, and the seven-day soak are the next
operational phase. See
`docs/LOCAL_RELEASE_CANDIDATE_HANDOFF.md` and
`docs/CANONICAL_PILOT_RUNBOOK.md`.

## License

Software is MIT-licensed. Knowledge-source copyrights and rights to institutional
names/branding are separate and require confirmation before public publication.
