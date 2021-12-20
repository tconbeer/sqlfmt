from typing import Counter, Dict

import pytest

from sqlfmt.dialect import Dialect, Polyglot, Rule, group


def test_group() -> None:
    regex = group(r"a", r"b", r"\d")
    assert regex == r"(a|b|\d)"

    group_of_one = group(r"\w+")
    assert group_of_one == r"(\w+)"


def test_dialect() -> None:
    # can't instantiate abc
    with pytest.raises(TypeError):
        _ = Dialect()  # type: ignore


class TestPolyglot:
    @pytest.fixture(scope="class")
    def polyglot(self) -> Polyglot:
        return Polyglot()

    @pytest.fixture(scope="class")
    def polyglot_rules_dict(self, polyglot: Polyglot) -> Dict[str, Rule]:
        return {rule.name: rule for rule in polyglot.get_rules()}

    def test_rule_props_are_unique(self, polyglot: Polyglot) -> None:
        name_counts = Counter([rule.name for rule in polyglot.RULES])
        assert max(name_counts.values()) == 1
        priority_counts = Counter([rule.priority for rule in polyglot.RULES])
        assert max(priority_counts.values()) == 1
        pattern_counts = Counter([rule.pattern for rule in polyglot.RULES])
        assert max(pattern_counts.values()) == 1

    @pytest.mark.parametrize(
        "rule_name,value",
        [
            ("fmt_off", "-- fmt: off"),
            ("fmt_off", "--FMT: off"),
            ("fmt_off", "# fmt: off"),
            ("fmt_on", "--fmt: ON"),
            ("jinja", "{% set my_var=macro('abc 123') %}"),
            ("jinja_comment", "{# A COMMENT #}"),
            ("jinja_start", "{%"),
            ("jinja_end", "}}"),
            ("quoted_name", "`my_backticked_field_name`"),
            ("quoted_name", "'my_quoted_literal'"),
            ("quoted_name", '"my_quoted_field_name"'),
            ("quoted_name", '"""triple " quotes!"""'),
            ("quoted_name", "'''triple '' singles!\\'''"),
            ("quoted_name", "$$ dollar delimited'$$"),
            ("quoted_name", "$label$ dollar delimited with label$label$"),
            ("quoted_name", "'single quote with '' doubled escape'"),
            ("quoted_name", "'single quote \\' c escape'"),
            ("quoted_name", '"double quote with "" doubled escape"'),
            ("quoted_name", '"double quote \\" c escape"'),
            ("quoted_name", "`backtick with \\` c escape`"),
            ("quoted_name", 'r"bq raw string"'),
            ("quoted_name", "U&'pg unicode string'"),
            ("quoted_name", 'rb"""bq raw bytes string"""'),
            ("comment", "-- my comment"),
            ("comment", "--no-space comment"),
            ("comment", "# mysql-style # comments"),
            ("comment", "#nospace"),
            ("comment_start", "/*"),
            ("comment_end", "*/"),
            ("statement_start", "case"),
            ("statement_end", "END"),
            ("star", "*"),
            ("number", "145.8"),
            ("number", "-.58"),
            ("bracket_open", "["),
            ("bracket_close", ")"),
            ("double_colon", "::"),
            ("semicolon", ";"),
            ("operator", "<>"),
            ("operator", "||"),
            ("word_operator", "is"),
            ("word_operator", "in"),
            ("as", "as"),
            ("on", "on"),
            ("boolean_operator", "AND"),
            ("comma", ","),
            ("dot", "."),
            ("unterm_keyword", "select DISTINCT"),
            ("unterm_keyword", "select"),
            ("unterm_keyword", "select\n\t    distinct"),
            ("unterm_keyword", "select top 25"),
            ("unterm_keyword", "select all"),
            ("unterm_keyword", "natural\t    full outer join"),
            ("unterm_keyword", "left join"),
            ("unterm_keyword", "join"),
            ("name", "my_table_45"),
            ("newline", "\n"),
        ],
    )
    def test_regex_exact_match(
        self, polyglot_rules_dict: Dict[str, Rule], rule_name: str, value: str
    ) -> None:
        rule = polyglot_rules_dict[rule_name]
        match = rule.program.match(value)
        assert match is not None, f"{rule_name} regex doesn't match {value}"
        start, end = match.span(1)

        assert (
            value[start:end] == value
        ), f"{rule_name} regex doesn't exactly match {value}"

    @pytest.mark.parametrize(
        "rule_name,value",
        [
            ("fmt_off", "# fmt:"),
            ("fmt_off", "-- fmt: off but not really"),
            ("jinja", "{% mismatched brackets }}"),
            ("jinja_start", "{"),
            ("jinja_end", "}"),
            ("quoted_name", "my_unquoted_name"),
            ("double_colon", ":"),
            ("operator", "."),
            ("unterm_keyword", "selection"),
        ],
    )
    def test_regex_anti_match(
        self, polyglot_rules_dict: Dict[str, Rule], rule_name: str, value: str
    ) -> None:
        """make sure our compiled programs do not match these values"""
        rule = polyglot_rules_dict[rule_name]
        match = rule.program.match(value)
        assert match is None, f"{rule_name} regex should not match {value}"

    def test_regex_should_not_match_empty_string(self, polyglot: Polyglot) -> None:
        for rule in polyglot.RULES:
            match = rule.program.match("")
            assert match is None, f"{rule.name} rule matches empty string"

    def test_match_first_jinja_Tag(self, polyglot_rules_dict: Dict[str, Rule]) -> None:
        source_string = (
            "{{ event_cte.source_cte_name}}.{{ event_cte.primary_key }} "
            "|| '-' || '{{ event_cte.event_name }}'"
        )
        rule = polyglot_rules_dict["jinja"]
        match = rule.program.match(source_string)

        assert match is not None
        start, end = match.span(1)
        assert source_string[start:end] == "{{ event_cte.source_cte_name}}"
