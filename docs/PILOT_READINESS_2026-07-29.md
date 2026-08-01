# Pilot Readiness and Internal Review

Last updated: 2026-07-29

Percentages separate software readiness from contractual achievement. They are
based only on repository evidence, local reports, and the green GitHub CI run available on this date.

| Area | Done | Evidence | Remaining |
|---|---:|---|---|
| Local web workspace | 92% | Auth boundary, persistent chats/projects, uploads, history, feedback, modes, artifacts, quotas, deletion, and retention implemented; Streamlit smoke passes | Browser usability review and real five-user exercise |
| Identity and privacy implementation | 88% | Verified OIDC claim validation, `issuer + sub` identity, access policies, ownership checks, private paths, HMAC WhatsApp IDs, retention tests | Live Google consent/logout and live Supabase isolation/redeployment test |
| Assistant, RAG, and trusted-source behavior | 86% | Versioned novice-oriented prompt, evidence ladder, project retrieval, trusted registry, bounded live-search fallback, risk checks, 30/30 bilingual retrieval | ESDU approval, connected-model scientific/economic/safety set, live citation audit |
| Tools, artifacts, and local MCP | 90% | Bounded tools, DOCX/XLSX validators, formula protection, artifact quota, local stdio MCP | ESDU review of generated templates and MCP client smoke on frozen commit |
| WhatsApp pilot code | 82% | FastAPI endpoints, signature and phone-ID checks, deduplication, HMAC identity, commands, quotas, splitting, mocked webhook tests | Render/Meta credentials and live Arabic/test-number end-to-end run |
| Automated/local validation | 90% | GitHub CI and local gates pass: 36/36 tests, lint, compile, 100% candidate retrieval, 3 ms local fallback median | Connected model/load test, two-hour availability, live auth/privacy gates |
| Operational deployment | 30% | `pilot` branch is pushed with green CI; migrations, secrets templates, Render blueprint, rollback/runbook exist | Supabase, Google, Streamlit, Render, Meta setup and live release gates |

## Roll-up

- **Local-only software completion: 89%.**
- **Code/configuration readiness for deployment: 86%.**
- **Operational deployment completion: 30%.**
- **Full internal-pilot readiness: 70%.**
- **Contractual achievement evidenced in this repository: 0%.**

The contractual percentage remains zero because software and draft documents do not
prove 40–50 stakeholder participation, four feedback sessions, 80% resolution of
validated high-priority feedback, or approval of the RRO. Off-repository evidence
may change that figure once reconciled by the logframe owner.

## Release blockers

1. User-owned provider credentials and accounts are not configured.
2. ESDU has not approved the expanded pilot question set or local knowledge.
3. No connected five-user load result exists.
4. No controlled two-hour availability result exists.
5. No live two-account Google/Supabase privacy test exists.
6. The Meta test-number channel has not been exercised end to end.
7. Provider deployment versions, URLs, and rollback targets are not yet frozen after live gates.
