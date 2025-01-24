import pytest

from sqlfmt.analyzer import Analyzer
from sqlfmt.operator_precedence import OperatorPrecedence


def test_tiers_sorted() -> None:
    tiers = OperatorPrecedence.tiers()
    assert tiers == sorted(tiers)


@pytest.mark.parametrize(
    "source_string,expected_precedence",
    [
        ("::", OperatorPrecedence.DOUBLE_COLON),
        ("as", OperatorPrecedence.AS),
        ("over", OperatorPrecedence.OTHER_TIGHT),
        ("^", OperatorPrecedence.EXPONENT),
        ("/", OperatorPrecedence.MULTIPLICATION),
        ("%", OperatorPrecedence.MULTIPLICATION),
        ("%%", OperatorPrecedence.MULTIPLICATION),
        ("+", OperatorPrecedence.ADDITION),
        ("-", OperatorPrecedence.ADDITION),
        ("in", OperatorPrecedence.MEMBERSHIP),
        ("not in", OperatorPrecedence.MEMBERSHIP),
        ("like", OperatorPrecedence.MEMBERSHIP),
        ("not like", OperatorPrecedence.MEMBERSHIP),
        ("similar to", OperatorPrecedence.MEMBERSHIP),
        ("between", OperatorPrecedence.MEMBERSHIP),
        ("=", OperatorPrecedence.COMPARATORS),
        ("<=", OperatorPrecedence.COMPARATORS),
        (">=", OperatorPrecedence.COMPARATORS),
        ("<", OperatorPrecedence.COMPARATORS),
        (">", OperatorPrecedence.COMPARATORS),
        ("<>", OperatorPrecedence.COMPARATORS),
        ("!=", OperatorPrecedence.COMPARATORS),
        ("is", OperatorPrecedence.PRESENCE),
        ("notnull", OperatorPrecedence.PRESENCE),
        ("not", OperatorPrecedence.BOOL_NOT),
        ("and", OperatorPrecedence.BOOL_AND),
        ("or", OperatorPrecedence.BOOL_OR),
        ("||/", OperatorPrecedence.OTHER),
        ("<@", OperatorPrecedence.OTHER),
        ("exists", OperatorPrecedence.OTHER),
    ],
)
def test_operator_precedence(
    source_string: str,
    expected_precedence: OperatorPrecedence,
    default_analyzer: Analyzer,
) -> None:
    q = default_analyzer.parse_query(source_string)
    node = q.nodes[0]
    precedence = OperatorPrecedence.from_node(node)
    assert precedence == expected_precedence


@pytest.mark.parametrize(
    "source_string,expected_precedence",
    [
        ("1 *", OperatorPrecedence.MULTIPLICATION),
        ("my_array[", OperatorPrecedence.SQUARE_BRACKETS),
    ],
)
def test_operator_precedence_second_node(
    source_string: str,
    expected_precedence: OperatorPrecedence,
    default_analyzer: Analyzer,
) -> None:
    q = default_analyzer.parse_query(source_string)
    node = q.nodes[1]
    precedence = OperatorPrecedence.from_node(node)
    assert precedence == expected_precedence


def test_operator_precedence_between_and(default_analyzer: Analyzer) -> None:
    source_string = "foo between 1 and 3"
    q = default_analyzer.parse_query(source_string)
    and_node = q.nodes[3]
    assert OperatorPrecedence.from_node(and_node) == OperatorPrecedence.OTHER_TIGHT


@pytest.mark.parametrize("source_string", ["select", "my_table"])
def test_operator_precedence_raises(
    source_string: str, default_analyzer: Analyzer
) -> None:
    q = default_analyzer.parse_query(source_string)
    node = q.nodes[0]
    with pytest.raises(AssertionError):
        _ = OperatorPrecedence.from_node(node)
