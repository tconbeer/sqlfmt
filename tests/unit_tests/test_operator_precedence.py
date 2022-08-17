from sqlfmt.operator_precedence import OperatorPrecedence


def test_tiers_sorted() -> None:
    tiers = OperatorPrecedence.tiers()
    assert tiers == sorted(tiers)
