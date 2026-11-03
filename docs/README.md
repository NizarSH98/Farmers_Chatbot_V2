# Documentation map

Purpose: identify the authoritative document for each kind of work and keep
historical material out of the active path.

## Start here

| Need | Document | Purpose |
| --- | --- | --- |
| Understand the product to build | [Product experience specification](product/PRODUCT_EXPERIENCE_SPEC.md) | Exact frontend, backend, reliability, phasing, and acceptance contract |
| Understand what runs | [Architecture](ARCHITECTURE.md) | Runtime boundaries, authoritative data, networks, and service responsibilities |
| Start, update, monitor, or recover | [Deployment and operations](DEPLOYMENT.md) | Local and VPS operator source of truth |
| Put the pilot on AWS quickly | [AWS Lightsail deployment](DEPLOY_AWS_LIGHTSAIL.md) | Single-VPS Caddy route with bounded costs, step by step |
| Understand the infrastructure reform | [Migration report](MIGRATION_REPORT.md) | Dated migration decisions and completed validation evidence |

When documents conflict, use this order:

1. product behavior: Product experience specification;
2. runtime/deployment: Deployment and operations;
3. service/data boundaries: Architecture;
4. policy/legal controls: Policy approval checklist and legal files;
5. archived files: never authoritative.

## Engineering and operations

| Document | One-line description |
| --- | --- |
| [Database migrations](DATABASE_MIGRATIONS.md) | How Alembic schema changes are created, applied, and checked |
| [Data portability](DATA_PORTABILITY.md) | What data is authoritative and how to move it to another host |
| [Evaluation harness](EVALUATION_HARNESS.md) | How retrieval/answer evaluation datasets, metrics, and gates work |
| [Migration report](MIGRATION_REPORT.md) | Evidence snapshot for the 2026-09 provider-neutral deployment reform |

## Knowledge, governance, and project controls

| Document | One-line description |
| --- | --- |
| [Governance and validation](GOVERNANCE_AND_VALIDATION.md) | Roles and methods for evidence, expert, field, and release validation |
| [Source document intake](SOURCE_DOCUMENT_INTAKE.md) | Intake and conflict-review process for external source material |
| [Internal knowledge intake](ESDU_INTERNAL_KNOWLEDGE_INTAKE.md) | Intake process for ESDU knowledge and performance evidence |
| [Logframe traceability](LOGFRAME_TRACEABILITY.md) | Mapping from contractual activities to repository evidence |
| [Policy approval checklist](POLICY_APPROVAL_CHECKLIST.md) | Required institutional, legal, privacy, and launch approvals |
| [Replication readiness output](RRO.md) | Working draft for the future approved replication deliverable |

## Working templates

| Document | One-line description |
| --- | --- |
| [Field session template](FIELD_SESSION_TEMPLATE.md) | Record one controlled field-feedback session |
| [Knowledge review template](KNOWLEDGE_REVIEW_TEMPLATE.md) | Record expert review of a knowledge item |
| [Stakeholder tracker schema](STAKEHOLDER_TRACKER_SCHEMA.md) | Define fields for the controlled off-repository stakeholder tracker |

## Archive

[docs/archive](archive/README.md) contains superseded plans, dated readiness
snapshots, and replaced runbooks. Git history preserves removed deployment
files and code; they are not copied back into the working tree.
