"""One-release synchronous facade over the canonical asynchronous engine."""

from __future__ import annotations

import asyncio
import threading
import uuid
from collections.abc import Coroutine
from typing import Any

from .assistant_contracts import TurnCommand
from .assistant_pipeline import AssistantEngine, PreparedTurn
from .llm import AssistantRequest, AssistantResponse
from .release_knowledge import ReleaseKnowledgeGateway
from .tools import ToolRegistry


def _run_sync[T](coroutine: Coroutine[Any, Any, T]) -> T:
    """Run an engine coroutine from sync adapters, including active-loop hosts."""

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coroutine)
    result: list[T] = []
    error: list[BaseException] = []

    def runner() -> None:
        try:
            result.append(asyncio.run(coroutine))
        except Exception as exc:  # noqa: BLE001
            error.append(exc)

    thread = threading.Thread(target=runner, name="raise-engine-compat", daemon=True)
    thread.start()
    thread.join()
    if error:
        raise error[0]
    return result[0]


class UnifiedAssistantFacade:
    """Compatibility response shape with no independent model/tool orchestration."""

    def __init__(
        self,
        knowledge: ReleaseKnowledgeGateway,
        tools: ToolRegistry,
        *,
        api_key: str | None = None,
    ) -> None:
        self.knowledge = knowledge
        self.tools = tools
        self.api_key = api_key

    def answer_request(
        self,
        request: AssistantRequest | TurnCommand,
        *,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> AssistantResponse:
        if isinstance(request, TurnCommand):
            command = request
        else:
            command = TurnCommand(
                request_id=str(uuid.uuid4()),
                actor_id=request.user_id,
                channel=request.channel,  # type: ignore[arg-type]
                conversation_id=request.conversation_id,
                project_id=request.project_id,
                text=request.text,
                attachments=request.attachments,
                mode=request.mode,
                model_id=request.model_id,
                clarification_style=request.clarification_style,
                project_instructions=request.project_instructions,
            )
        result, prepared = self.execute_turn(
            command,
            conversation_history=conversation_history,
        )
        return AssistantResponse(
            answer=result.content,
            sources=prepared.sources,
            model=result.model,
            mode=command.mode,
            language=result.language,
            duration_ms=result.duration_ms,
            kind=result.kind,
            citations=result.citations,
            assumptions=result.assumptions,
            tool_names=result.tools_used,
            artifact_ids=result.artifact_ids,
            warning=result.warnings[0] if result.warnings else None,
            success=result.success,
            error_type=result.error_type,
            trusted_searches=int("search_trusted_sources" in result.tools_used),
            follow_up_questions=result.follow_up_questions,
        )

    def execute_turn(
        self,
        command: TurnCommand,
        *,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> tuple[Any, PreparedTurn]:
        """Return the canonical terminal result for coordinated sync adapters."""

        return _run_sync(
            self._execute(command, history=conversation_history or [])
        )

    async def _execute(
        self,
        command: TurnCommand,
        *,
        history: list[dict[str, str]],
    ) -> tuple[Any, PreparedTurn]:
        engine = AssistantEngine(self.knowledge, api_key=self.api_key)
        try:
            prepared = await engine.prepare(
                command,
                tools=self.tools,
                history=history,
                clarification_count=0,
            )
            result = None
            async for event in engine.stream(
                command,
                prepared,
                tools=self.tools,
                history=history,
            ):
                if event.result is not None:
                    result = event.result
            if result is None:
                raise RuntimeError("Assistant engine ended without a terminal result")
            return result, prepared
        finally:
            await engine.close()
