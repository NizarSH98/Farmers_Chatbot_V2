# Knowledge Base

This directory is the editable, reviewable source for the farmer assistant. The legacy PDF remains available for comparison, but new production knowledge should be represented as structured Markdown or JSON with stable citations and review metadata.

## Canonical draft corpus

- `agrifood_knowledge_draft_v0.2.md`: canonical bilingual, graph-ready pilot
  draft used by the release builder.
- `agrifood_knowledge_draft_v0.2_ar.md`: standalone Arabic review companion
  with the same record IDs, sources, entities, and graph relations.
- `ESDU_Agrifood_Knowledge_Base_v0.1.docx`: unchanged source document; it is
  not a runtime retrieval source.

Regenerate both Markdown files locally:

```powershell
python -m scripts.convert_agrifood_docx
python -m scripts.ingest_knowledge_release --validate-only
```

The converter uses repository-owned Arabic drafts and performs no model or
translation network call. Repeated conversion is byte-for-byte deterministic.
Do not index `guide.json` alongside the v0.2 Markdown release: the Markdown
metadata records which legacy JSON items were merged or superseded.

Each record embeds its slice of
`raise-agrifood-ontology-v0.2.0`. The release compiler validates and produces
162 bilingual typed entities, 352 aliases, 183 qualified relations, and
passage evidence for every relation. The visible ontology gold fixture is a
developer structural regression, not a hidden product-quality benchmark.

## Status labels

- `draft`: may be indexed only in development.
- `technical_review`: checked by a subject reviewer but not field-language approved.
- `field_review`: checked for Akkar language and practicality.
- `approved`: eligible for pilot retrieval.
- `retired`: preserved for history but excluded from retrieval.

## Required metadata

Every section should identify:

- stable knowledge ID;
- title in English and Arabic;
- language;
- geography;
- topics/value chains;
- source IDs;
- evidence class;
- risk class;
- owner/reviewer;
- version and review dates;
- status.

## Content boundary

Static guidance must not pretend to be current weather, market price, grant, disease alert, pesticide registration, or regulation information. Those topics require approved dynamic tools and visible timestamps.

## Review warning

The initial strengthened guide is a sourced project draft. It is not an official ESDU publication until ESDU approves the content, title, branding, and publication status.

