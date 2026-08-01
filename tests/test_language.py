from farmers_chatbot.language import detect_language


def test_detects_arabic():
    assert detect_language("ما أفضل محصول في عكار؟") == "arabic"


def test_detects_english():
    assert detect_language("What grows well in Akkar?") == "english"


def test_empty_defaults_to_english():
    assert detect_language("") == "english"

