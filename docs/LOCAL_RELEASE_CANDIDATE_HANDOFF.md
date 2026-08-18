# RAISE local release-candidate handoff

Generated for the 2026-08 local release candidate. This is the operator source
of truth for moving the tested application to hosted infrastructure later.

## Verified local state

- PostgreSQL migration head: `20260812_0005`.
- Active pilot release: `release_4debc9a9de849675835bb255`.
- Release contents: 36 sources, 36 documents, 192 chunks, 192 claims, 260
  entities, 649 aliases, 494 relations, and 686 evidence links.
- Qdrant projection: 384 evidence points and 260 entity points in collections
  named with the exact release ID.
- Retrieval routes: vector-only for simple lookup, contextual hybrid for normal
  guidance, and lazy two-hop graph/PPR routing for Deep questions. PostgreSQL
  lexical/graph retrieval is the outage fallback.
- Corpus: matching v0.3 English and Arabic files, 18 knowledge records and 429
  validated semantic units, with all 32 source chapters dispositioned.
- Golden candidate: 240 tracked development cases plus 160 ignored/sealed
  acceptance cases. It is source-anchored but still requires human sampling.
- Development retrieval: Recall@10 99.58%, nDCG@10 88.22%, graph-path
  accuracy 89.09%, p95 225.48 ms, and Arabic/English gap 0.56 points.
- Sealed local acceptance retrieval: Recall@10 100%, nDCG@10 88.38%,
  graph-path accuracy 88%, p95 163.10 ms, and zero language gap.

The original DOCX checksum must remain:
`3C0BAF8145E4A2E287BA5783F8AB26A7CEAE1C5340322C1EE065887CC9B75B0E`.

## One-command local surface

Run these from the repository root in PowerShell:

```powershell
.\scripts\raise.ps1 start -Rebuild
.\scripts\raise.ps1 status
.\scripts\raise.ps1 build-graph
.\scripts\raise.ps1 evaluate
.\scripts\raise.ps1 smoke
.\scripts\raise.ps1 export
```

`export` writes a PostgreSQL custom-format dump, both Qdrant snapshots, their
checksums, and a handoff manifest under the ignored `backups/` directory.

To restore a selected export into the active local stack:

```powershell
.\scripts\raise.ps1 start
.\scripts\raise.ps1 restore -Path .\backups\raise-YYYYMMDD-HHMMSS
```

To prove portability in a separate empty stack on ports 3001/8001/55433/6434:

```powershell
.\scripts\verify_restore.ps1 -Path .\backups\raise-YYYYMMDD-HHMMSS
```

The verifier deletes only the fixed disposable `raise-restore` project, restores
all stores, rebuilds the app, and runs host and container smoke tests.

Restore is intentionally destructive to the selected local Compose databases.
It validates input location and snapshot hashes, restores both databases,
repairs the two Qdrant aliases, and runs the smoke test before success.

## Manual steps before hosted production

No manual repository edit is required. The operator must provide external
infrastructure and credentials because they cannot be invented or committed:

1. Create/choose managed PostgreSQL 16 with `vector`, Qdrant 1.17-compatible
   storage, one Render API service, and the Vercel web project.
2. Take a fresh production PostgreSQL/private-storage backup and perform a
   disposable restore before applying migrations.
3. Set production secrets from `.env.example`: database/storage/auth/provider
   values, exact origins, consent/retention policy, model allowlist, and Qdrant
   TLS URL/API key. Do not reuse local passwords or enable local auth.
4. Run `alembic upgrade head`, restore/import the immutable release, restore or
   rebuild its exact Qdrant collections, and compare the local handoff hashes
   and counts.
5. Keep `RAG_BACKEND=legacy` during shadow telemetry, then use `postgres`, then
   `qdrant` only after fixed-query comparison passes. Never activate PostgreSQL
   and Qdrant releases independently.
6. Canary authenticated users at 5%, 50%, and 100%, retaining the previous
   release ID and database/vector snapshots for immediate rollback.
7. Keep WhatsApp disabled and the hosted Streamlit deployment retired/frozen
   until the Next.js/FastAPI service completes a seven-day clean soak.
8. Have an agricultural reviewer and native Arabic reviewer sample the sealed
   acceptance set. Only human-reviewed, blind pairwise results can support a
   claim that RAISE beats frontier models.

## Honest limitations at this handoff

- The local 400-case run measures retrieval. Full answer safety, citation
  entailment, and matched GPT/Claude comparisons require authorized provider
  credentials and human labels; no superiority claim is made yet.
- The active embedding is multilingual E5-small. Candidate-model benchmarking
  and promotion of a multilingual cross-encoder reranker remain measurement
  decisions, not assumptions.
- Native Personalized PageRank/path pruning is implemented. HippoRAG, PathRAG,
  and Microsoft GraphRAG remain evaluation adapters/ablation targets and are not
  represented as installed production dependencies.
- Project uploads are tenant-filtered in PostgreSQL and fail back to lexical
  retrieval. A separate private Qdrant projection must not be enabled in hosted
  use until tenant-isolation integration tests pass against that environment.
- Legal/privacy/institutional publication approval and the hosted seven-day soak
  are external operational gates, not code tasks.

These limitations are deliberately explicit so a deployment decision cannot
mistake local software readiness for completed field, legal, or hosted evidence.
