# Evaluation data boundary

`benchmark_questions.jsonl` is the legacy, training-visible retrieval check. It
is useful for regression only and cannot support product-superiority claims.

`fixtures/` contains synthetic public records that exercise schemas and the
scorer. They contain no production knowledge and must never be indexed by RAG.

Real hidden cases belong outside the repository, or temporarily under ignored
`evaluation/hidden/`. Run the split guard before scoring. Only aggregate reports
may be copied into `reports/generated/`; prompts and case-level answer text must
remain in the protected evaluation location.

The authoritative workflow and metric definitions are in
`docs/EVALUATION_HARNESS.md`.
