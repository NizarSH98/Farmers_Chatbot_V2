# RAISE product experience specification

Purpose: this document is the build contract for the user-facing application
and the backend behavior that supports it.

Status: **draft baseline for owner review before implementation**

The decisions below replace vague goals such as making the chatbot more
user-friendly. A change is in scope only when it supports one of these flows or
acceptance criteria.

## 1. Product definition

RAISE is an Arabic-first, bilingual agricultural decision-support assistant for
farmers, field facilitators, and small agri-food operators, including people
using an AI chat product for the first time.

The primary job is:

> Help a user turn an agricultural question or observation into a clear,
> source-backed next step, while making missing information, uncertainty,
> safety limits, and escalation needs obvious.

RAISE is not a general-purpose chatbot, an autonomous farm-management agent, or
a replacement for an agronomist, veterinarian, laboratory, engineer,
food-safety professional, or competent authority.

## 2. Product principles

1. **Guide before generating.** Ask one concise clarification when missing crop,
   location, growth stage, timing, symptoms, or user goal changes the answer.
2. **Answer first, evidence beside it.** Give the direct answer and actions in
   the main thread; connect important claims to inspectable sources.
3. **Never fake certainty.** Use source-backed, mixed, or needs-verification
   labels, never invented confidence percentages.
4. **One obvious next action.** Advanced controls do not compete with the task.
5. **Preserve work.** Drafts, uploads, context, and messages survive restart.
6. **Recover in place.** Retry/edit never silently deletes the question.
7. **Arabic is first-class.** RTL and mixed-language content are tested.
8. **Low-bandwidth by default.** Text is core; rich media is optional.

## 3. Users and first-session outcome

Primary users:

- Arabic-speaking farmer with limited experience using AI.
- Field facilitator helping a farmer formulate a question.
- Small agricultural or food-processing operator seeking practical guidance.

Secondary users are agronomists, knowledge reviewers, and project
administrators.

Without reading a manual, a new user must be able to understand the product
boundary, choose Arabic or English, ask using a guided example, answer one
clarification, receive actions/cautions/sources, and continue or save the work.

## 4. Canonical information architecture

### Desktop

~~~text
Left sidebar          Main conversation                    Context drawer
---------------       --------------------------------     ----------------
New conversation     Conversation/project header          Sources
Search                Messages and clarification cards     Project files
Recent chats          Empty-state starters                 Answer details
Projects              Sticky composer
Settings/account
~~~

- The left sidebar is persistent and collapsible.
- The conversation is the only primary work surface.
- The right drawer is closed by default and opens for sources or project
  context. It is not a permanent third column on smaller screens.
- Administration remains a separate **/admin** area.

### Mobile

- A top bar opens the conversation/project drawer.
- Messages occupy the full width.
- Sources/project context open as a bottom sheet or full-screen drawer.
- The composer stays attached to the bottom safe area.
- Touch targets are at least 44 by 44 CSS pixels.

## 5. Frontend requirements

### 5.1 Application shell

The shell contains the RAISE identity/language, a dominant **New conversation**
action, title search, conversations grouped by recency, projects, bottom
settings/account, and the current project name in the chat header.

Conversation menus contain Rename, Archive, and Delete. Delete requires
confirmation and states whether files or only the conversation are affected.

### 5.2 Empty conversation

Show a greeting, one sentence explaining how to ask, and four starters:

- Diagnose a crop symptom.
- Plan irrigation or field work.
- Check treatment or food-safety precautions.
- Ask questions about project documents.

Starters prefill the composer; they do not submit automatically.

Suggested English composer text:

> Describe the crop, location, growth stage, and what you observed.

Suggested Arabic composer text:

> صف المحصول والموقع ومرحلة النمو وما الذي لاحظته.

Boundary below the composer:

> RAISE can make mistakes. Check important decisions and follow local labels and
> competent authorities.

### 5.3 Composer and answer style

The sticky composer supports multiline text, Send, Stop, Retry, an image
thumbnail, filename/remove action, size/type validation, upload progress, and a
preserved draft after failure. Enter sends and Shift+Enter adds a line.

Provider model names are not primary novice-facing controls:

| UI label | Backend mode | Meaning |
| --- | --- | --- |
| Guided (Recommended) | standard | balanced, source-backed default |
| Quick | quick | shorter response with fewer retrieved items |
| Detailed | deep | more retrieval, comparison, and verification |
| Sources only | source_only | reviewed/project evidence; no unsupported general claims |

The selected answer style affects the next message and remains visible near the
composer. Provider models belong in advanced settings only if intentionally
exposed by the operator.

### 5.4 Turn and clarification states

Render these states in text rather than an indefinite spinner:

1. Sending question
2. Understanding the request
3. Checking reviewed knowledge/project files
4. Preparing the answer
5. Verifying important claims
6. Complete
7. Clarification required
8. Cancelled
9. Failed with retry

Ask at most one material clarification at a time. Its card contains the exact
question, 2–5 useful choices, **Something else**, a short reason, and **Skip
with assumptions** only when safe. High-risk missing information cannot be
bypassed for convenience.

### 5.5 Assistant answer

Every substantive answer uses this visible order:

1. **Direct answer** — one short paragraph.
2. **What to do** — numbered practical steps.
3. **What to watch for** — cautions, stop conditions, or uncertainty.
4. **Sources** — inline markers and a source-summary action.
5. **Useful next questions** — no more than three.

Each answer has Copy, Helpful/Not helpful, Retry, Edit original question,
source-backed status, and optional technical details. Retry keeps the prior
answer. Editing branches or clearly warns which later messages will change.

### 5.6 Sources and reliability

An inline marker opens its exact source card. Cards show available title,
publisher, excerpt, date, language, review status, source type, and
open/download action.

Backend-derived answer states:

- **Source-backed** — important claims use reviewed/project evidence.
- **Mixed sources** — evidence plus allowed general model knowledge.
- **Needs verification** — current/high-risk information was not verified.
- **Unable to answer safely** — required evidence or context is missing.

The frontend never calculates confidence.

### 5.7 Projects and files

A project contains a name, optional instructions, files, and conversations.

Required flow:

1. Create a project with name and optional goal text.
2. Open a project home showing instructions, files, and conversations.
3. Upload documents with filename, size, status, and error state.
4. Start chat with a visible **Using project: …** indicator.
5. Download or delete owned files.
6. Edit project name/instructions.
7. Delete only after listing affected data.

Project content never leaks into another project or ordinary conversation. Team
sharing and cross-project memory are out of scope.

### 5.8 Onboarding, settings, and accessibility

Onboarding has a concise agreement summary, language choice, and three
dismissible tips available later from Help. Settings contain language, default
answer style, supported response preferences, export, sign out, and account
deletion.

Requirements:

- WCAG 2.2 AA contrast, keyboard access, and visible focus.
- Semantic headings, buttons, dialogs, statuses, and labels.
- aria-live announces stages without reading every streamed token.
- RTL tested at 360, 768, 1024, and 1440 pixels.
- Reduced-motion support; errors never rely only on color.

## 6. Frontend implementation boundaries

**ChatWorkspace.tsx** is too large to remain the unit of change. Phase 0 splits
it without changing behavior:

~~~text
components/app/AppShell
components/navigation/ConversationSidebar
components/chat/ChatHeader
components/chat/MessageList
components/chat/AssistantMessage
components/chat/ClarificationCard
components/chat/Composer
components/sources/SourcesDrawer
components/projects/ProjectHome
components/settings/SettingsDialog

hooks/useSession
hooks/useConversations
hooks/useTurnStream
hooks/useProjects
hooks/useUploads
~~~

Rules:

- visual components receive typed data/actions and do not call fetch;
- API calls remain in lib/api or feature-specific API modules;
- server state and temporary UI state remain separate;
- dialogs/drawers are reusable accessible primitives;
- Arabic/English copy stays centralized;
- each extracted feature gets focused component/hook tests.

## 7. Backend requirements

### 7.1 API responsibilities

The backend owns normalized identity, consent/access policy, ownership checks,
turn idempotency/quotas/persistence/cancellation, clarification, retrieval,
generation/verification, reliability metadata, feedback, and metrics.

The frontend owns presentation and temporary interaction state. It never
decides whether an answer is safe, source-backed, or authorized.

### 7.2 Backend module boundaries

**web_api.py** should become a thin composition root plus routers:

~~~text
api/routers/auth.py
api/routers/config.py
api/routers/conversations.py
api/routers/projects.py
api/routers/files.py
api/routers/turns.py
api/routers/feedback.py
api/routers/admin.py

services/turn_service.py
services/project_service.py
services/file_service.py
~~~

Existing auth, storage, persistence, retrieval, and assistant-pipeline modules
remain authoritative. Do not add wrappers that merely rename one call.

### 7.3 Turn processing contract

One turn follows this order:

1. authenticate, authorize, and validate consent;
2. normalize input and reserve an idempotency key;
3. classify language, intent, domain, location, risk, and currentness;
4. request one clarification if a material field is missing;
5. retrieve project/reviewed evidence with release identity;
6. generate under the selected answer-style policy;
7. verify required claims/citations and apply safety rules;
8. persist result and provider accounting;
9. emit completion and make the same result retrievable after reconnect.

Normal API startup never runs migrations or knowledge bootstrap.

### 7.4 Typed stream events

Keep server-sent events with this stable vocabulary:

| Event | Required fields |
| --- | --- |
| turn.accepted | turn ID, conversation ID |
| turn.stage | stage key, localized label key |
| clarification.required | question, options, allow-skip, reason |
| source.found | normalized source |
| answer.delta | text delta |
| answer.warning | warning key and display text |
| turn.completed | final answer envelope |
| turn.cancelled | turn ID, partial-result policy |
| turn.failed | stable error code, retryable flag, request ID |

Old clients ignore unknown events. Event names/payloads receive contract tests.

### 7.5 Final answer envelope

The durable completed turn exposes:

~~~text
turn_id, status, language
answer_markdown, direct_answer
action_steps[], cautions[], assumptions[]
follow_up_questions[], citations[]
reliability_label, reliability_reasons[]
retrieval_route, knowledge_release_id
model_id, request_id, timings
~~~

The API contract—not frontend Markdown parsing—owns these semantics.

### 7.6 Reliability policy

- Reviewed claims keep stable evidence/source identifiers.
- Every citation marker resolves to a returned citation.
- Important cited claims are checked for support before completion.
- General model knowledge is allowed only by mode and labelled as mixed.
- Current facts use approved trusted search or state they were not verified.
- High-risk missing context causes clarification, limitation, or referral.
- Pesticide, veterinary, food-safety, legal, and financial guidance includes
  the applicable local-label or competent-authority boundary.
- Retrieval failure is visible and never silently becomes source-backed.
- Logs exclude raw user content, credentials, tokens, and signed URLs.

### 7.7 API capabilities needed by the UI

Keep current endpoint families. Add capabilities only in the matching phase:

- cursor pagination and query/project/archive conversation filters;
- project name/instruction updates;
- file processing status and stable failure reasons;
- turn cancellation and reconnect/resume;
- retry/branch linkage;
- normalized citation/reliability objects;
- stable machine error codes with user-safe messages.

All lists are ownership-scoped. Retriable writes are idempotent.

### 7.8 Observability

Record request/turn/conversation and pseudonymous user IDs, mode, language,
stage durations, retrieval route/count/release, reliability outcome,
provider/model/token/cost totals, and cancellation/error code. Do not record raw
content. Product failures belong in turn state and structured logs; health
remains infrastructure-focused.

## 8. Admin experience

The separate admin area must:

- require admin role server-side;
- show releases and projection state;
- confirm/audit activation or rollback;
- inspect evidence neighborhoods readably;
- review changes without raw JSON by default;
- show operational errors without secrets.

Raw JSON may remain in an advanced technical panel.

## 9. Delivery sequence

### Phase 0 — behavior-preserving cleanup

Split ChatWorkspace.tsx and web_api.py along the boundaries above; add API/event
types and tests; preserve behavior and appearance.

Exit: existing tests pass and endpoint behavior is unchanged.

### Phase 1 — novice chat foundation

Implement shell, sidebar, empty state, composer, stages, error recovery, answer
actions, and responsive RTL accessibility. Hide provider complexity.

Exit: a new user completes a source-backed chat on desktop/mobile in Arabic and
English without assistance.

### Phase 2 — reliability presentation

Implement structured answers, reliability labels, sources drawer,
clarification, retry/edit/branch, and reconnect/resume.

Exit: every important source and degraded state is understandable in the UI.

### Phase 3 — project workflow

Integrate projects into navigation; add project home, instruction editing, file
status, project conversations, and destructive confirmations.

Exit: project data is isolated and survives refresh/restart.

### Phase 4 — admin usability and field validation

Replace raw admin controls with reviewed forms; run moderated Arabic/English
field sessions and resolve validated priority failures.

Exit: product owner approves local acceptance before remote deployment.

## 10. Acceptance scenarios

1. First-time Arabic user understands a well-specified answer/actions/sources.
2. Underspecified crop-symptom question asks one useful clarification.
3. High-risk question limits unsafe advice when evidence/context is missing.
4. Source marker opens the exact supporting source card.
5. Network interruption preserves the question and resumes or offers retry.
6. Stop cancels without corrupting the conversation.
7. Edit/retry retains history according to the visible branch policy.
8. Project file is uploaded, processed, cited, downloaded, and owner-deleted.
9. Refresh and Compose restart preserve conversations/projects/files.
10. Arabic RTL and English LTR pass keyboard, screen-reader, mobile, contrast.
11. No-key local mode returns a clearly labelled source-backed fallback.
12. Admin endpoints reject normal users regardless of hidden frontend links.

## 11. Product measures

Track first-question completion, clarification completion/abandonment,
source-open rate, feedback with reason, retries/errors by code, median/p95 time
to visible stage and completed answer, answers by reliability label, high-risk
referrals, Arabic/English task-success gap, and project-file processing/cited
use. Do not optimize for message count or time spent.

## 12. Explicit non-goals

- Copying another product's branding or proprietary visual details.
- Autonomous purchases, farm actions, messages, or external-system changes.
- Custom password authentication or public provider/model shopping.
- Shared/team projects or cross-project personal memory.
- Voice-first or WhatsApp-first experience.
- General web browsing without an approved source policy.
- A visual artifact editor.
- Remote deployment before local product acceptance.

## 13. Reference patterns

RAISE uses familiar conventions but applies its own users and safety boundary:

- OpenAI, [Projects in ChatGPT](https://help.openai.com/en/articles/10169521-projects-in-chatgpt):
  projects group chats, files, and instructions.
- OpenAI, [Searching the web with ChatGPT](https://help.openai.com/en/articles/9237897):
  citations are inspectable and important sources need verification.
- Anthropic, [What are projects?](https://support.anthropic.com/en/articles/9517075-what-are-projects):
  project-scoped conversations, instructions, knowledge, and RAG.
- Google, [Upload and analyse files in Gemini Apps](https://support.google.com/gemini/answer/14903178):
  composer attachments need explicit upload errors and limits.
- Microsoft Research, [Guidelines for Human-AI Interaction](https://www.microsoft.com/en-us/research/wp-content/uploads/2019/01/Guidelines-for-Human-AI-Interaction-camera-ready.pdf):
  set expectations, show status, support correction, and fail understandably.

## 14. Decision before implementation resumes

The owner should approve or amend this statement:

> Build the Guided/Quick/Detailed/Sources-only agricultural chat described
> here, with projects and visible source reliability; do not expand into
> general-purpose agent features during this cycle.

Once approved, Phase 0 is the only implementation starting point.
