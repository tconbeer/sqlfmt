from enum import IntEnum
from typing import Callable, List

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
    PRESENCE = 10
    BOOL_NOT = 11
    BOOL_AND = 12
    BOOL_OR = 13
    ON = 14

    @staticmethod
    def tiers() -> List["OperatorPrecedence"]:
        return [
            OperatorPrecedence.OTHER_TIGHT,
            OperatorPrecedence.PRESENCE,
            OperatorPrecedence.ON,
        ]

    @classmethod
    def from_node(cls, node: Node) -> "OperatorPrecedence":
        assert (
            node.is_operator
        ), f"Internal error! {node} is not an operator. Please open an issue"
        return cls._function_lookup(token_type=node.token.type)(node)

    @classmethod
    def _function_lookup(
        cls,
        token_type: TokenType,
    ) -> Callable[[Node], "OperatorPrecedence"]:
        mapping = {
            TokenType.DOUBLE_COLON: lambda x: OperatorPrecedence.DOUBLE_COLON,
            TokenType.AS: lambda x: OperatorPrecedence.AS,
            TokenType.BRACKET_OPEN: lambda x: OperatorPrecedence.SQUARE_BRACKETS,
            TokenType.TIGHT_WORD_OPERATOR: lambda x: OperatorPrecedence.OTHER_TIGHT,
            TokenType.BOOLEAN_OPERATOR: lambda x: OperatorPrecedence.BOOL_OR,
            TokenType.ON: lambda x: OperatorPrecedence.ON,
            TokenType.OPERATOR: cls._from_operator,
            TokenType.WORD_OPERATOR: cls._from_word_operator,
        }
        return mapping.get(token_type, lambda x: OperatorPrecedence.OTHER)

    @staticmethod
    def _from_operator(node: Node) -> "OperatorPrecedence":
        value_mapping = {
            "+": OperatorPrecedence.ADDITION,
            "-": OperatorPrecedence.ADDITION,
            "*": OperatorPrecedence.MULTIPLICATION,
            "/": OperatorPrecedence.MULTIPLICATION,
            "%": OperatorPrecedence.MULTIPLICATION,
            "%%": OperatorPrecedence.MULTIPLICATION,
            "^": OperatorPrecedence.EXPONENT,
            "=": OperatorPrecedence.COMPARATORS,
            "==": OperatorPrecedence.COMPARATORS,
            "!=": OperatorPrecedence.COMPARATORS,
            "<>": OperatorPrecedence.COMPARATORS,
            "<=": OperatorPrecedence.COMPARATORS,
            ">=": OperatorPrecedence.COMPARATORS,
            "~": OperatorPrecedence.MEMBERSHIP,
            "~*": OperatorPrecedence.MEMBERSHIP,
            "!~": OperatorPrecedence.MEMBERSHIP,
            "!~*": OperatorPrecedence.MEMBERSHIP,
        }
        return value_mapping.get(node.value, OperatorPrecedence.OTHER)

    @staticmethod
    def _from_word_operator(node: Node) -> "OperatorPrecedence":
        membership = ["between", "like", "similar"]
        presence = ["is", "null"]
        if any([w in node.value for w in membership]):
            return OperatorPrecedence.MEMBERSHIP
        elif any([w in node.value for w in presence]):
            return OperatorPrecedence.PRESENCE
        else:
            return OperatorPrecedence.OTHER
