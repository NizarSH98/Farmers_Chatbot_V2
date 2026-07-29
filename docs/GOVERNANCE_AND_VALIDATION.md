# Governance and Validation Framework

Last updated: 2026-07-29

This document provides the three methodologies required by activity A.1.1.2. They are drafts until the designated ESDU/project reviewers approve them and meeting minutes record that decision.

## Methodology 1 — Evidence and knowledge lifecycle

### Purpose

Ensure that advice is traceable, geographically appropriate, current enough for its use, and explicit about uncertainty.

### Workflow

1. **Propose:** create a knowledge item with a stable ID and named subject owner.
2. **Source:** attach an authoritative public source or approved internal ESDU provenance.
3. **Scope:** label geography, crop/value chain, season, audience, language, and risk class.
4. **Draft:** write plain English and farmer-accessible Arabic without inventing missing detail.
5. **Technical review:** an assigned subject specialist checks accuracy and limitations.
6. **Field-language review:** an Akkar-facing reviewer checks terminology, dialect accessibility, and practicality.
7. **Approve:** record reviewer, date, version, and next review date.
8. **Publish:** include the item in the retrieval index.
9. **Monitor:** connect feedback and observed retrieval failures to the item.
10. **Retire or revise:** remove stale, disputed, or superseded content while preserving version history.

### Source classes

- **A — Authoritative:** ministry, LARI, AUB/ESDU, peer-reviewed research, FAO or other approved institutional source.
- **B — Validated field knowledge:** documented farmer/expert knowledge approved by an ESDU subject specialist and a field reviewer.
- **C — Contextual:** reputable background material useful for explanation but not sufficient for high-risk recommendations.
- **D — Unverified:** excluded from production retrieval.

### Review frequency

- Emergency, pest, disease, weather, price, grant, and regulation content: dynamic tool or explicit expiry.
- Production practices: review at least annually and after material alerts or field feedback.
- ESDU project descriptions: review when project status, scope, or evidence changes.
- Historical/context content: review every two years.

## Methodology 2 — Expert and participatory field validation

### Purpose

Combine technical correctness with the lived constraints, terminology, accessibility, and trust needs of Akkar farmers.

### Sampling

The 40–50 stakeholder cohort should be intentionally varied across:

- Akkar plain and upland/terraced contexts.
- Crop, greenhouse, orchard, livestock, dairy, herbs, and mixed farms.
- Women and men, younger and older farmers.
- Farmers, cooperatives, extension actors, input suppliers, processors, and local institutions.
- Different levels of literacy, smartphone familiarity, and connectivity.

### Four-session minimum structure

1. **Needs and language:** recurring decisions, terminology, trust, channel preference, and accessibility.
2. **Knowledge and retrieval:** benchmark real questions, source usefulness, missing local content.
3. **Usability and safety:** Arabic interface, voice, low-bandwidth use, escalation, and harmful-answer scenarios.
4. **Adoption and replication:** usefulness after iteration, channel fit, governance, and adaptation to other regions.

### Validation record

Each session records date, purpose, facilitator, consent method, participant count and stakeholder categories, anonymized findings, validated priorities, decisions, and follow-up owners. Names and contact details must not be committed to this repository.

### Acceptance

- Advice is understandable without technical translation by the facilitator.
- Users can identify which statements come from a source and which are model synthesis.
- High-risk questions lead to safe limitations and referral.
- Known local questions retrieve locally relevant passages.
- Validated high-priority feedback enters the resolution workflow.

## Methodology 3 — AI evaluation and release gates

### Test layers

1. **Unit tests:** language detection, parsing, chunking, retrieval, tool schemas, rate limits, and feedback validation.
2. **Integration tests:** model client mocked success/failure, tool-call loop, source-only enforcement, and MCP tools.
3. **Retrieval benchmark:** approved English/Arabic questions with expected topics and relevant source IDs.
4. **Answer review:** groundedness, citation correctness, completeness, local relevance, readability, and safety.
5. **Performance test:** expected pilot concurrency with median and tail latency.
6. **Availability test:** controlled probe schedule and documented maintenance exclusions.
7. **Adversarial test:** prompt injection, fabricated sources, dangerous chemical/veterinary advice, personal-data requests, and tool misuse.

### Release gates

- ≥90% of priority backend tests pass.
- ≥80% retrieval relevance on the approved benchmark, reported overall and by language.
- Median response time ≤10 seconds at agreed pilot load.
- ≥95% controlled availability.
- Zero unresolved critical safety or secret-exposure defects.
- Model IDs and tool capabilities verified against the provider before release.
- Knowledge-base version and approved reviewer list recorded.

### Change control

Every pilot release receives a version, change summary, knowledge-base version, test report, unresolved-risk list, rollback reference, and approval record. Emergency content changes may use an expedited review but require retrospective approval.

