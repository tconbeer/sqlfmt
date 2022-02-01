from copy import deepcopy
from typing import List

import pytest

from sqlfmt.comment import Comment
from sqlfmt.line import Line
from sqlfmt.mode import Mode
from sqlfmt.token import Token, TokenType
from tests.util import read_test_data


@pytest.fixture
def source_string() -> str:
    return "with abc as (select * from my_table)\n"


@pytest.fixture
def bare_line() -> Line:
    line = Line(previous_node=None)
    return line


@pytest.fixture
def tokens() -> List[Token]:
    tokens = [
        Token(type=TokenType.UNTERM_KEYWORD, prefix="", token="with", spos=0, epos=4),
        Token(type=TokenType.NAME, prefix=" ", token="abc", spos=4, epos=8),
        Token(type=TokenType.WORD_OPERATOR, prefix=" ", token="as", spos=8, epos=11),
        Token(type=TokenType.BRACKET_OPEN, prefix=" ", token="(", spos=11, epos=13),
        Token(
            type=TokenType.UNTERM_KEYWORD, prefix="", token="select", spos=13, epos=19
        ),
        Token(type=TokenType.STAR, prefix=" ", token="*", spos=19, epos=21),
        Token(
            type=TokenType.UNTERM_KEYWORD, prefix=" ", token="from", spos=21, epos=26
        ),
        Token(type=TokenType.NAME, prefix=" ", token="my_table", spos=26, epos=35),
        Token(type=TokenType.BRACKET_CLOSE, prefix="", token=")", spos=35, epos=36),
        Token(type=TokenType.NEWLINE, prefix="", token="\n", spos=36, epos=36),
    ]
    return tokens


@pytest.fixture
def simple_line(tokens: List[Token], bare_line: Line) -> Line:
    simple_line = deepcopy(bare_line)
    for token in tokens:
        simple_line.append_token(token)
    return simple_line


def test_bare_line(bare_line: Line) -> None:
    assert str(bare_line) == ""

    assert not bare_line.starts_with_unterm_keyword
    assert not bare_line.contains_unterm_keyword
    assert not bare_line.contains_multiline_node
    assert not bare_line.contains_operator
    assert not bare_line.starts_with_comma
    assert not bare_line.starts_with_operator
    assert not bare_line.starts_with_low_priority_merge_operator
    assert not bare_line.is_blank_line
    assert not bare_line.is_standalone_multiline_node
    assert not bare_line.is_too_long(88)
    assert not bare_line.opens_new_bracket
    assert bare_line.open_brackets == []
    assert bare_line.open_jinja_blocks == []


def test_simple_line(
    source_string: str, tokens: List[Token], simple_line: Line
) -> None:
    assert simple_line.depth == (0, 0)
    assert len(simple_line.nodes) == len(tokens)
    assert simple_line.open_brackets == []

    assert str(simple_line) == source_string

    expected_token_repr = (
        "Token(type=TokenType.UNTERM_KEYWORD, prefix='', token='with', spos=0, epos=4)"
    )
    assert repr(simple_line.tokens[0]) == expected_token_repr
    new_token = eval(repr(simple_line.tokens[0]))
    assert simple_line.tokens[0] == new_token

    expected_node_repr = (
        "Node(\n"
        "\ttoken='Token(type=TokenType.UNTERM_KEYWORD, token=with, spos=0)',\n"
        "\tprevious_node=None,\n"
        "\tdepth=(0, 0),\n"
        "\tprefix=' ',\n"
        "\tvalue='with',\n"
        "\topen_brackets=[],\n"
        "\topen_jinja_blocks=[],\n"
        "\tformatting_disabled=False\n"
        ")"
    )
    assert repr(simple_line.nodes[0]) == expected_node_repr

    assert simple_line.starts_with_unterm_keyword
    assert simple_line.contains_unterm_keyword
    assert simple_line.contains_operator
    assert not simple_line.starts_with_comma
    assert not simple_line.starts_with_operator
    assert not simple_line.starts_with_low_priority_merge_operator
    assert not simple_line.contains_multiline_node
    assert not simple_line.is_blank_line
    assert not simple_line.is_standalone_multiline_node
    assert not simple_line.is_too_long(88)

    assert simple_line.nodes[5].token.type == TokenType.STAR
    assert not simple_line.nodes[5].is_multiplication_star


def test_bare_append_newline(bare_line: Line) -> None:
    # this line has no nodes
    assert not bare_line.nodes
    assert not bare_line.previous_node

    bare_line.append_newline()
    assert bare_line.nodes
    assert bare_line.is_blank_line
    new_last_node = bare_line.nodes[-1]
    assert new_last_node.token.type == TokenType.NEWLINE
    assert (new_last_node.token.spos, new_last_node.token.epos) == (0, 0)


def test_bare_with_previous_open_lists(bare_line: Line, simple_line: Line) -> None:
    bare_line.previous_node = simple_line.nodes[-1]
    assert bare_line.open_jinja_blocks == simple_line.nodes[-1].open_jinja_blocks
    assert bare_line.open_brackets == simple_line.nodes[-1].open_brackets


def test_bare_with_previous_append_newline(bare_line: Line, simple_line: Line) -> None:
    bare_line.previous_node = simple_line.nodes[-1]
    bare_line.append_newline()
    assert bare_line.nodes
    new_last_node = bare_line.nodes[-1]
    previous_token = simple_line.nodes[-1].token
    expected_position = (
        previous_token.epos,
        previous_token.epos,
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


@pytest.mark.parametrize(
    "raw_comment,normalized_comment",
    [
        ("-- my comment", "-- my comment"),
        ("--my comment", "-- my comment"),
        ("--    my comment", "-- my comment"),
        ("# my comment", "# my comment"),
        ("#my comment", "# my comment"),
        ("#    my comment", "# my comment"),
        ("/* my comment */", "/* my comment */"),
        ("/*my comment*/", "/* my comment*/"),
        ("/*    my comment */", "/* my comment */"),
    ],
)
def test_comment_rendering(
    simple_line: Line, bare_line: Line, raw_comment: str, normalized_comment: str
) -> None:

    assert simple_line.render_with_comments(88) == str(simple_line)
    assert bare_line.render_with_comments(88) == str(bare_line)

    last_node = simple_line.nodes[-1]

    comment_token = Token(
        type=TokenType.COMMENT,
        prefix="",
        token=raw_comment,
        spos=last_node.token.epos,
        epos=last_node.token.epos + 13,
    )

    inline_comment = Comment(token=comment_token, is_standalone=False)
    bare_line.append_newline()
    bare_line.comments = [inline_comment]
    expected_bare_render = normalized_comment + "\n"
    assert bare_line.render_with_comments(88) == expected_bare_render

    simple_line.comments = [inline_comment]
    expected_inline_render = (
        str(simple_line).rstrip() + "  " + normalized_comment + "\n"
    )
    assert simple_line.render_with_comments(88) == expected_inline_render

    standalone_comment = Comment(token=comment_token, is_standalone=True)
    simple_line.comments = [standalone_comment]
    expected_standalone_render = (
        simple_line.prefix + normalized_comment + "\n" + str(simple_line)
    )
    assert simple_line.render_with_comments(88) == expected_standalone_render

    simple_line.comments = [standalone_comment, inline_comment]
    expected_multiple_render = (
        simple_line.prefix
        + normalized_comment
        + "\n"
        + simple_line.prefix
        + normalized_comment
        + "\n"
        + str(simple_line)
    )
    assert simple_line.render_with_comments(88) == expected_multiple_render


def test_long_comment_wrapping(simple_line: Line) -> None:
    last_node = simple_line.nodes[-1]
    comment_token = Token(
        type=TokenType.COMMENT,
        prefix="",
        token="-- " + ("asdf " * 20),
        spos=last_node.token.epos,
        epos=last_node.token.epos + 13,
    )
    comment = Comment(token=comment_token, is_standalone=False)
    simple_line.comments = [comment]
    expected_render = (
        "-- asdf asdf asdf asdf asdf asdf asdf asdf asdf asdf asdf asdf asdf asdf "
        "asdf asdf\n"
        "-- asdf asdf asdf asdf\n"
        "with abc as (select * from my_table)\n"
    )
    assert simple_line.render_with_comments(88) == expected_render


@pytest.mark.parametrize(
    "raw_comment",
    [
        "-- " + ("asdf" * 30),
        "{# " + ("asdf" * 30) + "#}",
        "/* " + ("asdf" * 30) + "*/",
    ],
)
def test_long_comments_that_are_not_wrapped(
    simple_line: Line, raw_comment: str
) -> None:
    last_node = simple_line.nodes[-1]
    comment_token = Token(
        type=TokenType.COMMENT,
        prefix="",
        token=raw_comment,
        spos=last_node.token.epos,
        epos=last_node.token.epos + 13,
    )
    comment = Comment(token=comment_token, is_standalone=False)
    simple_line.comments = [comment]
    expected_render = raw_comment + "\n" "with abc as (select * from my_table)\n"
    assert simple_line.render_with_comments(88) == expected_render


def test_is_standalone_multiline_node(bare_line: Line, simple_line: Line) -> None:

    assert not bare_line.is_standalone_multiline_node
    assert not simple_line.is_standalone_multiline_node

    multiline_node = Token(
        type=TokenType.JINJA_EXPRESSION,
        prefix="",
        token="{{\nmy JINJA\n}}",
        spos=0,
        epos=16,
    )

    bare_line.append_token(multiline_node)
    simple_line.append_token(multiline_node)

    assert bare_line.is_standalone_multiline_node
    assert not simple_line.is_standalone_multiline_node

    bare_line.append_newline()
    simple_line.append_newline()

    assert bare_line.is_standalone_multiline_node
    assert not simple_line.is_standalone_multiline_node


def test_is_standalone_jinja_statement(bare_line: Line, simple_line: Line) -> None:

    assert not bare_line.is_standalone_jinja_statement
    assert not simple_line.is_standalone_jinja_statement

    jinja_statement = Token(
        type=TokenType.JINJA_STATEMENT,
        prefix="",
        token="{% my JINJA %}",
        spos=0,
        epos=14,
    )

    bare_line.append_token(jinja_statement)
    simple_line.append_token(jinja_statement)

    assert bare_line.is_standalone_jinja_statement
    assert not simple_line.is_standalone_jinja_statement

    bare_line.append_newline()
    simple_line.append_newline()

    assert bare_line.is_standalone_jinja_statement
    assert not simple_line.is_standalone_jinja_statement


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
    q = default_mode.dialect.initialize_analyzer(
        line_length=default_mode.line_length
    ).parse_query(source_string=source_string)
    result = [line.closes_bracket_from_previous_line for line in q.lines]
    expected = [False, False, False, False, False, False, True, False, True]
    assert result == expected


@pytest.mark.parametrize(
    "source_string",
    [
        "my_schema.my_table\n",
        "my_table.*\n",
        '"my_table".*\n',
        "{{ my_schema }}.my_table\n",
        "my_schema.{{ my_table }}\n",
        "my_database.my_schema.my_table\n",
        'my_schema."my_table"\n',
        '"my_schema".my_table\n',
        '"my_schema"."my_table"\n',
        pytest.param("my_table.$2\n", marks=pytest.mark.xfail),
        pytest.param('"my_table".$2\n', marks=pytest.mark.xfail),
        "my_schema.{% if foo %}bar{% else %}baz{% endif %}\n",
        "json_field:key_name\n",
        'json:"KeyName"\n',
        "my_table.json_field:key_name\n",
        '"JSONField":"KeyName"::varchar\n',
        '"JSONField":"KeyName"::varchar\n',
        "my_array[1]\n",
        "my_array[1:2]\n",
        '"my_array"[1]\n',
        '"my_array"[1:2]\n',
    ],
)
def test_identifier_whitespace(default_mode: Mode, source_string: str) -> None:
    """
    Ensure we do not inject spaces into qualified identifier names
    """
    q = default_mode.dialect.initialize_analyzer(
        line_length=default_mode.line_length
    ).parse_query(source_string=source_string)
    parsed_string = "".join(str(line) for line in q.lines)
    assert source_string == parsed_string


def test_jinja_whitespace_after_newline(default_mode: Mode) -> None:
    source_string = "select *\nfrom {{model}}\nwhere {{ column_name }} < 0\n"
    q = default_mode.dialect.initialize_analyzer(
        line_length=default_mode.line_length
    ).parse_query(source_string=source_string)
    where_node = [node for node in q.nodes if node.value == "where"][0]
    assert where_node.prefix == " "  # one space


def test_capitalization(default_mode: Mode) -> None:
    source_string = (
        "SELECT A, B, \"C\", {{ D }}, e, 'f', 'G'\n" 'fROM "H"."j" Join I ON k And L\n'
    )
    expected = (
        "select a, b, \"C\", {{ D }}, e, 'f', 'G'\n" 'from "H"."j" join i on k and l\n'
    )
    q = default_mode.dialect.initialize_analyzer(
        line_length=default_mode.line_length
    ).parse_query(source_string=source_string)
    parsed_string = "".join(str(line) for line in q.lines)
    assert parsed_string == expected


def test_formatting_disabled(default_mode: Mode) -> None:
    source_string, _ = read_test_data(
        "unit_tests/test_line/test_formatting_disabled.sql"
    )
    q = default_mode.dialect.initialize_analyzer(
        line_length=default_mode.line_length
    ).parse_query(source_string=source_string)
    expected = [
        False,  # select
        True,  # -- fmt: off
        True,  # 1, 2, 3
        True,  # 4, 5, 6
        True,  # -- fmt: on
        False,  # from something
        True,  # join something_else -- fmt: off
        True,  # --fmt: on
        False,  # where format is true
    ]
    actual = [line.formatting_disabled for line in q.lines]
    assert actual == expected


def test_is_multiplication_star_bare_line(bare_line: Line) -> None:
    star = Token(
        type=TokenType.STAR,
        prefix="",
        token="*",
        spos=0,
        epos=1,
    )
    bare_line.append_token(star)
    assert bare_line.nodes[0].token == star
    assert not bare_line.nodes[0].is_multiplication_star
