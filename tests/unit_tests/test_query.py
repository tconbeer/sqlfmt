import pytest

from sqlfmt.analyzer import Analyzer


def test_whitespace_formatting(default_analyzer: Analyzer) -> None:
    source_string = "  select 1\n    from my_table\nwhere true"
    expected_string = "select 1\nfrom my_table\nwhere true\n"
    q = default_analyzer.parse_query(source_string=source_string)
    assert str(q) == expected_string


def test_only_comment_formatting(default_analyzer: Analyzer) -> None:
    source_string = "-- a comment"
    expected_string = "-- a comment\n"
    q = default_analyzer.parse_query(source_string=source_string)
    assert str(q) == expected_string


@pytest.mark.parametrize("source_string", ["", "\n"])
def test_empty_formatting(default_analyzer: Analyzer, source_string: str) -> None:
    expected_string = ""
    q = default_analyzer.parse_query(source_string=source_string)
    assert str(q) == expected_string
