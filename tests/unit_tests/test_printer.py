from typing import List

import pytest

from sqlfmt.node import Node
from sqlfmt.printer import show_tree
from sqlfmt.token import Token, TokenType


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


def test_simple_tree_printer(simple_tree: Node) -> None:
    printed = show_tree(simple_tree)
    expected = (
        "\nwith\n    abc\n    as\n    (\n        select\n            *\n        from\n "
        "           my_table\n    )"
    )
    assert printed == expected
