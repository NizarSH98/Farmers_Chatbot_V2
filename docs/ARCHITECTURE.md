# Target Architecture

Last updated: 2026-08-20

> Current authority: Next.js on Vercel plus one FastAPI service on Render and
> Supabase-managed data. Streamlit has been removed. WhatsApp remains disabled
> until the canonical web soak passes. See `docs/CANONICAL_PILOT_RUNBOOK.md`.

## Product boundary

The product is an Arabic-first, bilingual agricultural knowledge assistant for Akkar and other Lebanese rural contexts. It should remain useful on low-bandwidth devices and should make the origin, date, geography, and confidence of advice visible.

## Components

1. **Knowledge layer**
   - Versioned Markdown/JSON knowledge items instead of an opaque PDF-only corpus.
   - Stable source IDs and chunk metadata.
   - Separate static validated guidance from dynamic information.
   - A versioned bilingual ontology. The active release holds 260 typed
     entities, 649 aliases, and 494 passage-backed relations across 32 entity
     types and 33 relation types.
2. **Retrieval layer**
   - Dense and sparse fusion over the activated release, with contextual hybrid
     and two-hop graph routes above it.
   - The ablation ladder (`scripts/run_ablations.py`) measures what each layer
     contributes; `scripts/profile_graph.py` describes the graph itself.
   - Deterministic source cards and confidence signals.
3. **Assistant layer**
   - One asynchronous `AssistantEngine` and one `ProviderClient` for every
     channel.
   - `TurnCoordinator` owns consent, idempotency, atomic quota/cost
     reservation, persistence, exact finalization, and recovery.
   - `ToolExecutor` owns schemas, risk/channel budgets, and timeouts.
   - Quick, Standard, Deep, and Source-only modes.
   - Reasoning effort is sent only to models whose capability registry allows it.
   - A bounded tool loop; tools never execute merely because model text resembles a command.
4. **Tool layer**
   - Search validated knowledge.
   - Read a source record.
   - Read logframe status.
   - Record structured, consent-aware feedback.
   - Direct live-source connectors fetch only exact endpoints approved in the
     versioned registry. Live connectors remain disabled until source/API
     authorization and reliability review.
5. **MCP layer**
   - The same safe tool implementations are exposed through an MCP server.
   - Local default transport is `stdio`; authenticated Streamable HTTP is a deployment option.
   - The MCP server does not expose arbitrary filesystem, shell, URL-fetch, or database-query tools.
6. **Channel layer**
   - Next.js is the canonical Arabic-first web interface.
   - Streamlit has been removed.
   - WhatsApp is mounted but disabled; its router reuses the canonical service
     container, coordinator, engine, provider, tools, and persisted turns. The
     root module is only a one-release import wrapper.
7. **Evidence layer**
   - Structured operational events, feedback status, benchmark reports, performance reports, and release records.
   - Personal data is kept outside the public repository.

## Interaction flow

```text
Farmer
  -> Web / approved messaging channel
  -> language + mode selection
  -> retrieval and safe internal tools
  -> model generation (when configured)
  -> answer + source cards + limitations + escalation
  -> optional feedback event
  -> logframe evidence reports
```

## Thinking and effort modes

| Mode | Intended use | Retrieval | Reasoning effort | General knowledge | Tool budget |
|---|---|---:|---|---|---:|
| Quick | Short routine question on weak connections | 4 passages | minimal/low | Clearly labeled | 1 round |
| Standard | Default farmer guidance | 6 passages | medium | Clearly labeled | 2 rounds |
| Deep | Planning or multi-factor comparison | 9 passages | high | Clearly labeled | 3 rounds |
| Source-only | Auditable guide lookup | 10 passages | low | Disabled | 1 round |

Internal reasoning is never displayed as hidden chain-of-thought. The interface may show a concise answer plan, tools used, sources used, and limitations.

## Deployment profiles

### Local connected

- Local retrieval and application runtime.
- OpenRouter for generation.
- Optional online TTS.

### Local offline

- Local retrieval.
- Local model runtime through a configurable OpenAI-compatible endpoint.
- Local speech-to-text and text-to-speech models.
- No dynamic web tools.

### Pilot cloud

- Next.js on Vercel and one FastAPI backend on Render.
- Supabase PostgreSQL/pgvector, authentication, and private object storage.
- Deployment-specific API key with spending cap and model allowlist.
- Persistent feedback/evidence store.
- Monitoring and controlled access.

## Locked implementation decisions

- Next.js is the only interface; Streamlit is removed.
- WhatsApp remains disabled until the web soak; its thin FastAPI router is
  already mounted in the canonical backend.
- PostgreSQL hosts lexical, vector, graph, provenance, and tenant data, and is
  the only persistence backend; no Neo4j service is added.
- OpenRouter remains the model and embedding gateway.

## Decisions still requiring team approval

- Approved model/provider data-retention policy.
- Whether the strengthened guide is formally an ESDU publication or an ESDU-supported project knowledge base.
- Expert owners for crops, livestock, water, food safety, business/value chains, and Arabic editorial review.
- Approved dynamic sources and update frequency.

