# Delivery audit and implementation route

Audit date: 2026-09-07. Baseline commit: 252c16b97c1b, with substantial pre-existing uncommitted work.

## Authority and scope

The owner's product brief is represented in ProjectGraph. The graph records intended behavior,
dependencies, findings, and evidence; it is also subject to audit. Documentation explains operation.
Tests prove only the cases they actually execute. A passing migrated contract is not a release decision.

RAISE is an Arabic-first agricultural assistant for novice and experienced users, with one assistant
runtime shared by web and WhatsApp, reviewed source knowledge, and a fresh VPS deployment.
No legacy user-data import is needed. Once launched, updates must preserve new user data.

ProjectGraph is the development architecture map. Runtime GraphRAG is a separate custom system:
PostgreSQL is authoritative; Qdrant combines dense and sparse retrieval with bounded graph expansion.
It is not an installation of Microsoft's GraphRAG library. Adding global summaries or another graph
database requires measured justification, rather than similarity to a product name.

This pass traced the main deployment, evaluation, retrieval, chat, and WhatsApp boundaries and ran
local build checks. It is not exhaustive proof of every source file, dependency, security boundary,
usability interaction, or production workload.

## Baseline evidence

| Check | Observed result | Limit |
| --- | --- | --- |
| Next.js production build | Passed | No browser/device usability acceptance |
| Web tests | 15 passed across 4 files | Very small compared with the workspace's interaction surface |
| Web lint | Passed | Naming and architecture still require semantic review |
| Python lint and pip dependency consistency | Passed | Does not establish vulnerability status |
| Backend baseline on an isolated PostgreSQL instance | 218 passed, 2 skipped | Both skips require pg_dump; no full backup proof |
| API Docker image | Built as raise-audit-api:local | Local build, not a published release |
| Empty application database | All seven Alembic revisions applied to 20260901_0007 | No active knowledge release |
| API process on the blank database | Started; health endpoint reachable | Returned ok despite missing knowledge and no generation provider |
| Graph structure before this audit | Validation and synchronization passed | Migrated broad globs do not prove semantic completeness |

Raw baseline test evidence is in reports/generated/audit/backend-baseline.xml.
Subsequent strict test runs write reports/generated/verification/backend-*.xml; ProjectGraph records
their commands, exit codes, output tails, and artifact hashes under .projectgraph/evidence/.
Generated local reports are ignored by Git. The source findings in this document are tracked.

## Findings and ownership

Status FIXED means a focused change was made; the relevant ProjectGraph verification result remains
the authority for executed evidence. OPEN means implementation or acceptance is still required.

| ID | Priority | Finding and evidence | Status / owning graph node |
| --- | --- | --- | --- |
| A01 | P0 verification | tests/conftest.py skipped when PostgreSQL connection or schema migration failed. Existing tool-runtime evidence even contained 12 skipped tests. A suite could therefore pass without exercising its database boundary. | FIXED setup now fails; scripts/verify_backend.py rejects skipped release checks. SYS_QUALITY |
| A02 | P0 test data | Test fixtures truncate tables, but previously accepted an arbitrary TEST_DATABASE_URL. The database name was interpolated into CREATE DATABASE. | FIXED loopback and raise_test naming guard, SQL identifier quoting. SYS_QUALITY |
| A03 | P0 measurement | scripts/run_ablations.py declared contextual_hybrid with graph_hops=0, while Qdrant _query_graph still traversed one hop. PostgreSQL graph_paths also clamped zero to one. | FIXED zero-hop guard in both paths and truthful hop metadata. REQ_MEASURABLE_GRAPHRAG_LIFT |
| A04 | P0 measurement | Retrieval runners synthesized entails=true citations from gold answers, used evidence overlap as answer quality, truncated returned paths to the gold path count, and the ablation runner always reported success. The negative control also overwrote normal run files. | FIXED no invented answer labels, retain full paths, backend failure propagates, separate negative-control files; language gate now measures Arabic recall deficit. REQ_MEASURABLE_GRAPHRAG_LIFT |
| A05 | P1 operations | API health returns HTTP 200/status ok with active_release_id=null and fallback_ready=false. Compose checks HTTP reachability only. Reproduced on the blank audit database. | OPEN separate liveness from readiness, add schema/release/projection/provider readiness policy and fresh-install smoke gate. REQ_PORTABLE_FAIL_CLOSED_OPERATIONS |
| A06 | P0 before pilot | web_api.py constructed approved-only knowledge for pilot/production, but Qdrant and PostgreSQL retrieval allowed drafts in ordinary pilot requests; critical risk differed between paths. | FIXED shared approved-only public policy, explicit internal preview only, high/critical/current turns restrict internal tools too. Regression matrix covers pilot/production/unknown scopes and activation races. REQ_SOURCE_GROUNDED_SAFE_ASSISTANCE |
| A07 | P1 reliability | WhatsApp registers an event and returns 202 before FastAPI BackgroundTasks finish. There is no durable worker demonstrated here. A crash can leave an accepted event without a reply; replay handling only specially retries send_failed. Status callbacks are not processed, media is ignored, consent acceptance recognizes English agree only. | OPEN durable inbox/outbox, recoverable worker leases, delivery receipts, bilingual consent and supported-message policy. REQ_CHANNEL_NEUTRAL_WHATSAPP |
| A08 | P1 provenance | PostgreSQL ignored release_pin, Qdrant fallback could select a newly activated release, and tool/source lookups could reselect the release during a turn. | FIXED PostgreSQL honors pins; Qdrant pins before projection lookup; prepared turns own isolated release-pinned tools and citation lookup. Missing knowledge stays unavailable for that turn. REQ_SOURCE_GROUNDED_SAFE_ASSISTANCE |
| A09 | P1 recovery | scripts/raise.ps1 snapshot includes PostgreSQL and a Qdrant manifest but does not copy private files; restore acts on the current application database. The restic restore script extracts and lists a dump, but does not rehearse a restored application. Backup health tests only whether last-success exists. | OPEN one complete, isolated recovery procedure; backup age check; source snapshots must include every authoritative object. REQ_PORTABLE_FAIL_CLOSED_OPERATIONS |
| A10 | P1 UX | ChatWorkspace rendered all clarification questions at once; submit clears the composer before acceptance and generic errors do not restore it. Starters and direct typing exist, but novice/expert usability is not established. | PARTIALLY FIXED: the current form now shows one question at a time with progress and Back/Next; resolved forms are no longer actionable. Browser audit at 390×844 found no user-facing unnamed controls, no targets under 44 px, and no horizontal overflow. Still OPEN for recoverable drafts, assistive-technology testing, and observed novice/expert scenarios. REQ_ADAPTIVE_AI_LITERACY |
| A11 | P1 evaluation | Executable ablation arms differ from evaluation/ablations.v1.json; vector actually means dense+sparse fusion. No measured no-retrieval LLM baseline, blinded answer assessment, agreed effect threshold, or VPS concurrency budget is established. | OPEN align manifests, record exact corpus/model/config/release versions, evaluate withheld scenarios, then choose routes by measured quality/cost/latency. REQ_MEASURABLE_GRAPHRAG_LIFT |
| A12 | P2 maintainability | Large mixed-responsibility files remain (ChatWorkspace, web_api, pilot_store). Some legacy/fallback names no longer describe their role. Broad component globs obscure ownership of individual capabilities. | OPEN split only along demonstrated state/behavior boundaries after contract coverage; review identifiers by meaning and lifetime, not cosmetic uniformity. CMP_FARMERS_CHATBOT / CMP_APPS_WEB |
| A13 | P1 tooling | Operator commands joined user arguments into sh -c and the restore path guard accepted textual path prefixes. | FIXED pass arguments directly to Python and require a child of the actual backup directory. CMP_SCRIPTS |
| A14 | P1 verification | Host portability checks lack pg_dump; the current backup tests restore private files but do not restore the database into a fresh database and prove application behavior. | OPEN provide PostgreSQL client tools in the verification environment and add a real isolated database/file recovery rehearsal. REQ_LOCAL_RELEASE_READINESS |
| A15 | P1 proxy review | Next.js proxy joins decoded route segments into a URL and buffers the full body. Origin confinement, malformed encoded paths, size limits, cancellation, and upstream timeout behavior lack dedicated tests in the inspected web suite. | OPEN adversarial proxy boundary tests before internet exposure; exploitability not asserted by this source review. REQ_AUTHORIZED_DURABLE_WORKSPACES |
| A16 | P1 adapter parity | assistant_compat.py constructs AssistantEngine without a retrieval service, which selects ProjectOnlyFallbackRetrieval. The synchronous MCP/benchmark adapter therefore does not exercise PostgreSQL/Qdrant retrieval despite receiving a release gateway. | OPEN inject the canonical configured retrieval stack with per-event-loop resource ownership; do not treat this benchmark as GraphRAG performance evidence. REQ_MEASURABLE_GRAPHRAG_LIFT / CMP_CUSTOM_TOOL_RUNTIME |

Source-safety repair check: 67 tests passed, zero skipped, using the isolated audit PostgreSQL
database. This proves the executed policy, activation-race, citation, and bounded-tool regressions;
it does not prove answer-level GraphRAG lift or production readiness. Public approved-only filtering
may expose a draft-only corpus as unavailable; review and approve actual evidence rather than
loosening the policy to obtain a successful demo.

Post-repair full backend run: 247 passed, 2 skipped, zero test failures. Strict release verification
correctly exited 1 because both PostgreSQL dump checks were skipped. The remaining warning is
the FastAPI/Starlette test-client HTTP transport deprecation; the old pytest-cache warning is gone.
Raw evidence: reports/generated/verification/backend-d4f22d4214594b019699db1e454ab898.xml.

## Ordered delivery work

1. Finish the verification foundation: strict tests with PostgreSQL client tools, actual backup restore,
   recorded test selection/skip counts, graph contracts that track their runner/configuration, and a
   reproducible local environment. Preserve the existing dirty worktree until its changes can be reviewed.
2. Repair evidence eligibility and release pinning (A06/A08), then proxy boundaries (A15).
   Establish canonical turn invariants across authentication, quotas, ownership, cancellation,
   persistence, tool budgets, and citation resolution.
3. Bootstrap a new reviewed knowledge release and its Qdrant projection in isolation. Add a readiness
   endpoint and prove a local web turn through the real API and persistence path. Keep external
   model calls explicitly separated from offline tests and record the model actually used.
4. Finish valid retrieval experiments (A11). Run dense/sparse baseline, contextual without graph,
   graph, and negative controls on the same pinned release. Then run answer-level baseline versus
   RAG comparisons with blinded assessment. Capture warm/cold p50/p95, concurrency, CPU/RAM,
   token cost, source support, Arabic/English/Arabizi outcomes, and confidence intervals.
   Choose performance targets against the actual VPS plan and expected usage; do not invent a pass.
5. Implement guided UX (A10), preserving immediate free-form expert access. Run mobile RTL,
   keyboard, screen-reader, slow-network, interrupted-turn, and novice/expert task scenarios.
6. Complete WhatsApp delivery (A07) using the same engine. Prove retry/restart/duplicate behavior
   locally, then perform Meta test-number acceptance when configuration is available.
7. Rehearse installation, update, rollback compatibility, complete backup/restore, monitoring,
   retention and troubleshooting on a disposable VPS-like stack. Check dependency vulnerabilities,
   pinned image release identity, resource limits, disk growth, log rotation, and secrets configuration.
8. Review and commit the complete intended changes. CI must pass on that commit, publish matching
   immutable API/web/backup image tags, and record the selected knowledge release. Configure VPS
   secrets/DNS/TLS/OIDC/backup/Meta, run deployment acceptance, then obtain the owner's launch decision.

The machine-readable order is in .projectgraph/milestones.yaml. Local operational readiness,
core assistant evidence, guided web, WhatsApp, VPS readiness, and launch remain separate gates.

## External prerequisites and acceptance

These are not prerequisites for source review and offline fixes:

- VPS CPU/RAM/disk plan and expected concurrent usage, needed for credible capacity targets.
- Domain, DNS, TLS, registry access and chosen Dokploy configuration.
- OIDC issuer/client registration, application session secret, privacy/contact settings.
- Generation provider credentials and an agreed evaluation spend limit.
- External backup repository and encryption credentials.
- Meta business account, phone number, application credentials, templates and test recipient.
- Representative novice and experienced users for observed usability acceptance.

Enter secrets through local/deployment environment configuration, not this report or the graph.
Only attest a product or deployment acceptance condition after the relevant observed exercise.

## Workspace discipline

No prior user files were reset or removed. The 22 orphan ProjectGraph state records were removed by
projectgraph sync --apply, with evidence files retained. Pytest cache now uses an ignored writable
reports/generated location. API audit images and audit database volumes are separate from prior
local deployment images/data. Temporary audit containers are stopped after checks; the audit volume
is retained for repeatability. Generated ProjectGraph views must be regenerated after graph edits.

## Local acceptance evidence — 2026-09-07

This exercise used a separate raise-ux-audit Compose project and volumes. It did not touch the
normal RAISE local stack or any external service. The API, PostgreSQL, Qdrant, migrations, and
production-built Next.js web service became healthy. The live browser exercise covered Arabic RTL
initial load, agreement acceptance, English/LTR switch, conversation persistence, clarification
streaming, and a 390×844 mobile viewport. Screenshots and structural browser output are generated
under reports/generated/audit/.

The current evidence score is **55/100 — not launchable and not evidence of GraphRAG achievement**:

| Dimension | Points | Result |
| --- | ---: | --- |
| Isolated stack, migrations, service health | 15 / 15 | Passed |
| Web build, lint, and behavioral tests | 15 / 15 | 18 web tests passed |
| Bilingual, responsive, accessible interaction structure | 15 / 15 | RTL/LTR switch; zero user-facing unnamed controls, undersized targets, or mobile overflow after repairs |
| Consent and durable browser-to-API interaction | 10 / 10 | Passed; an irrigation turn and clarification messages persisted |
| Reviewed GraphRAG evidence and citation path | 0 / 20 | Blocked: no active release or ready projection |
| Answer quality, safety calibration, and latency | 0 / 15 | Not measured: no generation provider and no grounded answer |
| Complete recovery and release portability | 0 / 10 | Not measured: PostgreSQL client checks still skip and isolated restore is incomplete |

The local smoke gate failed as designed with RuntimeError: pilot projection is not ready. The
embedding cache contains an incomplete download of intfloat/multilingual-e5-small; attempts to
bootstrap a release therefore produced no active release or Qdrant projection. Health still returns
HTTP 200 in this condition, which remains A05. A secondary Compose tools invocation also used its
default password unless the environment was repeated, producing a migration authentication failure;
the dedicated local command path must carry one environment file consistently.

### Required proof before claiming a GraphRAG achievement

Build and activate one reviewed release, make the smoke gate pass, then evaluate the same pinned
release with a pre-registered held-out set: 12 Arabic, 10 English, 4 Arabizi, and 4 high-risk
Lebanon/Akkar scenarios. Compare no-retrieval, lexical/dense baseline, contextual retrieval, and
the routed graph configuration using the same generation model, prompt, and token budget. Blind at
least two reviewers to configuration and score each answer 0–4 for factual support, citation
entailment, safety/calibration, local actionability, language clarity, novice comprehension, and
expert efficiency. Report disagreement, paired per-case results, p50/p95 latency, success rate,
CPU/RAM, and cost. A retrieval score alone must not be substituted for answer quality.
