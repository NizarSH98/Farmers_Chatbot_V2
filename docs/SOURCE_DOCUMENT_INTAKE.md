# Source Document Intake and Conflict Review

Use this process for the new larger source document. A document is never added to
the approved RAISE/ESDU knowledge layer merely because it was uploaded or is more
detailed than the current guide.

## Safe staging

1. Put the original file under `knowledge_base/incoming/` locally. This directory
   is ignored by Git so copyright-restricted or internal source material is not
   deployed accidentally.
2. Record the title, author/institution, publication date, version, URL or owner,
   permitted use, geographic scope, and reviewer.
3. Remove personal data, participant lists, phone numbers, signatures, precise
   household locations, and confidential annexes before AI processing.
4. Confirm that ESDU/RAISE has permission to process and use the material.

## Evidence and conflict classification

Review claims against `knowledge_base/guide.json` and `sources.json`. Classify each
candidate claim as one of:

- `supports`: consistent evidence that strengthens an existing item;
- `adds`: locally useful information not currently represented;
- `narrows`: applies only to a crop, altitude, soil, season, or locality;
- `conflicts`: disagrees with an existing value, recommendation, or safety rule;
- `supersedes`: a newer authoritative version replaces older material;
- `dynamic`: price, weather, regulation, registration, alert, or other information
  that must be obtained live rather than embedded as a timeless fact;
- `reject`: unsupported, unsafe, out of scope, or lacking usage rights.

Do not resolve a conflict by silently choosing the longer or newer-looking text.
Record both claims, their sources and dates, the affected locality, units, and a
named ESDU subject reviewer. High-risk pesticide, veterinary, food-safety, water,
engineering, and regulatory claims require an appropriate technical reviewer.

## Promotion into the knowledge base

Only approved claims are converted into structured items with a stable ID,
bilingual wording, evidence class, risk class, review status, review date, and
source IDs. Then:

1. update `knowledge_base/sources.json` and `guide.json`;
2. run `python scripts/build_guide.py`;
3. add bilingual benchmark questions for material new topics;
4. run the complete CI and retrieval gates;
5. obtain technical and Arabic field-language approval;
6. record the knowledge and application version in the release record.

Project uploads remain private, user-provided context and are always labelled as
non-authoritative. They do not modify the shared knowledge base.
