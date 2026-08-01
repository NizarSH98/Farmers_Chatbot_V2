# Pilot Provider Setup Checklist

This is the owner-operated sequence for the authenticated web pilot. Do not paste
real credentials into GitHub files, issues, email, or chat.

## 1. Approvals and named owners

- [ ] Confirm the organization that is responsible for pilot data.
- [ ] Name a privacy contact and incident owner.
- [ ] Have the bilingual agreement in `farmers_chatbot/legal.py` reviewed by the
  institutional privacy/legal owner. Code review is not legal approval.
- [ ] Confirm that the pilot accepts only public or non-sensitive agricultural
  material and invited adult/institutionally supervised testers.
- [ ] Approve the 30-day retention period and the list of subprocessors: Google,
  Streamlit/Snowflake, Supabase, OpenRouter and selected model providers. Add Meta
  and Render only when WhatsApp is enabled.
- [ ] Review each provider's terms, privacy notice, DPA availability, region, and
  breach-contact process against AUB/ESDU policy.

## 2. GitHub release control

- [ ] Continue development through pull requests into `pilot`.
- [ ] Create `release/pilot-2026-08` from a CI-passing `pilot` commit.
- [ ] Protect both branches. Require the CI check, block force pushes and deletion,
  and require at least one approving reviewer for the release branch.
- [ ] Do not store deployment credentials in GitHub unless a future deployment job
  actually needs them. Streamlit and Render keep their own managed secrets.
- [ ] Point Streamlit at the release branch, not the changing `pilot` branch.

Streamlit Community Cloud monitors its configured GitHub branch and deploys new
commits automatically. The freeze control is therefore a protected release branch
with no commits during the session, not an assumed auto-deploy toggle.

## 3. Supabase

- [ ] Create a dedicated project; use Pro for the formal test if pilot evidence
  must be recoverable. Enable MFA on administrator accounts.
- [ ] Select the institutionally approved region and record it.
- [ ] Apply `migrations/001_pilot_schema.sql` in SQL Editor.
- [ ] Create `pilot-files` with Public bucket disabled. Add no anonymous storage
  policies. The server-side service key bypasses RLS and must never reach a browser.
- [ ] Use the shared pooler session-mode URI for the persistent Streamlit backend
  when required by its network path. Use the direct connection for controlled
  migrations and database dumps when reachable.
- [ ] Put the database password, project URL, service-role key, and connection URI
  in the password manager and Streamlit managed secrets only.
- [ ] Before and after the test, make a logical database export. Back up required
  Storage objects separately because database backups cover Storage metadata, not
  the object contents.
- [ ] Follow `docs/DATA_PORTABILITY.md`; verify the SHA-256 manifest and rehearse a
  restore to a separate database/private storage target before collecting pilot data.
- [ ] Test two-user isolation and deletion using the deployed application.

## 4. Google OIDC

- [ ] Configure an External Google OAuth application.
- [ ] Request only `openid profile email`.
- [ ] Register the exact local and deployed callback URLs ending in
  `/oauth2callback`.
- [ ] Generate a long random Streamlit cookie secret and keep it in managed secrets.
- [ ] For internal testing, set `ACCESS_POLICY=email_allowlist` and list the exact
  tester emails. Keep `ADMIN_EMAILS` separate. Use `google_any` only after the
  public-access, abuse, agreement, support, and privacy review.

## 5. OpenRouter

- [ ] Create a pilot-only API key with a spending limit.
- [ ] Turn off prompt/completion logging and any use of inputs/outputs.
- [ ] Disable routing to providers that train on prompts.
- [ ] Allow only reviewed models and providers whose retention policy is acceptable.
- [ ] Start with conservative quotas and inspect cost/latency after the rehearsal.
- [ ] Never send intentionally sensitive data even when a provider advertises
  zero-data-retention controls.

## 6. Streamlit Community Cloud

- [ ] Create the app from `release/pilot-2026-08`, entry point `rag_chatbot.py`,
  Python 3.12.
- [ ] Copy `deployment/streamlit_secrets.toml.example` into managed secrets and
  replace every placeholder.
- [ ] Confirm `APP_ENV=pilot`; the application must refuse to start if Google,
  Postgres, Supabase Storage, OpenRouter, the privacy contact, or admin is missing.
- [ ] Record app URL, commit SHA, prompt/knowledge version and migration version.
- [ ] Check logs for errors but never print credentials or user message content.

## 7. Release gates

- [ ] Complete Google login, agreement, logout, export, account deletion, retention,
  two-user isolation, private downloads, prompt injection, safety, artifact, Arabic,
  five-user load, rollback and backup-restore checks.
- [ ] Confirm no critical authentication, privacy, safety, or tool-permission issue.
- [ ] Keep `pilot` open for improvements; promote only reviewed CI-passing commits
  to the frozen release branch outside a testing session.
- [ ] Add Render and Meta only after the web release passes. Use an always-on paid
  Render service for webhook reliability and keep Render auto-deploy disabled.

Official operational references are linked from `docs/PILOT_DEPLOYMENT_RUNBOOK.md`.
