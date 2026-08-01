# Target Architecture

Last updated: 2026-07-29

## Product boundary

The product is an Arabic-first, bilingual agricultural knowledge assistant for Akkar and other Lebanese rural contexts. It should remain useful on low-bandwidth devices and should make the origin, date, geography, and confidence of advice visible.

## Components

1. **Knowledge layer**
   - Versioned Markdown/JSON knowledge items instead of an opaque PDF-only corpus.
   - Stable source IDs and chunk metadata.
   - Separate static validated guidance from dynamic information.
2. **Retrieval layer**
   - Bilingual lexical retrieval as the reproducible baseline.
   - Benchmark-driven upgrade path to multilingual embeddings and hybrid ranking.
   - Deterministic source cards and confidence signals.
3. **Assistant layer**
   - OpenRouter-compatible chat client.
   - Quick, Standard, Deep, and Source-only modes.
   - Reasoning effort is sent only to models whose capability registry allows it.
   - A bounded tool loop; tools never execute merely because model text resembles a command.
4. **Tool layer**
   - Search validated knowledge.
   - Read a source record.
   - Read logframe status.
   - Record structured, consent-aware feedback.
   - Future dynamic tools: LARI/MoA alerts, weather, market information, and referrals after source/API approval.
5. **MCP layer**
   - The same safe tool implementations are exposed through an MCP server.
   - Local default transport is `stdio`; authenticated Streamable HTTP is a deployment option.
   - The MCP server does not expose arbitrary filesystem, shell, URL-fetch, or database-query tools.
6. **Channel layer**
   - Streamlit website first.
   - Telegram/WhatsApp adapters call the same assistant service and governance rules.
   - Channel credentials and webhook deployment are external configuration.
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

- Streamlit or containerized web service.
- Deployment-specific API key with spending cap and model allowlist.
- Persistent feedback/evidence store.
- Monitoring and controlled access.

## Decisions still requiring team approval

- Telegram versus WhatsApp for the contractual pilot.
- Approved model/provider data-retention policy.
- Whether the strengthened guide is formally an ESDU publication or an ESDU-supported project knowledge base.
- Expert owners for crops, livestock, water, food safety, business/value chains, and Arabic editorial review.
- Approved dynamic sources and update frequency.

