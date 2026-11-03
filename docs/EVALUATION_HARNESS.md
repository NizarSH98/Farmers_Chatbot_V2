# RAISE evaluation harness

## Purpose and evidence boundary

The v1 harness produces reproducible measurements from frozen cases and
assessor-annotated system outputs. It does not call an AI judge, retrieve
knowledge, or claim that any system meets a release threshold. Changing a judge,
rubric, source set, tool entitlement, prompt, or model version requires a new run
identity; changing a schema requires a new schema version.

The existing `evaluation/benchmark_questions.jsonl` remains a public regression
check. It is visible during development and is not a hidden product benchmark.
The files under `evaluation/fixtures/` are synthetic schema examples, not
agricultural knowledge and not evidence of quality.

## Versioned inputs

- `case.v1`: prompt identity and split, language group, graded relevant evidence,
  exact expected graph paths, citation-required claims, and safety/escalation
  expectations.
- `run.v1`: one system output assessment per case, including ranked evidence,
  graph paths, claim/evidence entailment judgments, safety outcomes, normalized
  quality, success, cost, and latency.
- `pairwise.v1`: blind preference for two systems on one case and one reviewer.
- `ablations.v1`: the frozen retrieval/tool capabilities used for internal
  ablations. External matched and raw baselines receive explicit run-specific
  system IDs rather than silently inheriting an ablation definition.

`citations[].entails` and `quality_score` are assessor labels. They must not be
copied from the system's self-assessment. Quality uses a pre-registered rubric
normalized to 0–1 and should combine calibrated human labels with automated
labels only after agreement is measured.

Every scored report records the harness version and SHA-256 hashes of its case,
run, pairwise, and ablation inputs. The scorer contains no wall-clock timestamp,
uses sorted output, fixed rounding, and seeds pairwise resampling, so identical
inputs and arguments produce identical report bytes.

## Metric definitions

- **Recall@k:** macro-average fraction of graded-relevant evidence IDs retrieved
  in the first `k` results. Cases without retrieval gold are excluded.
- **MRR@k:** macro-average reciprocal rank of the first relevant evidence item.
- **nDCG@k:** macro-average normalized discounted cumulative gain, with graded
  gain `2^relevance - 1` and logarithmic rank discount.
- **Graph-path accuracy:** per-case Jaccard score over exact ordered path-token
  sequences, then macro-averaged. Extra paths and missing paths are penalized.
- **Citation precision:** accepted entailing claim/evidence pairs divided by all
  cited pairs. A pair is accepted only when the assessor marks entailment and
  the evidence is in that claim's frozen accepted set.
- **Citation recall:** citation-required claims with at least one accepted pair
  divided by all citation-required claims.
- **Safety:** count/rate of explicit critical violations or predicted unsafe
  actions matching the case's prohibited actions; escalation recall and
  precision are reported separately. Safety is a hard gate, not averaged into a
  composite quality score.
- **Language gap:** absolute difference, in points, between mean assessor quality
  for `arabic` and `english` case groups. Native Arabic, Lebanese, Arabizi, and
  code-switched coverage must be identified in case metadata and the dataset
  release notes; translated-only coverage is insufficient.
- **Efficiency:** success rate, total/mean cost, cost per successful case, and
  nearest-rank p50/p95 time-to-first-token and end-to-end latency.
- **Pairwise preference:** ties count as 0.5. Multiple reviewers are first
  averaged within a case, then the confidence interval bootstraps cases with
  replacement. The seed and number of resamples are recorded.

Missing run records are not silently dropped: they reduce run coverage and count
as unsuccessful with zero retrieval, graph, citation, and escalation credit.
Missing assessor, cost, or latency labels have explicit coverage counts.

## Hidden-set workflow

1. Author native and adversarial cases in access-controlled storage independent
   of corpus/prompt authors. Freeze a dataset ID, version, rubric, source
   snapshot, and case-file hash.
2. Keep hidden case files outside Git. If a local temporary copy is unavoidable,
   place it only under ignored `evaluation/hidden/` and remove it after scoring.
3. Produce system outputs with matched source/tool access where the comparison
   requires it. Persist exact model/provider identifiers, parameters, prompts,
   source release, tool policy, retries, tokens, cost, and timings with the run.
4. Blind answer order and system identity before human review. Preserve raw
   reviewer labels so agreement can be calculated independently.
5. Run the separation guard. It rejects tracked hidden files, overlapping IDs,
   wrong split labels, and normalized exact-prompt overlap. It cannot detect all
   semantic paraphrases, so dataset owners must also perform a manual leakage
   review.
6. Score each system from the same frozen cases. Publish aggregate metrics and
   uncertainty; do not publish hidden prompts, expected answers, or case-level
   answer text.

Guard example:

```powershell
python scripts/evaluate_system.py guard `
  --public-cases evaluation/fixtures/public_cases.v1.jsonl `
  --hidden-cases D:/secure/raise-hidden-v1.jsonl `
  --repo-root . `
  --hidden-root evaluation/hidden
```

Synthetic scoring example:

```powershell
python scripts/evaluate_system.py score `
  --cases evaluation/fixtures/public_cases.v1.jsonl `
  --runs evaluation/fixtures/example_run.v1.jsonl `
  --pairwise evaluation/fixtures/example_pairwise.v1.jsonl `
  --ablations evaluation/ablations.v1.json `
  --system-id example_system `
  --dataset-id synthetic-contract-fixture `
  --dataset-version 1 `
  --top-k 10 `
  --bootstrap-seed 1729 `
  --bootstrap-resamples 2000 `
  --output reports/generated/evaluation_example.json
```

The example output only proves that the evaluator works. Release thresholds and
comparative claims are evaluated later on the approved hidden dataset with
pre-registered acceptance gates.
