# Data retention and the research interaction record

Purpose: explain what the application keeps, for how long, how the pilot
dataset is exported, and how a record is traced back to a person when needed.
The user-facing promise is in `legal/PRIVACY_POLICY.*.md` section 9 and
`legal/USER_AGREEMENT.*.md` sections 6 and 9 (agreement `project-2026-11-v3`).

## Why there are two windows

The pilot evaluation (roadmap D3 dataset, due 15 Feb 2027, and the Phase 4
performance evaluation) needs every question, answer, and feedback item from the
whole field-testing period, linked to the same participant over time. Before
agreement `project-2026-11-v3`, everything was deleted after 30 days. Questions
from December would have been gone by mid-January, and usage could not be
followed per participant.

The fix keeps the interaction record longer but removes direct identifiers early.

| Window | Setting | Hosted range | What happens when it ends |
| --- | --- | --- | --- |
| Files and contact details | `RETENTION_DAYS` | 1–30 (default 30) | Uploaded documents, chat images, and generated artifacts are deleted from storage and the database. Attachment references inside kept messages are scrubbed and marked `expired`. WhatsApp delivery records are deleted. Accounts inactive this long lose their email and name; `name` becomes the participant code. |
| Interaction record | `RESEARCH_RETENTION_DAYS` | 30–730 (default 365), not below `RETENTION_DAYS` | Conversations, messages, turn analysis, and model-call records are deleted. Query events and feedback lose their user link and remain only as anonymous aggregates. Accounts inactive this long are deleted. |

The hosted guard (`farmers_chatbot/hosted_runtime.py`) refuses to start outside
those ranges. The API applies both windows at startup and then every 24 hours
(`_retention_loop` in `farmers_chatbot/web_api.py`). Logic and its tests:
`farmers_chatbot/retention.py`, `tests/test_research_retention.py`.

A person who signs in again after de-identification gets their email and name
back from the identity provider. Their account, participant code, and history
are unchanged, because the account is matched on issuer and subject.

## Participant codes

Every account receives a random code such as `RAISE-7K3QX9` (migration
`20261110_0008`). The alphabet omits 0, O, 1, I, and L so a code read aloud is
not misrecorded. The code:

- carries no personal information;
- is shown to the participant in **Settings → Account**;
- is the only identifier in the research dataset.

**Linking a code to a person.** The field team records each participant's code
in the controlled stakeholder tracker during onboarding
([STAKEHOLDER_TRACKER_SCHEMA.md](STAKEHOLDER_TRACKER_SCHEMA.md)). That tracker,
not this database, is the only place where codes meet names and phone numbers.
While an account is active, an administrator can also look up a code by email:

```sql
SELECT participant_code FROM users WHERE email = 'person@example.org';
```

After de-identification only the tracker can make the link.

## Exporting the research dataset

| Where | Command | Output |
| --- | --- | --- |
| Local stack | `.\scripts\raise.ps1 research-export` | `pilot_exports\research-<stamp>\` |
| Lightsail VPS | `bash deploy/vps/raise-vps.sh research-export` | `/opt/raise/pilot_exports/research-<stamp>/` |

Both run `scripts/export_research_dataset.py` inside the API container. It
writes four UTF-8 CSV files (Excel shows the Arabic correctly) and a
`manifest.json` with row counts and SHA-256 checksums.

| File | One row per | Main columns |
| --- | --- | --- |
| `participants.csv` | account | participant_code, role, channel, consent_version, created_at, last_seen_at, contact_on_file |
| `interactions.csv` | question answered | participant_code, created_at, language, question, answer, intent, domain, risk, location, citation_count, clarification_count, status |
| `query_events.csv` | request | participant_code (blank once unlinked), occurred_at, language, mode, duration_ms, ttft_ms, success, tokens, estimated_cost_usd |
| `feedback.csv` | feedback item | participant_code, category, rating, comment, status, priority |

Email, name, identity-provider subject, and internal user IDs are never
exported. Filter `role = 'admin'` out of participant analysis; those are staff
accounts.

Handling rules:

1. Download the folder (for example with `scp`) and delete it from the server.
2. Store it only in the project's access-controlled storage, never in Git.
   `pilot_exports/` is git-ignored.
3. Free text (`question`, `answer`, `comment`) is exported as typed. Review it
   and redact anything identifying before sharing it outside the project team.
4. Exports follow the same `RESEARCH_RETENTION_DAYS` limit. Record a disposal
   date for each export.
5. When a participant deletes their account or asks to withdraw, remove their
   code from exports already made.

## Deletion requests

- **Delete account (in the app):** immediately removes the account, its
  conversations, files, and feedback, and unlinks its query events. Future
  exports no longer contain the participant.
- **Withdrawal by message to the privacy contact:** look up the participant's
  code in the tracker, delete the account from the database, and remove the
  code from earlier exports.

## Approvals still required

The retention design is implemented, but it is not an approval. Before the
pilot collects real data:

- [ ] AUB IRB or the AUB Data Protection Officer confirms that the
      pseudonymous interaction record and its retention period fit the approved
      research protocol and consent process.
- [ ] ESDU confirms `RESEARCH_RETENTION_DAYS` (default 365 covers the pilot,
      the April 2027 evaluation, and the final report).
- [ ] The field team adds `participant_code` to the stakeholder tracker and to
      the onboarding script.
- [ ] Exports have a named custodian and a disposal date.
