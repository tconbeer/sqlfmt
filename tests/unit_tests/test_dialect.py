import pytest

from sqlfmt.dialect import Dialect, Polyglot, group
from sqlfmt.token import TokenType


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

    def test_patterns_are_complete(self, polyglot: Polyglot) -> None:
        # make sure Dialect defines a match for every TokenType
        for t in list(TokenType):
            assert polyglot.PATTERNS[t]

    @pytest.mark.parametrize(
        "token_type,value",
        [
            (TokenType.FMT_OFF, "-- fmt: off"),
            (TokenType.FMT_OFF, "--FMT: off"),
            (TokenType.FMT_OFF, "# fmt: off"),
            (TokenType.FMT_ON, "--fmt: ON"),
            (TokenType.JINJA, "{% set my_var=macro('abc 123') %}"),
            (TokenType.JINJA_COMMENT, "{# A COMMENT #}"),
            (TokenType.JINJA_START, "{%"),
            (TokenType.JINJA_END, "}}"),
            (TokenType.QUOTED_NAME, "`my_quoted_field_name`"),
            (TokenType.QUOTED_NAME, "'my_quoted_literal'"),
            (TokenType.QUOTED_NAME, '"my_quoted_field_name"'),
            (TokenType.COMMENT, "-- my comment"),
            (TokenType.COMMENT, "--no-space comment"),
            (TokenType.COMMENT, "# mysql-style # comments"),
            (TokenType.COMMENT, "#nospace"),
            (TokenType.COMMENT_START, "/*"),
            (TokenType.COMMENT_END, "*/"),
            (TokenType.STATEMENT_START, "case"),
            (TokenType.STATEMENT_END, "END"),
            (TokenType.STAR, "*"),
            (TokenType.NUMBER, "145.8"),
            (TokenType.NUMBER, "-.58"),
            (TokenType.BRACKET_OPEN, "["),
            (TokenType.BRACKET_CLOSE, ")"),
            (TokenType.DOUBLE_COLON, "::"),
            (TokenType.OPERATOR, "<>"),
            (TokenType.OPERATOR, "||"),
            (TokenType.WORD_OPERATOR, "as"),
            (TokenType.WORD_OPERATOR, "AND"),
            (TokenType.COMMA, ","),
            (TokenType.DOT, "."),
            (TokenType.UNTERM_KEYWORD, "select DISTINCT"),
            (TokenType.UNTERM_KEYWORD, "select"),
            (TokenType.UNTERM_KEYWORD, "select\n\t    distinct"),
            (TokenType.UNTERM_KEYWORD, "select top 25"),
            (TokenType.UNTERM_KEYWORD, "select all"),
            (TokenType.UNTERM_KEYWORD, "natural\t    full outer join"),
            (TokenType.UNTERM_KEYWORD, "left join"),
            (TokenType.UNTERM_KEYWORD, "join"),
            (TokenType.NAME, "my_table_45"),
            (TokenType.NEWLINE, "\n"),
        ],
    )
    def test_regex_exact_match(
        self, polyglot: Polyglot, token_type: TokenType, value: str
    ) -> None:

        prog = polyglot.programs[token_type]
        match = prog.match(value)
        assert match is not None, str(token_type) + " regex doesn't match " + str(value)
        start, end = match.span(1)

        assert value[start:end] == value, (
            str(token_type) + " regex doesn't exactly match " + str(value)
        )

    def test_regex_anti_match(self, polyglot: Polyglot) -> None:

        should_not_match = [
            (TokenType.FMT_OFF, "# fmt:"),
            (TokenType.FMT_OFF, "-- fmt: off but not really"),
            (TokenType.JINJA, "{% mismatched brackets }}"),
            (TokenType.JINJA_START, "{"),
            (TokenType.JINJA_END, "}"),
            (TokenType.QUOTED_NAME, "my_unquoted_name"),
            (TokenType.DOUBLE_COLON, ":"),
            (TokenType.OPERATOR, "."),
            (TokenType.UNTERM_KEYWORD, "selection"),
        ]

        # make sure our compiled programs do not match these values
        for tt, v in should_not_match:
            prog = polyglot.programs[tt]
            match = prog.match(v)
            assert match is None, str(tt) + " regex should not match " + str(v)

    def test_regex_should_not_match_empty_string(self, polyglot: Polyglot) -> None:
        for token_type, prog in polyglot.programs.items():
            match = prog.match("")
            assert match is None, str(token_type)

    def test_match_first_jinja_Tag(self, polyglot: Polyglot) -> None:
        source_string = (
            "{{ event_cte.source_cte_name}}.{{ event_cte.primary_key }} "
            "|| '-' || '{{ event_cte.event_name }}'"
        )
        prog = polyglot.programs[TokenType.JINJA]
        match = prog.match(source_string)

        assert match is not None
        start, end = match.span(1)
        assert source_string[start:end] == "{{ event_cte.source_cte_name}}"
