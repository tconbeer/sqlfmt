from typing import Dict

import pytest

from sqlfmt.dialect import Dialect, Postgres, group
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
        for t in [t for t in list(TokenType) if t != TokenType.ERROR_TOKEN]:
            assert postgres.PATTERNS[t]

    def test_postgres_trivial_query(self, postgres: Postgres) -> None:
        assert isinstance(postgres, Dialect)

        basic_line = "select 1"
        gen = postgres.tokenize_line(line=basic_line, lnum=0)

        expected_token = Token(
            TokenType.TOP_KEYWORD, "", "select", (0, 0), (0, 6), "select 1"
        )
        assert next(gen) == expected_token

        expected_token = Token(TokenType.NUMBER, " ", "1", (0, 7), (0, 8), "select 1")
        assert next(gen) == expected_token

        with pytest.raises(StopIteration):
            next(gen)

    def test_regex_easy_match(self, postgres: Postgres) -> None:

        should_match_exactly: Dict[TokenType, str] = {
            TokenType.JINJA: "{% set my_var=macro('abc 123') %}",
            TokenType.JINJA_START: "{#",
            TokenType.JINJA_END: "}}",
            TokenType.QUOTED_NAME: '"my_quoted_field_name"',
            TokenType.COMMENT: "-- my comment",
            TokenType.COMMENT_START: "/*",
            TokenType.COMMENT_END: "*/",
            TokenType.STATEMENT_START: "case",
            TokenType.STATEMENT_END: "END",
            TokenType.NUMBER: "145.8",
            TokenType.BRACKET_OPEN: "[",
            TokenType.BRACKET_CLOSE: ")",
            TokenType.DOUBLE_COLON: "::",
            TokenType.OPERATOR: "<>",
            TokenType.COMMA: ",",
            TokenType.DOT: ".",
            TokenType.NEWLINE: "\n",
            TokenType.TOP_KEYWORD: "select DISTINCT",
            TokenType.NAME: "my_table_45",
        }

        # make sure we define an easy match for each TokenType
        for t in [t for t in list(TokenType) if t != TokenType.ERROR_TOKEN]:
            assert should_match_exactly[t]

        # make sure our compiled programs match these values exactly
        for k, v in should_match_exactly.items():
            prog = postgres.programs[k]
            match = prog.match(v)
            assert match is not None, str(k) + " regex doesn't match " + str(v)
            start, end = match.span(1)

            assert v[start:end] == v, str(k) + " regex doesn't match " + str(v)

    def test_regex_anti_match(self, postgres: Postgres) -> None:

        should_not_match: Dict[TokenType, str] = {
            TokenType.JINJA: "{% mismatched brackets }}",
            TokenType.JINJA_START: "{",
            TokenType.JINJA_END: "}",
            TokenType.QUOTED_NAME: "my_unquoted_name",
            TokenType.COMMENT: "# wrong comment delimiter",
            TokenType.DOUBLE_COLON: ":",
            TokenType.OPERATOR: ".",
            TokenType.TOP_KEYWORD: "selection",
        }

        # make sure our compiled programs do not match these values
        for k, v in should_not_match.items():
            prog = postgres.programs[k]
            match = prog.match(v)
            assert match is None, str(k) + " regex should not match " + str(v)

    def test_regex_should_not_match_empty_string(self, postgres: Postgres) -> None:
        for token_type, prog in postgres.programs.items():
            match = prog.match("")
            assert match is None, str(token_type)
