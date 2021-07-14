import re
from typing import Dict

import pytest

from sqlfmt.dialect import Dialect, Postgres, group
from sqlfmt.token import Token, TokenType


def test_group() -> None:
    regex = group(r"a", r"b", r"\d")

    assert regex == r"(a|b|\d)"


def test_dialect() -> None:

    # can't instantiate abc
    with pytest.raises(TypeError):
        _ = Dialect()  # type: ignore


def test_postgres_trivial_query() -> None:

    p = Postgres()
    assert isinstance(p, Dialect)

    basic_line = "select 1"
    gen = p.tokenize_line(line=basic_line, lnum=0)

    expected_token = Token(TokenType.TOP_KEYWORD, "select", (0, 0), (0, 6), "select 1")
    assert next(gen) == expected_token

    expected_token = Token(TokenType.NUMBER, "1", (0, 7), (0, 8), "select 1")
    assert next(gen) == expected_token

    with pytest.raises(StopIteration):
        next(gen)


def test_regex_easy_match() -> None:

    p = Postgres()

    should_match_exactly: Dict[TokenType, str] = {
        TokenType.JINJA_START: "{%",
        TokenType.JINJA_END: "}}",
        TokenType.QUOTED_NAME: '"my_quoted_field_name"',
        TokenType.COMMENT: "-- my comment",
        TokenType.COMMENT_START: "/*",
        TokenType.COMMENT_END: "*/",
        TokenType.NUMBER: "145.8",
        TokenType.BRACKET_OPEN: "[",
        TokenType.BRACKET_CLOSE: ")",
        TokenType.OPERATOR: "<>",
        TokenType.COMMA: ",",
        TokenType.DOT: ".",
        TokenType.NEWLINE: "\n",
        TokenType.TOP_KEYWORD: "union all",
        TokenType.NAME: "my_table",
    }

    for k, v in should_match_exactly.items():
        pattern = p.PATTERNS[k]
        match = re.match(pattern, v)
        assert match is not None, str(k) + " regex doesn't match " + str(v)
        start, end = match.span(0)

        assert v[start:end] == v, str(k) + " regex doesn't match " + str(v)

        broad_match = p.all_token_program.match(v)
        assert broad_match, "All Token Group doesn't match: " + str(k)
        start, end = match.span(0)

        assert v[start:end] == v, "All Token Group doesn't match: " + str(k)


def test_regex_should_not_match_empty_string() -> None:

    p = Postgres()

    for k, v in p.PATTERNS.items():
        match = re.match(v, "")
        assert match is None, str(k)
