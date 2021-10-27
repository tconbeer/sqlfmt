import pytest

from sqlfmt.dialect import Dialect, Postgres, SqlfmtParsingError, group
from sqlfmt.token import Token, TokenType


def test_group() -> None:
    regex = group(r"a", r"b", r"\d")
    assert regex == r"(a|b|\d)"

    group_of_one = group(r"\w+")
    assert group_of_one == r"(\w+)"


def test_dialect() -> None:
    # can't instantiate abc
    with pytest.raises(TypeError):
        _ = Dialect()  # type: ignore


class TestPostgres:
    @pytest.fixture(scope="class")
    def postgres(self) -> Postgres:
        return Postgres()

    def test_patterns_are_complete(self, postgres: Postgres) -> None:
        # make sure Dialect defines a match for every TokenType
        for t in list(TokenType):
            assert postgres.PATTERNS[t]

    def test_postgres_trivial_query(self, postgres: Postgres) -> None:
        assert isinstance(postgres, Dialect)

        basic_line = "select 1"
        gen = postgres.tokenize_line(line=basic_line, lnum=0)

        expected_token = Token(
            TokenType.UNTERM_KEYWORD, "", "select", (0, 0), (0, 6), "select 1"
        )
        assert next(gen) == expected_token

        expected_token = Token(TokenType.NUMBER, " ", "1", (0, 7), (0, 8), "select 1")
        assert next(gen) == expected_token

        with pytest.raises(StopIteration):
            next(gen)

    def test_regex_easy_match(self, postgres: Postgres) -> None:

        should_match_exactly = [
            (TokenType.JINJA, "{% set my_var=macro('abc 123') %}"),
            (TokenType.JINJA_START, "{#"),
            (TokenType.JINJA_END, "}}"),
            (TokenType.QUOTED_NAME, '"my_quoted_field_name"'),
            (TokenType.COMMENT, "-- my comment"),
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
            (TokenType.COMMA, ","),
            (TokenType.DOT, "."),
            (TokenType.NEWLINE, "\n"),
            (TokenType.UNTERM_KEYWORD, "select DISTINCT"),
            (TokenType.NAME, "my_table_45"),
        ]

        # make sure our compiled programs match these values exactly
        for tt, v in should_match_exactly:
            prog = postgres.programs[tt]
            match = prog.match(v)
            assert match is not None, str(tt) + " regex doesn't match " + str(v)
            start, end = match.span(1)

            assert v[start:end] == v, str(tt) + " regex doesn't match " + str(v)

    def test_regex_anti_match(self, postgres: Postgres) -> None:

        should_not_match = [
            (TokenType.JINJA, "{% mismatched brackets }}"),
            (TokenType.JINJA_START, "{"),
            (TokenType.JINJA_END, "}"),
            (TokenType.QUOTED_NAME, "my_unquoted_name"),
            (TokenType.COMMENT, "# wrong comment delimiter"),
            (TokenType.DOUBLE_COLON, ":"),
            (TokenType.OPERATOR, "."),
            (TokenType.UNTERM_KEYWORD, "selection"),
        ]

        # make sure our compiled programs do not match these values
        for tt, v in should_not_match:
            prog = postgres.programs[tt]
            match = prog.match(v)
            assert match is None, str(tt) + " regex should not match " + str(v)

    def test_regex_should_not_match_empty_string(self, postgres: Postgres) -> None:
        for token_type, prog in postgres.programs.items():
            match = prog.match("")
            assert match is None, str(token_type)

    def test_error_token(self, postgres: Postgres) -> None:
        gen = postgres.tokenize_line(line="select ?\n", lnum=33)
        select = next(gen)
        assert select

        with pytest.raises(SqlfmtParsingError) as e:
            _ = next(gen)
            assert "at 33:7" in str(e.value)

    def test_search_for_one_token(self, postgres: Postgres) -> None:
        line = "select 1 from my_table\n"

        expected_token = Token(
            type=TokenType.NUMBER,
            prefix="select ",
            token="1",
            spos=(0, 7),
            epos=(0, 8),
            line="select 1 from my_table\n",
        )

        actual_token = postgres.search_for_token([TokenType.NUMBER], line=line, lnum=0)
        assert actual_token == expected_token

    def test_search_for_multiple_tokens(self, postgres: Postgres) -> None:
        line = "select 1 from my_table\n"

        expected_token = Token(
            type=TokenType.NUMBER,
            prefix=" ",
            token="1",
            spos=(0, 7),
            epos=(0, 8),
            line="select 1 from my_table\n",
        )

        actual_token = postgres.search_for_token(
            [TokenType.NUMBER, TokenType.UNTERM_KEYWORD], line=line, lnum=0, skipchars=6
        )
        assert actual_token == expected_token
