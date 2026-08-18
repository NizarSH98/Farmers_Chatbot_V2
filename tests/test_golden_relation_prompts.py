from scripts.golden_relation_prompts import relation_hint


def test_relation_hint_names_both_graph_ends() -> None:
    value = relation_hint("en", "supports_action", "soil test", "فحص التربة", "fertilizer plan", "خطة السماد")
    assert "soil test" in value
    assert "fertilizer plan" in value
    assert "supports action" in value


def test_arabizi_hint_uses_latin_labels() -> None:
    value = relation_hint("arabizi", "depends_on", "irrigation", "الري", "water", "المياه")
    assert "irrigation" in value and "water" in value
    assert "الري" not in value
