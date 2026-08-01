import farmers_chatbot.streamlit_app as app


def test_public_legal_links_use_configured_application_url(monkeypatch):
    monkeypatch.setattr(app, "APP_PUBLIC_URL", "https://raise.streamlit.app")
    assert app._legal_url("privacy") == (
        "https://raise.streamlit.app?legal=privacy"
    )
    assert app._legal_url("terms") == "https://raise.streamlit.app?legal=terms"


def test_public_legal_links_work_before_deployment_url_is_known(monkeypatch):
    monkeypatch.setattr(app, "APP_PUBLIC_URL", "")
    assert app._legal_url("privacy") == "?legal=privacy"
