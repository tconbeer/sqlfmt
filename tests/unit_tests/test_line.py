from copy import deepcopy
from typing import List

import pytest

from sqlfmt.line import Line, Node, SqlfmtBracketError
from sqlfmt.mode import Mode
from sqlfmt.parser import Query
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
        "Token(type=TokenType.UNTERM_KEYWORD, prefix='', token='with', "
        "spos=(0, 0), epos=(0, 4), line='with abc as (select * from my_table)\\n')"
    )
    assert repr(simple_line.tokens[0]) == expected_token_repr
    new_token = eval(repr(simple_line.tokens[0]))
    assert simple_line.tokens[0] == new_token

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


def test_bare_append_newline(bare_line: Line) -> None:
    # this line has no nodes
    assert not bare_line.nodes
    assert not bare_line.previous_node

    bare_line.append_newline()
    assert bare_line.nodes
    new_last_node = bare_line.nodes[-1]
    assert new_last_node.token.type == TokenType.NEWLINE
    assert (new_last_node.token.spos, new_last_node.token.epos) == ((0, 0), (0, 1))


def test_bare_with_previous_append_newline(bare_line: Line, simple_line: Line) -> None:
    bare_line.previous_node = simple_line.nodes[-1]
    bare_line.append_newline()
    assert bare_line.nodes
    new_last_node = bare_line.nodes[-1]
    previous_token = simple_line.nodes[-1].token
    expected_position = (
        (previous_token.epos),
        (previous_token.epos[0], previous_token.epos[1] + 1),
    )
    assert (new_last_node.token.spos, new_last_node.token.epos) == expected_position


def test_simple_append_newline(simple_line: Line) -> None:

    # this line already ends with a newline
    last_node = simple_line.nodes[-1]
    assert last_node.token.type == TokenType.NEWLINE
    assert last_node.previous_node
    assert last_node.previous_node.token.type != TokenType.NEWLINE

    simple_line.append_newline()
    new_last_node = simple_line.nodes[-1]
    assert new_last_node != last_node
    assert new_last_node.token.type == TokenType.NEWLINE
    assert new_last_node.previous_node == last_node
    assert new_last_node.previous_node.token == last_node.token


def test_ends_with_comma(simple_line: Line) -> None:

    last_node = simple_line.nodes[-1]
    assert not last_node.token.type == TokenType.COMMA
    assert not simple_line.ends_with_comma

    comma = Token(
        type=TokenType.COMMA,
        prefix="",
        token=",",
        spos=last_node.token.epos,
        epos=(last_node.token.epos[0], last_node.token.epos[1] + 1),
        line=last_node.token.line,
    )

    simple_line.append_token(comma)

    assert simple_line.nodes[-1].token.type == TokenType.COMMA
    assert simple_line.ends_with_comma

    simple_line.append_newline()
    assert simple_line.nodes[-1].token.type == TokenType.NEWLINE
    assert simple_line.ends_with_comma


def test_ends_with_comment(simple_line: Line) -> None:

    last_node = simple_line.nodes[-1]
    assert not last_node.token.type == TokenType.COMMENT
    assert not simple_line.ends_with_comment

    comment = Token(
        type=TokenType.COMMENT,
        prefix="",
        token="-- my comment",
        spos=last_node.token.epos,
        epos=(last_node.token.epos[0], last_node.token.epos[1] + 13),
        line=last_node.token.line,
    )

    simple_line.append_token(comment)

    assert simple_line.nodes[-1].token.type == TokenType.COMMENT
    assert simple_line.ends_with_comment

    simple_line.append_newline()
    assert simple_line.nodes[-1].token.type == TokenType.NEWLINE
    assert simple_line.ends_with_comment

    assert not simple_line.is_standalone_comment


def test_is_standalone_comment(bare_line: Line, simple_line: Line) -> None:

    assert not bare_line.is_standalone_comment
    assert not simple_line.is_standalone_comment

    comment = Token(
        type=TokenType.COMMENT,
        prefix="",
        token="-- my comment",
        spos=(0, 0),
        epos=(0, 13),
        line="does not matter",
    )

    bare_line.append_token(comment)
    simple_line.append_token(comment)

    assert bare_line.is_standalone_comment
    assert not simple_line.is_standalone_comment

    bare_line.append_newline()
    simple_line.append_newline()

    assert bare_line.is_standalone_comment
    assert not simple_line.is_standalone_comment


def test_is_standalone_multiline_node(bare_line: Line, simple_line: Line) -> None:

    assert not bare_line.is_standalone_multiline_node
    assert not simple_line.is_standalone_multiline_node

    comment = Token(
        type=TokenType.COMMENT,
        prefix="",
        token="/*\nmy comment\n*/",
        spos=(0, 0),
        epos=(2, 2),
        line="/*\nmy comment\n*/",
    )

    bare_line.append_token(comment)
    simple_line.append_token(comment)

    assert bare_line.is_standalone_comment
    assert bare_line.is_standalone_multiline_node
    assert not simple_line.is_standalone_comment
    assert not simple_line.is_standalone_multiline_node

    bare_line.append_newline()
    simple_line.append_newline()

    assert bare_line.is_standalone_comment
    assert bare_line.is_standalone_multiline_node
    assert not simple_line.is_standalone_comment
    assert not simple_line.is_standalone_multiline_node


def test_last_content_index(simple_line: Line) -> None:
    idx = simple_line.last_content_index
    assert str(simple_line.nodes[idx]) == ")"


def test_calculate_depth_exception() -> None:

    close_paren = Token(
        type=TokenType.BRACKET_CLOSE,
        prefix="",
        token=")",
        spos=(0, 0),
        epos=(0, 1),
        line=")",
    )

    with pytest.raises(SqlfmtBracketError):
        Node.calculate_depth(close_paren, inherited_depth=0, open_brackets=[])


def test_closes_bracket_from_previous_line(
    simple_line: Line, default_mode: Mode
) -> None:
    assert not simple_line.closes_bracket_from_previous_line

    source_string = (
        "case\n"
        "    when\n"
        "        (\n"
        "            field_one\n"
        "            + (field_two)\n"
        "            + field_three\n"
        "        )\n"
        "    then true\n"
        "end\n"
    )
    q = Query.from_source(source_string=source_string, mode=default_mode)
    result = [line.closes_bracket_from_previous_line for line in q.lines]
    expected = [False, False, False, False, False, False, True, False, True]
    assert result == expected


def test_identifier_whitespace(default_mode: Mode) -> None:
    """
    Ensure we do not inject spaces into qualified identifier names
    """
    source_string = (
        "my_schema.my_table,\n"
        "my_schema.*,\n"
        "{{ my_schema }}.my_table,\n"
        "my_schema.{{ my_table }},\n"
        "my_database.my_schema.my_table,\n"
        'my_schema."my_table",\n'
        '"my_schema".my_table,\n'
        '"my_schema"."my_table",\n'
        '"my_schema".*,\n'
    )
    q = Query.from_source(source_string=source_string, mode=default_mode)
    parsed_string = "".join(str(line) for line in q.lines)
    assert source_string == parsed_string
