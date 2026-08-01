# Internal Deployment Readiness and Review

Last updated: 2026-08-01

These are internal planning estimates based only on repository evidence and the
local gates completed on this date. They are not legal approval, deployment
evidence, user acceptance, or contractual achievement.

| Area | Done | Evidence | Remaining |
|---|---:|---|---|
| Local web workspace | 94% | Auth boundary; persistent chats/projects; upload, history, feedback, modes, artifacts, quotas, export/deletion/retention; public pre-login legal pages; headless health check | Browser accessibility/usability review and real 20–30-user exercise |
| Identity, privacy, and lifecycle policy implementation | 91% | Verified OIDC claims; `issuer + sub`; open-registration and separate-admin rules; ownership checks; private paths; bilingual lifecycle agreement/privacy policy; versioned consent; approval checklist | Name legal controller, AUB/ESDU authority and DPO review, verified-domain OAuth route, live two-account isolation/deletion/redeployment test |
| Assistant, RAG, and trusted-source behavior | 86% | Versioned novice-oriented prompt, evidence ladder, project retrieval, trusted registry, bounded search fallback, risk checks, 30/30 candidate bilingual retrieval | ESDU approval, connected-model scientific/economic/safety set, live citation audit |
| Tools, artifacts, and local MCP | 90% | Bounded tools, DOCX/XLSX validators, formula protection, artifact quota, local stdio MCP | ESDU review of templates and MCP client smoke on frozen commit |
| WhatsApp test-channel code | 83% | FastAPI signature/phone-ID checks, deduplication, HMAC identity, lifecycle consent notice, commands, quotas, splitting, mocked tests | Render/Meta credentials and live Arabic/test-number run after web release |
| Automated and local validation | 93% | 45/45 tests, dependency check, compilation, lint, release preflight, 30/30 candidate retrieval, 60-request/30-worker local fallback at 100% success, 4 ms median and 11 ms p95 | Connected cloud/model load test, controlled two-hour availability, live auth/privacy/artifact gates |
| Operational web deployment | 35% | Portable migrations/storage abstraction, managed-secret templates, freeze/rollback/runbook and provider checklist exist | Supabase, Google OAuth, Streamlit setup; domain/publication decision; policy approval; deployed gates; resource-capacity approval or fallback host |
| WhatsApp operational deployment | 15% | Deployment blueprint and webhook runbook exist | Meta and Render owner setup; only after web passes |

## Roll-up

- **Local-only software completion: 92%.**
- **Code/configuration readiness for web deployment: 89%.**
- **Operational web deployment completion: 35%.**
- **Full internal-test readiness: 72%.**
- **Contractual achievement evidenced in this repository: 0%.**

The first two percentages describe software. Operational completion requires live
provider evidence. Contractual achievement remains zero because the repository
does not prove stakeholder participation, four feedback sessions, validated issue
resolution, or approval of the final replication and rollout output. The logframe
owner must reconcile any approved evidence held elsewhere.

## Release blockers and owner actions

1. Record the legal controller and obtain ESDU/RAISE authority and AUB privacy
   review using `docs/POLICY_APPROVAL_CHECKLIST.md`.
2. Decide the verified-domain route for a Google OAuth application open to any
   verified account; the current operator cannot verify `aub.edu.lb`.
3. Create/configure Supabase, Google, Streamlit, and capped OpenRouter credentials
   only in managed secrets.
4. Complete live two-account isolation, retention, deletion, source, safety, and
   artifact checks.
5. Rehearse 20–30 simultaneous connected users. Community Cloud remains
   conditional until this passes; use an approved paid container fallback if it
   does not.
6. Record a two-hour availability run, immutable release SHA, URLs, provider/model
   versions, and rollback target.
7. Exercise Meta's test-number channel only after the web release passes.
