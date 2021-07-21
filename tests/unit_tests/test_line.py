from sqlfmt.line import Line
from sqlfmt.token import Token, TokenType


def test_basic_line() -> None:
    source_string = "with abc as (select * from my_table)\n"

    line = Line(source_string, previous_node=None)

    assert line.source_string == source_string
    assert str(line) == ""

    tokens = [
        Token(
            type=TokenType.TOP_KEYWORD,
            prefix="",
            token="with",
            spos=(0, 0),
            epos=(0, 4),
            line="with abc as (select * from my_table\n)",
        ),
        Token(
            type=TokenType.NAME,
            prefix=" ",
            token="abc",
            spos=(0, 5),
            epos=(0, 8),
            line="with abc as (select * from my_table\n)",
        ),
        Token(
            type=TokenType.NAME,
            prefix=" ",
            token="as",
            spos=(0, 9),
            epos=(0, 11),
            line="with abc as (select * from my_table\n)",
        ),
        Token(
            type=TokenType.BRACKET_OPEN,
            prefix=" ",
            token="(",
            spos=(0, 12),
            epos=(0, 13),
            line="with abc as (select * from my_table\n)",
        ),
        Token(
            type=TokenType.TOP_KEYWORD,
            prefix="",
            token="select",
            spos=(0, 13),
            epos=(0, 19),
            line="with abc as (select * from my_table\n)",
        ),
        Token(
            type=TokenType.OPERATOR,
            prefix=" ",
            token="*",
            spos=(0, 20),
            epos=(0, 21),
            line="with abc as (select * from my_table\n)",
        ),
        Token(
            type=TokenType.TOP_KEYWORD,
            prefix=" ",
            token="from",
            spos=(0, 22),
            epos=(0, 26),
            line="with abc as (select * from my_table\n)",
        ),
        Token(
            type=TokenType.NAME,
            prefix=" ",
            token="my_table",
            spos=(0, 27),
            epos=(0, 35),
            line="with abc as (select * from my_table\n)",
        ),
        Token(
            type=TokenType.BRACKET_CLOSE,
            prefix="",
            token=")",
            spos=(0, 35),
            epos=(0, 36),
            line="with abc as (select * from my_table\n)",
        ),
        Token(
            type=TokenType.NEWLINE,
            prefix="",
            token="\n",
            spos=(0, 36),
            epos=(0, 37),
            line="with abc as (select * from my_table\n)",
        ),
    ]

    for token in tokens:
        line.append_token(token)

    assert line.depth == 0
    assert line.change_in_depth == 1
    assert len(line.nodes) == len(tokens)
    assert line.open_brackets == [tokens[0]]
    assert line.first_split == 1
    assert line.first_comma is None

    assert str(line) == source_string
