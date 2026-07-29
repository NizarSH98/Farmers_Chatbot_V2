from streamlit.testing.v1 import AppTest


def test_streamlit_initial_render_has_no_exception(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    monkeypatch.setenv("RUNTIME_DB_PATH", str(tmp_path / "app.sqlite3"))
    from farmers_chatbot.streamlit_app import get_services

    get_services.clear()
    app = AppTest.from_file("rag_chatbot.py", default_timeout=60).run()
    assert not app.exception
    assert len(app.chat_input) == 1


def test_streamlit_retrieval_fallback_conversation(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    monkeypatch.setenv("RUNTIME_DB_PATH", str(tmp_path / "app.sqlite3"))
    from farmers_chatbot.streamlit_app import get_services

    get_services.clear()
    app = AppTest.from_file("rag_chatbot.py", default_timeout=60).run()
    app.chat_input[0].set_value(
        "What has ESDU tested with livestock farmers in Akkar?"
    ).run(timeout=60)
    assert not app.exception
    assert [message.name for message in app.chat_message] == ["user", "assistant"]
    app.run(timeout=60)
    assert not app.exception
    assert [message.name for message in app.chat_message] == ["user", "assistant"]
