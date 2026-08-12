"""Validated, bounded asynchronous execution for model-requested tools."""

from __future__ import annotations

import asyncio
import json
import math
from dataclasses import dataclass
from typing import Any

from .assistant_contracts import TurnCapabilities
from .tools import ToolRegistry


class ToolValidationError(ValueError):
    pass


@dataclass(frozen=True)
class ToolExecution:
    call_id: str
    name: str
    content: str
    success: bool
    error_type: str | None = None


class ToolExecutor:
    def __init__(
        self,
        registry: ToolRegistry,
        *,
        capabilities: TurnCapabilities | None = None,
        timeout_seconds: float = 12.0,
        max_parallel_calls: int = 4,
        max_total_calls: int = 6,
    ) -> None:
        self.registry = registry
        self.capabilities = capabilities or TurnCapabilities()
        self.timeout_seconds = timeout_seconds
        self.max_parallel_calls = max(1, min(max_parallel_calls, 8))
        self.max_total_calls = max(0, min(max_total_calls, 20))
        self._calls_used = 0
        self._definitions = {
            item["function"]["name"]: item["function"]
            for item in registry.model_definitions()
        }

    def model_definitions(self) -> list[dict[str, Any]]:
        allowed = self.capabilities.allowed_tools
        definitions = self.registry.model_definitions()
        if allowed is None:
            return definitions
        return [
            item
            for item in definitions
            if item.get("function", {}).get("name") in allowed
        ]

    async def execute_many(
        self, calls: list[dict[str, Any]]
    ) -> list[ToolExecution]:
        remaining = max(0, self.max_total_calls - self._calls_used)
        allowed_count = min(len(calls), remaining, self.max_parallel_calls)
        allowed = calls[:allowed_count]
        self._calls_used += allowed_count
        results = list(
            await asyncio.gather(*(self.execute(call) for call in allowed))
        )
        for call in calls[allowed_count:]:
            function = call.get("function") or {}
            results.append(
                ToolExecution(
                    str(call.get("id") or ""),
                    str(function.get("name") or ""),
                    json.dumps({"error": "tool_budget_exceeded"}),
                    False,
                    "budget_exceeded",
                )
            )
        return results

    async def execute(self, call: dict[str, Any]) -> ToolExecution:
        function = call.get("function") or {}
        name = str(function.get("name") or "")
        call_id = str(call.get("id") or "")
        try:
            arguments = function.get("arguments", {})
            if isinstance(arguments, str):
                arguments = json.loads(arguments or "{}")
            if not isinstance(arguments, dict):
                raise ToolValidationError("Tool arguments must be an object")
            self._validate(name, arguments)
            content = await asyncio.wait_for(
                asyncio.to_thread(self.registry.execute, name, arguments),
                timeout=self.timeout_seconds,
            )
            return ToolExecution(call_id, name, str(content), True)
        except TimeoutError:
            return ToolExecution(
                call_id,
                name,
                json.dumps({"error": "tool_timeout"}),
                False,
                "timeout",
            )
        except (ToolValidationError, json.JSONDecodeError, ValueError, TypeError) as exc:
            return ToolExecution(
                call_id,
                name,
                json.dumps(
                    {"error": "invalid_tool_call", "detail": str(exc)[:300]}
                ),
                False,
                type(exc).__name__,
            )

    def _validate(self, name: str, arguments: dict[str, Any]) -> None:
        definition = self._definitions.get(name)
        allowed = self.capabilities.allowed_tools
        if not definition or (allowed is not None and name not in allowed):
            raise ToolValidationError("Tool is unknown or not allowed")
        schema = definition.get("parameters") or {}
        properties = schema.get("properties") or {}
        required = set(schema.get("required") or [])
        missing = required - set(arguments)
        if missing:
            raise ToolValidationError(
                "Missing required arguments: " + ", ".join(sorted(missing))
            )
        if schema.get("additionalProperties") is False:
            extras = set(arguments) - set(properties)
            if extras:
                raise ToolValidationError(
                    "Unexpected arguments: " + ", ".join(sorted(extras))
                )
        for key, value in arguments.items():
            if key in properties:
                self._validate_value(key, value, properties[key])

    @staticmethod
    def _validate_value(name: str, value: Any, schema: dict[str, Any]) -> None:
        expected = schema.get("type")
        valid = True
        if expected == "string":
            valid = isinstance(value, str)
        elif expected == "integer":
            valid = isinstance(value, int) and not isinstance(value, bool)
        elif expected == "number":
            valid = (
                isinstance(value, (int, float))
                and not isinstance(value, bool)
                and math.isfinite(float(value))
            )
        elif expected == "array":
            valid = isinstance(value, list)
        elif expected == "object":
            valid = isinstance(value, dict)
        elif expected == "boolean":
            valid = isinstance(value, bool)
        if not valid:
            raise ToolValidationError(f"{name} has an invalid type")
        if "enum" in schema and value not in schema["enum"]:
            raise ToolValidationError(f"{name} is not an allowed value")
        if isinstance(value, str) and len(value) < int(schema.get("minLength", 0)):
            raise ToolValidationError(f"{name} is too short")
        if isinstance(value, list) and len(value) > int(
            schema.get("maxItems", len(value))
        ):
            raise ToolValidationError(f"{name} contains too many items")
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if "minimum" in schema and value < schema["minimum"]:
                raise ToolValidationError(f"{name} is below its minimum")
            if "maximum" in schema and value > schema["maximum"]:
                raise ToolValidationError(f"{name} is above its maximum")
