import re
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
            OperatorPrecedence.EXPONENT,
            OperatorPrecedence.MULTIPLICATION,
            OperatorPrecedence.OTHER,
            OperatorPrecedence.COMPARATORS,
            OperatorPrecedence.BOOL_NOT,
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
            TokenType.ON: lambda x: OperatorPrecedence.ON,
            TokenType.STAR: lambda x: OperatorPrecedence.MULTIPLICATION,
            TokenType.BOOLEAN_OPERATOR: cls._from_boolean,
            TokenType.OPERATOR: cls._from_operator,
            TokenType.WORD_OPERATOR: cls._from_word_operator,
        }
        return mapping.get(token_type, lambda x: OperatorPrecedence.OTHER)

    @staticmethod
    def _from_operator(node: Node) -> "OperatorPrecedence":
        value_mapping = {
            "+": OperatorPrecedence.ADDITION,
            "-": OperatorPrecedence.ADDITION,
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
            ">": OperatorPrecedence.COMPARATORS,
            "<": OperatorPrecedence.COMPARATORS,
            "~": OperatorPrecedence.MEMBERSHIP,
            "~*": OperatorPrecedence.MEMBERSHIP,
            "!~": OperatorPrecedence.MEMBERSHIP,
            "!~*": OperatorPrecedence.MEMBERSHIP,
        }
        return value_mapping.get(node.value, OperatorPrecedence.OTHER)

    @staticmethod
    def _from_word_operator(node: Node) -> "OperatorPrecedence":
        membership = [
            r"(not\s+)?between",
            r"(not\s+)?in",
            r"(not\s+)?i?like(\s+any)?",
            r"(not\s+)?similar\s+to",
            r"(not\s+)?rlike",
            r"(not\s+)?regexp",
        ]
        membership_prog = [
            re.compile(patt, re.IGNORECASE | re.DOTALL) for patt in membership
        ]
        presence = [r"is(\s+not)?", r"isnull", r"notnull"]
        presence_prog = [
            re.compile(patt, re.IGNORECASE | re.DOTALL) for patt in presence
        ]

        if any([prog.match(node.value) for prog in membership_prog]):
            return OperatorPrecedence.MEMBERSHIP
        elif any([prog.match(node.value) for prog in presence_prog]):
            return OperatorPrecedence.PRESENCE
        else:
            return OperatorPrecedence.OTHER

    @staticmethod
    def _from_boolean(node: Node) -> "OperatorPrecedence":
        if node.is_the_and_after_the_between_operator:
            return OperatorPrecedence.OTHER_TIGHT

        value_mapping = {
            "and": OperatorPrecedence.BOOL_AND,
            "or": OperatorPrecedence.BOOL_OR,
            "not": OperatorPrecedence.BOOL_NOT,
        }
        return value_mapping.get(node.value, OperatorPrecedence.BOOL_AND)
