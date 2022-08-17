from enum import IntEnum
from typing import List, Optional

from sqlfmt.node import Node
from sqlfmt.token import TokenType


class OperatorPrecedence(IntEnum):
    DOUBLE_COLON = 0
    AS = 1
    SQUARE_BRACKETS = 2
    OTHER_TIGHT = 3
    EXPONENT = 4
    MULTIPLICATION = 5
    ADDITION = 6
    OTHER = 7
    MEMBERSHIP = 8
    COMPARATORS = 9
    BOOL_NOT = 10
    BOOL_AND = 11
    BOOL_OR = 12
    ON = 13

    @staticmethod
    def tiers() -> List["OperatorPrecedence"]:
        return [
            OperatorPrecedence.OTHER_TIGHT,
            OperatorPrecedence.COMPARATORS,
            OperatorPrecedence.ON,
        ]

    @staticmethod
    def _simple_lookup(token_type: TokenType) -> Optional["OperatorPrecedence"]:
        mapping = {
            TokenType.DOUBLE_COLON: OperatorPrecedence.DOUBLE_COLON,
            TokenType.AS: OperatorPrecedence.AS,
            TokenType.TIGHT_WORD_OPERATOR: OperatorPrecedence.OTHER_TIGHT,
            TokenType.BOOLEAN_OPERATOR: OperatorPrecedence.BOOL_OR,
            TokenType.ON: OperatorPrecedence.ON,
        }
        return mapping.get(token_type)

    @classmethod
    def from_node(cls, node: Node) -> "OperatorPrecedence":
        assert (
            node.is_operator
        ), f"Internal error! {node} is not an operator. Please open an issue"
        token_lookup = cls._simple_lookup(token_type=node.token.type)
        if token_lookup is not None:
            return token_lookup
        elif node.is_square_bracket_operator:
            return OperatorPrecedence.SQUARE_BRACKETS
        else:
            return OperatorPrecedence.OTHER
