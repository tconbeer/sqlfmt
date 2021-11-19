from typing import List

import pytest

from sqlfmt.mode import Mode
from sqlfmt.node import Node
from sqlfmt.parser import Query
from sqlfmt.token import Token, TokenType
from tests.util import read_test_data


@pytest.fixture
def source_string() -> str:
    return "with abc as (select * from my_table)\n"


@pytest.fixture
def root_node() -> Node:
    return Node.create_root()


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
    ]
    return tokens


@pytest.fixture
def simple_tree(root_node: Node, tokens: List[Token]) -> Node:
    prev = root_node
    for t in tokens:
        n = Node.from_token(t, previous_node=prev)
        prev = n
    return root_node


def test_simple_tree(
    source_string: str, tokens: List[Token], simple_tree: Node
) -> None:

    nodes = list(simple_tree.traverse_children())

    assert nodes[1].depth == 0
    assert nodes[1].change_in_depth == 1
    assert len(nodes) == len(tokens) + 1  # for root
    assert nodes[1].open_brackets == [tokens[0]]

    assert "".join([str(n) for n in nodes]) + "\n" == " " + source_string

    expected_token_repr = (
        "Token(type=TokenType.UNTERM_KEYWORD, prefix='', token='with', spos=0, epos=4)"
    )
    assert repr(nodes[1].token) == expected_token_repr
    new_token = eval(repr(nodes[1].token))
    assert nodes[1].token == new_token

    expected_node_repr = (
        "Node(\n\ttoken=Token(type=TokenType.UNTERM_KEYWORD, prefix='', token='with',"
        " spos=0, epos=4)',\n\tprevious_node=Node(token=Token(type=TokenType.ROOT,"
        " prefix='', token='', spos=0,"
        " epos=0)),\n\tinherited_depth=0,\n\tdepth=0,\n\tchange_in_depth=1,\n\tprefix='"
        " ',\n\tvalue='with',\n\topen_brackets=[Token(type=TokenType.UNTERM_KEYWORD,"
        " prefix='', token='with', spos=0,"
        " epos=4)],\n\tformatting_disabled=False,"
        "\n\tparent=Node(token=Token(type=TokenType.ROOT,"
        " prefix='', token='', spos=0,"
        " epos=0)),\n\tchildren=[Node(token=Token(type=TokenType.NAME, prefix=' ',"
        " token='abc', spos=4, epos=8)), Node(token=Token(type=TokenType.WORD_OPERATOR,"
        " prefix=' ', token='as', spos=8, epos=11)),"
        " Node(token=Token(type=TokenType.BRACKET_OPEN, prefix=' ', token='(', spos=11,"
        " epos=13)), Node(token=Token(type=TokenType.BRACKET_CLOSE, prefix='',"
        " token=')', spos=35, epos=36))]\n)"
    )
    assert repr(nodes[1]) == expected_node_repr


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
    parsed_string = str(q)
    assert parsed_string == " " + source_string.replace("\n", " ").rstrip() + "\n"


def test_capitalization(default_mode: Mode) -> None:
    source_string = (
        'SELECT A, B, "C", {{ D }}, e, \'f\', \'G\'\nfROM "H"."j" Join I ON k And L\n'
    )
    expected = (
        ' select a, b, "C", {{ D }}, e, \'f\', \'G\' from "H"."j" join i on k and l\n'
    )
    q = Query.from_source(source_string=source_string, mode=default_mode)
    parsed_string = str(q)
    assert parsed_string == expected


def test_formatting_disabled(default_mode: Mode) -> None:
    source_string, _ = read_test_data(
        "unit_tests/test_node/test_formatting_disabled.sql"
    )
    q = Query.from_source(source_string=source_string, mode=default_mode)
    # fmt: off
    expected = [
        False,  # root
        False,  # select
        True,  # -- fmt: off
        True, True, True, True, True, True,  # 1, 2, 3,
        True, True, True, True, True,  # 4, 5, 6
        True,  # -- fmt: on
        False, False,  # from something
        False, False, True,  # join something_else -- fmt: off
        True,  # --fmt: on
        False, False, False, False,  # where format is true
    ]
    # fmt: on
    actual = [node.formatting_disabled for node in q.nodes]
    assert actual == expected
