# RAISE v2 Cleanup and Pruning Plan

Created: 2026-08-20

This plan governs the transition from the compatibility-preserving pilot
codebase to a single, maintainable local-first stack that deploys unchanged.

**Framing decision:** backward compatibility with earlier versions is explicitly
*not* a constraint. Treat this as a new version. Registered users are retained;
their prior workspace data is archived, not migrated.

**Primary goal:** develop locally with maintainability as the top priority, then
deploy exactly what runs locally, as a repeatable update cycle.

## Standing decisions

| Decision | Choice |
|---|---|
| Persistence | PostgreSQL only. SQLite runtime path deleted. |
| Local mode | Docker Compose only. Bare-uvicorn mode deleted. |
| Test database | The compose PostgreSQL on `127.0.0.1:55432`, session-scoped fixture with per-test isolation. Not testcontainers. |
| Prior user data | Cold export to object storage at cutover, then purge hot tables. Users stay registered. |
| Streamlit | Deleted. |
| WhatsApp | **Retained.** Blocked on Meta API access, not on code. Only the `whatsapp_api.py` root wrapper is deleted. |
| Language workflow | English first, Arabic as a separate gated pass. |

### Why WhatsApp is retained

`whatsapp_router.py` is already on the canonical contracts — `_execute_turn`
builds a `TurnCommand` and drives `pipeline.prepare/stream`. It is not a second
orchestration path. What it contains is expensive, compliance-sensitive Meta
protocol work: HMAC-SHA256 signature verification with constant-time compare,
the `hub.mode`/`hub.verify_token`/`hub.challenge` handshake, message-ID dedup,
delivery retry that reuses the persisted turn without re-running the provider,
HMAC-derived pseudonymous identities, reply chunking, and text-channel citation
rendering. `tests/test_whatsapp_api.py` covers the semantics that are painful to
rediscover and runs green today, so the code is not rotting.

Carrying it costs roughly one extra hour across this plan: four store methods and
one table join the PostgreSQL migration, and it inherits the Tier 0 corpus fix
like any other channel.

## Tier 0 — safety-relevant, do first

The `search_knowledge` tool does not query the v0.3 release. It queries
`KnowledgeIndex`, which is TF-IDF over the era-1 `knowledge_base/guide.json`
(`tools.py:512` -> `knowledge.py:113`).

- `KnowledgeIndex.from_directory()` is loaded unconditionally at startup
  (`web_api.py:175`) and is a required constructor argument for
  `AssistantEngine`, `ToolRegistry`, and `LegacyHybridRetrieval`.
- Under `APP_ENV=development` — the compose stack — `allowed_statuses` includes
  `draft`, so the model can retrieve and cite unapproved legacy content.
- `LegacyHybridRetrieval` is the innermost retrieval fallback. If Qdrant and
  PostgreSQL both fail, the runtime answers from the legacy corpus instead of
  refusing. `scripts/local_smoke_test.py` refuses silent fallback; the runtime
  does not.

`knowledge_base/README.md` states `guide.json` "must never be indexed alongside
v0.3". It currently is.

**Action:** repoint `search_knowledge` and `get_source` at the active release.
Delete `KnowledgeIndex`, `guide.json`, `sources.json`, `LegacyHybridRetrieval`,
and `RAG_BACKEND=legacy`. The terminal fallback becomes an explicit refusal.

## Tier 1 — dead surfaces

| Surface | Files | Catch |
|---|---|---|
| Streamlit | `rag_chatbot.py`, `farmers_chatbot/streamlit_app.py` (1,398), `ui_copy.py` (333), `voice.py`, `.streamlit/`, `packages.txt`, `runtime.txt`, `deployment/streamlit_secrets.toml.example`, `requirements-voice.txt`; deps `streamlit`, `edge-tts`; tests `test_app`, `test_public_legal`, `test_ui_copy` | `auth.py` exports `UserIdentity`, imported by `pilot_store.py:18`. Move that dataclass, then delete the Google-OIDC half and the dead `AUTH_MODE`/`ACCESS_POLICY`/`ALLOWED_EMAILS`/`ALLOWED_DOMAINS` config. |
| Compat shims | `assistant_compat.py`, `AssistantService` (`llm.py:400-465`), `test_llm.py` | `mcp_server.py:20` and `scripts/benchmark_service.py:19` import the facade; repoint to `AssistantEngine`. |
| WhatsApp wrapper | `whatsapp_api.py` only | The router stays mounted and fail-closed. |
| Era-1 corpus | `Agricultural Guide for Lebanon.pdf`, `RAISE_Akkar_Agricultural_Guide.md`, `agrifood_knowledge_draft_v0.2*.md`, `scripts/build_guide.py` | All recoverable from git history. |

`tests/test_image_privacy.py` targets `streamlit_app._prepare_chat_image`, which
is already dead — sanitation moved to `image_processing.py`. Retarget the test,
do not delete the coverage.

## Tier 2 — parity fixes

### Delete SQLite

Currently carried:

- 13 tables of hand-maintained DDL in Python (`pilot_store.py:172-370`)
  duplicating the Alembic schema, with no test that the two agree.
- A third schema-evolution mechanism: runtime `ALTER TABLE` patching
  (`pilot_store.py:418`).
- `_sql()` `?` -> `%s` placeholder translation on every query.
- 13 `is_postgres` branches across four modules.

### Fold `EvidenceStore` into PostgreSQL

`ToolRegistry` defaults to `EvidenceStore()` (`tools.py:29`), which writes
`data/runtime.sqlite3`. The compose stack is therefore *not* PostgreSQL-only:
rate-limit, telemetry, and feedback state land in SQLite, and on hosted
ephemeral disk that state vanishes on every restart. Fold it into `PilotStore`
and delete `farmers_chatbot/storage.py`.

### One local mode

Delete the bare-uvicorn/SQLite section of `docs/CANONICAL_PILOT_RUNBOOK.md`.
`.\scripts\raise.ps1 start` becomes the only supported local path.

### Close the remaining dev/hosted divergence

Local runs `APP_ENV=development` with `AUTH_MODE=disabled`; hosted runs
`APP_ENV=pilot` with Supabase and the fail-closed guard. These are different code
paths, so "deploy what runs locally" is not yet true even with PostgreSQL
everywhere. Add a compose profile that boots `APP_ENV=pilot` against local
equivalents, plus a CI stage that exercises the pilot guard. Consider MinIO to
close the `storage_backends.py` local-vs-Supabase gap.

## Tier 3 — hygiene

- Delete `temp_dir/` (25+ stale scratch directories), the stale `venv/` beside
  `.venv/`, and `.coverage`.
- Reduce `docs/` from 25 files to roughly 8. `DEPLOYMENT.md` self-labels as
  historical; there are two dated `PILOT_READINESS_*` files;
  `PILOT_DEPLOYMENT_RUNBOOK.md` is superseded by `CANONICAL_PILOT_RUNBOOK.md`.
- Reduce 11 branches to `master` plus working branches. `pilot` and
  `release/pilot-2026-08` forked in April 2026 and are 22 commits behind
  `master`; they are archaeology, not branches. Documentation still describes
  `pilot` as the active development branch, which is wrong.
- Make `CLAUDE.md` tracked and accurate. It currently describes era 2/3.
- Reconcile the active release ID and ontology counts across `README.md`,
  `docs/ARCHITECTURE.md`, and `knowledge_base/README.md`. README names
  `release_bdc0dd68eb2c9b857994f664`; the live release is
  `release_4debc9a9de849675835bb255`. ARCHITECTURE says 21 entity types / 162
  entities / 183 relations; the knowledge README says 31 / 260 / 494.

## English-first, Arabic-gated

This is a test-execution rule, not a corpus rule. The v0.3 corpus is dual-file
with shared knowledge, claim, entity, relation, and source IDs; Arabic is a
validated projection of English. Breaking that link would cost the bilingual
traceability the product depends on.

The golden dev set is `en 60 / ar 57 / ar-LB 47 / ar-LB-Latn 40 /
ar-LB-x-code 36` of 240 — English is 25%.

- Mark the suite by language. `pytest -m "not arabic"` is the inner loop;
  `pytest -m arabic` is required before merge.
- Same split in the eval harness by language group.
- Make `arabic_english_gap` (currently 0.56 points) a hard CI threshold, e.g.
  fail above 2.0. Without it, English-first quietly becomes English-only, which
  is the real risk in an Arabic-first product.
- Frontend: iterate in `en` via `lib/i18n.ts`, keep an RTL render test in the
  pre-merge gate.

## Confirming the GraphRAG actually links well

At present this cannot be confirmed, and the headline numbers do not say what
they appear to say. From `build-reports/evaluation/qdrant_public.report.v1.json`:

```
scope.kind = "retrieval_only"
scope.does_not_measure = [answer_generation, verifier_enforcement,
                          human_preference, frontier_model_comparison]
efficiency.total_cost_usd = 0.0     # no model was ever called
citations.precision = 1.0           # judged against the golden set's own anchors
safety.escalation_recall = 0.0      # 0 of 60 required escalations, nothing generates
graph.path_accuracy = 0.890909      # over 55 applicable cases, not 240
```

Decisively, **the ablation ladder has never been run.**
`evaluation/ablations.v1.json` defines the right seven arms (`legacy_tfidf` ->
`vector_only` -> `hybrid` -> `contextual_hybrid` -> `hybrid_graph` ->
`full_raise` -> `base_no_rag_tools`), but `scripts/evaluation/cli.py:49-53` only
stamps `{path, sha256}` into the report as provenance. No runner executes the
arms.

In order of value:

1. **Build the ablation runner.** The number that answers the question is
   `hybrid_graph` minus `contextual_hybrid` on graph-applicable cases. If that
   delta is near zero, the graph is decoration.
2. **Add a negative control.** Shuffle the relation edges and re-run. If
   graph-path accuracy does not collapse, the paths are not carrying signal.
3. **Raise graph coverage past 55/240.** 23% is thin evidence for a
   graph-centric architecture.
4. **Profile the graph structurally** — degree distribution, orphan entities,
   relation-type coverage against the 34 declared types, path-length
   distribution, alias collisions. 494 relations over 192 chunks is ~2.6 per
   chunk; nobody has checked whether that is rich or skeletal.
5. **Then answer-level evaluation** — entailment and escalation. Requires
   provider credentials, and closes `does_not_measure`.

Steps 1-4 are local, deterministic, and need no API key.

## Archive cutover carries a legal dependency

`hosted_runtime.py` refuses startup unless
`CONSENT_VERSION == AGREEMENT_TEXT_VERSION`, and `legal/` publishes a retention
promise that `RETENTION_DAYS=30` enforces. Changing the data lifecycle therefore
requires new bilingual legal text and a consent-version bump, with re-consent at
rollout. Plan it as a release event, not a migration.

## Stages

| Stage | Content |
|---|---|
| 0 | Green gates, this plan committed, branch pushed |
| 1 | Tier 0 legacy-corpus excision |
| 2 | Tier 1 deletions, one surface per commit, gates between |
| 3 | SQLite and `EvidenceStore` removal, PostgreSQL test fixtures, single local mode, archive script |
| 4 | Ablation runner and graph profiling |
| 5 | English/Arabic split and language-gap threshold |
| 6 | Docs, branches, and `CLAUDE.md` rewritten against the pruned reality |

Stages 1-3 remove roughly 25% of the codebase and two whole classes of
divergence. Stage 4 determines whether the remaining architecture earns its
place.

## Open items

- `mcp_server.py` is a fourth surface that no cleanup decision has covered yet.
  It imports the compat facade and must be repointed in Stage 2. Decide whether
  it stays a supported surface.
- Qdrant hosting is still unselected; hosted topology discussion is deferred.
