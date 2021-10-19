from copy import deepcopy
from typing import List

import pytest

from sqlfmt.line import Line
from sqlfmt.token import Token, TokenType


@pytest.fixture
def source_string() -> str:
    return "with abc as (select * from my_table)\n"


@pytest.fixture
def bare_line(source_string: str) -> Line:
    line = Line(source_string, previous_node=None)
    return line


@pytest.fixture
def tokens(source_string: str) -> List[Token]:
    tokens = [
        Token(
            type=TokenType.UNTERM_KEYWORD,
            prefix="",
            token="with",
            spos=(0, 0),
            epos=(0, 4),
            line=source_string,
        ),
        Token(
            type=TokenType.NAME,
            prefix=" ",
            token="abc",
            spos=(0, 5),
            epos=(0, 8),
            line=source_string,
        ),
        Token(
            type=TokenType.NAME,
            prefix=" ",
            token="as",
            spos=(0, 9),
            epos=(0, 11),
            line=source_string,
        ),
        Token(
            type=TokenType.BRACKET_OPEN,
            prefix=" ",
            token="(",
            spos=(0, 12),
            epos=(0, 13),
            line=source_string,
        ),
        Token(
            type=TokenType.UNTERM_KEYWORD,
            prefix="",
            token="select",
            spos=(0, 13),
            epos=(0, 19),
            line=source_string,
        ),
        Token(
            type=TokenType.OPERATOR,
            prefix=" ",
            token="*",
            spos=(0, 20),
            epos=(0, 21),
            line=source_string,
        ),
        Token(
            type=TokenType.UNTERM_KEYWORD,
            prefix=" ",
            token="from",
            spos=(0, 22),
            epos=(0, 26),
            line=source_string,
        ),
        Token(
            type=TokenType.NAME,
            prefix=" ",
            token="my_table",
            spos=(0, 27),
            epos=(0, 35),
            line=source_string,
        ),
        Token(
            type=TokenType.BRACKET_CLOSE,
            prefix="",
            token=")",
            spos=(0, 35),
            epos=(0, 36),
            line=source_string,
        ),
        Token(
            type=TokenType.NEWLINE,
            prefix="",
            token="\n",
            spos=(0, 36),
            epos=(0, 37),
            line=source_string,
        ),
    ]
    return tokens


@pytest.fixture
def simple_line(source_string: str, tokens: List[Token], bare_line: Line) -> Line:
    simple_line = deepcopy(bare_line)
    for token in tokens:
        simple_line.append_token(token)
    return simple_line


def test_bare_line(source_string: str, bare_line: Line) -> None:
    assert bare_line.source_string == source_string
    assert str(bare_line) == ""

    assert not bare_line.starts_with_select
    assert not bare_line.starts_with_unterm_keyword
    assert not bare_line.contains_unterm_keyword
    assert not bare_line.contains_comment
    assert not bare_line.contains_multiline_node
    assert not bare_line.ends_with_comma
    assert not bare_line.ends_with_comment
    assert not bare_line.is_standalone_comment
    assert not bare_line.is_standalone_multiline_node
    assert not bare_line.is_too_long(88)
    assert not bare_line.can_be_depth_split


def test_simple_line(
    source_string: str, tokens: List[Token], simple_line: Line
) -> None:
    assert simple_line.depth == 0
    assert simple_line.change_in_depth == 1
    assert len(simple_line.nodes) == len(tokens)
    assert simple_line.open_brackets == [tokens[0]]
    assert simple_line.depth_split == 1
    assert simple_line.first_comma is None

    assert str(simple_line) == source_string

    expected_token_repr = (
        "Token(type=<TokenType.UNTERM_KEYWORD: 19>, prefix='', token='with', "
        "spos=(0, 0), epos=(0, 4), line='with abc as (select * from my_table)\\n')"
    )
    assert repr(simple_line.tokens[0]) == expected_token_repr

    expected_node_repr = (
        "Node(\n\ttoken='Token(type=TokenType.UNTERM_KEYWORD, token=with, "
        "spos=(0, 0))',\n\tprevious_node=None,\n\tinherited_depth=0,\n\tdepth=0,"
        "\n\tchange_in_depth=1,\n\tprefix='',\n\tvalue='with',\n\topen_brackets=["
        "'Token(type=TokenType.UNTERM_KEYWORD, token=with, spos=(0, 0))']\n)"
    )
    assert repr(simple_line.nodes[0]) == expected_node_repr

    assert simple_line.starts_with_select
    assert simple_line.starts_with_unterm_keyword
    assert simple_line.contains_unterm_keyword
    assert not simple_line.contains_comment
    assert not simple_line.contains_multiline_node
    assert not simple_line.ends_with_comma
    assert not simple_line.ends_with_comment
    assert not simple_line.is_standalone_comment
    assert not simple_line.is_standalone_multiline_node
    assert not simple_line.is_too_long(88)
    assert simple_line.can_be_depth_split
