import pytest

from sqlfmt.mode import Mode
from sqlfmt.node_manager import NodeManager
from sqlfmt.token import Token, TokenType
from tests.util import read_test_data


@pytest.fixture
def node_manager(default_mode: Mode) -> NodeManager:
    return NodeManager(default_mode.dialect.case_sensitive_names)


@pytest.mark.parametrize(
    "token,result", [("between", True), ("BETWEEN", True), ("like", False)]
)
def test_is_the_between_operator(
    token: str, result: bool, node_manager: NodeManager
) -> None:
    t = Token(
        type=TokenType.WORD_OPERATOR,
        prefix="",
        token=token,
        spos=0,
        epos=7,
    )
    n = node_manager.create_node(t, previous_node=None)
    assert n.is_the_between_operator is result


@pytest.mark.parametrize(
    "token,result", [("[", True), ("(", False), ("]", False), ("{", False)]
)
def test_is_opening_square_bracket(
    token: str, result: bool, node_manager: NodeManager
) -> None:
    t = Token(
        type=TokenType.BRACKET_OPEN,
        prefix="",
        token=token,
        spos=0,
        epos=1,
    )
    n = node_manager.create_node(t, previous_node=None)
    assert n.is_opening_square_bracket is result


def test_is_the_and_after_the_between_operator(default_mode: Mode) -> None:
    source_string, _ = read_test_data(
        "unit_tests/test_node/test_is_the_and_after_the_between_operator.sql"
    )
    q = default_mode.dialect.initialize_analyzer(
        line_length=default_mode.line_length
    ).parse_query(source_string=source_string)

    and_nodes = [
        node for node in q.nodes if node.token.type == TokenType.BOOLEAN_OPERATOR
    ]
    other_nodes = [
        node for node in q.nodes if node.token.type != TokenType.BOOLEAN_OPERATOR
    ]
    boolean_ands = and_nodes[::2]
    between_ands = and_nodes[1::2]
    assert all([not n.is_the_and_after_the_between_operator for n in boolean_ands])
    assert all([n.is_the_and_after_the_between_operator for n in between_ands])
    assert all([not n.is_the_and_after_the_between_operator for n in other_nodes])
