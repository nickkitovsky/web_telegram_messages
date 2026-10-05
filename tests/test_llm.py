from saved_messages.llm import _clean_tags


def test_clean_tags_normalizes_and_deduplicates_values() -> None:
    assert _clean_tags([" Work ", "work", "", "Reading"]) == ["work", "reading"]


def test_clean_tags_accepts_a_single_string() -> None:
    assert _clean_tags(" Notes ") == ["notes"]
