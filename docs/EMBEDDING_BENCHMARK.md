# Embedding benchmark and vector cutover

Vector retrieval is disabled by default. `RAG_VECTOR_BENCHMARK_APPROVED=true`
is accepted only with a model and a supported 768- or 1,536-dimensional index.
This is an operational acknowledgement that the frozen bilingual benchmark
passed; it is not set by the benchmark script itself.

The checked-in candidate snapshot includes Gemini Embedding 2 Preview at 768
and 1,536 dimensions and the stable OpenAI Text Embedding 3 Large alternative
at the same dimensions. Refresh the manifest from OpenRouter's embeddings model
endpoint before every benchmark and record the observed date and current token
prices.

Prepare a hidden `case.v1` file and a separate JSONL corpus with one object per
line: `{"evidence_id":"...","text":"...","language":"ar-LB"}`. Relevant
evidence IDs in the cases must all resolve to this corpus. Neither file may be
used for ingestion or prompt development.

```powershell
python scripts/benchmark_embeddings.py `
  --cases D:/secure/raise-retrieval-v1.jsonl `
  --corpus D:/secure/raise-passages-v1.jsonl `
  --output reports/generated/embedding_benchmark_v1.json
```

The report allows vector cutover only when Recall@10 is at least 90%, the
Arabic/English nDCG gap is below five points, retrieval p95 is below 300 ms, and
the candidate is within one nDCG point of the best. Among those candidates it
selects the lowest estimated cost. If none passes, lexical, alias, and graph
retrieval remain active and no embedding model is configured.
