# Web UI source and provenance audit

Audit date: 2026-08-11

## Scope and conclusion

This audit covers first-party code under `apps/web`, especially
`components/ChatWorkspace.tsx`, `app/globals.css`, and `lib/api.ts`. It records
what the repository can establish; it does not infer authorship or license from
visual similarity.

The repository establishes when the UI entered this project and which packaged
dependencies it uses. It does **not** currently identify the external GitHub
repository that the project owner recalls consulting or adapting. Therefore the
provenance of distinctive first-party component structure and CSS remains
unresolved. Nothing in this audit should be read as a claim that the UI is an
unmodified third-party work, or that it was independently authored.

## Evidence recorded

- Commit `e28b20dc0edfe0955d2a7970b9628540f2bde082` is the first commit touching
  `apps/web`. It added the complete Next.js UI on 2026-08-02. Its message names
  no upstream repository and records `Claude Opus 4.6` as a co-author.
- Git history before that commit contains no earlier `apps/web` version from
  which file ancestry can be established.
- At the introduction commit, the Git blob IDs were:
  - `ChatWorkspace.tsx`: `b648480bfd424a726f4848f3a496b864a6e0a201`
  - `globals.css`: `a45c1b9d87fe814bdc2e4c0344a65690b9188bd6`
  - `api.ts`: `727ae9a0c0aca477841ee094be5e603b0778ec32`
- No copyright notice, SPDX identifier, “adapted from” note, or upstream source
  URL was found in the first-party UI files at that commit.
- The root repository declares MIT for this project's software. That declaration
  does not by itself establish permission for any unidentified upstream code.
- Direct runtime packages are declared in `apps/web/package.json` and resolved
  in `package-lock.json`. Installed package metadata reports MIT for Next.js,
  React, React DOM, React Markdown, Remark GFM, and the Supabase clients, and ISC
  for Lucide React. These packages have explicit package identities and are not
  part of the unresolved first-party-code question.
- The current UI contains no checked-in image, icon, or font asset copied into
  `apps/web`; icons come from Lucide React and the layout references Google-hosted
  Noto Sans Arabic at runtime.

## Required disposition

Before public release, the owner should search browser history, GitHub stars and
forks, local clones, AI-session transcripts, and development notes for the
remembered repository URL. Once found, record its exact commit, license, copied
or adapted files, required notices, and a file-by-file disposition here.

If the source cannot be identified, treat `ChatWorkspace.tsx` and `globals.css`
as requiring a clean replacement before public release. Reimplement their
documented behavior from RAISE requirements and tests without copying the
present component organization or styling expressions. Standard framework and
package usage may be retained under the packages' respective licenses.

Until either attribution review or replacement is complete:

- do not describe the UI as wholly original or provenance-cleared;
- do not remove this audit as part of normal refactoring;
- do not add branding or public distribution claims that depend on cleared UI
  provenance; and
- keep new UI work behavior-driven and record any new external reference with a
  URL, version/commit, license, and affected files at the time it is introduced.

## Review record template

When a candidate repository is identified, append a row for each reviewed file:

| RAISE file | Candidate URL and commit | Similarity finding | Candidate license | Required notice/action | Reviewer/date |
|---|---|---|---|---|---|
| _Pending_ | _Pending_ | _Pending_ | _Pending_ | Identify, attribute, replace, or clear | _Pending_ |
