from conftest import new_pilot_store

from farmers_chatbot.auth import UserIdentity
from farmers_chatbot.config import MAX_USER_WEEKLY_COST_USD
from farmers_chatbot.pilot_store import PilotStore


def _make_user(store: PilotStore, subject: str = "subject"):
    return store.upsert_user(
        UserIdentity(
            user_id="",
            issuer="test",
            subject=subject,
            email=f"{subject}@example.org",
            name="Tester",
            is_admin=False,
        )
    )


def _record_query(store: PilotStore, user_id: str, cost: float) -> None:
    """Insert a completed query event directly, bypassing the cooldown gate."""
    from farmers_chatbot.pilot_store import utc_now

    now = utc_now()
    with store._connect() as connection:
        connection.execute(
            store._sql(
                """
                INSERT INTO query_events
                    (occurred_at, day_utc, user_id, mode, duration_ms,
                     success, estimated_cost_usd)
                VALUES (?, ?, ?, 'standard', 10, 1, ?)
                """
            ),
            (now, now[:10], user_id, cost),
        )


def test_weekly_usage_reflects_recorded_spend(tmp_path):
    store = new_pilot_store()
    user = _make_user(store)
    _record_query(store, user["id"], 1.5)
    _record_query(store, user["id"], 2.0)

    usage = store.get_weekly_usage(user["id"])
    assert usage.spend_usd == 3.5
    assert usage.limit_usd == MAX_USER_WEEKLY_COST_USD


def test_rate_limit_blocks_once_weekly_spend_reaches_the_cap(tmp_path):
    store = new_pilot_store()
    user = _make_user(store)
    _record_query(store, user["id"], MAX_USER_WEEKLY_COST_USD)

    limit = store.check_rate_limit(user["id"])
    assert not limit.allowed
    assert limit.message == "Weekly spending limit reached."


def test_spend_from_a_prior_week_does_not_count_toward_the_current_week(tmp_path):
    store = new_pilot_store()
    user = _make_user(store)
    _record_query(store, user["id"], MAX_USER_WEEKLY_COST_USD)

    last_week = "2020-01-01T00:00:00+00:00"
    with store._connect() as connection:
        connection.execute(
            "UPDATE query_events SET occurred_at = %s, day_utc = %s",
            (last_week, "2020-01-01"),
        )

    usage = store.get_weekly_usage(user["id"])
    assert usage.spend_usd == 0.0
    assert store.check_rate_limit(user["id"]).allowed


def test_weekly_usage_is_isolated_per_user(tmp_path):
    store = new_pilot_store()
    user_a = _make_user(store, "subject-a")
    user_b = _make_user(store, "subject-b")
    _record_query(store, user_a["id"], MAX_USER_WEEKLY_COST_USD)

    assert not store.check_rate_limit(user_a["id"]).allowed
    assert store.check_rate_limit(user_b["id"]).allowed
    assert store.get_weekly_usage(user_b["id"]).spend_usd == 0.0
