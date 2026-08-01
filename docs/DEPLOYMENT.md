# Deployment and Pilot Release

Last updated: 2026-08-01

> For the authenticated Streamlit/Supabase/Google and Meta test-number pilot,
> use `docs/PILOT_DEPLOYMENT_RUNBOOK.md`. This older checklist remains as the
> general release baseline.

## 1. Pre-release approvals

- Confirm whether the product name may use ESDU/AUB branding.
- Approve knowledge items and assign version/review dates.
- Approve the bilingual retrieval benchmark.
- Select Telegram or WhatsApp for the contractual messaging pilot.
- Approve privacy notice, consent text, retention period, and incident owner.
- Confirm the expected pilot concurrency used for the ≤10-second target.
- Confirm the controlled availability test window.

## 2. Provider controls

- Create an OpenRouter key dedicated to the pilot.
- Set a strict spending limit and reset interval.
- Apply a model allowlist.
- Keep the management key separate from the inference key.
- Record the approved provider data policy.
- Verify the configured model IDs, reasoning levels, and tool support before release.

## 3. Streamlit Community Cloud

1. Push the approved release to GitHub.
2. Create a Streamlit Community Cloud app.
3. Select the repository, approved branch, and `rag_chatbot.py`.
4. Select Python 3.12 in Advanced settings.
5. Add root-level secrets:

   ```toml
   OPENROUTER_API_KEY = "deployment-only-key"
   APP_ENV = "pilot"
   APP_PUBLIC_URL = "https://your-app.streamlit.app"
   OPENROUTER_DEFAULT_MODEL = "google/gemini-3.6-flash"
   OPENROUTER_ALLOWED_MODELS = "google/gemini-3.6-flash,xiaomi/mimo-v2.5,minimax/minimax-m3,moonshotai/kimi-k3"
   OPENROUTER_FAST_MODEL = "google/gemini-3.6-flash"
   OPENROUTER_DEEP_MODEL = "moonshotai/kimi-k3"
   OPENROUTER_ENFORCE_ZDR = true
   OPENROUTER_DATA_COLLECTION = "deny"
   MAX_QUERIES_PER_SESSION = 25
   MAX_QUERIES_PER_DAY_GLOBAL = 300
   COOLDOWN_SECONDS = 3
   ```

6. Set `SUPABASE_URL` to the project origin only:
   `https://PROJECT-REF.supabase.co`, with no dashboard or API path.
7. Deploy and review build logs.
8. Execute smoke, retrieval, safety, latency, and fallback checks.

The local SQLite store is suitable for development and a single-instance controlled run. It is not the final evidence store for multi-replica or durable production use.

## 4. MCP deployment

- Keep `stdio` for local integration.
- Use Streamable HTTP only behind authentication, TLS, restrictive CORS/host checks, request limits, and monitoring.
- Do not expose the feedback tool to anonymous internet clients.
- Do not add general shell, filesystem, or arbitrary URL tools.
- Version tool schemas and record MCP client/server versions in release evidence.

## 5. Messaging channel

The repository contains a channel-neutral contract but no provider credentials or public webhook.

Before implementation:

- choose Telegram or WhatsApp;
- document platform terms and personal-data flow;
- define user consent and opt-out;
- decide how external user IDs are pseudonymized;
- configure webhook verification and replay protection;
- define message length, voice-note, retry, and escalation behavior;
- test Arabic display and low-bandwidth use.

## 6. Release verification

- `python -m pytest -q`
- `python scripts/evaluate_retrieval.py`
- 90% or more of approved priority backend tests pass.
- 80% or more approved retrieval relevance overall and by language.
- Median end-to-end response is at most 10 seconds at approved pilot load.
- Controlled availability is at least 95%.
- No critical unresolved safety, secret, or tool-permission issue.
- Online/offline voice boundaries are visible.
- Source and knowledge versions appear in the release record.
- Rollback commit/version is recorded.

## 7. Post-release evidence

- Export sanitized performance and availability reports.
- Keep stakeholder/outreach records in an access-controlled project system.
- Log each feedback session with consent-aware attendance categories.
- Validate and prioritize feedback.
- Calculate the 80% feedback-resolution indicator only from validated high-priority items.
- Update the RRO with actual cost, staffing, performance, adoption, and adaptation evidence.
