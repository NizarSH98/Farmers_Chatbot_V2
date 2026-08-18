from farmers_chatbot.arabizi import arabic_to_arabizi


def test_arabic_to_arabizi_is_deterministic_and_search_safe() -> None:
    assert arabic_to_arabizi("مياه الري") == "myah alry"
    assert arabic_to_arabizi("مِيَاهُ   الرَّي") == "myah alry"
