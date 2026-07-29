# RAISE Logframe Traceability

Last updated: 2026-07-29

This document translates `RAISE_Logframe_final.xlsx` into product requirements and auditable evidence. The workbook remains the contractual source of truth. This file is a derived implementation tracker and must not be used to silently reinterpret targets.

## Objective

Create an Arabic- and English-language platform, delivered through a website and a messaging channel such as Telegram or WhatsApp, for rural agri-food stakeholders. Produce a Replication Readiness Output (RRO) that documents how the approach can be adapted and scaled.

## Delivery rules

- Report **build readiness** and **contractual achievement** separately.
- A software feature is not evidence of stakeholder adoption.
- A draft is not an approved governance methodology or completed RRO.
- A person counts as a stakeholder participant only when a consent-aware outreach or participation record exists.
- Feedback counts toward the resolution indicator only after it is validated, prioritized, and assigned a resolution status.
- Performance targets must be supported by timestamped test results or monitoring exports.

## Traceability matrix

| Logframe activity | Contractual indicator and target | Product requirement | Means of verification | Current evidence |
|---|---|---|---|---|
| A.1.1.1 System Architecture Refinement | ≥90% priority backend tests pass | Automated unit, integration, retrieval, MCP, and application smoke tests | `tests/`, CI results, release record | 36/36 current automated tests pass locally, including identity, ownership, artifacts, retention, trusted-source, prompt, and WhatsApp webhook controls; CI and priority-set approval pending |
| A.1.1.1 System Architecture Refinement | Median response ≤10 seconds under expected pilot load | Request timing, fixed pilot-load scenario, percentile report | `reports/performance/`, application logs | Local retrieval-fallback benchmark passes (3 ms median in the latest 30-request run); connected-model pilot-load measurement is pending |
| A.1.1.1 System Architecture Refinement | ≥95% availability in controlled testing | Health probe and controlled uptime run | Monitoring export and test report | Local health check passed once; not sufficient for target |
| A.1.1.1 System Architecture Refinement | ≥80% retrieval relevance | Approved bilingual Akkar benchmark and scored retrieval report | `evaluation/benchmark_questions.jsonl`, `reports/generated/` | Candidate 30-question benchmark currently scores 100% overall and by language; team/field approval pending |
| A.1.1.2 Governance and Validation Framework | ≥3 methodologies | Evidence governance, expert/field validation, and AI release-gate methodologies | `docs/GOVERNANCE_AND_VALIDATION.md`, approval minutes | Three methodologies drafted; approval and meeting minutes pending |
| A.1.1.3 Stakeholder Identification and Field Alignment | 40–50 stakeholders enrolled | Consent-aware stakeholder registry and outreach workflow | Controlled stakeholder registry and outreach record | No stakeholder record in repository |
| A.1.2.1 System Deployment | 40–50 stakeholders try the model | Website plus approved Telegram or WhatsApp pilot channel; privacy notice; participation logging | Deployment record and participation export | Authenticated Streamlit and Meta test-number service builds exist with deployment runbook; no live deployment or participation evidence |
| A.1.2.2 Field Testing | ≥4 feedback sessions | Facilitated Arabic-first feedback protocol and session template | Event logs, agendas, attendance and consent records | No session evidence |
| A.1.2.3 Iterative Improvement | ≥80% validated high-priority feedback resolved | Feedback workflow with validation, priority, owner, release, and verification fields | Feedback log and release notes | Consent-aware collection and calculation schema implemented; percentage not yet computable |
| A.1.2.4 System Performance Evaluation | 1 RRO | Versioned replication package covering context, architecture, governance, cost, adaptation, risks, and evidence | `docs/RRO.md` and approved final output | Working draft created; pilot results and approval pending |

## Internal review gates

### Gate 1 — Architecture review

- Reproducible Python 3.12 environment.
- Secrets are external to Git.
- Supported model identifiers and model capability registry.
- Bounded tool loop and documented tool permissions.
- Website health check.
- Messaging adapter interface, even when pilot credentials are not yet available.

### Gate 2 — Knowledge review

- Every knowledge item has a stable ID, title, owner/publisher, URL or internal provenance, geography, language, review date, and confidence.
- ESDU-specific claims cite an AUB/ESDU source or an approved internal ESDU document.
- Time-sensitive opportunities, prices, weather, pest alerts, and regulations are not presented as timeless static facts.
- Arabic content receives expert review; machine translation alone is not approval.

### Gate 3 — Safety and governance review

- Agronomic advice distinguishes source-backed guidance from model synthesis.
- Pesticide, veterinary, food-safety, and emergency advice uses escalation language and avoids unsupported dosage or treatment claims.
- Data collection follows minimization and informed-consent rules.
- Feedback and telemetry exclude secrets and unnecessary personal information.

### Gate 4 — Pilot release

- Priority tests meet the 90% target.
- Retrieval benchmark meets the 80% target in both languages and for Akkar-specific questions.
- Controlled median response time is at most 10 seconds.
- Controlled availability is at least 95%.
- Spending limits, model allowlists, incident response, and rollback procedures are active.

### Gate 5 — Contractual closeout

- Stakeholder, adoption, session, and feedback evidence is complete.
- RRO is approved.
- Internal percentage report reconciles with the workbook without substituting proxy metrics for contractual indicators.
