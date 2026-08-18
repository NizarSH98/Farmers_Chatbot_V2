"""Asynchronous request analysis, evidence preparation, streaming, and verification."""

from __future__ import annotations

import asyncio
import json
import os
import re
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass, replace
from typing import Any

import httpx

from .assistant_contracts import TurnCommand, TurnEvent, TurnResult
from .config import (
    ANSWER_VERIFIER_MODEL,
    MODE_PROFILES,
    OPENROUTER_DATA_COLLECTION,
    OPENROUTER_ENFORCE_ZDR,
    REQUEST_ANALYZER_MODEL,
    ModeProfile,
    resolve_model_id,
)
from .documents import ProjectSearchResult
from .knowledge import KnowledgeIndex, SearchResult
from .language import detect_language
from .llm import AssistantPromptBuilder, AssistantRequest, extract_follow_up_questions
from .provider import ProviderClient
from .retrieval import LegacyHybridRetrieval, RetrievalRequest, RetrievalService
from .tool_executor import ToolExecutor
from .tools import ToolRegistry
from .trusted_sources import requires_live_verification, url_is_trusted


@dataclass(frozen=True)
class RequestAnalysis:
    intent: str
    decision: str
    domain: str
    risk: str
    currentness: str
    location: str | None
    missing_fields: tuple[str, ...]
    needs_clarification: bool
    clarification_question: str | None
    retrieval_queries: tuple[str, ...]
    evidence_requirements: tuple[str, ...]
    output_shape: str
    clarification_options: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent,
            "decision": self.decision,
            "domain": self.domain,
            "risk": self.risk,
            "currentness": self.currentness,
            "location": self.location,
            "missing_fields": list(self.missing_fields),
            "needs_clarification": self.needs_clarification,
            "clarification_question": self.clarification_question,
            "clarification_options": list(self.clarification_options),
            "retrieval_queries": list(self.retrieval_queries),
            "evidence_requirements": list(self.evidence_requirements),
            "output_shape": self.output_shape,
            "assumptions": list(self.assumptions),
        }


REQUEST_ANALYSIS_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "intent": {"type": "string"},
        "decision": {"type": "string"},
        "domain": {"type": "string"},
        "risk": {"type": "string", "enum": ["low", "medium", "high"]},
        "currentness": {"type": "string", "enum": ["stable", "current"]},
        "location": {"type": ["string", "null"]},
        "missing_fields": {"type": "array", "items": {"type": "string"}},
        "needs_clarification": {"type": "boolean"},
        "clarification_question": {"type": ["string", "null"]},
        "clarification_options": {"type": "array", "items": {"type": "string"}},
        "retrieval_queries": {"type": "array", "items": {"type": "string"}},
        "evidence_requirements": {"type": "array", "items": {"type": "string"}},
        "output_shape": {"type": "string"},
        "assumptions": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "intent",
        "decision",
        "domain",
        "risk",
        "currentness",
        "location",
        "missing_fields",
        "needs_clarification",
        "clarification_question",
        "clarification_options",
        "retrieval_queries",
        "evidence_requirements",
        "output_shape",
        "assumptions",
    ],
    "additionalProperties": False,
}


@dataclass
class PreparedTurn:
    analysis: RequestAnalysis
    language: str
    sources: list[SearchResult]
    project_sources: list[ProjectSearchResult]
    citations: list[dict[str, Any]]
    trusted_context: str
    warning: str | None
    tools_used: list[str]
    stage_durations: dict[str, int]
    retrieval_metrics: dict[str, Any]
    graph_paths: list[dict[str, Any]]
    provider_record_start: int = 0


@dataclass
class PipelineResult(TurnResult):
    """Backward-compatible name for the canonical terminal result."""


@dataclass
class PipelineEvent(TurnEvent):
    """Backward-compatible name for the canonical typed turn event."""

class AssistantEngine:
    def __init__(
        self,
        knowledge: KnowledgeIndex,
        *,
        api_key: str | None = None,
        client: httpx.AsyncClient | None = None,
        provider: ProviderClient | None = None,
        retrieval: RetrievalService | None = None,
    ) -> None:
        self.knowledge = knowledge
        resolved_key = api_key if api_key is not None else os.getenv(
            "OPENROUTER_API_KEY", ""
        )
        self.provider = provider or ProviderClient(
            api_key=resolved_key,
            client=client,
        )
        self.api_key = self.provider.api_key
        self.retrieval = retrieval or LegacyHybridRetrieval(knowledge)

    async def close(self) -> None:
        await self.provider.close()
        close_retrieval = getattr(self.retrieval, "close", None)
        if close_retrieval is not None:
            await close_retrieval()

    async def prepare(
        self,
        request: AssistantRequest | TurnCommand,
        *,
        tools: ToolRegistry,
        history: list[dict[str, str]],
        clarification_count: int,
    ) -> PreparedTurn:
        language = detect_language(request.text)
        provider_record_start = len(self.provider.records)
        analysis_started = time.perf_counter()
        analysis = await self._analyze(
            request,
            language=language,
            history=history,
            clarification_count=clarification_count,
        )
        profile = MODE_PROFILES.get(request.mode, MODE_PROFILES["standard"])
        timings = {
            "analysis": int((time.perf_counter() - analysis_started) * 1000)
        }
        retrieval_started = time.perf_counter()
        bundle = await self.retrieval.retrieve(
            RetrievalRequest(
                query=request.text,
                queries=analysis.retrieval_queries,
                language=language,
                mode=request.mode,
                actor_id=(
                    request.actor_id
                    if isinstance(request, TurnCommand)
                    else request.user_id
                ),
                project_id=request.project_id,
                geography=analysis.location,
                domain=analysis.domain,
                risk=analysis.risk,
                currentness=analysis.currentness,
                top_k=profile.top_k,
                graph_hops=2 if request.mode == "deep" else 1,
            ),
            project_chunks=tools.project_chunks,
        )
        sources = bundle.knowledge_results
        project_sources = bundle.project_results
        timings["retrieval"] = int(
            (time.perf_counter() - retrieval_started) * 1000
        )
        builder = AssistantPromptBuilder(self.knowledge, tools, api_key=self.api_key)
        if bundle.retrieval_metrics.get("backend") == "postgres_hybrid_graph":
            citations = [
                item.citation() for item in [*bundle.passages, *bundle.claims]
            ]
        else:
            citations = builder._internal_citations(sources)
            citations.extend(builder._project_citations(project_sources))
        used = ["search_project_knowledge"] if project_sources else []
        warning = None
        trusted_context = ""
        if not analysis.needs_clarification and self._requires_trusted_search(
            request.text, analysis
        ):
            trusted_started = time.perf_counter()
            if tools.trusted_client:
                result = await asyncio.to_thread(
                    tools.trusted_client.search,
                    analysis.retrieval_queries[0]
                    if analysis.retrieval_queries
                    else request.text,
                )
                timings["trusted_search"] = int(
                    (time.perf_counter() - trusted_started) * 1000
                )
                used.append("search_trusted_sources")
                if result.verified:
                    trusted_context = result.summary
                    citations.extend(dict(item) for item in result.citations)
                else:
                    warning = result.warning or self._verification_warning(language)
            else:
                warning = self._verification_warning(language)
        return PreparedTurn(
            analysis=analysis,
            language=language,
            sources=sources,
            project_sources=project_sources,
            citations=self._dedupe_citations(citations),
            trusted_context=trusted_context,
            warning=warning,
            tools_used=used,
            stage_durations=timings,
            retrieval_metrics=dict(bundle.retrieval_metrics),
            graph_paths=[dict(path) for path in bundle.graph_paths],
            provider_record_start=provider_record_start,
        )

    async def stream(
        self,
        request: AssistantRequest | TurnCommand,
        prepared: PreparedTurn,
        *,
        tools: ToolRegistry,
        history: list[dict[str, str]],
    ) -> AsyncIterator[PipelineEvent]:
        started = time.perf_counter()
        analysis = prepared.analysis
        if analysis.needs_clarification and analysis.clarification_question:
            content = analysis.clarification_question
            result = PipelineResult(
                content=content,
                kind="clarification",
                language=prepared.language,
                model=REQUEST_ANALYZER_MODEL if self.api_key else None,
                citations=[],
                assumptions=list(analysis.assumptions),
                warnings=[],
                tools_used=prepared.tools_used,
                artifact_ids=[],
                duration_ms=int((time.perf_counter() - started) * 1000),
                ttft_ms=0,
                stage_durations=dict(prepared.stage_durations),
            )
            yield PipelineEvent(
                "clarification",
                {
                    "content": content,
                    "missing_fields": list(analysis.missing_fields),
                    "options": list(analysis.clarification_options),
                },
            )
            yield PipelineEvent(
                "turn.completed", {"kind": "clarification"}, result=result
            )
            return

        for citation in prepared.citations:
            yield PipelineEvent("source", {"citation": citation})
        profile = MODE_PROFILES.get(request.mode, MODE_PROFILES["standard"])
        try:
            profile = replace(
                profile,
                model=resolve_model_id(request.model_id, profile.model),
            )
        except ValueError as exc:
            yield self._error_result(
                prepared, started, "invalid_model", str(exc)
            )
            return

        builder = AssistantPromptBuilder(self.knowledge, tools, api_key=self.api_key)
        messages = builder._build_messages(
            query=request.text,
            sources=prepared.sources,
            project_sources=prepared.project_sources,
            trusted_context=prepared.trusted_context,
            language=prepared.language,
            profile=profile,
            history=history,
            clarification_style=request.clarification_style,
            attachments=list(request.attachments),
            verification_required=self._requires_trusted_search(
                request.text, analysis
            ),
            project_instructions=request.project_instructions,
        )
        if not self.api_key:
            requires_verification = (
                analysis.risk == "high" or analysis.currentness == "current"
            )
            fallback = (
                self._safe_verification_fallback(prepared.language)
                if requires_verification
                else builder._fallback_answer(
                    request.text,
                    prepared.sources,
                    prepared.project_sources,
                    prepared.language,
                )
            )
            yield PipelineEvent("content.delta", {"text": fallback})
            result = PipelineResult(
                content=fallback,
                kind="refusal" if requires_verification else "answer",
                language=prepared.language,
                model=None,
                citations=prepared.citations,
                assumptions=list(analysis.assumptions),
                warnings=(
                    [prepared.warning or self._verification_warning(prepared.language)]
                    if requires_verification
                    else [prepared.warning] if prepared.warning else []
                ),
                tools_used=prepared.tools_used,
                artifact_ids=[],
                duration_ms=int((time.perf_counter() - started) * 1000),
                ttft_ms=0,
                stage_durations=dict(prepared.stage_durations),
            )
            yield PipelineEvent(
                "turn.completed", {"kind": result.kind}, result=result
            )
            return

        yield PipelineEvent("status", {"stage": "generation"})
        generation_started = time.perf_counter()
        verification_required = (
            profile.key == "deep"
            or analysis.risk == "high"
            or analysis.currentness == "current"
        )
        try:
            (
                answer,
                usage,
                annotations,
                executed_tools,
            ) = await self._generate_with_tools(
                messages=messages,
                profile=profile,
                executor=self._tool_executor(request, tools, profile),
            )
        except (httpx.HTTPError, ValueError, KeyError, json.JSONDecodeError) as exc:
            yield self._error_result(
                prepared,
                started,
                "model_service",
                "The model service could not complete this answer.",
                detail=type(exc).__name__,
            )
            return

        prepared.stage_durations["generation"] = int(
            (time.perf_counter() - generation_started) * 1000
        )
        if not answer:
            yield self._error_result(
                prepared, started, "empty_response", "The model returned no answer."
            )
            return
        answer, follow_up_questions = extract_follow_up_questions(answer)
        for citation in annotations:
            yield PipelineEvent("source", {"citation": citation})

        warning = prepared.warning
        if verification_required:
            yield PipelineEvent("status", {"stage": "verification"})
            verification_started = time.perf_counter()
            answer, verifier_warning, verifier_approved = await self._verify(
                query=request.text,
                answer=answer,
                citations=[*prepared.citations, *annotations],
                language=prepared.language,
                risk=analysis.risk,
                currentness=analysis.currentness,
            )
            prepared.stage_durations["verification"] = int(
                (time.perf_counter() - verification_started) * 1000
            )
            warning = verifier_warning or warning
        else:
            verifier_approved = True

        ttft_ms = int((time.perf_counter() - started) * 1000)
        for part in self._display_chunks(answer):
            yield PipelineEvent("content.delta", {"text": part})

        citations = self._dedupe_citations(
            [*prepared.citations, *annotations, *tools.recent_citations]
        )
        tools_used = list(dict.fromkeys([*prepared.tools_used, *executed_tools]))
        warnings = [warning] if warning else []
        if warning:
            yield PipelineEvent("warning", {"message": warning})
        prompt_tokens = self._int_or_none(
            usage.get("prompt_tokens") or usage.get("input_tokens")
        )
        completion_tokens = self._int_or_none(
            usage.get("completion_tokens") or usage.get("output_tokens")
        )
        result = PipelineResult(
            content=answer,
            kind="answer" if verifier_approved else "refusal",
            language=prepared.language,
            model=profile.model,
            citations=citations,
            assumptions=list(analysis.assumptions),
            warnings=warnings,
            tools_used=tools_used,
            artifact_ids=list(tools.recent_artifact_ids),
            duration_ms=int((time.perf_counter() - started) * 1000),
            ttft_ms=ttft_ms,
            stage_durations=dict(prepared.stage_durations),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            estimated_cost_usd=self._float_or_none(usage.get("cost")),
            follow_up_questions=follow_up_questions,
            provider_calls=[
                record.to_dict()
                for record in self.provider.records[prepared.provider_record_start :]
            ],
        )
        yield PipelineEvent(
            "usage",
            {
                "model": profile.model,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
            },
        )
        yield PipelineEvent(
            "turn.completed",
            {
                "kind": result.kind,
                "model": profile.model,
                "duration_ms": result.duration_ms,
                "ttft_ms": ttft_ms,
                "content": answer,
                "quick_replies": follow_up_questions,
            },
            result=result,
        )

    async def _generate_with_tools(
        self,
        *,
        messages: list[dict[str, Any]],
        profile: ModeProfile,
        executor: ToolExecutor,
    ) -> tuple[str, dict[str, Any], list[dict[str, Any]], list[str]]:
        """Run a bounded model/tool loop and return one final answer."""

        working_messages = [dict(message) for message in messages]
        annotations: list[dict[str, Any]] = []
        tool_names: list[str] = []
        prompt_tokens = 0
        completion_tokens = 0
        cost = 0.0
        has_cost = False

        for round_number in range(profile.max_tool_rounds + 1):
            payload: dict[str, Any] = {
                "model": profile.model,
                "messages": working_messages,
                "temperature": profile.temperature,
                "max_tokens": profile.max_tokens,
                "reasoning": {
                    "effort": profile.reasoning_effort,
                    "exclude": True,
                },
            }
            if round_number < profile.max_tool_rounds:
                definitions = executor.model_definitions()
                if definitions:
                    payload["tools"] = definitions
                    payload["tool_choice"] = "auto"
                    payload["parallel_tool_calls"] = True

            response = await self.provider.complete(
                stage=f"generation_round_{round_number + 1}",
                payload=payload,
                timeout=45.0,
            )
            if response.usage.prompt_tokens is not None:
                prompt_tokens += response.usage.prompt_tokens
            if response.usage.completion_tokens is not None:
                completion_tokens += response.usage.completion_tokens
            if response.usage.cost_usd is not None:
                cost += response.usage.cost_usd
                has_cost = True

            message = response.message
            for annotation in message.get("annotations") or []:
                citation = self._annotation_citation(annotation)
                if citation and citation not in annotations:
                    annotations.append(citation)

            calls = message.get("tool_calls") or []
            if not calls:
                content = message.get("content")
                if not isinstance(content, str) or not content.strip():
                    raise ValueError("Model returned no final answer")
                usage = {
                    "prompt_tokens": prompt_tokens or None,
                    "completion_tokens": completion_tokens or None,
                    "cost": cost if has_cost else None,
                }
                return content.strip(), usage, annotations, tool_names

            working_messages.append(dict(message))
            executions = await executor.execute_many(list(calls))
            for execution in executions:
                tool_names.append(execution.name)
                working_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": execution.call_id,
                        "name": execution.name,
                        "content": execution.content,
                    }
                )

        raise ValueError("Tool loop ended without a final answer")

    async def _analyze(
        self,
        request: AssistantRequest | TurnCommand,
        *,
        language: str,
        history: list[dict[str, str]],
        clarification_count: int,
    ) -> RequestAnalysis:
        fallback = self._heuristic_analysis(
            request.text,
            language=language,
            clarification_style=request.clarification_style,
            clarification_count=clarification_count,
        )
        if not self.api_key:
            return fallback
        context = [
            {
                "role": item.get("role"),
                "content": str(item.get("content") or "")[:1200],
            }
            for item in history[-4:]
            if item.get("role") in {"user", "assistant"}
        ]
        payload = {
            "model": REQUEST_ANALYZER_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Analyze this agricultural or rural-enterprise request. "
                        "Return JSON only with intent, decision, domain, risk "
                        "(low|medium|high), currentness (stable|current), location, "
                        "missing_fields, needs_clarification, clarification_question, "
                        "clarification_options (array of 2-4 short suggested answers "
                        "the user can pick from), "
                        "retrieval_queries, evidence_requirements, output_shape, and "
                        "assumptions. Ask only when missing context materially changes "
                        "safety or usefulness. Ask at most two details in accessible "
                        "language. When clarifying, always provide 2-4 short options "
                        "the user can choose from. "
                        "If clarifications_already_asked >= 1 and the user gave a "
                        "vague or deflecting reply (e.g. 'you choose', 'anything', "
                        "'I don't know'), set needs_clarification to false and fill "
                        "assumptions with what you assumed instead. "
                        "Do not include reasoning or chain-of-thought."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "question": request.text,
                            "language": language,
                            "mode": request.mode,
                            "clarification_style": request.clarification_style,
                            "clarifications_already_asked": clarification_count,
                            "recent_context": context,
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
            "temperature": 0,
            "max_tokens": 450,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "request_analysis",
                    "strict": True,
                    "schema": REQUEST_ANALYSIS_JSON_SCHEMA,
                },
            },
            "reasoning": {"effort": "low", "exclude": True},
            "provider": self._provider_policy(),
        }
        try:
            response = await self.provider.complete(
                stage="analyzer",
                payload=payload,
                timeout=15.0,
            )
            content = response.message["content"]
            return self._coerce_analysis(
                json.loads(content),
                fallback=fallback,
                clarification_style=request.clarification_style,
                clarification_count=clarification_count,
            )
        except (httpx.HTTPError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            return fallback

    async def _openrouter_stream(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
        reasoning_effort: str,
    ) -> AsyncIterator[dict[str, Any]]:
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
            "stream_options": {"include_usage": True},
            "reasoning": {"effort": reasoning_effort, "exclude": True},
            "provider": self._provider_policy(),
        }
        async for event in self.provider.stream(stage="generation", payload=payload):
            if event["type"] == "annotation":
                citation = self._annotation_citation(event["annotation"])
                if citation:
                    yield {"type": "citation", "citation": citation}
                continue
            yield event

    async def _verify(
        self,
        *,
        query: str,
        answer: str,
        citations: list[dict[str, Any]],
        language: str,
        risk: str,
        currentness: str,
    ) -> tuple[str, str | None, bool]:
        payload = {
            "model": ANSWER_VERIFIER_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Verify this draft without revealing chain-of-thought. Check "
                        "citation support, units, dates, geography, uncertainty, "
                        "unsafe pesticide, veterinary, and food-safety instructions, "
                        "and unsupported certainty. Square-bracket citation IDs like "
                        "[RAISE-K001] or [AKKAR-PROFILE-001] are intentional inline "
                        "references to the knowledge base and must NOT be flagged as "
                        "raw citation tags or incomplete formatting. Return JSON "
                        "only: approved, revised_answer, warning. Preserve the "
                        "user's language. If evidence is insufficient for a "
                        "high-risk claim, replace it with a limitation and "
                        "qualified-expert referral."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "question": query,
                            "draft": answer,
                            "language": language,
                            "risk": risk,
                            "currentness": currentness,
                            "citations": citations,
                        },
                        ensure_ascii=False,
                    )[:28000],
                },
            ],
            "temperature": 0,
            "max_tokens": 1400,
            "response_format": {"type": "json_object"},
            "reasoning": {"effort": "medium", "exclude": True},
            "provider": self._provider_policy(),
        }
        try:
            response = await self.provider.complete(
                stage="verifier",
                payload=payload,
                timeout=30.0,
            )
            content = response.message["content"]
            parsed = json.loads(content)
            approved = parsed.get("approved") is True
            revised = str(parsed.get("revised_answer") or "").strip()
            warning = str(parsed.get("warning") or "").strip() or None
            if approved:
                return (revised or answer), warning, True
            if revised:
                return (
                    revised,
                    warning
                    or "The verifier revised unsupported or unsafe parts of the draft.",
                    False,
                )
            return (
                self._safe_verification_fallback(language),
                warning
                or "The draft did not pass verification and was replaced with a safe limitation.",
                False,
            )
        except (httpx.HTTPError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            warning = (
                "تعذّر إكمال التحقق الإضافي؛ راجع هذا التوجيه مع خبير محلي مؤهل."
                if language == "arabic"
                else "Additional verification could not be completed; review this "
                "guidance with a qualified local expert."
            )
            return self._safe_verification_fallback(language), warning, False

    @staticmethod
    def _tool_executor(
        request: AssistantRequest | TurnCommand,
        tools: ToolRegistry,
        profile: ModeProfile,
    ) -> ToolExecutor:
        defaults = {"quick": 2, "standard": 6, "deep": 10, "source_only": 2}
        if isinstance(request, TurnCommand):
            capabilities = request.capabilities
            maximum = capabilities.max_tool_calls
            timeout = max(0.1, min(capabilities.tool_timeout_seconds, 30.0))
        else:
            capabilities = None
            maximum = None
            timeout = 12.0
        return ToolExecutor(
            tools,
            capabilities=capabilities,
            timeout_seconds=timeout,
            max_parallel_calls=4,
            max_total_calls=(
                maximum
                if maximum is not None
                else defaults.get(profile.key, 6)
            ),
        )

    @staticmethod
    def _safe_verification_fallback(language: str) -> str:
        if language == "arabic":
            return (
                "لا أستطيع تأكيد توصية آمنة ومحددة من الأدلة المتاحة الآن. "
                "اجمع تفاصيل الحالة وتواصل مع خبير زراعي أو بيطري محلي مؤهل، "
                "ولا تستخدم جرعة أو علاجاً غير موثق."
            )
        return (
            "I cannot confirm a specific safe recommendation from the available "
            "evidence. Record the observations and consult a qualified local "
            "agronomist or veterinarian; do not apply an unverified dose or treatment."
        )

    @staticmethod
    def _heuristic_analysis(
        query: str,
        *,
        language: str,
        clarification_style: str,
        clarification_count: int,
    ) -> RequestAnalysis:
        normalized = query.casefold()
        high_risk = bool(
            re.search(
                r"\b(pesticide|dose|poison|veterinar|diagnos|emergency|"
                r"food safety|contaminat|chemical)\b|"
                r"(مبيد|جرعة|سم|بيطري|تشخيص|طوارئ|تسمم|تلوث)",
                normalized,
            )
        )
        current = bool(
            re.search(
                r"\b(today|now|current|price|market|weather|law|regulation)\b|"
                r"(اليوم|الآن|حالي|سعر|سوق|طقس|قانون|قرار)",
                normalized,
            )
        )
        ambiguous = len(query.split()) < 4 or bool(
            re.fullmatch(
                r"\s*(help|what should i do|ساعدني|ماذا أفعل|شو اعمل)[؟?!. ]*",
                normalized,
            )
        )
        needs = (
            ambiguous
            and clarification_style != "direct"
            and clarification_count < 1
        )
        question = None
        options: tuple[str, ...] = ()
        if needs:
            if language == "arabic":
                question = "ما الموضوع الذي تريد المساعدة فيه؟"
                options = (
                    "زراعة خضروات",
                    "تربية مواشي أو دواجن",
                    "تخطيط مشروع زراعي",
                    "مكافحة آفات أو أمراض",
                )
            else:
                question = "What do you need help with?"
                options = (
                    "Growing vegetables",
                    "Livestock or poultry",
                    "Farm project planning",
                    "Pest or disease control",
                )
        return RequestAnalysis(
            intent="decision_support",
            decision="Provide practical guidance",
            domain="agriculture",
            risk="high" if high_risk else "medium",
            currentness="current" if current else "stable",
            location=None,
            missing_fields=("topic", "desired_outcome") if needs else (),
            needs_clarification=needs,
            clarification_question=question,
            clarification_options=options,
            retrieval_queries=(query,),
            evidence_requirements=(
                ("trusted_current_source",) if current or high_risk else ("raise",)
            ),
            output_shape="practical_answer",
        )

    @staticmethod
    def _coerce_analysis(
        value: dict[str, Any],
        *,
        fallback: RequestAnalysis,
        clarification_style: str,
        clarification_count: int,
    ) -> RequestAnalysis:
        risk = str(value.get("risk") or fallback.risk).lower()
        if risk not in {"low", "medium", "high"}:
            risk = fallback.risk
        currentness = str(
            value.get("currentness") or fallback.currentness
        ).lower()
        if currentness not in {"stable", "current"}:
            currentness = fallback.currentness
        needs = bool(value.get("needs_clarification"))
        if clarification_style == "direct" and risk != "high":
            needs = False
        if clarification_count >= 1:
            needs = False
        question = str(value.get("clarification_question") or "").strip() or None
        if needs and not question:
            question = fallback.clarification_question
        options = tuple(
            str(item).strip()[:120]
            for item in value.get("clarification_options") or []
            if str(item).strip()
        )[:4]
        if needs and not options:
            options = fallback.clarification_options
        queries = tuple(
            str(item).strip()[:500]
            for item in value.get("retrieval_queries") or []
            if str(item).strip()
        )[:4] or fallback.retrieval_queries
        return RequestAnalysis(
            intent=str(value.get("intent") or fallback.intent)[:120],
            decision=str(value.get("decision") or fallback.decision)[:300],
            domain=str(value.get("domain") or fallback.domain)[:80],
            risk=risk,
            currentness=currentness,
            location=str(value.get("location") or "").strip()[:120] or None,
            missing_fields=tuple(
                str(item).strip()[:80]
                for item in value.get("missing_fields") or []
                if str(item).strip()
            )[:6],
            needs_clarification=needs and bool(question),
            clarification_question=question if needs else None,
            clarification_options=options if needs else (),
            retrieval_queries=queries,
            evidence_requirements=tuple(
                str(item).strip()[:100]
                for item in value.get("evidence_requirements") or []
                if str(item).strip()
            )[:8],
            output_shape=str(
                value.get("output_shape") or fallback.output_shape
            )[:80],
            assumptions=tuple(
                str(item).strip()[:300]
                for item in value.get("assumptions") or []
                if str(item).strip()
            )[:5],
        )

    @staticmethod
    def _requires_trusted_search(
        query: str, analysis: RequestAnalysis
    ) -> bool:
        return (
            analysis.currentness == "current"
            or analysis.risk == "high"
            or requires_live_verification(query)
        )

    @staticmethod
    def _verification_warning(language: str) -> str:
        if language == "arabic":
            return "تعذّر التحقق من المعلومات الحالية عبر المصادر الموثوقة."
        return "Current information could not be verified from trusted sources."

    def _headers(self) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Title": "RAISE agricultural assistant",
        }
        public_url = os.getenv("APP_PUBLIC_URL", "").strip()
        if public_url:
            headers["HTTP-Referer"] = public_url
        return headers

    @staticmethod
    def _provider_policy() -> dict[str, Any]:
        return {
            "data_collection": OPENROUTER_DATA_COLLECTION,
            "zdr": OPENROUTER_ENFORCE_ZDR,
        }

    @staticmethod
    def _annotation_citation(
        annotation: dict[str, Any],
    ) -> dict[str, Any] | None:
        if annotation.get("type") != "url_citation":
            return None
        value = annotation.get("url_citation") or {}
        url = str(value.get("url") or "").strip()
        if not url or not url_is_trusted(url):
            return None
        return {
            "source_type": "model_url_annotation",
            "title": str(value.get("title") or url)[:300],
            "url": url,
        }

    @staticmethod
    def _dedupe_citations(
        citations: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        result = []
        seen = set()
        for citation in citations:
            key = (
                citation.get("source_type"),
                citation.get("item_id"),
                citation.get("document_id"),
                citation.get("url"),
                citation.get("title"),
            )
            if key in seen:
                continue
            seen.add(key)
            result.append(citation)
        return result

    @staticmethod
    def _display_chunks(content: str, size: int = 90) -> list[str]:
        return [
            content[index : index + size]
            for index in range(0, len(content), size)
        ]

    @staticmethod
    def _int_or_none(value: Any) -> int | None:
        try:
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _float_or_none(value: Any) -> float | None:
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _error_result(
        prepared: PreparedTurn,
        started: float,
        error_type: str,
        message: str,
        *,
        detail: str | None = None,
    ) -> PipelineEvent:
        result = PipelineResult(
            content=message,
            kind="answer",
            language=prepared.language,
            model=None,
            citations=prepared.citations,
            assumptions=list(prepared.analysis.assumptions),
            warnings=[message],
            tools_used=prepared.tools_used,
            artifact_ids=[],
            duration_ms=int((time.perf_counter() - started) * 1000),
            ttft_ms=None,
            stage_durations=dict(prepared.stage_durations),
            success=False,
            error_type=error_type,
        )
        return PipelineEvent(
            "error",
            {"code": error_type, "message": message, "detail": detail},
            result=result,
        )


# One-release compatibility name. All orchestration lives in AssistantEngine.
AsyncAssistantPipeline = AssistantEngine
