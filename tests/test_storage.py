import pytest


def test_feedback_validation(store):
    with pytest.raises(ValueError):
        store.record_feedback(
            session_id="abc",
            category="other",
            comment="",
            consent=True,
        )
    with pytest.raises(ValueError):
        store.record_feedback(
            session_id="abc",
            category="unknown",
            comment="Something",
            consent=True,
        )


def test_performance_summary_updates_reserved_query(store):
    result = store.check_rate_limit("session-a")
    assert result.allowed
    store.complete_query(
        "session-a",
        mode="quick",
        language="english",
        duration_ms=240,
        success=True,
    )
    summary = store.performance_summary()
    assert summary["measured_queries"] == 1
    assert summary["median_response_ms"] == 240
    assert summary["success_percent"] == 100.0


def test_validated_high_priority_feedback_resolution(store):
    feedback_id = store.record_feedback(
        session_id="abc",
        category="incorrect_answer",
        comment="The answer used the wrong locality.",
        consent=True,
        rating=2,
    )
    store.update_feedback(
        feedback_id,
        status="validated",
        priority="high",
        verification_note="Confirmed by field facilitator.",
    )
    assert store.feedback_summary()["resolution_percent"] == 0.0
    store.update_feedback(
        feedback_id,
        status="verified",
        priority="high",
        release_version="0.4.0",
        verification_note="Retested with the original question.",
    )
    assert store.feedback_summary()["resolution_percent"] == 100.0
