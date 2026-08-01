# Project Policy Approval Checklist

Status: **DRAFT — not institutionally or legally approved**

Policy version: `project-2026-08-v1`

Applies to: the complete RAISE-ESDU Farmer Assistant lifecycle, including design,
testing, deployment, operation, evaluation, replication, and retirement

This checklist is an operational control, not legal advice. The application may
use the draft for an authorized internal evaluation, but it must not describe the
policy as AUB-approved or the service as an approved public AUB service until the
reviews below are recorded.

## Documents to review

- `legal/USER_AGREEMENT.en.md`
- `legal/USER_AGREEMENT.ar.md`
- `legal/PRIVACY_POLICY.en.md`
- `legal/PRIVACY_POLICY.ar.md`

The application renders these files before sign-in and again before consent. Its
managed `CONSENT_VERSION` must exactly match the policy version in the code.

## Confirmed project decisions

- Operational name: RAISE-ESDU
- Application name: RAISE
- Public privacy contact: supplied by the project operator through managed secrets
- Access: any verified Google account may register
- Administrators: one separately configured email
- Current upload rule: public or non-sensitive material only
- Expected internal-test concurrency: 20–30 simultaneous users
- Default identifiable-content retention: up to 30 days

## Required approval before public production use

- [ ] Name the legal data controller. Do not assume that `RAISE-ESDU`, ESDU, or
  AUB is the controller solely because a project or faculty account uses those
  names.
- [ ] Obtain written authorization from the responsible ESDU/RAISE project
  authority for the service, operator name, branding, user population, and public
  registration.
- [ ] Submit the four documents, data-flow summary, provider register, retention
  schedule, and incident procedure to the AUB Data Protection Officer at
  `dpo@aub.edu.lb`; record the response and required changes.
- [ ] Confirm the lawful basis for account, workspace, feedback, evaluation, and
  messaging data under Lebanese law and AUB requirements.
- [ ] Confirm the approved process for users under 18 or disable their access.
- [ ] Confirm whether project evaluation is ordinary service evaluation or human-
  subjects research requiring ethics/IRB review and separate consent.
- [ ] Approve international processing, including Streamlit Community Cloud
  hosting in the United States and each configured AI/model provider.
- [ ] Review provider terms, retention/training settings, data-processing
  agreements, breach contacts, and deletion limitations for Google, Streamlit/
  Snowflake, Supabase, OpenRouter and selected models; add Render and Meta only
  when WhatsApp is enabled.
- [ ] Approve the 30-day schedule for application records and document the actual
  expiry schedules for backups, provider logs, OAuth records, and security logs.
- [ ] Approve the privacy contact, complaint route, incident owner, response
  times, account-deletion process, and data-request identity checks.
- [ ] Confirm the right to use all local knowledge, project documents, AUB/ESDU/
  RAISE names, and any logos in each deployment.
- [ ] Review Arabic and English for equivalent meaning and accessible language.

## Google public-registration prerequisite

For a Google OAuth application published for any Google account, create a public
application home page and privacy-policy page on a domain controlled and verified
by the responsible operator. Because the current project operator does not
control the `aub.edu.lb` domain, use one of these approved routes:

1. ask AUB/ESDU to host or approve the pages and complete domain verification; or
2. register a low-cost project domain controlled by the project, publish the
   pages there, and have the responsible authority approve the identity and
   branding used on those pages.

The Streamlit application also exposes the policy at `?legal=privacy` and the
agreement at `?legal=terms`, but its `streamlit.app` address does not establish
ownership of an AUB domain. Keep the internal URL unlisted until the approval and
OAuth publication route is confirmed.

## Approval record

| Decision | Name and role | Organization | Date | Evidence/link | Status |
|---|---|---|---|---|---|
| Project authority and branding |  |  |  |  | Pending |
| Privacy/data protection |  |  |  |  | Pending |
| Legal/lawful basis |  |  |  |  | Pending |
| Research/ethics applicability |  |  |  |  | Pending |
| Security and incident process |  |  |  |  | Pending |
| Production release owner |  |  |  |  | Pending |

When all applicable rows are approved, remove the DRAFT statement only through a
reviewed policy-version change. Changing the text requires a new version and
renewed user acceptance.

## Reference points for reviewers

- AUB privacy statement: https://www.aub.edu.lb/Pages/privacy.aspx
- Lebanese Law No. 81/2018 listing: https://www.banqueduliban.gov.lb/laws.php
- Google OAuth production readiness:
  https://developers.google.com/identity/protocols/oauth2/production-readiness/policy-compliance
- Google OAuth app audience and publication:
  https://support.google.com/cloud/answer/15549945
- Streamlit authentication:
  https://docs.streamlit.io/develop/concepts/connections/authentication
- Streamlit Community Cloud resource limits:
  https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app
