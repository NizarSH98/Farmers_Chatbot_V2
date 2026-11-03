"""Concurrency and exact-finalization regressions for canonical turns."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest
from conftest import new_pilot_store

from farmers_chatbot.assistant_contracts import TurnCommand, TurnResult
from farmers_chatbot.auth import UserIdentity
from farmers_chatbot.pilot_store import (
    IdempotencyConflict,
    PilotStore,
    TurnStateConflict,
)
from farmers_chatbot.turn_coordinator import TurnCoordinator


def _workspace(store: PilotStore) -> tuple[str, str]:
    user = store.upsert_user(
        UserIdentity(
            user_id="",
            issuer="test",
            subject="coordinator-user",
            email="coordinator@example.org",
            name="Coordinator Tester",
            is_admin=False,
        )
    )
    conversation_id = store.create_conversation(user["id"], "Atomic turns")
    return str(user["id"]), conversation_id


def _command(actor_id: str, conversation_id: str, index: int) -> TurnCommand:
    return TurnCommand(
        request_id=f"request-{index}",
        actor_id=actor_id,
        channel="test",
        conversation_id=conversation_id,
        text=f"question {index}",
        mode="standard",
    )


def _reserve(coordinator: TurnCoordinator, command: TurnCommand):
    return coordinator.reserve(
        command,
        language="en",
        stored_attachments=[],
        clarification_count=0,
    )


def test_fifty_concurrent_reservations_cannot_exceed_limits(
    tmp_path, monkeypatch
) -> None:
    import farmers_chatbot.pilot_store as store_module

    monkeypatch.setattr(store_module, "PILOT_COOLDOWN_SECONDS", 0)
    monkeypatch.setattr(store_module, "MAX_QUERIES_PER_USER_DAY", 12)
    monkeypatch.setattr(store_module, "MAX_PILOT_QUERIES_PER_DAY", 100)
    monkeypatch.setattr(store_module, "MAX_USER_WEEKLY_COST_USD", 100.0)
    store = new_pilot_store()
    actor_id, conversation_id = _workspace(store)
    coordinator = TurnCoordinator(store)

    with ThreadPoolExecutor(max_workers=50) as pool:
        results = list(
            pool.map(
                lambda index: _reserve(
                    coordinator, _command(actor_id, conversation_id, index)
                ),
                range(50),
            )
        )

    assert sum(result.allowed for result in results) == 12
    with store._connect() as connection:
        assert (
            connection.execute("SELECT COUNT(*) AS n FROM query_events").fetchone()["n"] == 12
        )
        assert (
            connection.execute("SELECT COUNT(*) AS n FROM assistant_turns").fetchone()["n"]
            == 12
        )
        assert connection.execute("SELECT COUNT(*) AS n FROM messages").fetchone()["n"] == 12
    store.close()


def test_fifty_duplicate_keys_create_one_turn_and_one_reservation(
    tmp_path, monkeypatch
) -> None:
    import farmers_chatbot.pilot_store as store_module

    monkeypatch.setattr(store_module, "PILOT_COOLDOWN_SECONDS", 0)
    store = new_pilot_store()
    actor_id, conversation_id = _workspace(store)
    coordinator = TurnCoordinator(store)
    command = _command(actor_id, conversation_id, 1)

    with ThreadPoolExecutor(max_workers=50) as pool:
        results = list(pool.map(lambda _: _reserve(coordinator, command), range(50)))

    assert all(result.allowed for result in results)
    assert len({result.turn_id for result in results}) == 1
    assert sum(not result.existing for result in results) == 1
    with store._connect() as connection:
        assert (
            connection.execute("SELECT COUNT(*) AS n FROM query_events").fetchone()["n"] == 1
        )
        assert (
            connection.execute("SELECT COUNT(*) AS n FROM assistant_turns").fetchone()["n"]
            == 1
        )
        assert connection.execute("SELECT COUNT(*) AS n FROM messages").fetchone()["n"] == 1
    store.close()


def test_reused_key_with_different_payload_is_rejected(tmp_path) -> None:
    store = new_pilot_store()
    actor_id, conversation_id = _workspace(store)
    coordinator = TurnCoordinator(store)
    original = _command(actor_id, conversation_id, 1)
    _reserve(coordinator, original)
    changed = TurnCommand(
        **{
            **original.__dict__,
            "text": "a different question",
        }
    )

    try:
        coordinator.replay(changed)
    except IdempotencyConflict:
        pass
    else:
        raise AssertionError("different payload must not reuse an idempotency key")
    store.close()


def _result() -> TurnResult:
    return TurnResult(
        content="Supported answer",
        kind="answer",
        language="en",
        model="test/model",
    )


def test_failure_cannot_replace_a_completed_terminal_turn(tmp_path) -> None:
    store = new_pilot_store()
    actor_id, conversation_id = _workspace(store)
    coordinator = TurnCoordinator(store)
    command = _command(actor_id, conversation_id, 1)
    reservation = _reserve(coordinator, command)
    message_id = coordinator.finalize(
        command,
        str(reservation.turn_id),
        _result(),
        analysis={},
        terminal_sequence=4,
    )

    coordinator.fail(
        actor_id,
        str(reservation.turn_id),
        status="cancelled",
        error_type="late_disconnect",
        duration_ms=20,
        terminal_sequence=5,
    )

    state = coordinator.status(actor_id, str(reservation.turn_id))
    assert state["status"] == "complete"
    assert state["message"]["id"] == message_id
    assert state["terminal_sequence"] == 4
    store.close()


def test_completion_cannot_replace_a_cancelled_terminal_turn(tmp_path) -> None:
    store = new_pilot_store()
    actor_id, conversation_id = _workspace(store)
    coordinator = TurnCoordinator(store)
    command = _command(actor_id, conversation_id, 1)
    reservation = _reserve(coordinator, command)
    coordinator.fail(
        actor_id,
        str(reservation.turn_id),
        status="cancelled",
        error_type="client_cancelled",
        duration_ms=10,
        terminal_sequence=2,
    )

    with pytest.raises(TurnStateConflict, match="terminal"):
        coordinator.finalize(
            command,
            str(reservation.turn_id),
            _result(),
            analysis={},
            terminal_sequence=3,
        )

    state = coordinator.status(actor_id, str(reservation.turn_id))
    assert state["status"] == "cancelled"
    assert state["message"] is None
    assert state["terminal_sequence"] == 2
    store.close()


def test_clarification_interaction_survives_finalization_and_reload(tmp_path) -> None:
    store = new_pilot_store()
    actor_id, conversation_id = _workspace(store)
    coordinator = TurnCoordinator(store)
    command = _command(actor_id, conversation_id, 1)
    reservation = _reserve(coordinator, command)
    interaction = {
        "schema_version": "raise-clarification-v1",
        "type": "clarification",
        "round": 1,
        "max_rounds": 3,
        "question": "Which crop?",
        "options": [
            {"id": "1", "label": "Potato", "value": "Potato"},
            {"id": "2", "label": "Tomato", "value": "Tomato"},
            {"id": "3", "label": "Other", "value": "Other"},
        ],
        "missing_fields": ["crop"],
        "language": "english",
    }
    result = TurnResult(
        content="Which crop?",
        kind="clarification",
        language="english",
        model="test/analyzer",
        interaction=interaction,
    )
    coordinator.finalize(
        command, str(reservation.turn_id), result, analysis={}, terminal_sequence=2
    )
    status = coordinator.status(actor_id, str(reservation.turn_id))
    messages = store.list_messages(actor_id, conversation_id)
    assert status["message"]["interaction"] == interaction
    assert messages[-1]["interaction"] == interaction
