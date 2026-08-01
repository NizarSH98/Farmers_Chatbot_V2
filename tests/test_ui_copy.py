from farmers_chatbot.ui_copy import (
    DEFAULT_UI_LANGUAGE,
    MODEL_DESCRIPTION_KEYS,
    UI_COPY,
    normalize_ui_language,
    text,
)


def test_ui_defaults_to_arabic_and_language_is_exclusive():
    assert DEFAULT_UI_LANGUAGE == "ar"
    assert normalize_ui_language(None) == "ar"
    assert normalize_ui_language("unknown") == "ar"
    assert normalize_ui_language("en") == "en"


def test_arabic_and_english_interfaces_have_matching_copy_keys():
    assert set(UI_COPY["ar"]) == set(UI_COPY["en"])


def test_primary_arabic_copy_is_clear_and_not_mojibake():
    assert text("ar", "new_chat") == "محادثة جديدة"
    assert "Ø" not in " ".join(UI_COPY["ar"].values())
    assert "اسأل" in text("ar", "intro")


def test_every_model_has_localized_plain_language_help():
    assert MODEL_DESCRIPTION_KEYS
    for copy_key in MODEL_DESCRIPTION_KEYS.values():
        assert text("ar", copy_key)
        assert text("en", copy_key)
