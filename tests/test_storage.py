"""Evidence, quota, and feedback behaviour on the shared PostgreSQL store.

These used to run against a second SQLite database. PostgreSQL enforces the
foreign key from query_events to users, which SQLite did not, so quota and
telemetry now require a real account.
"""

import pytest


def _user(store) -> str:
    record = store.upsert_supabase_user(
        auth_user_id="auth-storage-1",
        email="tester@example.org",
        name="Tester",
        google_subject=None,
        is_admin=False,
    )
    return str(record["id"])


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
    user_id = _user(store)
    # check_rate_limit reserves the event; complete_query matches it by mode.
    assert store.check_rate_limit(user_id, "quick").allowed
    store.complete_query(
        user_id,
        mode="quick",
        language="english",
        duration_ms=240,
        success=True,
    )
    summary = store.performance_summary()
    assert summary["measured_queries"] == 1
    assert summary["median_response_ms"] == 240
    assert summary["success_percent"] == 100.0


def test_quota_events_require_a_real_account(store):
    """The SQLite store accepted orphan session IDs; PostgreSQL must not."""

    with pytest.raises(Exception, match="(?i)foreign key|violates"):
        store.check_rate_limit("not-a-user", "quick")


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
