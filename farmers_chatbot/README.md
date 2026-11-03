# Backend package map

Purpose: identify the main FastAPI, persistence, retrieval, and assistant
modules without requiring a reader to infer responsibilities from filenames.

| Module | Responsibility |
| --- | --- |
| config.py | Central environment values and answer-mode/model policies |
| runtime_settings.py | Provider-neutral runtime setting snapshots used by services |
| hosted_runtime.py | Fail-closed pilot/production configuration validation |
| auth.py | Normalized user identity and access-policy checks |
| oidc_auth.py | OIDC authorization-code flow and signed application sessions |
| web_api.py | Current FastAPI composition and routes; planned Phase 0 router split |
| pilot_store.py | PostgreSQL workspace, ownership, quota, turn, and feedback persistence |
| storage_backends.py | Private local-volume and S3-compatible file storage |
| assistant_pipeline.py | Clarification, retrieval preparation, streaming generation, and verification |
| clarification.py | Structured one-question-at-a-time clarification workflow |
| retrieval.py | Common evidence retrieval contract and orchestration |
| qdrant_retrieval.py | Qdrant projection retrieval with PostgreSQL fallback behavior |
| graph_repository.py | Versioned knowledge graph persistence and queries |
| graph_build.py | Deterministic knowledge release build inputs and validation |
| legal.py | Bilingual agreement/privacy document rendering |

Supporting modules are deliberately narrower helpers for citations, documents,
evaluation, providers, search, usage, WhatsApp compatibility, and projections.

## Runtime flow

~~~text
web_api
  -> auth/session and ownership
  -> pilot_store
  -> assistant_pipeline
       -> clarification
       -> retrieval / Qdrant / graph
       -> provider when configured
       -> verification and citations
  -> persisted turn streamed to the browser
~~~

The future router/service boundaries are specified in
[the product experience specification](../docs/product/PRODUCT_EXPERIENCE_SPEC.md).
Database migration and knowledge bootstrap remain separate operator actions.
