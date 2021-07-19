from enum import Enum, auto
from typing import NamedTuple, Tuple


class TokenType(Enum):
    JINJA = auto()
    JINJA_START = auto()
    JINJA_END = auto()
    QUOTED_NAME = auto()
    COMMENT = auto()
    COMMENT_START = auto()
    COMMENT_END = auto()
    STATEMENT_START = auto()
    STATEMENT_END = auto()
    NUMBER = auto()
    BRACKET_OPEN = auto()
    BRACKET_CLOSE = auto()
    DOUBLE_COLON = auto()
    OPERATOR = auto()
    COMMA = auto()
    DOT = auto()
    NEWLINE = auto()
    TOP_KEYWORD = auto()
    NAME = auto()
    ERROR_TOKEN = auto()


class Token(NamedTuple):
    """
    Representation of a syntactic element. Tokens always reference their position
    in the source query, and contain the full text of the line from the source
    query. Tokens are immutable, but some operations replace Tokens in order to
    update their type, prefix, or token in the formatted result.
    """

    type: TokenType
    prefix: str
    token: str
    spos: Tuple[int, int]
    epos: Tuple[int, int]
    line: str
