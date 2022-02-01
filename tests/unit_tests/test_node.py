import pytest

from sqlfmt.exception import SqlfmtBracketError
from sqlfmt.mode import Mode
from sqlfmt.node import Node
from sqlfmt.token import Token, TokenType
from tests.util import read_test_data


def test_calculate_depth() -> None:
    select_t = Token(
        type=TokenType.UNTERM_KEYWORD,
        prefix="",
        token="select",
        spos=0,
        epos=6,
    )
    select_n = Node.from_token(token=select_t, previous_node=None)
    assert (select_n.depth, select_n.open_brackets) == ((0, 0), [])

    open_paren_t = Token(
        type=TokenType.BRACKET_OPEN,
        prefix="    ",
        token="(",
        spos=8,
        epos=9,
    )
    open_paren_n = Node.from_token(token=open_paren_t, previous_node=select_n)
    assert (open_paren_n.depth, open_paren_n.open_brackets) == ((1, 0), [select_n])

    one_t = Token(
        type=TokenType.NUMBER,
        prefix=" ",
        token="1",
        spos=10,
        epos=11,
    )
    one_n = Node.from_token(token=one_t, previous_node=open_paren_n)
    assert (one_n.depth, one_n.open_brackets) == ((2, 0), [select_n, open_paren_n])

    close_paren_t = Token(
        type=TokenType.BRACKET_CLOSE,
        prefix="",
        token=")",
        spos=11,
        epos=12,
    )
    close_paren_n = Node.from_token(token=close_paren_t, previous_node=one_n)
    assert (close_paren_n.depth, close_paren_n.open_brackets) == ((1, 0), [select_n])


def test_calculate_depth_exception() -> None:
    close_paren = Token(
        type=TokenType.BRACKET_CLOSE,
        prefix="",
        token=")",
        spos=0,
        epos=1,
    )
    with pytest.raises(SqlfmtBracketError):
        _ = Node.from_token(close_paren, previous_node=None)


def test_jinja_depth(default_mode: Mode) -> None:
    source_string, _ = read_test_data("unit_tests/test_line/test_jinja_depth.sql")
    q = default_mode.dialect.initialize_analyzer(
        line_length=default_mode.line_length
    ).parse_query(source_string=source_string)
    expected = [
        (0, 0),  # {{ config(materialized="table") }}
        (0, 0),  # \n
        (0, 0),  # \n
        (0, 0),  # {%- set n = 5 -%}
        (0, 0),  # \n
        (0, 0),  # with
        (1, 0),  # \n
        (1, 0),  # {% for i in range(n) %}
        (1, 1),  # \n
        (1, 1),  # dont_do_this_
        (1, 1),  # {{ i }}
        (1, 1),  # as
        (1, 1),  # (
        (2, 1),  # \n
        (2, 1),  # {% if foo %}
        (2, 2),  # \n
        (2, 2),  # select
        (3, 2),  # \n
        (2, 1),  # {% elif bar %}
        (2, 2),  # \n
        (2, 2),  # select distinct
        (3, 2),  # \n
        (2, 1),  # {% elif baz %}
        (2, 2),  # \n
        (2, 2),  # select top 25
        (3, 2),  # \n
        (2, 1),  # {% else %}
        (2, 2),  # \n
        (2, 2),  # select
        (3, 2),  # \n
        (3, 1),  # {% endif %}
        (3, 1),  # \n
        (3, 1),  # my_col
        (3, 1),  # \n
        (2, 1),  # from
        (3, 1),  # \n
        (3, 1),  # {% if i == qux %}
        (3, 2),  # \n
        (3, 2),  # zip
        (3, 2),  # \n
        (3, 1),  # {% else %}
        (3, 2),  # \n
        (3, 2),  # zap
        (3, 2),  # \n
        (3, 1),  # {% endif %}
        (3, 1),  # \n
        (1, 1),  # )
        (1, 1),  # {% if not loop.last %}
        (1, 2),  # ,
        (1, 1),  # {% endif%}
        (1, 1),  # \n
        (1, 0),  # {% endfor %}
        (1, 0),  # \n
        (1, 0),  # {% for i in range(n) %}
        (1, 1),  # \n
        (0, 1),  # select
        (1, 1),  # \n
        (1, 1),  # *
        (1, 1),  # \n
        (0, 1),  # from
        (1, 1),  # \n
        (1, 1),  # dont_do_this_
        (1, 1),  # {{ i }}
        (1, 1),  # \n
        (1, 1),  # {% if not loop.last -%}
        (1, 2),  # \n
        (0, 2),  # union all
        (1, 2),  # \n
        (0, 1),  # {%- endif %}
        (0, 1),  # \n
        (0, 0),  # {% endfor %}
        (0, 0),  # \n
    ]
    actual = [node.depth for node in q.nodes]
    assert actual == expected


def test_from_token_raises_bracket_error_on_jinja_block_end() -> None:
    t = Token(
        type=TokenType.JINJA_BLOCK_END,
        prefix="",
        token="{% endif %}",
        spos=0,
        epos=11,
    )
    with pytest.raises(SqlfmtBracketError):
        _ = Node.from_token(t, previous_node=None)
