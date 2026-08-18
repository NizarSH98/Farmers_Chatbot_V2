# Knowledge Base

This directory contains the reviewable source material for RAISE. PostgreSQL is
the authoritative release store and Qdrant is a rebuildable retrieval
projection; neither database replaces these versioned source files.

## Canonical pilot corpus

- `agrifood_knowledge_v0.3.en.md`: authoritative English pilot knowledge.
- `agrifood_knowledge_v0.3.ar.md`: locally generated and validated Arabic
  companion with identical knowledge, claim, entity, relation, and source IDs.
- `agrifood_knowledge_v0.3.disposition.json`: body-order disposition for all 32
  source chapters.
- `ESDU_Agrifood_Knowledge_Base_v0.1.docx`: unchanged local source document. It
  is excluded from runtime images and must not leave the operator's machine.

The v0.3 files are approved by the project owner for authenticated pilot use.
Expert verification remains pending editorial metadata; it does not display a
recurring warning to farmers and does not relax high-risk safety rules.

The v0.2 Markdown files and `guide.json` are migration/reference inputs only.
They must never be indexed alongside v0.3. The active runtime release is built
only by `scripts.build_graph_release` and pinned by its immutable release ID.

## Reproducible local commands

From the repository root:

```powershell
.\scripts\raise.ps1 start -Rebuild
.\scripts\raise.ps1 build-graph
.\scripts\raise.ps1 evaluate
.\scripts\raise.ps1 export
.\scripts\raise.ps1 smoke
```

The graph build verifies source/configuration hashes, chunks both language
files, resolves the schema-first ontology, writes evidence-backed PostgreSQL
records, projects the exact release into two versioned Qdrant collections, and
switches aliases only after validation. Repeating an unchanged build resumes
from its content-addressed caches and does not create duplicate records.

## v0.3 ontology

The ontology covers 31 entity types across production, symptoms, pests,
diseases, inputs, soil, water, climate, equipment, measurements, value chains,
services, markets, finance, opportunities, regulations, risks, costs,
sustainability impacts, and outcomes. It defines 34 typed relations. Every
persisted relation requires a source passage plus geography, validity, risk,
review state, polarity, conditions, and confidence metadata.

The current immutable local release contains 260 entities, 649 bilingual/local
aliases, 494 passage-backed relations, 192 semantic chunks, 192 claims, and 686
evidence links.

## Editorial and safety rules

- `review_status: approved` means project-owner approval for the authenticated
  pilot; it does not claim institutional or expert endorsement.
- `expert_verification_status: pending` remains available to editors/admins.
- Approved static text still cannot authorize exact chemical doses,
  veterinary prescriptions, definitive diagnosis, food-processing safety
  parameters, or unstamped legal/market/weather claims.
- Current values require timestamped live evidence with an expiry.
- Editors propose changes into a new immutable release; an active release is
  never edited in place.

## Evaluation boundary

`evaluation/golden/public_dev.v1.jsonl` contains 240 source-anchored development
cases. The ignored, checksum-sealed acceptance file contains 160 further cases.
Together they have the exact required 400-case domain, language, task, and risk
distribution. These labels are a deterministic golden-set candidate until
agricultural and Arabic reviewers accept a sample; they are not indexed as
knowledge and they do not justify a public superiority claim.
