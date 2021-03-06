from sqlfmt.analyzer import Analyzer


def test_whitespace_formatting(default_analyzer: Analyzer) -> None:
    source_string = "  select 1\n    from my_table\nwhere true"
    expected_string = "select 1\nfrom my_table\nwhere true\n"
    q = default_analyzer.parse_query(source_string=source_string)
    assert str(q) == expected_string
