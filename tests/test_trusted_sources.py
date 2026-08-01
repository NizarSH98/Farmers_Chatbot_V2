from farmers_chatbot.trusted_sources import (
    host_is_trusted,
    requires_live_verification,
)


def test_trusted_registry_rejects_lookalike_domains():
    assert host_is_trusted("www.fao.org")
    assert host_is_trusted("agris.fao.org")
    assert not host_is_trusted("fao.org.evil.example")
    assert not host_is_trusted("random-blog.example")


def test_current_and_high_risk_questions_require_live_verification():
    assert requires_live_verification("What is the latest potato price?")
    assert requires_live_verification("Which pesticide dose is registered now?")
    assert not requires_live_verification("Explain photosynthesis in simple language.")

