from streamlit.testing.v1 import AppTest


def test_streamlit_initial_render_has_no_exception(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    monkeypatch.setenv("LOCAL_PILOT_DB_PATH", str(tmp_path / "app.sqlite3"))
    monkeypatch.setenv("RUNTIME_DB_PATH", str(tmp_path / "app.sqlite3"))
    from farmers_chatbot.streamlit_app import get_services

    get_services.clear()
    app = AppTest.from_file("rag_chatbot.py", default_timeout=60).run()
    assert not app.exception
    assert len(app.chat_input) == 1


def test_streamlit_retrieval_fallback_conversation(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    monkeypatch.setenv("LOCAL_PILOT_DB_PATH", str(tmp_path / "app.sqlite3"))
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


def test_streamlit_defaults_to_arabic_and_settings_open(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    monkeypatch.setenv("LOCAL_PILOT_DB_PATH", str(tmp_path / "ui.sqlite3"))
    from farmers_chatbot.streamlit_app import get_services

    get_services.clear()
    app = AppTest.from_file("rag_chatbot.py", default_timeout=60).run()
    assert not app.exception
    labels = [button.label for button in app.button]
    assert "＋ محادثة جديدة" in labels
    assert "📁 إدارة المشاريع" in labels
    settings = next(button for button in app.button if button.label == "⚙️ الإعدادات")
    settings.click().run(timeout=60)
    assert not app.exception
    assert {
        "مستوى الإجابة",
        "نموذج الذكاء الاصطناعي",
        "طريقة طرح الأسئلة التوضيحية",
    }.issubset({control.label for control in app.selectbox})
