# Project Privacy Policy

**Application:** {{APP_NAME}}

**Version:** {{LEGAL_VERSION}}

**Operator named for this deployment:** {{OPERATOR}}

**Privacy contact:** {{PRIVACY_CONTACT}}

**Approval status:** DRAFT — the responsible institution and lawful basis must be confirmed before public production use.

## 1. Coverage and responsibility

This policy explains how personal information is handled throughout the project
lifecycle: research and design, development, demonstrations, internal and field
testing, deployment, operation, support, evaluation, replication, archiving, and
retirement. It covers the web application, project workspaces, retrieval and tool
activity, feedback, generated artifacts, and enabled messaging or media channels.

The operational project name is {{OPERATOR}}. The final legal data controller,
institutional accountability, and authority to use affiliated names must be
documented in the deployment approval record before public production use. The
contact for this deployment is {{PRIVACY_CONTACT}}. This policy supports, but does
not replace, review under applicable Lebanese law and institutional requirements.

## 2. Information we process

Depending on the features you use, the service may process:

- **Account information:** identity-provider issuer and stable account identifier,
  verified email address, display name, role, agreement version, acceptance time,
  preferences, account creation, and last activity time. We do not receive or
  store your Google password.
- **Workspace content:** projects, instructions, conversations, questions,
  answers, uploaded documents, images, extracted text, generated artifacts, and
  source or tool records.
- **Feedback and evaluation data:** ratings, comments, issue categories,
  verification status, language, and voluntary session observations.
- **Technical and security data:** timestamps, channel, model and mode, latency,
  success or error type, quota events, trusted-search counts, consent events,
  security logs, and limited diagnostics. Hosting and identity providers may also
  process IP address, browser, device, and cookie data under their policies.
- **Messaging identifiers:** when a messaging channel is enabled, a secret-keyed
  hash derived from the external identifier, message IDs for deduplication, and
  message content. The application database does not store the raw WhatsApp phone
  number, although the channel provider necessarily processes it to deliver the
  message.
- **Media:** supplied images and, if enabled, voice or transcription content. The
  service is not intended to collect biometric templates or medical records.

## 3. Information you should not provide

Do not provide government identifiers, passwords or API keys, payment records,
health records, exact home locations, confidential participant or institutional
records, private phone numbers, or third-party personal data. Do not upload a
person's image, voice, or information without authority and an appropriate notice.
Current deployments accept only public or non-sensitive agricultural material
unless a separately approved protocol explicitly permits additional categories.

If sensitive information is submitted accidentally, stop using that conversation,
delete it through the available controls, and contact {{PRIVACY_CONTACT}} when
assistance is needed. Security logs and downstream provider copies may follow
separate expiry schedules.

## 4. Why we process information

Information is processed to:

- authenticate users, maintain private workspaces, and enforce roles and quotas;
- understand requests, retrieve relevant material, generate answers and artifacts,
  and preserve conversation continuity;
- provide source transparency, safety warnings, clarification, and referrals;
- operate, secure, troubleshoot, back up, restore, and improve the service;
- measure accessibility, correctness, usefulness, latency, source quality, and
  project outcomes;
- investigate abuse, privacy or security incidents, and enforce the agreement;
- meet approved project, research, audit, contractual, and legal obligations; and
- produce anonymous aggregate statistics and lifecycle documentation.

Personal information is not sold. It is not used for third-party advertising or
unrelated direct marketing. A new purpose that is incompatible with this policy
requires an updated notice, an appropriate lawful basis, and renewed consent when
required.

## 5. Basis for processing and consent

The service records affirmative acceptance before normal use. Depending on the
approved deployment and applicable rules, processing may rely on consent,
necessary service operation, legitimate project interests with safeguards, a
legal obligation, or an approved public or research task. The responsible
institution must confirm and document the applicable basis before public
production use.

You may withdraw consent by deleting your account or contacting
{{PRIVACY_CONTACT}}. Withdrawal does not make earlier lawful processing unlawful,
but it normally ends access to features that require an account and workspace.

## 6. AI, retrieval, and automated processing

Questions, limited recent conversation context, relevant retrieved passages,
project instructions, and supplied images may be sent to configured AI or search
providers to generate a response. Only the context judged necessary for the task
should be sent. Uploaded documents are treated as untrusted user material and do
not become approved shared knowledge merely by being uploaded.

The service uses automated processing to generate decision support, not to make
legal, employment, credit, insurance, benefit, disciplinary, or similarly
significant decisions about users. Tool and model outputs are subject to human
review and the limitations in the User Agreement.

## 7. Providers and recipients

Configured providers may include:

- Google for OpenID Connect account authentication;
- Streamlit Community Cloud/Snowflake or another approved application host;
- PostgreSQL and private object-storage providers, currently compatible with
  Supabase but designed for export and migration;
- OpenRouter and the selected model providers for AI generation and approved web
  search;
- Microsoft Edge text-to-speech when online speech output is enabled;
- Meta WhatsApp Cloud API and Render or another approved webhook host when the
  messaging channel is enabled; and
- reviewed public scientific, agricultural, economic, food-security, and
  government sources reached through bounded retrieval tools.

Providers receive only the data needed for their enabled function and operate
under their own terms and privacy documentation. Before production, the operator
must maintain a current provider register, review retention and training settings,
restrict credentials and models, and complete any required data-processing
agreements. Personal information may also be disclosed when lawfully required or
necessary to protect users, security, rights, or the service.

## 8. International processing

Cloud and AI providers may process information outside Lebanon, including in the
United States or other provider regions. Laws and government-access rules may
differ from those in Lebanon. Region selection, contractual safeguards, provider
logging, model training settings, and international-transfer requirements must be
reviewed in each deployment approval. Do not submit sensitive information even
when a provider offers zero-retention controls.

## 9. Retention and deletion

The configured identifiable-content retention period is up to
**{{RETENTION_DAYS}} days**. Conversations, files, artifacts, and inactive account
records are deleted or de-identified according to the active schedule. Users may
delete individual content or their account earlier. Query events may remain only
after the user link is removed, and genuinely anonymous aggregate metrics may be
retained for project evaluation and accountability.

Provider backups, fraud-prevention records, OAuth grants, delivery records, and
security logs may expire later under documented provider schedules. Before each
production phase, the operator must publish the actual schedule, test deletion,
and set a disposal date for exports and backups. Legal holds or documented audit
requirements may temporarily suspend deletion where authorized.

## 10. Security

Safeguards include verified identity claims, separate authorization rules,
least-privilege administrator access, private storage, owner-scoped database
queries, time-limited downloads, input and file validation, bounded tools,
rate limits, secret management, logging minimization, retention jobs, integrity
checked backups, CI tests, and incident rollback procedures. No system is
perfectly secure. Do not use the service for information whose disclosure would
create serious harm.

Suspected incidents should be reported promptly to {{PRIVACY_CONTACT}}. The
operator must document triage, containment, credential rotation, notification,
recovery, and lessons learned according to the approved incident process.

## 11. Your choices and rights

Subject to applicable law and verified identity, you may request to:

- access and export active workspace records;
- correct inaccurate account or project information;
- delete conversations, files, artifacts, or the account;
- withdraw consent or object to a use where applicable;
- ask how information was used, shared, retained, or sourced; and
- raise a complaint with the responsible institution or competent authority.

The application provides self-service export and deletion controls. Uploaded
binaries and generated files may be downloaded separately from their cards. Send
requests that cannot be completed in the application to {{PRIVACY_CONTACT}}. We
may need to verify identity and preserve a minimal request record for security and
accountability.

## 12. Evaluation, research, and publication

Anonymous aggregate measures may be used to evaluate performance, accessibility,
knowledge gaps, safety, adoption, and project obligations. Identifiable research,
recording, quotation, publication, model training, or reuse outside normal service
operation requires a separate protocol, appropriate ethics or institutional
approval, and additional consent when required. Declining optional research use
must not remove access to ordinary service functions unless participation itself
is the approved research activity and this is explained in advance.

## 13. Children and supervised use

The service is not directed to unsupervised children. A person under 18 may use it
only under an approved adult or institutional process. Do not knowingly submit a
child's personal information without documented authority, necessity, safeguards,
and the notices and consent required by the applicable process. If such data is
found outside an approved process, contact {{PRIVACY_CONTACT}} for deletion.

## 14. Policy changes and contact

Material changes receive a new version and require renewed acceptance. Previous
versions and approval records should be retained for accountability without
retaining unnecessary user content. The version displayed in the application is
the active version for that deployment.

Privacy, access, correction, deletion, safety, and security inquiries may be sent
to {{PRIVACY_CONTACT}}.
