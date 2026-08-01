# ESDU Internal AI Pilot Deployment Runbook

Last updated: 2026-07-30
Release freeze target: 2026-08-05  
Pilot size: up to 15 testers and five concurrent users

The web workspace is the release requirement. WhatsApp is a stretch channel and
must not block web release. All real credentials belong in provider-managed secrets,
never Git, issue trackers, documents, or chat.

## 1. Current release state

- Development branch: `pilot`; deployment target: protected
  `release/pilot-2026-08` created from a passing commit.
- GitHub CI gates compilation, Ruff, tests, release preflight, retrieval evaluation,
  dependency consistency, and the local service benchmark.
- Web entry point: `rag_chatbot.py`.
- WhatsApp entry point: `whatsapp_api:app`.
- Postgres migration: `migrations/001_pilot_schema.sql`.
- Render blueprint: `render.yaml` with automatic deployment disabled.
- Streamlit secrets template: `deployment/streamlit_secrets.toml.example`.
- Provider-neutral export/restore procedure: `docs/DATA_PORTABILITY.md`.
- Contractual workbook: explicitly excluded from Git/deployed runtime.
- Local automated gate: run and record the current test count for each release SHA.
- Candidate bilingual retrieval gate: 30/30, 100% overall and by language.
- Local retrieval-fallback benchmark: 3 ms median, 100% success over 30 requests.

These local results are not substitutes for connected-model latency, live
authentication/privacy testing, controlled availability, ESDU approval, stakeholder
participation, or contractual achievement.

## 2. Local release gate

Use Python 3.12:

```powershell
python -m pip install -r requirements-dev.txt
python -m compileall -q farmers_chatbot rag_chatbot.py mcp_server.py whatsapp_api.py
python -m ruff check .
python -m pytest -q
python scripts/evaluate_retrieval.py
python scripts/benchmark_service.py --iterations 30
```

Run the web app locally without Google login:

```powershell
Copy-Item .env.example .env
streamlit run rag_chatbot.py
```

For local Google OIDC, set `AUTH_MODE=google`, create
`.streamlit/secrets.toml` from `.streamlit/secrets.toml.example`, and register:

```text
http://localhost:8501/oauth2callback
```

## 3. Supabase setup

1. Create a dedicated pilot Supabase project in the approved region.
2. Record the project URL, service-role key, and hosted Postgres pooler URI in the
   password manager.
3. Open SQL Editor and execute `migrations/001_pilot_schema.sql`.
4. In Storage, create a bucket named `pilot-files` and keep **Public bucket**
   disabled.
5. Do not add anonymous read/write policies. The server uses the service role,
   checks database ownership first, and uses user-scoped object paths.
6. Set database backups and project spending alerts appropriate to the pilot.
   Database backups do not contain the private Storage object bytes, so back up
   required objects separately.
   Run `scripts/pilot_data_portability.py` before the rehearsal and verify the
   database dump, every private object, and the SHA-256 manifest.
7. Test with two users:
   - user A cannot read user B's project, conversation, document, or artifact;
   - a deleted item cannot be fetched using the prior path;
   - history survives an application restart/redeployment;
   - 30-day cleanup removes private content and anonymizes older metrics.

Do not release if the app silently falls back to hosted SQLite. In Streamlit
Community Cloud, `DATABASE_URL`, `SUPABASE_URL`, and
`SUPABASE_SERVICE_ROLE_KEY` must all be present.

## 4. Google OAuth setup

1. In Google Cloud, configure the OAuth consent screen as **External**.
2. Publish the app for verified Google accounts.
3. Request only `openid`, `profile`, and `email`.
4. Create a Web application OAuth client.
5. Register the local callback and the exact deployed callback:

```text
http://localhost:8501/oauth2callback
https://YOUR-APP.streamlit.app/oauth2callback
```

6. For the internal test, set `ACCESS_POLICY=email_allowlist` and configure the
   invited testers in `ALLOWED_EMAILS`. Keep administration separate through
   `ADMIN_EMAILS`. Reconsider `google_any` only before wider public access.
7. Verify login, consent, logout, denied unverified email claims, and that the
   persistent database key is `issuer + sub`, not email.

## 5. Streamlit Community Cloud deployment

1. Connect Streamlit Community Cloud to the GitHub repository.
2. Select protected branch `release/pilot-2026-08` and entry point
   `rag_chatbot.py`.
3. Use Python 3.12.
4. Copy `deployment/streamlit_secrets.toml.example` into the managed secrets
   editor and replace placeholders.
5. Use a pilot-only OpenRouter key with a spending cap and model allowlist.
6. Deploy and record:
   - Git commit SHA;
   - app URL;
   - deployment time;
   - knowledge/prompt version;
   - configured model IDs;
   - database migration version.
7. Community Cloud automatically follows commits on its configured branch. Freeze
   the protected release branch during the ESDU session and continue improvements
   on `pilot`.
8. Keep the prior tested release commit SHA as the rollback target.

## 6. Web release gates

The web release is allowed only when all are true:

- unauthenticated requests cannot access workspace content;
- Google login/logout/consent work on the deployed URL;
- the approved agreement version, privacy contact, data export, and account
  deletion work;
- two-account isolation passes for projects, chats, files, and artifacts;
- history survives logout and redeployment;
- deletion makes content and private files inaccessible;
- prompt-injection content in uploads cannot override safeguards;
- live source links belong to the server registry;
- high-risk/current claims show a verified citation or an explicit verification
  failure;
- DOCX/XLSX artifacts open and contain date, assumptions, units, and sources;
- the approved 30-question bilingual retrieval set remains at or above 80%;
- a five-user, 30-request connected workload has at least 90% priority test success
  and median end-to-end latency no greater than 10 seconds;
- a controlled two-hour check records at least 95% availability;
- no critical authentication, privacy, safety, or tool-permission defect remains.

Record usefulness, correctness, source quality, clarification quality, artifact
usefulness, latency, and failure type per answer. Update percentages only from those
records.

## 7. Render and Meta WhatsApp test channel

Start only after the web gates pass.

1. Create a Render web service from `render.yaml`.
2. Supply managed secrets:
   - `DATABASE_URL`;
   - `OPENROUTER_API_KEY`;
   - `META_APP_SECRET`;
   - `META_VERIFY_TOKEN`;
   - `META_ACCESS_TOKEN`;
   - `META_PHONE_NUMBER_ID`;
   - `WHATSAPP_ID_SECRET`.
3. Confirm `GET /healthz` returns `status=ok` and
   `whatsapp_configured=true`.
4. In the Meta developer app, configure the callback:

```text
https://YOUR-RENDER-SERVICE.onrender.com/webhooks/whatsapp
```

5. Use the same `META_VERIFY_TOKEN` for webhook verification.
6. Subscribe to WhatsApp message events and use only Meta's test number and
   approved tester numbers.
7. Validate:
   - invalid signatures return 401;
   - a wrong phone-number ID returns 400;
   - duplicate message IDs do not produce a second answer;
   - text works in English and Arabic;
   - `/new`, `/help`, `/mode`, and `/feedback` work;
   - long answers split safely and include source links;
   - quotas and trusted-search fallback are visible;
   - the database contains only an HMAC identifier, never the raw phone number.

The raw phone number is held in process memory only while sending the reply. Web and
WhatsApp conversations are deliberately separate.

## 8. Freeze, rollback, and incident handling

1. Tag the tested commit or record the immutable SHA in the release record.
2. Make no commits to the protected Streamlit release branch during testing and
   keep Render automatic deployment disabled.
3. Keep the previous tested Streamlit commit and Render version available.
4. If an authentication, cross-user access, unsafe tool, or source-verification
   defect appears, stop testing, revoke exposed tokens if applicable, and roll back.
5. After the session, export sanitized metrics, record defects/owners, and decide
   whether the pilot can continue.

## 9. Deferred after internal feedback

Voice-note transcription, cross-channel linking, shared projects, public links,
conversation branching, permanent personal memory, Google Drive, presentations,
arbitrary code execution, production MCP over HTTP, and production WhatsApp
business-number onboarding remain out of scope.

## 10. Official provider references

- Streamlit OIDC authentication:
  https://docs.streamlit.io/develop/concepts/connections/authentication
- Streamlit managed secrets:
  https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management
- Streamlit automatic GitHub updates:
  https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app
- Supabase database connections and poolers:
  https://supabase.com/docs/guides/database/connecting-to-postgres
- Supabase Storage access control:
  https://supabase.com/docs/guides/storage/security/access-control
- Supabase database backups:
  https://supabase.com/docs/guides/platform/backups
- OpenRouter data collection and provider logging:
  https://openrouter.ai/docs/guides/privacy/data-collection
  and https://openrouter.ai/docs/guides/privacy/provider-logging
- GitHub deployment environments and protected secrets:
  https://docs.github.com/en/actions/concepts/workflows-and-actions/deployment-environments
